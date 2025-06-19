"""
Memory Bank Error Handler
=========================

Specialized error handling for Memory Bank operations, leveraging the 
Phase 1 error handling infrastructure with Memory Bank-specific scenarios,
recovery strategies, and monitoring.
"""

import os
import time
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, Callable, Union, List
from functools import wraps
from dataclasses import dataclass
from enum import Enum

try:
    from ..central_error_handler import safe_execute, async_safe_execute, ErrorCategory, ErrorSeverity
    from .config_manager import get_memory_bank_config_manager
except ImportError:
    try:
        from central_error_handler import safe_execute, async_safe_execute, ErrorCategory, ErrorSeverity
        from memory_bank_enhanced.config_manager import get_memory_bank_config_manager
    except ImportError:
        # Create stub classes for standalone operation
        def safe_execute(*args, **kwargs):
            def decorator(func):
                return func
            return decorator
        
        def async_safe_execute(*args, **kwargs):
            def decorator(func):
                return func  
            return decorator
        
        class ErrorCategory:
            MEMORY_BANK = "memory_bank"
        
        class ErrorSeverity:
            LOW = "low"
            MEDIUM = "medium"
            HIGH = "high"
        
        from memory_bank_enhanced.config_manager import get_memory_bank_config_manager


class MemoryBankErrorType(Enum):
    """Memory Bank specific error types"""
    FILE_NOT_FOUND = "file_not_found"
    FILE_CORRUPTED = "file_corrupted"
    PERMISSION_DENIED = "permission_denied"
    DISK_FULL = "disk_full"
    BACKUP_FAILED = "backup_failed"
    SEARCH_FAILED = "search_failed"
    CONFIG_INVALID = "config_invalid"
    API_LIMIT_EXCEEDED = "api_limit_exceeded"
    DOCUMENT_TOO_LARGE = "document_too_large"
    ENCODING_ERROR = "encoding_error"
    TIMEOUT_ERROR = "timeout_error"
    INTEGRITY_CHECK_FAILED = "integrity_check_failed"


