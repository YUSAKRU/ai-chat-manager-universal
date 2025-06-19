"""
Configuration Validators - Yapılandırma doğrulama sistemi
"""
import os
from typing import Dict, Any, List, Tuple
from pathlib import Path


class ValidationError(Exception):
    """Configuration validation hatası"""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        super().__init__(message)
        self.field = field
        self.value = value


class ConfigValidator:
    """Configuration validation sistemi"""
    
    def __init__(self):
        self.warnings: List[str] = []
        self.errors: List[str] = []
    
    def validate(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Configuration'ı validate et"""
        self.warnings.clear()
        self.errors.clear()
        
        try:
            self._validate_core_structure(config)
            self._validate_handlers(config.get('handlers', {}))
            self._validate_rotation_settings(config.get('rotation', {}))
            self._validate_security_settings(config)
            
        except ValidationError as e:
            self.errors.append(f"{e.field}: {str(e)}" if e.field else str(e))
        except Exception as e:
            self.errors.append(f"Unexpected validation error: {str(e)}")
        
        is_valid = len(self.errors) == 0
        all_messages = self.errors + self.warnings
        return is_valid, all_messages
    
    def _validate_core_structure(self, config: Dict[str, Any]):
        """Core configuration validation"""
        required_fields = ['level', 'format', 'log_dir', 'handlers']
        
        for field in required_fields:
            if field not in config:
                raise ValidationError(f"Required field '{field}' is missing", field)
        
        # Validate level
        level = config.get('level')
        if level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            raise ValidationError(f"Invalid log level: {level}", 'level', level)
        
        # Validate format
        format_type = config.get('format')
        if format_type not in ['json', 'plain']:
            raise ValidationError(f"Invalid format: {format_type}", 'format', format_type)
        
        # Validate log_dir
        self._validate_directory_path(config.get('log_dir'), 'log_dir')
    
    def _validate_directory_path(self, path: str, field_name: str):
        """Directory path validation"""
        if not path:
            raise ValidationError(f"Directory path cannot be empty", field_name, path)
        
        try:
            path_obj = Path(path)
            
            # Try to create directory if it doesn't exist
            if not path_obj.exists():
                try:
                    path_obj.mkdir(parents=True, exist_ok=True)
                    self.warnings.append(f"Created log directory: {path}")
                except PermissionError:
                    self.warnings.append(f"Cannot create log directory (permission denied): {path}")
            
            # Check write permissions
            elif not os.access(path_obj, os.W_OK):
                self.warnings.append(f"Log directory is not writable: {path}")
                
        except Exception as e:
            raise ValidationError(f"Invalid directory path: {str(e)}", field_name, path)
    
    def _validate_handlers(self, handlers: Dict[str, Any]):
        """Handler configuration validation"""
        if not handlers:
            raise ValidationError("At least one handler must be configured", 'handlers')
        
        valid_handlers = ['console', 'file', 'error_file', 'api_file']
        enabled_handlers = []
        
        for handler_name, handler_config in handlers.items():
            if handler_name not in valid_handlers:
                self.warnings.append(f"Unknown handler type: {handler_name}")
                continue
            
            if not isinstance(handler_config, dict):
                raise ValidationError(f"Handler config must be dict: {handler_name}", 
                                    f'handlers.{handler_name}', handler_config)
            
            if handler_config.get('enabled', True):
                enabled_handlers.append(handler_name)
                
                # Validate level
                level = handler_config.get('level')
                if level and level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                    raise ValidationError(f"Invalid level for {handler_name}: {level}", 
                                        f'handlers.{handler_name}.level', level)
        
        if not enabled_handlers:
            raise ValidationError("At least one handler must be enabled", 'handlers')
    
    def _validate_rotation_settings(self, rotation: Dict[str, Any]):
        """Log rotation settings validation"""
        if not rotation:
            return
        
        max_size = rotation.get('max_size')
        if max_size is not None:
            if not isinstance(max_size, int) or max_size <= 0:
                raise ValidationError("max_size must be positive integer", 
                                    'rotation.max_size', max_size)
            
            if max_size > 1024*1024*1024:  # 1GB
                self.warnings.append(f"Very large max_size: {max_size} bytes")
        
        backup_count = rotation.get('backup_count')
        if backup_count is not None:
            if not isinstance(backup_count, int) or backup_count < 0:
                raise ValidationError("backup_count must be non-negative integer",
                                    'rotation.backup_count', backup_count)
    
    def _validate_security_settings(self, config: Dict[str, Any]):
        """Security-related validation"""
        config_str = str(config).lower()
        sensitive_patterns = ['password', 'secret', 'key', 'token', 'credential']
        
        for pattern in sensitive_patterns:
            if pattern in config_str and pattern not in ['api_key', 'log_key']:
                self.warnings.append(f"Potential sensitive information in config: {pattern}")
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Validation sonuçlarının özeti"""
        return {
            'errors': self.errors,
            'warnings': self.warnings,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'is_valid': len(self.errors) == 0
        } 