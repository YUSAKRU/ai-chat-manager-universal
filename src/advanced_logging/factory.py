"""
LoggerFactory - Merkezi logger oluşturma ve yönetim sistemi
"""
import logging
import logging.handlers
import os
import sys
import threading
from typing import Dict, Optional, Any, Union
from datetime import datetime
import json
from pathlib import Path

from .formatters import JSONFormatter, PlainTextFormatter


class LoggerFactory:
    """
    Merkezi logger factory - tüm logging ihtiyaçlarını karşılar
    
    Features:
    - Structured JSON logging
    - Multiple handler support
    - Configuration-driven setup
    - Thread-safe operations
    - Performance optimized
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = self._load_config(config)
        self._loggers: Dict[str, logging.Logger] = {}
        self._handlers: Dict[str, logging.Handler] = {}
        self._lock = threading.Lock()
        
        # Log dizinini oluştur
        self._ensure_log_directory()
        
        # Temel handler'ları hazırla
        self._setup_base_handlers()
    
    def _load_config(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Yapılandırmayı yükle"""
        default_config = {
            'level': 'INFO',
            'format': 'json',  # json veya plain
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
        
        if config:
            default_config.update(config)
        
        return default_config
    
    def _ensure_log_directory(self):
        """Log dizinini oluştur"""
        log_dir = Path(self.config['log_dir'])
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Archived logs için alt dizin
        archived_dir = log_dir / 'archived'
        archived_dir.mkdir(exist_ok=True)
    
    def _setup_base_handlers(self):
        """Temel handler'ları kur"""
        handlers_config = self.config['handlers']
        
        # Console Handler
        if handlers_config['console']['enabled']:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, handlers_config['console']['level']))
            
            if handlers_config['console']['format'] == 'json':
                console_handler.setFormatter(JSONFormatter())
            else:
                console_handler.setFormatter(PlainTextFormatter())
            
            self._handlers['console'] = console_handler
        
        # File Handler (Ana log dosyası)
        if handlers_config['file']['enabled']:
            file_path = Path(self.config['log_dir']) / handlers_config['file']['filename']
            file_handler = logging.handlers.RotatingFileHandler(
                filename=str(file_path),
                maxBytes=self.config['rotation']['max_size'],
                backupCount=self.config['rotation']['backup_count'],
                encoding='utf-8'
            )
            file_handler.setLevel(getattr(logging, handlers_config['file']['level']))
            
            if handlers_config['file']['format'] == 'json':
                file_handler.setFormatter(JSONFormatter())
            else:
                file_handler.setFormatter(PlainTextFormatter())
                
            self._handlers['file'] = file_handler
        
        # Error File Handler (Sadece error ve critical)
        if handlers_config['error_file']['enabled']:
            error_file_path = Path(self.config['log_dir']) / handlers_config['error_file']['filename']
            error_handler = logging.handlers.RotatingFileHandler(
                filename=str(error_file_path),
                maxBytes=self.config['rotation']['max_size'],
                backupCount=self.config['rotation']['backup_count'],
                encoding='utf-8'
            )
            error_handler.setLevel(getattr(logging, handlers_config['error_file']['level']))
            
            if handlers_config['error_file']['format'] == 'json':
                error_handler.setFormatter(JSONFormatter())
            else:
                error_handler.setFormatter(PlainTextFormatter())
                
            self._handlers['error_file'] = error_handler
        
        # API Tracking Handler (API çağrıları için özel)
        if handlers_config['api_file']['enabled']:
            api_file_path = Path(self.config['log_dir']) / handlers_config['api_file']['filename']
            api_handler = logging.handlers.RotatingFileHandler(
                filename=str(api_file_path),
                maxBytes=self.config['rotation']['max_size'],
                backupCount=self.config['rotation']['backup_count'],
                encoding='utf-8'
            )
            api_handler.setLevel(getattr(logging, handlers_config['api_file']['level']))
            api_handler.setFormatter(JSONFormatter())
            
            # API handler sadece 'api_tracker' component'ini loglar
            api_handler.addFilter(ComponentFilter('api_tracker'))
            
            self._handlers['api_file'] = api_handler
    
    def get_logger(self, name: str, component: Optional[str] = None) -> 'StructuredLogger':
        """
        Logger oluştur veya var olanı döndür
        
        Args:
            name: Logger adı
            component: Bileşen adı (opsiyonel)
            
        Returns:
            StructuredLogger instance
        """
        with self._lock:
            logger_key = f"{name}:{component}" if component else name
            
            if logger_key not in self._loggers:
                # Yeni logger oluştur
                base_logger = logging.getLogger(logger_key)
                base_logger.setLevel(getattr(logging, self.config['level']))
                
                # Handler'ları ekle
                for handler_name, handler in self._handlers.items():
                    if handler_name == 'api_file' and component != 'api_tracker':
                        continue  # API handler sadece api_tracker için
                    base_logger.addHandler(handler)
                
                # Propagation'ı kapat (duplicate logları önlemek için)
                base_logger.propagate = False
                
                # Structured logger wrapper oluştur
                structured_logger = StructuredLogger(
                    base_logger, 
                    component or name,
                    self.config
                )
                
                self._loggers[logger_key] = structured_logger
            
            return self._loggers[logger_key]
    
    def reconfigure(self, new_config: Dict[str, Any]):
        """Runtime'da yapılandırmayı güncelle"""
        with self._lock:
            # Mevcut handler'ları temizle
            for logger in self._loggers.values():
                if hasattr(logger, '_base_logger'):
                    for handler in logger._base_logger.handlers[:]:
                        logger._base_logger.removeHandler(handler)
                        handler.close()
            
            # Handler'ları temizle
            for handler in self._handlers.values():
                handler.close()
            self._handlers.clear()
            
            # Yeni config ile yeniden kur
            self.config.update(new_config)
            self._setup_base_handlers()
            
            # Mevcut logger'ları yeniden yapılandır
            for logger in self._loggers.values():
                if hasattr(logger, '_base_logger'):
                    for handler_name, handler in self._handlers.items():
                        if handler_name == 'api_file' and logger.component != 'api_tracker':
                            continue
                        logger._base_logger.addHandler(handler)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Logger istatistiklerini döndür"""
        return {
            'active_loggers': len(self._loggers),
            'active_handlers': len(self._handlers),
            'config': self.config,
            'log_files': self._get_log_files_info()
        }
    
    def _get_log_files_info(self) -> Dict[str, Any]:
        """Log dosyalarının bilgilerini döndür"""
        log_dir = Path(self.config['log_dir'])
        info = {}
        
        for log_file in log_dir.glob('*.log*'):
            try:
                stat = log_file.stat()
                info[log_file.name] = {
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'exists': True
                }
            except OSError:
                info[log_file.name] = {'exists': False}
        
        return info


class StructuredLogger:
    """
    Structured logging wrapper - JSON formatında zengin loglar oluşturur
    """
    
    def __init__(self, base_logger: logging.Logger, component: str, config: Dict[str, Any]):
        self._base_logger = base_logger
        self.component = component
        self.config = config
        self._context = {}
    
    def set_context(self, **kwargs):
        """Logger context'ini güncelle"""
        self._context.update(kwargs)
    
    def clear_context(self):
        """Context'i temizle"""
        self._context.clear()
    
    def _build_record(self, level: str, message: str, **kwargs) -> Dict[str, Any]:
        """Structured log record oluştur"""
        record = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': level,
            'component': self.component,
            'message': message
        }
        
        # Context bilgilerini ekle
        if self._context:
            record['context'] = self._context.copy()
        
        # Extra data ekle
        if kwargs:
            record['data'] = kwargs
        
        # Request ID ekle (thread local'dan)
        if hasattr(threading.current_thread(), 'request_id'):
            record['request_id'] = threading.current_thread().request_id
        
        # User session ekle
        if hasattr(threading.current_thread(), 'user_session'):
            record['user_session'] = threading.current_thread().user_session
        
        return record
    
    def debug(self, message: str, **kwargs):
        """Debug seviyesinde log"""
        record = self._build_record('DEBUG', message, **kwargs)
        self._base_logger.debug(json.dumps(record, ensure_ascii=False))
    
    def info(self, message: str, **kwargs):
        """Info seviyesinde log"""
        record = self._build_record('INFO', message, **kwargs)
        self._base_logger.info(json.dumps(record, ensure_ascii=False))
    
    def warning(self, message: str, **kwargs):
        """Warning seviyesinde log"""
        record = self._build_record('WARNING', message, **kwargs)
        self._base_logger.warning(json.dumps(record, ensure_ascii=False))
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Error seviyesinde log"""
        if exception:
            kwargs['exception'] = {
                'type': type(exception).__name__,
                'message': str(exception),
                'module': getattr(exception, '__module__', None)
            }
        
        record = self._build_record('ERROR', message, **kwargs)
        self._base_logger.error(json.dumps(record, ensure_ascii=False), exc_info=exception)
    
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Critical seviyesinde log"""
        if exception:
            kwargs['exception'] = {
                'type': type(exception).__name__,
                'message': str(exception),
                'module': getattr(exception, '__module__', None)
            }
        
        record = self._build_record('CRITICAL', message, **kwargs)
        self._base_logger.critical(json.dumps(record, ensure_ascii=False), exc_info=exception)
    
    def log_api_call(self, provider: str, model: str, **metrics):
        """API çağrısı logla"""
        self.info(f"API Call: {provider}/{model}", 
                 provider=provider, 
                 model=model,
                 **metrics)
    
    def log_performance(self, operation: str, duration: float, **metrics):
        """Performans metriği logla"""
        self.info(f"Performance: {operation}",
                 operation=operation,
                 duration=duration,
                 **metrics)
    
    def log_user_action(self, action: str, **details):
        """Kullanıcı eylemini logla"""
        self.info(f"User Action: {action}",
                 action=action,
                 **details)


class ComponentFilter(logging.Filter):
    """Belirli component'leri filtrele"""
    
    def __init__(self, allowed_component: str):
        super().__init__()
        self.allowed_component = allowed_component
    
    def filter(self, record):
        # Record'da component bilgisi var mı kontrol et
        try:
            log_data = json.loads(record.getMessage())
            return log_data.get('component') == self.allowed_component
        except (json.JSONDecodeError, AttributeError):
            return False


# Convenience function
def get_logger(name: str, component: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> StructuredLogger:
    """Hızlı logger oluşturma fonksiyonu"""
    factory = LoggerFactory(config)
    return factory.get_logger(name, component) 