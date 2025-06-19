"""
Request Logging Middleware - Flask request'lerini izleyen middleware
"""
import threading
import time
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from flask import Flask, request, g
from .factory import get_logger


class RequestLoggingMiddleware:
    """
    Flask request'lerini izleyen middleware
    - Request ID tracking
    - Performance monitoring
    - User session tracking
    - Automatic request/response logging
    """
    
    def __init__(self, app: Optional[Flask] = None, 
                 logger_name: str = 'request_middleware',
                 log_requests: bool = True,
                 log_responses: bool = True,
                 log_performance: bool = True):
        
        self.logger_name = logger_name
        self.log_requests = log_requests
        self.log_responses = log_responses
        self.log_performance = log_performance
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Flask app'e middleware'ı kaydet"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_appcontext(self.teardown_request)
        
        # Logger'ı hazırla
        self.logger = get_logger(self.logger_name, 'request_middleware')
    
    def before_request(self):
        """Request başlangıcında çalışır"""
        # Request ID oluştur
        request_id = self._generate_request_id()
        g.request_id = request_id
        g.request_start_time = time.time()
        
        # Thread local'a request bilgilerini kaydet
        current_thread = threading.current_thread()
        current_thread.request_id = request_id
        current_thread.request_start_time = time.time()
        current_thread.http_method = request.method
        current_thread.endpoint = request.endpoint
        current_thread.ip_address = self._get_client_ip()
        
        # User session tracking (eğer session varsa)
        if hasattr(request, 'session') and request.session:
            user_id = request.session.get('user_id') or request.session.get('id', 'anonymous')
            current_thread.user_session = user_id
            g.user_session = user_id
        
        # Request'i logla
        if self.log_requests:
            self._log_request_start()
    
    def after_request(self, response):
        """Request tamamlandığında çalışır"""
        # Response'ı logla
        if self.log_responses:
            self._log_request_end(response)
        
        # Performance metriklerini logla
        if self.log_performance:
            self._log_performance_metrics(response)
        
        return response
    
    def teardown_request(self, exception=None):
        """Request cleanup"""
        # Exception varsa logla
        if exception:
            self.logger.error("Request failed with exception", 
                            exception=exception,
                            request_id=g.get('request_id'),
                            endpoint=request.endpoint,
                            method=request.method)
        
        # Thread local'ı temizle
        current_thread = threading.current_thread()
        for attr in ['request_id', 'request_start_time', 'http_method', 
                    'endpoint', 'ip_address', 'user_session']:
            if hasattr(current_thread, attr):
                delattr(current_thread, attr)
    
    def _generate_request_id(self) -> str:
        """Benzersiz request ID oluştur"""
        return f"REQ-{uuid.uuid4().hex[:12].upper()}"
    
    def _get_client_ip(self) -> str:
        """Gerçek client IP'sini al"""
        # Proxy headers'ını kontrol et
        forwarded_ips = request.headers.get('X-Forwarded-For')
        if forwarded_ips:
            return forwarded_ips.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.remote_addr or 'unknown'
    
    def _log_request_start(self):
        """Request başlangıcını logla"""
        self.logger.info("Request started",
                        method=request.method,
                        url=request.url,
                        endpoint=request.endpoint,
                        ip_address=self._get_client_ip(),
                        user_agent=request.headers.get('User-Agent', 'unknown'),
                        content_length=request.content_length or 0,
                        args=dict(request.args) if request.args else {},
                        headers=self._filter_headers(dict(request.headers)))
    
    def _log_request_end(self, response):
        """Request bitişini logla"""
        duration = time.time() - g.get('request_start_time', time.time())
        
        self.logger.info("Request completed",
                        method=request.method,
                        url=request.url,
                        endpoint=request.endpoint,
                        status_code=response.status_code,
                        response_size=len(response.data) if response.data else 0,
                        duration=round(duration, 3),
                        content_type=response.content_type)
    
    def _log_performance_metrics(self, response):
        """Performance metriklerini logla"""
        duration = time.time() - g.get('request_start_time', time.time())
        
        # Performance kategorileri
        if duration > 5.0:
            level = 'warning'
            message = "Slow request detected"
        elif duration > 2.0:
            level = 'info'
            message = "Request performance warning"
        else:
            level = 'debug'
            message = "Request performance normal"
        
        metrics = {
            'duration': round(duration, 3),
            'status_code': response.status_code,
            'method': request.method,
            'endpoint': request.endpoint,
            'response_size': len(response.data) if response.data else 0,
            'is_slow': duration > 2.0
        }
        
        # Log level'a göre logla
        if level == 'warning':
            self.logger.warning(message, **metrics)
        elif level == 'info':
            self.logger.info(message, **metrics)
        else:
            self.logger.debug(message, **metrics)
    
    def _filter_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Sensitive header'ları filtrele"""
        sensitive_headers = {
            'authorization', 'cookie', 'x-api-key', 'x-auth-token'
        }
        
        filtered = {}
        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                filtered[key] = '[FILTERED]'
            else:
                filtered[key] = value
        
        return filtered


