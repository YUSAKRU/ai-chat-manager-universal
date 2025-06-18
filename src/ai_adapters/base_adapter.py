"""
Base AI Adapter - Tüm AI adaptörlerinin temel sınıfı
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import asyncio
import time

@dataclass
class AIResponse:
    """Standart AI yanıt formatı"""
    content: str
    model: str
    usage: Dict[str, int]  # tokens, cost vs.
    metadata: Dict[str, Any]
    timestamp: float

@dataclass
class AIConfig:
    """AI servis konfigürasyonu"""
    api_key: str
    model_name: str
    max_tokens: int = 2000
    temperature: float = 0.7
    rate_limit_rpm: int = 60
    rate_limit_tpm: int = 1000000
    timeout: int = 30

class BaseAIAdapter(ABC):
    """Tüm AI adaptörlerinin implement etmesi gereken temel sınıf"""
    
    def __init__(self, config: AIConfig):
        self.config = config
        self.rate_limiter = RateLimiter(
            requests_per_minute=config.rate_limit_rpm,
            tokens_per_minute=config.rate_limit_tpm
        )
        self.conversation_history: List[Dict] = []
        
    @abstractmethod
    async def send_message(
        self, 
        message: str, 
        context: Optional[str] = None,
        role_context: Optional[str] = None
    ) -> AIResponse:
        """AI'ya mesaj gönder ve yanıt al"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Kullanılabilir model listesini döndür"""
        pass
    
    @abstractmethod
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Tahmini maliyet hesapla"""
        pass
    
    def add_to_history(self, user_msg: str, ai_response: str):
        """Konuşma geçmişine ekle"""
        self.conversation_history.append({
            "user": user_msg,
            "assistant": ai_response,
            "timestamp": time.time()
        })
        
        # Geçmişi sınırla (son 20 mesaj)
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
    
    def clear_history(self):
        """Konuşma geçmişini temizle"""
        self.conversation_history = []
    
    def check_rate_limit(self) -> bool:
        """Rate limit kontrolü"""
        return self.rate_limiter.can_make_request()

class RateLimiter:
    """Birleşik rate limiter"""
    
    def __init__(self, requests_per_minute: int, tokens_per_minute: int):
        self.rpm_limit = requests_per_minute
        self.tpm_limit = tokens_per_minute
        self.requests: List[float] = []
        self.tokens_used = 0
        self.last_reset = time.time()
    
    def can_make_request(self, estimated_tokens: int = 0) -> bool:
        """Request yapılabilir mi kontrol et"""
        current_time = time.time()
        
        # Dakika başı reset
        if current_time - self.last_reset >= 60:
            self.requests = []
            self.tokens_used = 0
            self.last_reset = current_time
        
        # Eski requestleri temizle
        self.requests = [r for r in self.requests if current_time - r < 60]
        
        # Limit kontrolü
        if len(self.requests) >= self.rpm_limit:
            return False
            
        if self.tokens_used + estimated_tokens > self.tpm_limit:
            return False
            
        return True
    
    def record_usage(self, tokens: int):
        """Kullanımı kaydet"""
        self.requests.append(time.time())
        self.tokens_used += tokens 