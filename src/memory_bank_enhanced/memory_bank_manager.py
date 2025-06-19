"""
Enhanced Memory Bank Manager
============================

Main orchestrator for the Memory Bank system, integrating all Phase 3 components:
- Configuration management with environment detection
- Robust error handling and recovery
- Performance monitoring and metrics
- Security validation and protection
- Comprehensive logging integration

This is the crown jewel that brings together Phase 1, 2, and 3 capabilities.
"""

import os
import time
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import asdict

try:
    from ..advanced_logging.factory import LoggerFactory
    from .config_manager import get_memory_bank_config_manager, MemoryBankConfig
    from .error_handler import get_memory_bank_error_handler, memory_bank_safe_execute
    from .performance_monitor import get_memory_bank_performance_monitor, track_memory_bank_performance
    from .security_validator import get_memory_bank_security_validator
except ImportError:
    try:
        from advanced_logging.factory import LoggerFactory
        from memory_bank_enhanced.config_manager import get_memory_bank_config_manager, MemoryBankConfig
        from memory_bank_enhanced.error_handler import get_memory_bank_error_handler, memory_bank_safe_execute
        from memory_bank_enhanced.performance_monitor import get_memory_bank_performance_monitor, track_memory_bank_performance
        from memory_bank_enhanced.security_validator import get_memory_bank_security_validator
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
        from memory_bank_enhanced.config_manager import get_memory_bank_config_manager, MemoryBankConfig
        from memory_bank_enhanced.error_handler import get_memory_bank_error_handler, memory_bank_safe_execute
        from memory_bank_enhanced.performance_monitor import get_memory_bank_performance_monitor, track_memory_bank_performance
        from memory_bank_enhanced.security_validator import get_memory_bank_security_validator


