"""
Base AI Adapter - Tüm AI adaptörlerinin temel sınıfı
Enhanced with real-time performance tracking
"""
from abc import ABC
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
import time
from datetime import datetime
import statistics


@dataclass
class AIResponse:
    """Standart AI yanıt formatı"""
    content: str
    model: str
    usage: Dict[str, Any]  # tokens, cost vs.
    response_time: float = 0.0  # Response time in seconds
    timestamp: str = ""


class PerformanceTracker:
    """Real-time performance tracking için yardımcı sınıf"""
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.response_times: List[float] = []
        self.success_count = 0
        self.error_count = 0
        self.start_time = time.time()
        
    def add_response_time(self, response_time: float, success: bool = True):
        """Response time ve başarı durumunu kaydet"""
        self.response_times.append(response_time)
        
        # Geçmiş verilerini sınırla
        if len(self.response_times) > self.max_history:
            self.response_times.pop(0)
            
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
    
    def get_avg_response_time(self) -> float:
        """Ortalama response time"""
        if not self.response_times:
            return 0.0
        return statistics.mean(self.response_times)
    
    def get_success_rate(self) -> float:
        """Başarı oranı (yüzde)"""
        total = self.success_count + self.error_count
        if total == 0:
            return 100.0
        return (self.success_count / total) * 100
    
    def get_requests_per_minute(self) -> float:
        """Dakika başına istek sayısı"""
        uptime_minutes = (time.time() - self.start_time) / 60
        if uptime_minutes == 0:
            return 0.0
        total_requests = self.success_count + self.error_count
        return total_requests / uptime_minutes


class BaseAIAdapter:
    """Tüm AI adaptörlerinin inherit etmesi gereken temel sınıf"""
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.last_request_time = 0
        self.request_count = 0
        
        # Enhanced stats with real-time tracking
        self.stats = {
            'total_requests': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'total_errors': 0,
            'input_tokens': 0,
            'output_tokens': 0
        }
        
        # Performance tracker for real-time metrics
        self.performance = PerformanceTracker()
        self.status = 'active'  # active, standby, error
        self.last_error = None
        
    async def send_message(self, message: str, context: Optional[str] = None) -> AIResponse:
        """AI'ya mesaj gönder ve yanıt al - Performance tracking ile"""
        start_time = time.time()
        success = False
        
        try:
            # Alt sınıflar bu metodu implement etmeli
            response = await self._send_message_impl(message, context)
            success = True
            
            # Response time hesapla
            response_time = time.time() - start_time
            response.response_time = response_time
            response.timestamp = datetime.now().isoformat()
            
            # Performance tracking
            self.performance.add_response_time(response_time, success=True)
            
            # Stats güncelle
            if response.usage:
                self._update_stats(
                    input_tokens=response.usage.get('input_tokens', 0),
                    output_tokens=response.usage.get('output_tokens', 0), 
                    cost=response.usage.get('total_cost', 0.0)
                )
            
            self.status = 'active'
            self.last_error = None
            
            return response
            
        except Exception as e:
            # Hata durumunda performance tracking
            response_time = time.time() - start_time
            self.performance.add_response_time(response_time, success=False)
            
            self.stats['total_errors'] += 1
            self.status = 'error'
            self.last_error = str(e)
            
            raise e
    
    async def _send_message_impl(self, message: str, context: Optional[str] = None) -> AIResponse:
        """Alt sınıflar bu metodu implement etmeli"""
        raise NotImplementedError("Alt sınıflar _send_message_impl metodunu implement etmeli")
    
    def check_rate_limit(self) -> Dict[str, Any]:
        """Rate limit kontrolü"""
        current_time = time.time()
        
        # Basit rate limiting (saniyede 1 istek)
        if current_time - self.last_request_time < 1.0:
            return {
                'available': False,
                'retry_after': 1.0 - (current_time - self.last_request_time)
            }
        
        return {
            'available': True,
            'retry_after': 0
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Detaylı adapter istatistiklerini döndür"""
        base_stats = self.stats.copy()
        
        # Performance metrikleri ekle
        base_stats.update({
            'avg_response_time': round(self.performance.get_avg_response_time(), 2),
            'success_rate': round(self.performance.get_success_rate(), 1),
            'requests_per_minute': round(self.performance.get_requests_per_minute(), 1),
            'status': self.status,
            'last_error': self.last_error,
            'uptime_seconds': int(time.time() - self.performance.start_time)
        })
        
        return base_stats
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Frontend için özet performans verileri"""
        return {
            'model': self.model,
            'status': self.status,
            'avg_response_time': round(self.performance.get_avg_response_time(), 2),
            'success_rate': round(self.performance.get_success_rate(), 1),
            'total_requests': self.stats['total_requests'],
            'total_cost': round(self.stats['total_cost'], 4),
            'total_tokens': self.stats['total_tokens'],
            'requests_per_minute': round(self.performance.get_requests_per_minute(), 1),
            'is_available': self.check_rate_limit()['available']
        }
    
    def _update_stats(self, input_tokens: int = 0, output_tokens: int = 0, cost: float = 0.0):
        """İstatistikleri güncelle - Enhanced version"""
        self.stats['total_requests'] += 1
        self.stats['input_tokens'] += input_tokens
        self.stats['output_tokens'] += output_tokens
        self.stats['total_tokens'] = self.stats['input_tokens'] + self.stats['output_tokens']
        self.stats['total_cost'] += cost
        self.last_request_time = time.time()
    
    def set_status(self, status: str):
        """Adapter statusunu manuel güncelle (active, standby, error)"""
        self.status = status 