"""
Advanced Logging Infrastructure
AI Chrome Chat Manager için kurumsal seviyede loglama sistemi

Bu modül şunları sağlar:
- Structured JSON logging
- Request ID tracking
- Performance monitoring
- Automatic log rotation
- Multi-handler management
"""

from .factory import LoggerFactory, get_logger
from .formatters import JSONFormatter, PlainTextFormatter
from .handlers import RotatingFileHandler, APITrackingHandler
from .middleware import RequestLoggingMiddleware

__version__ = "1.0.0"
__all__ = [
    "LoggerFactory",
    "get_logger", 
    "JSONFormatter",
    "PlainTextFormatter",
    "RotatingFileHandler",
    "APITrackingHandler",
    "RequestLoggingMiddleware"
]

# Varsayılan logger factory instance
_default_factory = None

def configure_logging(config=None):
    """Global logging yapılandırması"""
    global _default_factory
    _default_factory = LoggerFactory(config)
    return _default_factory

def get_default_logger(name: str):
    """Varsayılan factory'den logger al"""
    if _default_factory is None:
        _default_factory = LoggerFactory()
    return _default_factory.get_logger(name) 