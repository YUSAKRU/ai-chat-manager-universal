"""
Merkezi Hata Yönetimi Sistemi
AI Chrome Chat Manager için kapsamlı error handling
"""
import traceback
import sys
from typing import Optional, Dict, Any, Union
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, render_template
import logging

from .logger import logger


class ErrorTypes:
    """Hata tiplerini tanımlayan constants"""
    
    # API/Network Errors
    API_CONNECTION_ERROR = "api_connection_error"
    API_RATE_LIMIT = "api_rate_limit"
    API_INVALID_KEY = "api_invalid_key"
    API_QUOTA_EXCEEDED = "api_quota_exceeded"
    API_TIMEOUT = "api_timeout"
    
    # File/IO Errors
    FILE_NOT_FOUND = "file_not_found"
    FILE_PERMISSION_ERROR = "file_permission_error"
    FILE_CORRUPTION = "file_corruption"
    DISK_SPACE_ERROR = "disk_space_error"
    
    # Configuration Errors
    CONFIG_MISSING = "config_missing"
    CONFIG_INVALID = "config_invalid"
    SECURITY_ERROR = "security_error"
    
    # Validation Errors
    INVALID_INPUT = "invalid_input"
    MISSING_PARAMETER = "missing_parameter"
    INVALID_FORMAT = "invalid_format"
    
    # System Errors
    MEMORY_ERROR = "memory_error"
    SYSTEM_OVERLOAD = "system_overload"
    DEPENDENCY_ERROR = "dependency_error"
    
    # Business Logic Errors
    ROLE_NOT_ASSIGNED = "role_not_assigned"
    ADAPTER_UNAVAILABLE = "adapter_unavailable"
    CONVERSATION_ERROR = "conversation_error"


