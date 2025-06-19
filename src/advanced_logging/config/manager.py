"""
Configuration Manager - YAML/JSON yapılandırma dosyalarını yönetir
"""
import os
import yaml
import json
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from .environments import EnvironmentDetector
from .validators import ConfigValidator
from .secrets import SecretsManager


class EnvironmentConfig:
    """Environment-specific configuration wrapper"""
    
    def __init__(self, 
                 environment: str,
                 config_data: Dict[str, Any],
                 loaded_from: List[str] = None):
        self.environment = environment
        self.config_data = config_data.copy()
        self.loaded_from = loaded_from or []
        self.loaded_at = datetime.utcnow()
        self.access_count = 0
    
    def get(self, key: str, default: Any = None) -> Any:
        """Configuration değerini al (dot notation destekli)"""
        self.access_count += 1
        return self._get_nested_value(self.config_data, key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Configuration değerini ayarla (dot notation destekli)"""
        self._set_nested_value(self.config_data, key, value)
    
    def _get_nested_value(self, data: Dict[str, Any], key: str, default: Any) -> Any:
        """Nested dictionary'den değer al (logging.level gibi)"""
        keys = key.split('.')
        current = data
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        
        return current
    
    def _set_nested_value(self, data: Dict[str, Any], key: str, value: Any) -> None:
        """Nested dictionary'ye değer ata"""
        keys = key.split('.')
        current = data
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Configuration'ı dictionary olarak döndür"""
        return self.config_data.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Configuration istatistiklerini döndür"""
        return {
            'environment': self.environment,
            'loaded_from': self.loaded_from,
            'loaded_at': self.loaded_at.isoformat(),
            'access_count': self.access_count,
            'config_keys': list(self._flatten_keys(self.config_data))
        }
    
    def _flatten_keys(self, data: Dict[str, Any], prefix: str = '') -> List[str]:
        """Dictionary'deki tüm key'leri flat list olarak döndür"""
        keys = []
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            keys.append(full_key)
            
            if isinstance(value, dict):
                keys.extend(self._flatten_keys(value, full_key))
        
        return keys


class ConfigManager:
    """Ana Configuration Manager"""
    
    def __init__(self, 
                 config_dir: str = 'config/logging',
                 enable_secrets: bool = True):
        
        self.config_dir = Path(config_dir)
        self.enable_secrets = enable_secrets
        
        # Core components
        self.environment_detector = EnvironmentDetector()
        self.validator = ConfigValidator()
        self.secrets_manager = SecretsManager() if enable_secrets else None
        
        # Configuration cache
        self._config_cache: Dict[str, EnvironmentConfig] = {}
        self._cache_lock = threading.RLock()
        
        # Default configuration
        self._default_config = self._get_default_config()
        
        # Initialize
        self._ensure_config_directory()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Varsayılan configuration"""
        return {
            'level': 'INFO',
            'format': 'json',
            'log_dir': 'logs',
            'rotation': {
                'max_size': 100 * 1024 * 1024,  # 100MB
                'backup_count': 10,
                'when': 'midnight',
                'interval': 1
            },
            'handlers': {
                'console': {
                    'enabled': True,
                    'level': 'INFO',
                    'format': 'plain'
                },
                'file': {
                    'enabled': True,
                    'level': 'DEBUG',
                    'format': 'json',
                    'filename': 'app.log'
                },
                'error_file': {
                    'enabled': True,
                    'level': 'ERROR',
                    'format': 'json',
                    'filename': 'errors.log'
                },
                'api_file': {
                    'enabled': True,
                    'level': 'INFO',
                    'format': 'json',
                    'filename': 'api.log'
                }
            },
            'filters': {
                'exclude_components': [],
                'include_only': [],
                'max_message_length': 10000
            },
            'context': {
                'include_request_id': True,
                'include_user_session': True,
                'include_performance': True,
                'include_system_info': False
            }
        }
    
    def _ensure_config_directory(self):
        """Configuration dizinini oluştur"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Default configuration files oluştur (yoksa)
        default_files = {
            'default.yml': self._default_config,
            'development.yml': {
                'level': 'DEBUG',
                'handlers': {
                    'console': {'level': 'DEBUG', 'format': 'plain'},
                    'file': {'level': 'DEBUG', 'format': 'json'}
                }
            },
            'production.yml': {
                'level': 'WARNING',
                'handlers': {
                    'console': {'enabled': False},
                    'file': {'level': 'INFO', 'format': 'json'},
                    'error_file': {'level': 'WARNING'}
                },
                'context': {
                    'include_system_info': True
                }
            }
        }
        
        for filename, config in default_files.items():
            file_path = self.config_dir / filename
            if not file_path.exists():
                self._write_config_file(file_path, config)
    
    def _write_config_file(self, file_path: Path, config: Dict[str, Any]):
        """Configuration dosyasını yaz"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2, allow_unicode=True)
        except Exception as e:
            print(f"Warning: Could not write config file {file_path}: {e}")
    
    def get_logging_config(self, 
                          config_path: Optional[str] = None,
                          environment: Optional[str] = None) -> EnvironmentConfig:
        """Logging configuration'ını al"""
        # Environment detect et
        if environment is None:
            environment = self.environment_detector.detect()
        
        # Cache key oluştur
        cache_key = f"{environment}:{config_path or 'default'}"
        
        with self._cache_lock:
            # Cache'den kontrol et
            if cache_key in self._config_cache:
                return self._config_cache[cache_key]
            
            # Configuration'ı yükle
            config = self._load_configuration(config_path, environment)
            
            # Cache'e kaydet
            self._config_cache[cache_key] = config
            return config
    
    def _load_configuration(self, 
                           config_path: Optional[str],
                           environment: str) -> EnvironmentConfig:
        """Configuration dosyalarını yükle ve merge et"""
        loaded_files = []
        merged_config = self._default_config.copy()
        
        # 1. Default configuration yükle
        default_file = self.config_dir / 'default.yml'
        if default_file.exists():
            default_config = self._load_config_file(default_file)
            if default_config:
                merged_config = self._deep_merge(merged_config, default_config)
                loaded_files.append(str(default_file))
        
        # 2. Environment-specific configuration yükle
        env_file = self.config_dir / f'{environment}.yml'
        if env_file.exists():
            env_config = self._load_config_file(env_file)
            if env_config:
                merged_config = self._deep_merge(merged_config, env_config)
                loaded_files.append(str(env_file))
        
        # 3. Custom configuration yükle (varsa)
        if config_path:
            custom_file = Path(config_path)
            if custom_file.exists():
                custom_config = self._load_config_file(custom_file)
                if custom_config:
                    merged_config = self._deep_merge(merged_config, custom_config)
                    loaded_files.append(str(custom_file))
        
        # 4. Environment variables'dan override'lar
        merged_config = self._apply_env_overrides(merged_config)
        
        # 5. Secrets'ları çöz
        if self.secrets_manager:
            merged_config = self.secrets_manager.resolve_secrets(merged_config)
        
        # 6. Validation
        is_valid, errors = self.validator.validate(merged_config)
        if not is_valid:
            print(f"Configuration validation warnings: {errors}")
        
        return EnvironmentConfig(environment, merged_config, loaded_files)
    
    def _load_config_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Tek bir config dosyasını yükle"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix.lower() in ['.yml', '.yaml']:
                    return yaml.safe_load(f) or {}
                elif file_path.suffix.lower() == '.json':
                    return json.load(f) or {}
                else:
                    print(f"Unsupported config file format: {file_path}")
                    return None
        except Exception as e:
            print(f"Error loading config file {file_path}: {e}")
            return None
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """İki dictionary'yi deep merge et"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Environment variables'dan configuration override'ları uygula"""
        env_mappings = {
            'LOG_LEVEL': 'level',
            'LOG_FORMAT': 'format',
            'LOG_DIR': 'log_dir',
            'LOG_CONSOLE_ENABLED': 'handlers.console.enabled',
            'LOG_CONSOLE_LEVEL': 'handlers.console.level',
            'LOG_FILE_ENABLED': 'handlers.file.enabled',
            'LOG_FILE_LEVEL': 'handlers.file.level'
        }
        
        for env_var, config_key in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Type conversion
                if env_value.lower() in ['true', 'false']:
                    env_value = env_value.lower() == 'true'
                elif env_value.isdigit():
                    env_value = int(env_value)
                
                # Set nested value
                self._set_nested_config_value(config, config_key, env_value)
        
        return config
    
    def _set_nested_config_value(self, config: Dict[str, Any], key: str, value: Any):
        """Nested configuration değerini set et"""
        keys = key.split('.')
        current = config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def reload_all_configs(self):
        """Tüm configuration'ları yeniden yükle"""
        with self._cache_lock:
            self._config_cache.clear()
    
    def get_available_environments(self) -> List[str]:
        """Mevcut environment'ları listele"""
        environments = []
        for config_file in self.config_dir.glob('*.yml'):
            env_name = config_file.stem
            if env_name != 'default':
                environments.append(env_name)
        return environments
    
    def get_statistics(self) -> Dict[str, Any]:
        """Configuration manager istatistikleri"""
        with self._cache_lock:
            cache_stats = {}
            for key, config in self._config_cache.items():
                cache_stats[key] = config.get_statistics()
        
        return {
            'config_directory': str(self.config_dir),
            'secrets_enabled': self.enable_secrets,
            'cached_configurations': len(self._config_cache),
            'available_environments': self.get_available_environments(),
            'cache_details': cache_stats
        }
    
    def close(self):
        """Configuration manager'ı kapat"""
        if self.secrets_manager:
            self.secrets_manager.close() 