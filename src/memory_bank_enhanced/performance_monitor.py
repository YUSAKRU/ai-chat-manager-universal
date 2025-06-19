"""
Memory Bank Performance Monitor
===============================

Advanced performance monitoring for Memory Bank operations with:
- Real-time operation timing and metrics
- Memory usage tracking  
- API call cost monitoring
- Performance trend analysis
- Integration with Phase 1 logging system
"""

import time
import psutil
import threading
from typing import Dict, List, Optional, Any, Callable
from functools import wraps
from dataclasses import dataclass, field
from collections import defaultdict, deque
from pathlib import Path

try:
    from ..advanced_logging.factory import LoggerFactory
    from .config_manager import get_memory_bank_config_manager
except ImportError:
    try:
        from advanced_logging.factory import LoggerFactory
        from memory_bank_enhanced.config_manager import get_memory_bank_config_manager
    except ImportError:
        # Create stub classes for standalone operation
        class LoggerFactory:
            def get_logger(self, *args): 
                class MockLogger:
                    def debug(self, *args, **kwargs): pass
                    def info(self, *args, **kwargs): pass
                    def warning(self, *args, **kwargs): pass
                    def error(self, *args, **kwargs): pass
                return MockLogger()
        from memory_bank_enhanced.config_manager import get_memory_bank_config_manager


@dataclass
class OperationMetrics:
    """Metrics for a single operation"""
    operation_name: str
    start_time: float
    end_time: float
    duration: float
    memory_before: int  # MB
    memory_after: int   # MB
    memory_peak: int    # MB
    cpu_percent: float
    success: bool
    error_message: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def memory_delta(self) -> int:
        """Memory change during operation"""
        return self.memory_after - self.memory_before


@dataclass
class APICallMetrics:
    """Metrics for API calls"""
    provider: str
    model: str
    operation: str
    tokens_input: int
    tokens_output: int
    cost_estimate: float
    duration: float
    timestamp: float
    success: bool
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentMetrics:
    """Metrics for document operations"""
    document_type: str
    operation: str  # read, write, search, backup
    file_size: int  # bytes
    duration: float
    success: bool
    timestamp: float
    context: Dict[str, Any] = field(default_factory=dict)


