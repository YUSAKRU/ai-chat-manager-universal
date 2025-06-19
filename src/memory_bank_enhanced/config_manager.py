"""
Memory Bank Configuration Manager
=================================

Manages Memory Bank-specific configurations using the advanced configuration
system from Phase 2. Provides environment-specific settings, validation,
and runtime configuration management.
"""

import os
import threading
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field

# Import with fallback handling
try:
    from ..advanced_logging.config.manager import ConfigManager
    from ..advanced_logging.config.environments import EnvironmentDetector  
    from ..advanced_logging.config.validators import ConfigValidator
except ImportError:
    try:
        from advanced_logging.config.manager import ConfigManager
        from advanced_logging.config.environments import EnvironmentDetector
        from advanced_logging.config.validators import ConfigValidator
    except ImportError:
        # Create stub classes for standalone operation
        class ConfigManager:
            def load_config(self, *args, **kwargs): return {}
        class EnvironmentDetector:
            def detect(self): 
                return "development"
        class ConfigValidator:
            def validate_config(self, *args, **kwargs):
                class MockResult:
                    is_valid = True
                    errors = []
                return MockResult()


@dataclass
class MemoryBankConfig:
    """Memory Bank configuration data class"""
    
    # Storage Configuration
    storage_type: str = "file_system"
    base_path: str = "memory-bank"
    backup_enabled: bool = True
    backup_path: str = "memory-bank/backups"
    auto_backup_interval: int = 3600
    
    # Document Configuration
    max_document_sizes: Dict[str, int] = field(default_factory=lambda: {
        'projectbrief': 50000,
        'productContext': 100000,
        'systemPatterns': 75000,
        'techContext': 75000,
        'activeContext': 25000,
        'progress': 50000
    })
    
    # Search Configuration
    search_enabled: bool = True
    search_provider: str = "gemini"
    search_model: str = "gemini-2.5-flash"
    embedding_cache: bool = True
    cache_ttl: int = 3600
    max_results: int = 10
    similarity_threshold: float = 0.7
    
    # Performance Configuration
    enable_caching: bool = True
    cache_size: int = 1000  # MB
    preload_documents: bool = False
    concurrent_operations: int = 3
    timeout: int = 30
    
    # Logging Configuration
    log_level: str = "INFO"
    include_performance_metrics: bool = True
    log_file_operations: bool = True
    log_search_queries: bool = True
    log_api_calls: bool = True
    sensitive_data_mask: bool = True
    
    # Security Configuration
    encryption_enabled: bool = False
    backup_encryption: bool = False
    access_logging: bool = True
    integrity_checks: bool = True
    max_file_age: int = 86400  # seconds
    
    # Integration Configuration
    gemini_api_key: Optional[str] = None
    gemini_timeout: int = 30
    gemini_retry_attempts: int = 3
    gemini_rate_limit: int = 60
    
    # Error Handling Configuration
    auto_retry: bool = True
    max_retries: int = 3
    retry_delay: int = 1
    fallback_mode: bool = True
    emergency_backup: bool = True
    corruption_detection: bool = True


