"""
Advanced Logging Configuration Management
Kurumsal seviyede yapılandırma yönetimi sistemi
"""

from .manager import ConfigManager, EnvironmentConfig
from .validators import ConfigValidator, ValidationError
from .secrets import SecretsManager
from .environments import EnvironmentDetector

__version__ = "1.0.0"
__all__ = [
    "ConfigManager",
    "EnvironmentConfig", 
    "ConfigValidator",
    "ValidationError",
    "SecretsManager",
    "EnvironmentDetector"
]

# Global config manager instance
_global_config_manager = None

def get_config_manager() -> ConfigManager:
    """Global configuration manager'ı döndür"""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager()
    return _global_config_manager

def configure_logging_from_config(config_path: str = None, environment: str = None):
    """Configuration dosyasından logging sistemini yapılandır"""
    config_manager = get_config_manager()
    logging_config = config_manager.get_logging_config(config_path, environment)
    
    from ..factory import LoggerFactory
    factory = LoggerFactory(logging_config)
    return factory 