class APICallTracker:
    """
    API çağrılarını izleyen utility sınıf
    """
    
    def __init__(self, logger_name: str = 'api_tracker'):
        self.logger = get_logger(logger_name, 'api_tracker')
    
    def track_api_call(self, 
                      provider: str,
                      model: str,
                      operation: str,
                      duration: float,
                      tokens_used: int = 0,
                      cost: float = 0.0,
                      success: bool = True,
                      error: Optional[str] = None,
                      **extra_metrics):
        """
        API çağrısını detaylı şekilde logla
        
        Args:
            provider: AI provider (gemini, openai, etc.)
            model: Model adı
            operation: Operasyon tipi (chat, completion, embedding, etc.)
            duration: Çağrı süresi (saniye)
            tokens_used: Kullanılan token sayısı
            cost: Maliyet (USD)
            success: Başarılı olup olmadığı
            error: Hata mesajı (varsa)
            **extra_metrics: Ek metrikler
        """
        
        metrics = {
            'provider': provider,
            'model': model,
            'operation': operation,
            'duration': round(duration, 3),
            'total_tokens': tokens_used,
            'cost': cost,
            'success': success,
            **extra_metrics
        }
        
        if success:
            self.logger.info(f"API Call: {provider}/{model}",
                           **metrics)
        else:
            self.logger.error(f"API Call Failed: {provider}/{model}",
                            error_message=error,
                            **metrics)
    
    def track_rate_limit(self, provider: str, retry_after: Optional[int] = None):
        """Rate limit'i logla"""
        self.logger.warning("Rate limit encountered",
                          provider=provider,
                          retry_after=retry_after)
    
    def track_cost_threshold(self, provider: str, current_cost: float, threshold: float):
        """Maliyet eşiği aşımını logla"""
        self.logger.warning("Cost threshold exceeded",
                          provider=provider,
                          current_cost=current_cost,
                          threshold=threshold,
                          percentage=round((current_cost / threshold) * 100, 1))


class SecurityLogger:
    """
    Güvenlik olaylarını izleyen logger
    """
    
    def __init__(self, logger_name: str = 'security'):
        self.logger = get_logger(logger_name, 'security')
    
    def log_failed_login(self, username: str, ip_address: str, user_agent: str):
        """Başarısız login denemesini logla"""
        self.logger.warning("Failed login attempt",
                          username=username,
                          ip_address=ip_address,
                          user_agent=user_agent,
                          event_type='failed_login')
    
    def log_suspicious_activity(self, activity: str, ip_address: str, details: Dict[str, Any]):
        """Şüpheli aktiviteyi logla"""
        self.logger.warning("Suspicious activity detected",
                          activity=activity,
                          ip_address=ip_address,
                          event_type='suspicious_activity',
                          **details)
    
    def log_rate_limit_violation(self, ip_address: str, endpoint: str, attempt_count: int):
        """Rate limit ihlalini logla"""
        self.logger.warning("Rate limit violation",
                          ip_address=ip_address,
                          endpoint=endpoint,
                          attempt_count=attempt_count,
                          event_type='rate_limit_violation')
    
    def log_permission_denied(self, user_id: str, resource: str, action: str):
        """Yetki ihlalini logla"""
        self.logger.warning("Permission denied",
                          user_id=user_id,
                          resource=resource,
                          action=action,
                          event_type='permission_denied') 