class MemoryBankConfigManager:
    """
    Enhanced Memory Bank Configuration Manager
    
    Leverages the Phase 2 configuration system to provide Memory Bank-specific
    configuration management with environment detection, validation, and 
    runtime overrides.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize Memory Bank configuration manager"""
        self._lock = threading.RLock()
        self._config: Optional[MemoryBankConfig] = None
        self._environment = None
        self._config_path = config_path or "config/memory-bank"
        
        # Initialize Phase 2 components
        self._environment_detector = EnvironmentDetector()
        self._config_manager = ConfigManager()
        self._validator = ConfigValidator()
        
        # Memory Bank specific validation schema
        self._memory_bank_schema = {
            'memory_bank': {
                'type': 'object',
                'required': ['storage', 'search', 'performance'],
                'properties': {
                    'storage': {
                        'type': 'object',
                        'required': ['type', 'base_path'],
                        'properties': {
                            'type': {'type': 'string', 'enum': ['file_system', 'database', 'cloud']},
                            'base_path': {'type': 'string'},
                            'backup_enabled': {'type': 'boolean'},
                            'auto_backup_interval': {'type': 'integer', 'minimum': 0}
                        }
                    },
                    'search': {
                        'type': 'object',
                        'required': ['enabled', 'provider'],
                        'properties': {
                            'enabled': {'type': 'boolean'},
                            'provider': {'type': 'string', 'enum': ['gemini', 'openai', 'local']},
                            'model': {'type': 'string'},
                            'similarity_threshold': {'type': 'number', 'minimum': 0, 'maximum': 1}
                        }
                    },
                    'performance': {
                        'type': 'object',
                        'properties': {
                            'enable_caching': {'type': 'boolean'},
                            'cache_size': {'type': 'integer', 'minimum': 10},
                            'concurrent_operations': {'type': 'integer', 'minimum': 1, 'maximum': 10},
                            'timeout': {'type': 'integer', 'minimum': 5}
                        }
                    }
                }
            }
        }
    
    def load_config(self, environment: Optional[str] = None) -> MemoryBankConfig:
        """
        Load Memory Bank configuration for the specified or detected environment
        
        Args:
            environment: Target environment (development, staging, production)
            
        Returns:
            MemoryBankConfig: Loaded and validated configuration
        """
        with self._lock:
            # Detect environment if not specified
            if environment is None:
                try:
                    environment = self._environment_detector.detect()
                except:
                    environment = "development"
            
            self._environment = environment
            
            # Load base configuration
            base_config_path = Path(self._config_path) / "default.yml"
            env_config_path = Path(self._config_path) / f"{environment}.yml"
            
            try:
                # Load and merge configurations
                config_data = self._config_manager.load_config(
                    str(base_config_path),
                    environment_override=str(env_config_path) if env_config_path.exists() else None
                )
                
                # Validate configuration
                validation_result = self._validator.validate_config(
                    config_data, 
                    self._memory_bank_schema
                )
                
                if not validation_result.is_valid:
                    error_msg = f"Memory Bank configuration validation failed: {validation_result.errors}"
                    raise ValueError(error_msg)
                
                # Convert to MemoryBankConfig object
                self._config = self._dict_to_config(config_data.get('memory_bank', {}))
                
                return self._config
                
            except Exception as e:
                # Fallback to default configuration
                fallback_config = MemoryBankConfig()
                self._config = fallback_config
                
                print(f"Warning: Failed to load Memory Bank configuration, using defaults: {e}")
                return fallback_config
    
    def get_config(self) -> MemoryBankConfig:
        """Get current Memory Bank configuration"""
        if self._config is None:
            return self.load_config()
        return self._config
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """
        Update configuration at runtime
        
        Args:
            updates: Dictionary of configuration updates
            
        Returns:
            bool: True if update successful
        """
        with self._lock:
            try:
                if self._config is None:
                    self.load_config()
                
                # Apply updates
                for key, value in updates.items():
                    if hasattr(self._config, key):
                        setattr(self._config, key, value)
                
                return True
                
            except Exception as e:
                print(f"Error updating Memory Bank configuration: {e}")
                return False
    
    def get_storage_path(self, relative_path: str = "") -> Path:
        """Get absolute storage path for Memory Bank files"""
        config = self.get_config()
        base_path = Path(config.base_path)
        
        if relative_path:
            return base_path / relative_path
        return base_path
    
    def get_backup_path(self, relative_path: str = "") -> Path:
        """Get absolute backup path for Memory Bank files"""
        config = self.get_config()
        backup_path = Path(config.backup_path)
        
        if relative_path:
            return backup_path / relative_path
        return backup_path
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a specific feature is enabled"""
        config = self.get_config()
        feature_map = {
            'backup': config.backup_enabled,
            'search': config.search_enabled,
            'caching': config.enable_caching,
            'encryption': config.encryption_enabled,
            'access_logging': config.access_logging,
            'integrity_checks': config.integrity_checks,
            'auto_retry': config.auto_retry,
            'emergency_backup': config.emergency_backup,
            'corruption_detection': config.corruption_detection,
            'performance_metrics': config.include_performance_metrics
        }
        
        return feature_map.get(feature, False)
    
    def get_document_config(self, document_type: str) -> Dict[str, Any]:
        """Get configuration for specific document type"""
        config = self.get_config()
        
        return {
            'max_size': config.max_document_sizes.get(document_type, 50000),
            'filename': f"{document_type}.md",
            'auto_save': True,
            'version_control': document_type != 'activeContext'
        }
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get current environment information"""
        return {
            'environment': self._environment,
            'config_path': self._config_path,
            'storage_path': str(self.get_storage_path()),
            'backup_path': str(self.get_backup_path()),
            'features_enabled': {
                feature: self.is_feature_enabled(feature)
                for feature in ['backup', 'search', 'caching', 'encryption', 'access_logging']
            }
        }
    
    def _dict_to_config(self, config_dict: Dict[str, Any]) -> MemoryBankConfig:
        """Convert configuration dictionary to MemoryBankConfig object"""
        config = MemoryBankConfig()
        
        # Storage configuration
        if 'storage' in config_dict:
            storage = config_dict['storage']
            config.storage_type = storage.get('type', config.storage_type)
            config.base_path = storage.get('base_path', config.base_path)
            config.backup_enabled = storage.get('backup_enabled', config.backup_enabled)
            config.backup_path = storage.get('backup_path', config.backup_path)
            config.auto_backup_interval = storage.get('auto_backup_interval', config.auto_backup_interval)
        
        # Document configuration
        if 'documents' in config_dict:
            documents = config_dict['documents']
            for doc_type, doc_config in documents.items():
                if 'max_size' in doc_config:
                    config.max_document_sizes[doc_type] = doc_config['max_size']
        
        # Search configuration
        if 'search' in config_dict:
            search = config_dict['search']
            config.search_enabled = search.get('enabled', config.search_enabled)
            config.search_provider = search.get('provider', config.search_provider)
            config.search_model = search.get('model', config.search_model)
            config.embedding_cache = search.get('embedding_cache', config.embedding_cache)
            config.cache_ttl = search.get('cache_ttl', config.cache_ttl)
            config.max_results = search.get('max_results', config.max_results)
            config.similarity_threshold = search.get('similarity_threshold', config.similarity_threshold)
        
        # Performance configuration
        if 'performance' in config_dict:
            performance = config_dict['performance']
            config.enable_caching = performance.get('enable_caching', config.enable_caching)
            config.cache_size = performance.get('cache_size', config.cache_size)
            config.preload_documents = performance.get('preload_documents', config.preload_documents)
            config.concurrent_operations = performance.get('concurrent_operations', config.concurrent_operations)
            config.timeout = performance.get('timeout', config.timeout)
        
        # Logging configuration
        if 'logging' in config_dict:
            logging_config = config_dict['logging']
            config.log_level = logging_config.get('level', config.log_level)
            config.include_performance_metrics = logging_config.get('include_performance_metrics', config.include_performance_metrics)
            config.log_file_operations = logging_config.get('log_file_operations', config.log_file_operations)
            config.log_search_queries = logging_config.get('log_search_queries', config.log_search_queries)
            config.log_api_calls = logging_config.get('log_api_calls', config.log_api_calls)
            config.sensitive_data_mask = logging_config.get('sensitive_data_mask', config.sensitive_data_mask)
        
        # Security configuration
        if 'security' in config_dict:
            security = config_dict['security']
            config.encryption_enabled = security.get('encryption_enabled', config.encryption_enabled)
            config.backup_encryption = security.get('backup_encryption', config.backup_encryption)
            config.access_logging = security.get('access_logging', config.access_logging)
            config.integrity_checks = security.get('integrity_checks', config.integrity_checks)
            config.max_file_age = security.get('max_file_age', config.max_file_age)
        
        # Integration configuration
        if 'integrations' in config_dict and 'gemini_api' in config_dict['integrations']:
            gemini = config_dict['integrations']['gemini_api']
            config.gemini_api_key = gemini.get('api_key')
            config.gemini_timeout = gemini.get('timeout', config.gemini_timeout)
            config.gemini_retry_attempts = gemini.get('retry_attempts', config.gemini_retry_attempts)
            config.gemini_rate_limit = gemini.get('rate_limit', config.gemini_rate_limit)
        
        # Error handling configuration
        if 'error_handling' in config_dict:
            error_handling = config_dict['error_handling']
            config.auto_retry = error_handling.get('auto_retry', config.auto_retry)
            config.max_retries = error_handling.get('max_retries', config.max_retries)
            config.retry_delay = error_handling.get('retry_delay', config.retry_delay)
            config.fallback_mode = error_handling.get('fallback_mode', config.fallback_mode)
            config.emergency_backup = error_handling.get('emergency_backup', config.emergency_backup)
            config.corruption_detection = error_handling.get('corruption_detection', config.corruption_detection)
        
        return config


# Global configuration manager instance
_config_manager_instance: Optional[MemoryBankConfigManager] = None
_config_manager_lock = threading.RLock()


def get_memory_bank_config_manager() -> MemoryBankConfigManager:
    """Get global Memory Bank configuration manager instance"""
    global _config_manager_instance
    
    with _config_manager_lock:
        if _config_manager_instance is None:
            _config_manager_instance = MemoryBankConfigManager()
        return _config_manager_instance


def configure_memory_bank_from_config(environment: Optional[str] = None) -> MemoryBankConfig:
    """Configure Memory Bank from configuration files"""
    config_manager = get_memory_bank_config_manager()
    return config_manager.load_config(environment) 