class MemoryBankManager:
    """
    Enhanced Memory Bank Manager
    
    The main interface for all Memory Bank operations with enterprise-grade:
    - Error handling and recovery
    - Performance monitoring
    - Security validation
    - Configuration management
    - Comprehensive logging
    """
    
    def __init__(self, environment: Optional[str] = None):
        """
        Initialize Enhanced Memory Bank Manager
        
        Args:
            environment: Target environment (development, staging, production)
        """
        # Initialize core components
        self.config_manager = get_memory_bank_config_manager()
        self.error_handler = get_memory_bank_error_handler()
        self.performance_monitor = get_memory_bank_performance_monitor()
        self.security_validator = get_memory_bank_security_validator()
        
        # Load configuration for specified environment
        self.config = self.config_manager.load_config(environment)
        
        # Initialize logging
        self.logger_factory = LoggerFactory()
        self.logger = self.logger_factory.get_logger("memory_bank", "manager")
        
        # Initialize storage directories
        self._ensure_directories()
        
        # Log initialization
        self.logger.info(
            "Memory Bank Manager initialized",
            extra={
                'environment': environment,
                'config_summary': self._get_config_summary(),
                'features_enabled': self._get_enabled_features()
            }
        )
    
    @track_memory_bank_performance("read_document")
    @memory_bank_safe_execute("read_document", enable_backup=True)
    def read_document(
        self, 
        document_type: str,
        validate_security: bool = True,
        decrypt_content: bool = True
    ) -> Optional[str]:
        """
        Read a document with full security and performance monitoring
        
        Args:
            document_type: Type of document to read
            validate_security: Whether to validate file security
            decrypt_content: Whether to decrypt content if encrypted
            
        Returns:
            str: Document content or None if not found/error
        """
        tracking_id = self.performance_monitor.start_operation_tracking(
            "read_document",
            context={'document_type': document_type}
        )
        
        try:
            # Get document configuration
            doc_config = self.config_manager.get_document_config(document_type)
            file_path = self.config_manager.get_storage_path(doc_config['filename'])
            
            # Validate file access if security is enabled
            if validate_security and not self.security_validator.validate_file_access(
                str(file_path), "read", {'operation': 'read_document'}
            ):
                self.logger.warning(
                    "File access denied for security reasons",
                    extra={'document_type': document_type, 'file_path': str(file_path)}
                )
                return None
            
            # Check if file exists
            if not file_path.exists():
                self.logger.info(
                    "Document not found",
                    extra={'document_type': document_type, 'file_path': str(file_path)}
                )
                return None
            
            # Validate file integrity
            if self.config.integrity_checks:
                if not self.security_validator.validate_file_integrity(str(file_path)):
                    self.logger.error(
                        "File integrity validation failed",
                        extra={'document_type': document_type, 'file_path': str(file_path)}
                    )
                    return None
            
            # Read file content
            start_time = time.time()
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            read_duration = time.time() - start_time
            
            # Decrypt content if needed
            if decrypt_content and self.config.encryption_enabled:
                content = self.security_validator.decrypt_content(content)
            
            # Track document operation
            self.performance_monitor.track_document_operation(
                document_type=document_type,
                operation="read",
                file_path=str(file_path),
                duration=read_duration,
                success=True
            )
            
            # Log successful read
            if self.config.log_file_operations:
                self.logger.info(
                    "Document read successfully",
                    extra={
                        'document_type': document_type,
                        'file_size': len(content),
                        'duration': read_duration
                    }
                )
            
            self.performance_monitor.end_operation_tracking(tracking_id, success=True)
            return content
            
        except Exception as e:
            # Handle error with specialized error handler
            self.error_handler.handle_file_operation_error(
                "read_document",
                str(file_path) if 'file_path' in locals() else '',
                e,
                document_type
            )
            
            self.performance_monitor.end_operation_tracking(
                tracking_id,
                success=False,
                error_message=str(e)
            )
            
            self.logger.error(
                "Failed to read document",
                extra={
                    'document_type': document_type,
                    'error': str(e)
                }
            )
            return None
    
    @track_memory_bank_performance("write_document")
    @memory_bank_safe_execute("write_document", enable_backup=True)
    def write_document(
        self,
        document_type: str,
        content: str,
        validate_security: bool = True,
        encrypt_content: bool = True,
        create_backup: bool = True
    ) -> bool:
        """
        Write a document with full security validation and backup
        
        Args:
            document_type: Type of document to write
            content: Document content
            validate_security: Whether to validate content security
            encrypt_content: Whether to encrypt content if encryption is enabled
            create_backup: Whether to create backup before writing
            
        Returns:
            bool: True if write successful
        """
        tracking_id = self.performance_monitor.start_operation_tracking(
            "write_document",
            context={'document_type': document_type, 'content_size': len(content)}
        )
        
        try:
            # Validate content security
            if validate_security:
                validation_result = self.security_validator.validate_content(
                    content, document_type, {'operation': 'write_document'}
                )
                
                if not validation_result.is_valid:
                    self.logger.error(
                        "Content security validation failed",
                        extra={
                            'document_type': document_type,
                            'violations': [asdict(v) for v in validation_result.violations]
                        }
                    )
                    self.performance_monitor.end_operation_tracking(
                        tracking_id, success=False, error_message="Security validation failed"
                    )
                    return False
                
                # Use sanitized content if available
                if validation_result.sanitized_content:
                    content = validation_result.sanitized_content
            
            # Get document configuration
            doc_config = self.config_manager.get_document_config(document_type)
            file_path = self.config_manager.get_storage_path(doc_config['filename'])
            
            # Validate file access
            if validate_security and not self.security_validator.validate_file_access(
                str(file_path), "write", {'operation': 'write_document'}
            ):
                self.logger.warning(
                    "File write access denied for security reasons",
                    extra={'document_type': document_type, 'file_path': str(file_path)}
                )
                self.performance_monitor.end_operation_tracking(
                    tracking_id, success=False, error_message="Access denied"
                )
                return False
            
            # Create backup if file exists and backup is enabled
            if create_backup and file_path.exists() and self.config.backup_enabled:
                self._create_backup(document_type, file_path)
            
            # Encrypt content if needed
            if encrypt_content and self.config.encryption_enabled:
                content = self.security_validator.encrypt_content(content)
            
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            start_time = time.time()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            write_duration = time.time() - start_time
            
            # Track document operation
            self.performance_monitor.track_document_operation(
                document_type=document_type,
                operation="write",
                file_path=str(file_path),
                duration=write_duration,
                success=True
            )
            
            # Log successful write
            if self.config.log_file_operations:
                self.logger.info(
                    "Document written successfully",
                    extra={
                        'document_type': document_type,
                        'file_size': len(content),
                        'duration': write_duration,
                        'encrypted': encrypt_content and self.config.encryption_enabled
                    }
                )
            
            self.performance_monitor.end_operation_tracking(tracking_id, success=True)
            return True
            
        except Exception as e:
            # Handle error with specialized error handler
            self.error_handler.handle_file_operation_error(
                "write_document",
                str(file_path) if 'file_path' in locals() else '',
                e,
                document_type
            )
            
            # Create emergency backup if possible
            if 'content' in locals():
                self.error_handler.create_emergency_backup(
                    document_type, content, "write_failure"
                )
            
            self.performance_monitor.end_operation_tracking(
                tracking_id,
                success=False,
                error_message=str(e)
            )
            
            self.logger.error(
                "Failed to write document",
                extra={
                    'document_type': document_type,
                    'error': str(e)
                }
            )
            return False
    
    @track_memory_bank_performance("search_documents")
    @memory_bank_safe_execute("search_documents", enable_backup=False)
    def search_documents(
        self,
        query: str,
        document_types: Optional[List[str]] = None,
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search documents with performance monitoring and error handling
        
        Args:
            query: Search query
            document_types: List of document types to search (None for all)
            max_results: Maximum number of results (None for config default)
            
        Returns:
            List of search results with metadata
        """
        tracking_id = self.performance_monitor.start_operation_tracking(
            "search_documents",
            context={'query': query, 'query_length': len(query)}
        )
        
        try:
            if not self.config.search_enabled:
                self.logger.warning("Search is disabled in configuration")
                return []
            
            # Validate query security
            validation_result = self.security_validator.validate_content(
                query, "search_query", {'operation': 'search_documents'}
            )
            
            if not validation_result.is_valid:
                self.logger.warning(
                    "Search query failed security validation",
                    extra={'query': query, 'violations': len(validation_result.violations)}
                )
                return []
            
            # Get search parameters
            max_results = max_results or self.config.max_results
            document_types = document_types or ['projectbrief', 'productContext', 'systemPatterns', 'techContext', 'activeContext', 'progress']
            
            results = []
            search_start_time = time.time()
            
            # Simple text search implementation (would be replaced with vector search in production)
            for doc_type in document_types:
                content = self.read_document(doc_type, validate_security=False)
                if content and query.lower() in content.lower():
                    # Calculate simple relevance score
                    query_count = content.lower().count(query.lower())
                    relevance = min(query_count / 10.0, 1.0)  # Normalize to 0-1
                    
                    results.append({
                        'document_type': doc_type,
                        'relevance_score': relevance,
                        'snippet': self._extract_snippet(content, query),
                        'file_path': str(self.config_manager.get_storage_path(f"{doc_type}.md"))
                    })
            
            # Sort by relevance and limit results
            results.sort(key=lambda x: x['relevance_score'], reverse=True)
            results = results[:max_results]
            
            search_duration = time.time() - search_start_time
            
            # Log search operation
            if self.config.log_search_queries:
                self.logger.info(
                    "Document search completed",
                    extra={
                        'query': query,
                        'results_count': len(results),
                        'duration': search_duration,
                        'document_types_searched': len(document_types)
                    }
                )
            
            self.performance_monitor.end_operation_tracking(
                tracking_id,
                success=True,
                additional_context={'results_count': len(results)}
            )
            
            return results
            
        except Exception as e:
            # Handle search error
            self.error_handler.handle_search_error(
                "search_documents",
                query,
                e,
                {'document_types': document_types, 'max_results': max_results}
            )
            
            self.performance_monitor.end_operation_tracking(
                tracking_id,
                success=False,
                error_message=str(e)
            )
            
            self.logger.error(
                "Document search failed",
                extra={
                    'query': query,
                    'error': str(e)
                }
            )
            return []
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'timestamp': time.time(),
            'environment': self.config_manager._environment,
            'configuration': self._get_config_summary(),
            'performance': self.performance_monitor.get_performance_summary(hours=1),
            'security': self.security_validator.get_security_summary(hours=1),
            'errors': self.error_handler.get_error_statistics(),
            'storage': self._get_storage_status(),
            'features': self._get_enabled_features()
        }
    
    def perform_maintenance(self) -> Dict[str, Any]:
        """Perform system maintenance tasks"""
        maintenance_results = {
            'timestamp': time.time(),
            'tasks_completed': [],
            'errors': []
        }
        
        try:
            # Cleanup old log files
            if self._cleanup_old_files():
                maintenance_results['tasks_completed'].append('log_cleanup')
            
            # Create scheduled backups
            if self.config.backup_enabled and self._create_scheduled_backups():
                maintenance_results['tasks_completed'].append('scheduled_backup')
            
            # Validate file integrity
            if self.config.integrity_checks and self._validate_all_files():
                maintenance_results['tasks_completed'].append('integrity_check')
            
            self.logger.info(
                "System maintenance completed",
                extra=maintenance_results
            )
            
        except Exception as e:
            maintenance_results['errors'].append(str(e))
            self.logger.error(
                "System maintenance failed",
                extra={'error': str(e)}
            )
        
        return maintenance_results
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            self.config_manager.get_storage_path(),
            self.config_manager.get_backup_path(),
            self.config_manager.get_backup_path("emergency")
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _create_backup(self, document_type: str, file_path: Path) -> bool:
        """Create backup of existing file"""
        try:
            backup_dir = self.config_manager.get_backup_path()
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = int(time.time())
            backup_file = backup_dir / f"{document_type}_{timestamp}.md"
            
            import shutil
            shutil.copy2(file_path, backup_file)
            
            self.logger.debug(
                "Backup created",
                extra={
                    'document_type': document_type,
                    'original_path': str(file_path),
                    'backup_path': str(backup_file)
                }
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Failed to create backup",
                extra={
                    'document_type': document_type,
                    'error': str(e)
                }
            )
            return False
    
    def _extract_snippet(self, content: str, query: str, snippet_length: int = 200) -> str:
        """Extract relevant snippet from content"""
        query_lower = query.lower()
        content_lower = content.lower()
        
        # Find first occurrence of query
        index = content_lower.find(query_lower)
        if index == -1:
            return content[:snippet_length] + "..." if len(content) > snippet_length else content
        
        # Extract snippet around the query
        start = max(0, index - snippet_length // 2)
        end = min(len(content), index + len(query) + snippet_length // 2)
        
        snippet = content[start:end]
        
        # Add ellipsis if needed
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
        
        return snippet
    
    def _get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary for logging"""
        return {
            'storage_path': str(self.config_manager.get_storage_path()),
            'backup_enabled': self.config.backup_enabled,
            'search_enabled': self.config.search_enabled,
            'encryption_enabled': self.config.encryption_enabled,
            'log_level': self.config.log_level
        }
    
    def _get_enabled_features(self) -> Dict[str, bool]:
        """Get enabled features summary"""
        return {
            feature: self.config_manager.is_feature_enabled(feature)
            for feature in ['backup', 'search', 'caching', 'encryption', 'access_logging', 'integrity_checks', 'performance_metrics']
        }
    
    def _get_storage_status(self) -> Dict[str, Any]:
        """Get storage status information"""
        storage_path = self.config_manager.get_storage_path()
        
        # Count files and calculate total size
        file_count = 0
        total_size = 0
        
        if storage_path.exists():
            for file_path in storage_path.rglob("*.md"):
                if file_path.is_file():
                    file_count += 1
                    total_size += file_path.stat().st_size
        
        return {
            'storage_path': str(storage_path),
            'file_count': file_count,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / 1024 / 1024, 2),
            'storage_exists': storage_path.exists()
        }
    
    def _cleanup_old_files(self) -> bool:
        """Cleanup old backup files"""
        try:
            backup_path = self.config_manager.get_backup_path()
            if not backup_path.exists():
                return True
            
            current_time = time.time()
            max_age = self.config.max_file_age
            
            cleaned_count = 0
            for file_path in backup_path.rglob("*"):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age:
                        file_path.unlink()
                        cleaned_count += 1
            
            if cleaned_count > 0:
                self.logger.info(
                    f"Cleaned up {cleaned_count} old backup files"
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"File cleanup failed: {e}")
            return False
    
    def _create_scheduled_backups(self) -> bool:
        """Create scheduled backups of all documents"""
        try:
            document_types = ['projectbrief', 'productContext', 'systemPatterns', 'techContext', 'activeContext', 'progress']
            backup_count = 0
            
            for doc_type in document_types:
                file_path = self.config_manager.get_storage_path(f"{doc_type}.md")
                if file_path.exists():
                    if self._create_backup(doc_type, file_path):
                        backup_count += 1
            
            self.logger.info(f"Created {backup_count} scheduled backups")
            return True
            
        except Exception as e:
            self.logger.error(f"Scheduled backup failed: {e}")
            return False
    
    def _validate_all_files(self) -> bool:
        """Validate integrity of all files"""
        try:
            storage_path = self.config_manager.get_storage_path()
            validation_count = 0
            
            for file_path in storage_path.glob("*.md"):
                if self.security_validator.validate_file_integrity(str(file_path)):
                    validation_count += 1
            
            self.logger.info(f"Validated {validation_count} files")
            return True
            
        except Exception as e:
            self.logger.error(f"File validation failed: {e}")
            return False


# Factory function for easy initialization
def create_memory_bank_manager(environment: Optional[str] = None) -> MemoryBankManager:
    """
    Create a Memory Bank Manager instance with automatic environment detection
    
    Args:
        environment: Target environment (None for auto-detection)
        
    Returns:
        MemoryBankManager: Configured manager instance
    """
    return MemoryBankManager(environment) 