class AIChromeChatError(Exception):
    """Ana hata sınıfı - özelleştirilmiş hata bilgileri içerir"""
    
    def __init__(
        self, 
        message: str, 
        error_type: str = "general_error",
        component: str = "unknown",
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        recoverable: bool = True,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.component = component
        self.details = details or {}
        self.user_message = user_message or self._get_user_friendly_message()
        self.recoverable = recoverable
        self.original_exception = original_exception
        self.timestamp = datetime.now().isoformat()
        self.request_id = self._generate_request_id()
    
    def _get_user_friendly_message(self) -> str:
        """Kullanıcı dostu hata mesajı oluştur"""
        friendly_messages = {
            ErrorTypes.API_CONNECTION_ERROR: "AI servisine bağlantı sağlanamıyor. Lütfen internet bağlantınızı kontrol edin.",
            ErrorTypes.API_RATE_LIMIT: "API kullanım limiti aşıldı. Lütfen birkaç dakika bekleyip tekrar deneyin.",
            ErrorTypes.API_INVALID_KEY: "API anahtarı geçersiz. Lütfen ayarlarınızı kontrol edin.",
            ErrorTypes.API_QUOTA_EXCEEDED: "API kotanız dolmuş. Lütfen hesap ayarlarınızı kontrol edin.",
            ErrorTypes.FILE_NOT_FOUND: "Gerekli dosya bulunamadı. Sistem dosyaları eksik olabilir.",
            ErrorTypes.CONFIG_MISSING: "Yapılandırma eksik. Lütfen kurulum işlemini tamamlayın.",
            ErrorTypes.INVALID_INPUT: "Girdiğiniz bilgiler geçersiz. Lütfen kontrol edip tekrar deneyin.",
            ErrorTypes.ROLE_NOT_ASSIGNED: "Bu işlem için gerekli roller atanmamış. Ayarlar sayfasından rolleri atayın.",
            ErrorTypes.ADAPTER_UNAVAILABLE: "AI servisi şu anda kullanılamıyor. Lütfen daha sonra tekrar deneyin."
        }
        return friendly_messages.get(self.error_type, "Beklenmeyen bir hata oluştu. Lütfen daha sonra tekrar deneyin.")
    
    def _generate_request_id(self) -> str:
        """Hata takibi için benzersiz ID oluştur"""
        import uuid
        return f"ERR-{str(uuid.uuid4())[:8].upper()}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Hata bilgilerini dictionary olarak döndür"""
        return {
            'error_id': self.request_id,
            'error_type': self.error_type,
            'component': self.component,
            'message': self.message,
            'user_message': self.user_message,
            'details': self.details,
            'recoverable': self.recoverable,
            'timestamp': self.timestamp,
            'original_exception': str(self.original_exception) if self.original_exception else None
        }


class CentralErrorHandler:
    """Merkezi hata yönetim sistemi"""
    
    def __init__(self, app: Optional[Flask] = None):
        self.app = app
        self.error_stats = {
            'total_errors': 0,
            'error_by_type': {},
            'error_by_component': {},
            'recent_errors': []
        }
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Flask uygulamasına hata yöneticisini entegre et"""
        self.app = app
        self.setup_flask_error_handlers()
        
        # Before request ile request ID tracking
        @app.before_request
        def before_request():
            request.error_context = {
                'request_id': f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S')}-{id(request) % 10000:04d}",
                'timestamp': datetime.now().isoformat(),
                'endpoint': request.endpoint,
                'method': request.method,
                'url': request.url
            }
    
    def setup_flask_error_handlers(self):
        """Flask error handler'larını kur"""
        
        @self.app.errorhandler(404)
        def handle_404(error):
            """404 Not Found handler"""
            return self._render_error_page(
                error_code=404,
                title="Sayfa Bulunamadı",
                message="Aradığınız sayfa mevcut değil.",
                description="URL'yi kontrol edin veya ana sayfaya dönün.",
                show_navigation=True
            ), 404
        
        @self.app.errorhandler(500)
        def handle_500(error):
            """500 Internal Server Error handler"""
            error_id = self._log_error(error, "server_error")
            return self._render_error_page(
                error_code=500,
                title="Sunucu Hatası",
                message="Sunucu tarafında bir hata oluştu.",
                description=f"Bu hata kaydedildi. Hata ID: {error_id}",
                show_support=True
            ), 500
        
        @self.app.errorhandler(403)
        def handle_403(error):
            """403 Forbidden handler"""
            return self._render_error_page(
                error_code=403,
                title="Erişim Reddedildi",
                message="Bu işlemi yapmaya yetkiniz yok.",
                description="Lütfen yetkili kişi ile iletişime geçin.",
                show_navigation=True
            ), 403
        
        @self.app.errorhandler(429)
        def handle_429(error):
            """429 Too Many Requests handler"""
            return self._render_error_page(
                error_code=429,
                title="Çok Fazla İstek",
                message="İstek limitini aştınız.",
                description="Lütfen birkaç dakika bekleyip tekrar deneyin.",
                show_retry=True
            ), 429
        
        @self.app.errorhandler(AIChromeChatError)
        def handle_custom_error(error):
            """Özel hata sınıfı handler"""
            self._log_error(error, error.component)
            
            if request.is_json or 'api/' in request.path:
                return jsonify(error.to_dict()), 500
            else:
                return self._render_error_page(
                    error_code=500,
                    title="Uygulama Hatası",
                    message=error.user_message,
                    description=f"Hata ID: {error.request_id}",
                    show_support=True,
                    error_details=error.to_dict()
                ), 500
    
    def _render_error_page(
        self, 
        error_code: int,
        title: str,
        message: str,
        description: str = "",
        show_navigation: bool = False,
        show_support: bool = False,
        show_retry: bool = False,
        error_details: Optional[Dict] = None
    ) -> str:
        """Design System'e uygun hata sayfası render et"""
        try:
            return render_template(
                'error.html',
                error_code=error_code,
                title=title,
                message=message,
                description=description,
                show_navigation=show_navigation,
                show_support=show_support,
                show_retry=show_retry,
                error_details=error_details,
                timestamp=datetime.now().isoformat()
            )
        except Exception:
            # Template bulunamazsa basit HTML döndür
            return self._render_simple_error_page(error_code, title, message, description)
    
    def _render_simple_error_page(self, error_code: int, title: str, message: str, description: str) -> str:
        """Template bulunamazsa kullanılacak basit hata sayfası"""
        return f"""
        <!DOCTYPE html>
        <html lang="tr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title} - AI Chrome Chat Manager</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
                       margin: 0; padding: 40px; background: #f5f7fa; color: #2d3748; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; 
                            padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
                .error-code {{ font-size: 4rem; font-weight: bold; color: #e53e3e; margin-bottom: 20px; }}
                .title {{ font-size: 1.8rem; font-weight: 600; margin-bottom: 15px; }}
                .message {{ font-size: 1.1rem; margin-bottom: 20px; line-height: 1.6; }}
                .description {{ color: #718096; margin-bottom: 30px; }}
                .btn {{ background: #4299e1; color: white; padding: 12px 24px; 
                       border: none; border-radius: 8px; text-decoration: none; 
                       display: inline-block; font-weight: 500; }}
                .btn:hover {{ background: #3182ce; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="error-code">{error_code}</div>
                <h1 class="title">{title}</h1>
                <p class="message">{message}</p>
                <p class="description">{description}</p>
                <a href="/" class="btn">Ana Sayfaya Dön</a>
            </div>
        </body>
        </html>
        """
    
    def _log_error(self, error: Exception, component: str = "unknown") -> str:
        """Hatayı kaydet ve istatistikleri güncelle"""
        error_id = f"ERR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{id(error) % 10000:04d}"
        
        # Hata bilgilerini topla
        error_info = {
            'error_id': error_id,
            'component': component,
            'error_type': type(error).__name__,
            'message': str(error),
            'timestamp': datetime.now().isoformat(),
            'traceback': traceback.format_exc(),
            'request_info': getattr(request, 'error_context', {}) if 'request' in globals() else {}
        }
        
        # İstatistikleri güncelle
        self.error_stats['total_errors'] += 1
        error_type = error_info['error_type']
        self.error_stats['error_by_type'][error_type] = self.error_stats['error_by_type'].get(error_type, 0) + 1
        self.error_stats['error_by_component'][component] = self.error_stats['error_by_component'].get(component, 0) + 1
        
        # Son hataları tut (max 100)
        self.error_stats['recent_errors'].append(error_info)
        if len(self.error_stats['recent_errors']) > 100:
            self.error_stats['recent_errors'] = self.error_stats['recent_errors'][-100:]
        
        # Logger'a kaydet
        logger.error(f"[{error_id}] {component}: {str(error)}", component=component, exception=error)
        
        return error_id
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Hata istatistiklerini döndür"""
        return self.error_stats.copy()


def safe_execute(
    func,
    component: str = "unknown",
    error_type: str = ErrorTypes.SYSTEM_OVERLOAD,
    user_message: Optional[str] = None,
    default_return: Any = None,
    raise_on_error: bool = False
):
    """
    Güvenli fonksiyon çalıştırma decorator'ı
    
    Args:
        func: Çalıştırılacak fonksiyon
        component: Hangi bileşende hata oluştuğu
        error_type: Hata tipi
        user_message: Kullanıcı için özel mesaj
        default_return: Hata durumunda döndürülecek değer
        raise_on_error: True ise hatayı tekrar fırlat
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except AIChromeChatError:
                # Özel hatalarımızı olduğu gibi geçir
                raise
            except Exception as e:
                # Diğer hataları özel hata sınıfına dönüştür
                wrapped_error = AIChromeChatError(
                    message=str(e),
                    error_type=error_type,
                    component=component,
                    user_message=user_message,
                    original_exception=e
                )
                
                if raise_on_error:
                    raise wrapped_error
                else:
                    logger.error(f"Safe execute caught error in {component}: {str(e)}", 
                               component=component, exception=e)
                    return default_return
        
        return wrapper
    return decorator


def async_safe_execute(
    component: str = "unknown",
    error_type: str = ErrorTypes.SYSTEM_OVERLOAD,
    user_message: Optional[str] = None,
    default_return: Any = None,
    raise_on_error: bool = False
):
    """Async fonksiyon için güvenli çalıştırma decorator'ı"""
    def decorator(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            try:
                return await f(*args, **kwargs)
            except AIChromeChatError:
                raise
            except Exception as e:
                wrapped_error = AIChromeChatError(
                    message=str(e),
                    error_type=error_type,
                    component=component,
                    user_message=user_message,
                    original_exception=e
                )
                
                if raise_on_error:
                    raise wrapped_error
                else:
                    logger.error(f"Async safe execute caught error in {component}: {str(e)}", 
                               component=component, exception=e)
                    return default_return
        
        return wrapper
    return decorator


# Global error handler instance
central_error_handler = CentralErrorHandler() 