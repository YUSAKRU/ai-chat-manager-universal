import logging
import sys
import os
from datetime import datetime
from typing import Optional

class AIChromeChatLogger:
    """AI Chrome Chat Manager için merkezi logging sistemi"""
    
    def __init__(self, log_level: str = "INFO"):
        self.logger = logging.getLogger("ai_chrome_chat_manager")
        self.setup_logger(log_level)
    
    def setup_logger(self, log_level: str):
        """Logger'ı ayarla"""
        # Log seviyesini ayarla
        level = getattr(logging, log_level.upper(), logging.INFO)
        self.logger.setLevel(level)
        
        # Eğer handler'lar zaten eklenmişse, tekrar ekleme
        if self.logger.handlers:
            return
            
        # Formatter
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
        
        log_file = os.path.join(log_dir, f'ai_chrome_chat_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def info(self, message: str, component: Optional[str] = None):
        """Info seviyesinde log"""
        if component:
            message = f"[{component}] {message}"
        self.logger.info(message)
    
    def error(self, message: str, component: Optional[str] = None, exception: Optional[Exception] = None):
        """Error seviyesinde log"""
        if component:
            message = f"[{component}] {message}"
        if exception:
            message += f" - Exception: {str(exception)}"
        self.logger.error(message, exc_info=exception is not None)
    
    def warning(self, message: str, component: Optional[str] = None):
        """Warning seviyesinde log"""
        if component:
            message = f"[{component}] {message}"
        self.logger.warning(message)
    
    def debug(self, message: str, component: Optional[str] = None):
        """Debug seviyesinde log"""
        if component:
            message = f"[{component}] {message}"
        self.logger.debug(message)

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