class MemoryBankPerformanceMonitor:
    """
    Enhanced Memory Bank Performance Monitor
    
    Provides comprehensive performance monitoring with real-time metrics,
    trend analysis, and integration with the logging system.
    """
    
    def __init__(self):
        """Initialize performance monitor"""
        self.config_manager = get_memory_bank_config_manager()
        self.logger = LoggerFactory().get_logger("memory_bank", "performance")
        
        # Metrics storage
        self.operation_metrics: List[OperationMetrics] = []
        self.api_metrics: List[APICallMetrics] = []
        self.document_metrics: List[DocumentMetrics] = []
        
        # Real-time tracking
        self.active_operations: Dict[str, Dict[str, Any]] = {}
        self.metrics_lock = threading.RLock()
        
        # Performance aggregations
        self.operation_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'count': 0,
            'total_duration': 0.0,
            'success_count': 0,
            'error_count': 0,
            'avg_duration': 0.0,
            'max_duration': 0.0,
            'min_duration': float('inf')
        })
        
        # Recent metrics for trend analysis (last 100 operations)
        self.recent_operations = deque(maxlen=100)
        self.recent_api_calls = deque(maxlen=100)
        
        # System monitoring
        self.process = psutil.Process()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
    
    def start_operation_tracking(
        self, 
        operation_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start tracking a Memory Bank operation
        
        Args:
            operation_name: Name of the operation to track
            context: Additional context information
            
        Returns:
            str: Tracking ID for this operation
        """
        config = self.config_manager.get_config()
        
        if not config.include_performance_metrics:
            return ""
        
        tracking_id = f"{operation_name}_{int(time.time() * 1000000)}"
        
        with self.metrics_lock:
            self.active_operations[tracking_id] = {
                'operation_name': operation_name,
                'start_time': time.time(),
                'start_memory': self.process.memory_info().rss / 1024 / 1024,
                'context': context or {}
            }
        
        self.logger.debug(
            "Started tracking operation",
            extra={
                'operation_name': operation_name,
                'tracking_id': tracking_id,
                'context': context
            }
        )
        
        return tracking_id
    
    def end_operation_tracking(
        self,
        tracking_id: str,
        success: bool = True,
        error_message: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Optional[OperationMetrics]:
        """
        End tracking a Memory Bank operation
        
        Args:
            tracking_id: Tracking ID from start_operation_tracking
            success: Whether the operation succeeded
            error_message: Error message if operation failed
            additional_context: Additional context to add
            
        Returns:
            OperationMetrics: Completed operation metrics
        """
        config = self.config_manager.get_config()
        
        if not config.include_performance_metrics or not tracking_id:
            return None
        
        with self.metrics_lock:
            if tracking_id not in self.active_operations:
                return None
            
            operation_data = self.active_operations.pop(tracking_id)
            
            # Calculate metrics
            end_time = time.time()
            current_memory = self.process.memory_info().rss / 1024 / 1024
            cpu_percent = self.process.cpu_percent()
            
            metrics = OperationMetrics(
                operation_name=operation_data['operation_name'],
                start_time=operation_data['start_time'],
                end_time=end_time,
                duration=end_time - operation_data['start_time'],
                memory_before=int(operation_data['start_memory']),
                memory_after=int(current_memory),
                memory_peak=int(current_memory),  # Simplified - could track peak
                cpu_percent=cpu_percent,
                success=success,
                error_message=error_message,
                context={**operation_data['context'], **(additional_context or {})}
            )
            
            # Store metrics
            self.operation_metrics.append(metrics)
            self.recent_operations.append(metrics)
            
            # Update aggregated stats
            self._update_operation_stats(metrics)
            
            # Log performance metrics
            self._log_operation_metrics(metrics)
            
            return metrics
    
    def track_api_call(
        self,
        provider: str,
        model: str,
        operation: str,
        tokens_input: int,
        tokens_output: int,
        duration: float,
        success: bool,
        context: Optional[Dict[str, Any]] = None
    ) -> APICallMetrics:
        """
        Track an API call for performance monitoring
        
        Args:
            provider: API provider (gemini, openai, etc.)
            model: Model used for the call
            operation: Type of operation (embedding, completion, etc.)
            tokens_input: Number of input tokens
            tokens_output: Number of output tokens
            duration: Call duration in seconds
            success: Whether the call succeeded
            context: Additional context information
            
        Returns:
            APICallMetrics: API call metrics
        """
        config = self.config_manager.get_config()
        
        # Estimate cost (simplified - would use real pricing)
        cost_estimate = self._estimate_api_cost(provider, model, tokens_input, tokens_output)
        
        metrics = APICallMetrics(
            provider=provider,
            model=model,
            operation=operation,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            cost_estimate=cost_estimate,
            duration=duration,
            timestamp=time.time(),
            success=success,
            context=context or {}
        )
        
        with self.metrics_lock:
            self.api_metrics.append(metrics)
            self.recent_api_calls.append(metrics)
        
        # Log API metrics if enabled
        if config.log_api_calls:
            self.logger.info(
                "API call completed",
                extra={
                    'provider': provider,
                    'model': model,
                    'operation': operation,
                    'tokens_input': tokens_input,
                    'tokens_output': tokens_output,
                    'duration': duration,
                    'cost_estimate': cost_estimate,
                    'success': success
                }
            )
        
        return metrics
    
    def track_document_operation(
        self,
        document_type: str,
        operation: str,
        file_path: str,
        duration: float,
        success: bool,
        context: Optional[Dict[str, Any]] = None
    ) -> DocumentMetrics:
        """
        Track a document operation
        
        Args:
            document_type: Type of document (projectbrief, etc.)
            operation: Operation type (read, write, search, backup)
            file_path: Path to the document file
            duration: Operation duration in seconds
            success: Whether the operation succeeded
            context: Additional context information
            
        Returns:
            DocumentMetrics: Document operation metrics
        """
        config = self.config_manager.get_config()
        
        # Get file size
        file_size = 0
        try:
            file_size = Path(file_path).stat().st_size
        except:
            pass
        
        metrics = DocumentMetrics(
            document_type=document_type,
            operation=operation,
            file_size=file_size,
            duration=duration,
            success=success,
            timestamp=time.time(),
            context=context or {}
        )
        
        with self.metrics_lock:
            self.document_metrics.append(metrics)
        
        # Log document operation if enabled
        if config.log_file_operations:
            self.logger.info(
                "Document operation completed",
                extra={
                    'document_type': document_type,
                    'operation': operation,
                    'file_size': file_size,
                    'duration': duration,
                    'success': success,
                    'file_path': file_path
                }
            )
        
        return metrics
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get performance summary for the specified time period
        
        Args:
            hours: Number of hours to include in summary
            
        Returns:
            Dict containing performance summary
        """
        cutoff_time = time.time() - (hours * 3600)
        
        with self.metrics_lock:
            # Filter metrics by time
            recent_ops = [m for m in self.operation_metrics if m.end_time > cutoff_time]
            recent_apis = [m for m in self.api_metrics if m.timestamp > cutoff_time]
            recent_docs = [m for m in self.document_metrics if m.timestamp > cutoff_time]
            
            # Calculate operation statistics
            op_stats = self._calculate_operation_statistics(recent_ops)
            api_stats = self._calculate_api_statistics(recent_apis)
            doc_stats = self._calculate_document_statistics(recent_docs)
            
            # System performance
            current_memory = self.process.memory_info().rss / 1024 / 1024
            memory_growth = current_memory - self.start_memory
            
            return {
                'time_period_hours': hours,
                'operation_statistics': op_stats,
                'api_statistics': api_stats,
                'document_statistics': doc_stats,
                'system_performance': {
                    'current_memory_mb': current_memory,
                    'memory_growth_mb': memory_growth,
                    'cpu_percent': self.process.cpu_percent(),
                    'thread_count': self.process.num_threads()
                },
                'total_metrics': {
                    'operations': len(recent_ops),
                    'api_calls': len(recent_apis),
                    'document_operations': len(recent_docs)
                }
            }
    
    def get_slow_operations(self, threshold_seconds: float = 5.0) -> List[OperationMetrics]:
        """Get operations that took longer than the threshold"""
        with self.metrics_lock:
            return [m for m in self.operation_metrics if m.duration > threshold_seconds]
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of errors and failures"""
        with self.metrics_lock:
            operation_errors = [m for m in self.operation_metrics if not m.success]
            api_errors = [m for m in self.api_metrics if not m.success]
            doc_errors = [m for m in self.document_metrics if not m.success]
            
            return {
                'operation_errors': len(operation_errors),
                'api_errors': len(api_errors),
                'document_errors': len(doc_errors),
                'total_errors': len(operation_errors) + len(api_errors) + len(doc_errors),
                'error_rate': {
                    'operations': len(operation_errors) / max(1, len(self.operation_metrics)),
                    'api_calls': len(api_errors) / max(1, len(self.api_metrics)),
                    'documents': len(doc_errors) / max(1, len(self.document_metrics))
                }
            }
    
    def _update_operation_stats(self, metrics: OperationMetrics):
        """Update aggregated operation statistics"""
        stats = self.operation_stats[metrics.operation_name]
        
        stats['count'] += 1
        stats['total_duration'] += metrics.duration
        
        if metrics.success:
            stats['success_count'] += 1
        else:
            stats['error_count'] += 1
        
        stats['avg_duration'] = stats['total_duration'] / stats['count']
        stats['max_duration'] = max(stats['max_duration'], metrics.duration)
        stats['min_duration'] = min(stats['min_duration'], metrics.duration)
    
    def _log_operation_metrics(self, metrics: OperationMetrics):
        """Log operation metrics with appropriate level"""
        extra_data = {
            'operation_name': metrics.operation_name,
            'duration': metrics.duration,
            'memory_delta': metrics.memory_delta,
            'cpu_percent': metrics.cpu_percent,
            'success': metrics.success
        }
        
        # Log slow operations as warnings
        if metrics.duration > 5.0:
            self.logger.warning(
                f"Slow operation detected: {metrics.operation_name}",
                extra=extra_data
            )
        elif not metrics.success:
            self.logger.error(
                f"Operation failed: {metrics.operation_name}",
                extra={**extra_data, 'error_message': metrics.error_message}
            )
        else:
            self.logger.info(
                f"Operation completed: {metrics.operation_name}",
                extra=extra_data
            )
    
    def _estimate_api_cost(
        self, 
        provider: str, 
        model: str, 
        tokens_input: int, 
        tokens_output: int
    ) -> float:
        """Estimate API call cost (simplified pricing)"""
        # Simplified cost estimation - would use real pricing in production
        pricing = {
            'gemini': {
                'gemini-2.5-flash': {'input': 0.00002, 'output': 0.00006},
                'gemini-2.5-pro': {'input': 0.00025, 'output': 0.00075}
            }
        }
        
        if provider in pricing and model in pricing[provider]:
            rates = pricing[provider][model]
            return (tokens_input * rates['input']) + (tokens_output * rates['output'])
        
        return 0.0
    
    def _calculate_operation_statistics(self, operations: List[OperationMetrics]) -> Dict[str, Any]:
        """Calculate statistics for operations"""
        if not operations:
            return {}
        
        total_ops = len(operations)
        successful_ops = sum(1 for op in operations if op.success)
        total_duration = sum(op.duration for op in operations)
        
        return {
            'total_operations': total_ops,
            'successful_operations': successful_ops,
            'failed_operations': total_ops - successful_ops,
            'success_rate': successful_ops / total_ops,
            'average_duration': total_duration / total_ops,
            'total_duration': total_duration,
            'operations_by_type': self._group_by_attribute(operations, 'operation_name')
        }
    
    def _calculate_api_statistics(self, api_calls: List[APICallMetrics]) -> Dict[str, Any]:
        """Calculate statistics for API calls"""
        if not api_calls:
            return {}
        
        total_calls = len(api_calls)
        successful_calls = sum(1 for call in api_calls if call.success)
        total_cost = sum(call.cost_estimate for call in api_calls)
        total_tokens_in = sum(call.tokens_input for call in api_calls)
        total_tokens_out = sum(call.tokens_output for call in api_calls)
        
        return {
            'total_api_calls': total_calls,
            'successful_calls': successful_calls,
            'failed_calls': total_calls - successful_calls,
            'success_rate': successful_calls / total_calls,
            'total_cost_estimate': total_cost,
            'total_tokens_input': total_tokens_in,
            'total_tokens_output': total_tokens_out,
            'calls_by_provider': self._group_by_attribute(api_calls, 'provider'),
            'calls_by_model': self._group_by_attribute(api_calls, 'model')
        }
    
    def _calculate_document_statistics(self, doc_ops: List[DocumentMetrics]) -> Dict[str, Any]:
        """Calculate statistics for document operations"""
        if not doc_ops:
            return {}
        
        total_ops = len(doc_ops)
        successful_ops = sum(1 for op in doc_ops if op.success)
        total_size = sum(op.file_size for op in doc_ops)
        
        return {
            'total_document_operations': total_ops,
            'successful_operations': successful_ops,
            'failed_operations': total_ops - successful_ops,
            'success_rate': successful_ops / total_ops,
            'total_bytes_processed': total_size,
            'operations_by_type': self._group_by_attribute(doc_ops, 'operation'),
            'operations_by_document': self._group_by_attribute(doc_ops, 'document_type')
        }
    
    def _group_by_attribute(self, items: List[Any], attribute: str) -> Dict[str, int]:
        """Group items by attribute and count"""
        groups = defaultdict(int)
        for item in items:
            groups[getattr(item, attribute)] += 1
        return dict(groups)


# Decorator for automatic performance tracking
def track_memory_bank_performance(operation_name: str):
    """
    Decorator to automatically track performance of Memory Bank operations
    
    Args:
        operation_name: Name of the operation to track
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            monitor = get_memory_bank_performance_monitor()
            tracking_id = monitor.start_operation_tracking(
                operation_name,
                context={'args_count': len(args), 'kwargs_keys': list(kwargs.keys())}
            )
            
            try:
                result = func(*args, **kwargs)
                monitor.end_operation_tracking(tracking_id, success=True)
                return result
            except Exception as e:
                monitor.end_operation_tracking(
                    tracking_id,
                    success=False,
                    error_message=str(e)
                )
                raise
        
        return wrapper
    return decorator


# Global performance monitor instance
_performance_monitor_instance: Optional[MemoryBankPerformanceMonitor] = None
_monitor_lock = threading.RLock()


def get_memory_bank_performance_monitor() -> MemoryBankPerformanceMonitor:
    """Get global Memory Bank performance monitor instance"""
    global _performance_monitor_instance
    
    with _monitor_lock:
        if _performance_monitor_instance is None:
            _performance_monitor_instance = MemoryBankPerformanceMonitor()
        return _performance_monitor_instance 