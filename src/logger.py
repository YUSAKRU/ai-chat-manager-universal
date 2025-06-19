import logging
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any
import json
import traceback

class AIChromeChatLogger:
    """AI Chrome Chat Manager için merkezi logging sistemi"""
    
    def __init__(self, log_level: str = "INFO"):
        self.logger = logging.getLogger("ai_chrome_chat_manager")
        self.setup_logger(log_level)
        
        # Hata istatistikleri
        self.error_counts = {
            'total': 0,
            'by_component': {},
            'by_severity': {'error': 0, 'warning': 0, 'critical': 0}
        }
    
    def setup_logger(self, log_level: str):
        """Logger'ı ayarla"""
        # Log seviyesini ayarla
        level = getattr(logging, log_level.upper(), logging.INFO)
        self.logger.setLevel(level)
        
        # Eğer handler'lar zaten eklenmişse, tekrar ekleme
        if self.logger.handlers:
            return
            
        # Formatter - daha detaylı
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (logs klasörü oluştur)
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Ana log dosyası
        log_file = os.path.join(log_dir, f'ai_chrome_chat_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Hata-özel log dosyası
        error_log_file = os.path.join(log_dir, f'errors_{datetime.now().strftime("%Y%m%d")}.log')
        error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(name)s - %(message)s\n%(pathname)s:%(lineno)d\n%(funcName)s()\n---',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        self.logger.addHandler(error_handler)
    
    def info(self, message: str, component: Optional[str] = None, extra_data: Optional[Dict[str, Any]] = None):
        """Info seviyesinde log"""
        formatted_message = self._format_message(message, component, extra_data)
        self.logger.info(formatted_message)
    
    def error(self, message: str, component: Optional[str] = None, exception: Optional[Exception] = None, extra_data: Optional[Dict[str, Any]] = None):
        """Error seviyesinde log"""
        # İstatistikleri güncelle
        self.error_counts['total'] += 1
        self.error_counts['by_severity']['error'] += 1
        if component:
            self.error_counts['by_component'][component] = self.error_counts['by_component'].get(component, 0) + 1
        
        formatted_message = self._format_message(message, component, extra_data)
        
        if exception:
            formatted_message += f"\nException: {str(exception)}"
            formatted_message += f"\nTraceback: {traceback.format_exc()}"
        
        self.logger.error(formatted_message, exc_info=exception is not None)
    
    def warning(self, message: str, component: Optional[str] = None, extra_data: Optional[Dict[str, Any]] = None):
        """Warning seviyesinde log"""
        self.error_counts['by_severity']['warning'] += 1
        if component:
            self.error_counts['by_component'][component] = self.error_counts['by_component'].get(component, 0) + 1
        
        formatted_message = self._format_message(message, component, extra_data)
        self.logger.warning(formatted_message)
    
    def debug(self, message: str, component: Optional[str] = None, extra_data: Optional[Dict[str, Any]] = None):
        """Debug seviyesinde log"""
        formatted_message = self._format_message(message, component, extra_data)
        self.logger.debug(formatted_message)
    
    def critical(self, message: str, component: Optional[str] = None, exception: Optional[Exception] = None, extra_data: Optional[Dict[str, Any]] = None):
        """Critical seviyesinde log"""
        self.error_counts['total'] += 1
        self.error_counts['by_severity']['critical'] += 1
        if component:
            self.error_counts['by_component'][component] = self.error_counts['by_component'].get(component, 0) + 1
        
        formatted_message = self._format_message(message, component, extra_data)
        
        if exception:
            formatted_message += f"\nCRITICAL Exception: {str(exception)}"
            formatted_message += f"\nTraceback: {traceback.format_exc()}"
        
        self.logger.critical(formatted_message, exc_info=exception is not None)
    
    def _format_message(self, message: str, component: Optional[str] = None, extra_data: Optional[Dict[str, Any]] = None) -> str:
        """Log mesajını formatla"""
        formatted = message
        
        if component:
            formatted = f"[{component}] {formatted}"
        
        if extra_data:
            try:
                data_str = json.dumps(extra_data, ensure_ascii=False, indent=2)
                formatted += f"\nExtra Data: {data_str}"
            except Exception:
                formatted += f"\nExtra Data: {str(extra_data)}"
        
        return formatted
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Hata istatistiklerini döndür"""
        return self.error_counts.copy()
    
    def reset_error_stats(self):
        """Hata istatistiklerini sıfırla"""
        self.error_counts = {
            'total': 0,
            'by_component': {},
            'by_severity': {'error': 0, 'warning': 0, 'critical': 0}
        }
    
    def log_system_status(self, status_data: Dict[str, Any]):
        """Sistem durumu logla"""
        self.info("System Status Check", component="system", extra_data=status_data)
    
    def log_api_call(self, provider: str, model: str, input_tokens: int, output_tokens: int, cost: float, response_time: float):
        """API çağrısı logla"""
        api_data = {
            'provider': provider,
            'model': model,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': input_tokens + output_tokens,
            'cost': cost,
            'response_time': response_time
        }
        self.info(f"API Call: {provider}/{model}", component="api_tracker", extra_data=api_data)
    
    def log_user_action(self, action: str, user_data: Optional[Dict[str, Any]] = None):
        """Kullanıcı eylemini logla"""
        self.info(f"User Action: {action}", component="user_tracker", extra_data=user_data)

# Global logger instance
logger = AIChromeChatLogger()

def setup_logger(name: str = "ai_chrome_chat_manager", log_level: str = "INFO"):
    """Standalone setup_logger function for easy import and use"""
    logger_instance = AIChromeChatLogger(log_level)
    return logger_instance

def safe_execute(func, error_message: str, component: str = None, default_return=None):
    """Güvenli fonksiyon çalıştırma wrapper'ı"""
    try:
        return func()
    except Exception as e:
        logger.error(error_message, component=component, exception=e)
        return default_return

def validate_config(config_dict: dict, required_keys: list) -> bool:
    """Konfigürasyon doğrulama"""
    missing_keys = [key for key in required_keys if key not in config_dict]
    if missing_keys:
        logger.error(f"Missing configuration keys: {missing_keys}", component="CONFIG")
        return False
    return True

def log_performance_metric(metric_name: str, value: float, component: str = "performance"):
    """Performans metriği logla"""
    logger.info(f"Performance Metric: {metric_name} = {value}", 
               component=component, 
               extra_data={'metric': metric_name, 'value': value, 'timestamp': datetime.now().isoformat()})

def log_security_event(event_type: str, details: Dict[str, Any]):
    """Güvenlik olayı logla"""
    logger.warning(f"Security Event: {event_type}", 
                  component="security", 
                  extra_data=details)