@dataclass
class MemoryBankError:
    """Memory Bank error information"""
    error_type: MemoryBankErrorType
    message: str
    operation: str
    document_type: Optional[str] = None
    file_path: Optional[str] = None
    timestamp: float = 0.0
    context: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class MemoryBankErrorHandler:
    """
    Enhanced Memory Bank Error Handler
    
    Provides specialized error handling for Memory Bank operations with:
    - Automatic recovery strategies
    - Backup and restore mechanisms
    - Detailed error context and logging
    - Integration with Phase 1 error handling
    """
    
    def __init__(self):
        """Initialize Memory Bank error handler"""
        self.config_manager = get_memory_bank_config_manager()
        self.error_history: List[MemoryBankError] = []
        self.recovery_attempts: Dict[str, int] = {}
        
    def handle_file_operation_error(
        self, 
        operation: str,
        file_path: str,
        error: Exception,
        document_type: Optional[str] = None
    ) -> Optional[Any]:
        """
        Handle file operation errors with automatic recovery
        
        Args:
            operation: Name of the failed operation
            file_path: Path of the file that caused the error
            error: The original exception
            document_type: Type of document (if applicable)
            
        Returns:
            Recovery result or None if recovery failed
        """
        config = self.config_manager.get_config()
        
        # Determine error type
        error_type = self._classify_file_error(error)
        
        # Create error record
        memory_error = MemoryBankError(
            error_type=error_type,
            message=str(error),
            operation=operation,
            document_type=document_type,
            file_path=file_path,
            context={
                'file_exists': Path(file_path).exists(),
                'file_size': Path(file_path).stat().st_size if Path(file_path).exists() else 0,
                'parent_dir_exists': Path(file_path).parent.exists(),
                'disk_space': self._get_disk_space(file_path)
            }
        )
        
        self.error_history.append(memory_error)
        
        # Attempt recovery if enabled
        if config.auto_retry:
            return self._attempt_recovery(memory_error)
        
        return None
    
    def handle_search_error(
        self,
        operation: str,
        query: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        Handle search operation errors
        
        Args:
            operation: Search operation name
            query: Search query that failed
            error: The original exception
            context: Additional context information
            
        Returns:
            Recovery result or None if recovery failed
        """
        config = self.config_manager.get_config()
        
        memory_error = MemoryBankError(
            error_type=MemoryBankErrorType.SEARCH_FAILED,
            message=str(error),
            operation=operation,
            context={
                'query': query,
                'query_length': len(query),
                'search_provider': config.search_provider,
                'search_model': config.search_model,
                **(context or {})
            }
        )
        
        self.error_history.append(memory_error)
        
        # Attempt fallback search strategies
        return self._attempt_search_recovery(memory_error, query)
    
    def handle_api_error(
        self,
        operation: str,
        api_provider: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        Handle API-related errors
        
        Args:
            operation: API operation name
            api_provider: API provider (e.g., 'gemini', 'openai')
            error: The original exception
            context: Additional context information
            
        Returns:
            Recovery result or None if recovery failed
        """
        config = self.config_manager.get_config()
        
        # Determine if it's a rate limit error
        error_type = MemoryBankErrorType.API_LIMIT_EXCEEDED
        if "rate limit" not in str(error).lower():
            error_type = MemoryBankErrorType.SEARCH_FAILED
        
        memory_error = MemoryBankError(
            error_type=error_type,
            message=str(error),
            operation=operation,
            context={
                'api_provider': api_provider,
                'rate_limit': config.gemini_rate_limit,
                'timeout': config.gemini_timeout,
                **(context or {})
            }
        )
        
        self.error_history.append(memory_error)
        
        # Implement backoff strategy for rate limits
        if error_type == MemoryBankErrorType.API_LIMIT_EXCEEDED:
            return self._handle_rate_limit_error(memory_error)
        
        return None
    
    def create_emergency_backup(
        self, 
        document_type: str, 
        content: str,
        reason: str = "emergency_backup"
    ) -> bool:
        """
        Create emergency backup of document content
        
        Args:
            document_type: Type of document
            content: Document content to backup
            reason: Reason for emergency backup
            
        Returns:
            bool: True if backup successful
        """
        try:
            config = self.config_manager.get_config()
            
            if not config.emergency_backup:
                return False
            
            # Create emergency backup directory
            backup_dir = self.config_manager.get_backup_path("emergency")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Create backup file with timestamp
            timestamp = int(time.time())
            backup_file = backup_dir / f"{document_type}_{reason}_{timestamp}.md"
            
            # Write backup content
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            # Emergency backup failed - log but don't raise
            print(f"Emergency backup failed: {e}")
            return False
    
    def validate_document_integrity(
        self, 
        file_path: str,
        expected_size: Optional[int] = None
    ) -> bool:
        """
        Validate document integrity
        
        Args:
            file_path: Path to document file
            expected_size: Expected file size (optional)
            
        Returns:
            bool: True if document is valid
        """
        config = self.config_manager.get_config()
        
        if not config.corruption_detection:
            return True
        
        try:
            path = Path(file_path)
            
            # Check if file exists
            if not path.exists():
                return False
            
            # Check file size
            file_size = path.stat().st_size
            
            if expected_size and abs(file_size - expected_size) > expected_size * 0.1:
                # File size differs by more than 10%
                return False
            
            # Try to read file content
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic content validation
            if len(content.strip()) == 0:
                return False
            
            # Check for common corruption indicators
            corruption_indicators = [
                '\x00',  # Null bytes
                '\ufffd',  # Replacement character
            ]
            
            for indicator in corruption_indicators:
                if indicator in content:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics and trends"""
        if not self.error_history:
            return {'total_errors': 0}
        
        # Count errors by type
        error_counts = {}
        recent_errors = []
        current_time = time.time()
        
        for error in self.error_history:
            error_type = error.error_type.value
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
            
            # Errors in last hour
            if current_time - error.timestamp < 3600:
                recent_errors.append(error)
        
        # Most common error types
        most_common = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'total_errors': len(self.error_history),
            'recent_errors': len(recent_errors),
            'error_counts': error_counts,
            'most_common_errors': most_common[:5],
            'recovery_attempts': sum(self.recovery_attempts.values()),
        }
    
    def _classify_file_error(self, error: Exception) -> MemoryBankErrorType:
        """Classify file operation error by type"""
        error_str = str(error).lower()
        
        if "no such file" in error_str or "file not found" in error_str:
            return MemoryBankErrorType.FILE_NOT_FOUND
        elif "permission denied" in error_str or "access denied" in error_str:
            return MemoryBankErrorType.PERMISSION_DENIED
        elif "no space left" in error_str or "disk full" in error_str:
            return MemoryBankErrorType.DISK_FULL
        elif "codec" in error_str or "encoding" in error_str:
            return MemoryBankErrorType.ENCODING_ERROR
        elif "timeout" in error_str:
            return MemoryBankErrorType.TIMEOUT_ERROR
        else:
            return MemoryBankErrorType.FILE_CORRUPTED
    
    def _attempt_recovery(self, memory_error: MemoryBankError) -> Optional[Any]:
        """Attempt to recover from file operation error"""
        config = self.config_manager.get_config()
        
        # Track recovery attempts
        recovery_key = f"{memory_error.operation}_{memory_error.file_path}"
        self.recovery_attempts[recovery_key] = self.recovery_attempts.get(recovery_key, 0) + 1
        
        if self.recovery_attempts[recovery_key] > config.max_retries:
            return None
        
        # Recovery strategies by error type
        if memory_error.error_type == MemoryBankErrorType.FILE_NOT_FOUND:
            return self._recover_missing_file(memory_error)
        elif memory_error.error_type == MemoryBankErrorType.PERMISSION_DENIED:
            return self._recover_permission_error(memory_error)
        elif memory_error.error_type == MemoryBankErrorType.DISK_FULL:
            return self._recover_disk_full_error(memory_error)
        elif memory_error.error_type == MemoryBankErrorType.FILE_CORRUPTED:
            return self._recover_corrupted_file(memory_error)
        
        return None
    
    def _recover_missing_file(self, memory_error: MemoryBankError) -> Optional[Any]:
        """Recover from missing file error"""
        if not memory_error.file_path:
            return None
        
        file_path = Path(memory_error.file_path)
        
        # Create parent directory if missing
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Try to restore from backup
        backup_path = self.config_manager.get_backup_path(file_path.name)
        if backup_path.exists():
            try:
                shutil.copy2(backup_path, file_path)
                return str(file_path)
            except Exception:
                pass
        
        # Create empty file as last resort
        try:
            file_path.touch()
            return str(file_path)
        except Exception:
            return None
    
    def _recover_permission_error(self, memory_error: MemoryBankError) -> Optional[Any]:
        """Recover from permission error"""
        if not memory_error.file_path:
            return None
        
        file_path = Path(memory_error.file_path)
        
        try:
            # Try to change file permissions
            file_path.chmod(0o666)
            return str(file_path)
        except Exception:
            return None
    
    def _recover_disk_full_error(self, memory_error: MemoryBankError) -> Optional[Any]:
        """Recover from disk full error"""
        # Try to free up space by cleaning old logs
        try:
            logs_dir = Path("logs/archived")
            if logs_dir.exists():
                # Remove files older than 30 days
                current_time = time.time()
                for file_path in logs_dir.glob("*"):
                    if file_path.is_file():
                        file_age = current_time - file_path.stat().st_mtime
                        if file_age > 30 * 24 * 3600:  # 30 days
                            file_path.unlink()
            
            return "disk_cleanup_attempted"
        except Exception:
            return None
    
    def _recover_corrupted_file(self, memory_error: MemoryBankError) -> Optional[Any]:
        """Recover from corrupted file error"""
        if not memory_error.file_path:
            return None
        
        file_path = Path(memory_error.file_path)
        
        # Try to restore from backup
        backup_path = self.config_manager.get_backup_path(file_path.name)
        if backup_path.exists():
            try:
                shutil.copy2(backup_path, file_path)
                return str(file_path)
            except Exception:
                pass
        
        return None
    
    def _attempt_search_recovery(self, memory_error: MemoryBankError, query: str) -> Optional[Any]:
        """Attempt to recover from search error"""
        config = self.config_manager.get_config()
        
        # Fallback strategies for search
        fallback_strategies = [
            lambda q: q.lower(),  # Convert to lowercase
            lambda q: q[:100],    # Truncate query
            lambda q: ' '.join(q.split()[:10]),  # Limit to 10 words
        ]
        
        for strategy in fallback_strategies:
            try:
                modified_query = strategy(query)
                if modified_query != query:
                    # This would integrate with actual search implementation
                    # For now, return the modified query as a signal
                    return {'fallback_query': modified_query}
            except Exception:
                continue
        
        return None
    
    def _handle_rate_limit_error(self, memory_error: MemoryBankError) -> Optional[Any]:
        """Handle rate limit error with exponential backoff"""
        config = self.config_manager.get_config()
        
        # Calculate backoff time
        attempt = self.recovery_attempts.get(memory_error.operation, 0)
        backoff_time = min(2 ** attempt, 60)  # Max 60 seconds
        
        return {
            'backoff_time': backoff_time,
            'suggested_action': 'retry_after_backoff'
        }
    
    def _get_disk_space(self, file_path: str) -> Dict[str, int]:
        """Get disk space information"""
        try:
            statvfs = os.statvfs(Path(file_path).parent)
            free_space = statvfs.f_frsize * statvfs.f_available
            total_space = statvfs.f_frsize * statvfs.f_blocks
            
            return {
                'free_bytes': free_space,
                'total_bytes': total_space,
                'used_percentage': int((1 - free_space / total_space) * 100)
            }
        except:
            return {'free_bytes': 0, 'total_bytes': 0, 'used_percentage': 100}


# Decorator for Memory Bank operations
def memory_bank_safe_execute(
    operation_name: str,
    document_type: Optional[str] = None,
    enable_backup: bool = True
):
    """
    Decorator for safe Memory Bank operations with specialized error handling
    
    Args:
        operation_name: Name of the operation
        document_type: Type of document being processed
        enable_backup: Whether to create backups on errors
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = MemoryBankErrorHandler()
            
            try:
                # Execute the operation with Phase 1 error handling
                return safe_execute(
                    operation=func,
                    context={
                        'operation_name': operation_name,
                        'document_type': document_type,
                        'args': args,
                        'kwargs': kwargs
                    },
                    category=ErrorCategory.MEMORY_BANK,
                    severity=ErrorSeverity.MEDIUM
                )(*args, **kwargs)
                
            except Exception as e:
                # Handle with Memory Bank specific error handling
                if 'file_path' in kwargs:
                    return error_handler.handle_file_operation_error(
                        operation_name, 
                        kwargs['file_path'], 
                        e, 
                        document_type
                    )
                elif 'query' in kwargs:
                    return error_handler.handle_search_error(
                        operation_name,
                        kwargs['query'],
                        e
                    )
                else:
                    # Generic error handling
                    memory_error = MemoryBankError(
                        error_type=MemoryBankErrorType.CONFIG_INVALID,
                        message=str(e),
                        operation=operation_name,
                        document_type=document_type
                    )
                    error_handler.error_history.append(memory_error)
                    raise
        
        return wrapper
    return decorator


# Global error handler instance
_error_handler_instance: Optional[MemoryBankErrorHandler] = None


def get_memory_bank_error_handler() -> MemoryBankErrorHandler:
    """Get global Memory Bank error handler instance"""
    global _error_handler_instance
    
    if _error_handler_instance is None:
        _error_handler_instance = MemoryBankErrorHandler()
    
    return _error_handler_instance 