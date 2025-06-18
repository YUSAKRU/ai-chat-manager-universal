"""
Base AI Adapter - Tüm AI adaptörlerinin temel sınıfı
"""
from abc import ABC
from typing import Dict, Optional, Any
from dataclasses import dataclass
import time


@dataclass
class AIResponse:
    """Standart AI yanıt formatı"""
    content: str
    model: str
    usage: Dict[str, Any]  # tokens, cost vs.


class BaseAIAdapter:
    """Tüm AI adaptörlerinin inherit etmesi gereken temel sınıf"""
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.last_request_time = 0
        self.request_count = 0
        self.stats = {
            'requests': 0,
            'tokens': 0,
            'cost': 0.0,
            'errors': 0
        }
        
    async def send_message(self, message: str, context: Optional[str] = None) -> AIResponse:
        """AI'ya mesaj gönder ve yanıt al - Alt sınıflar override etmeli"""
        raise NotImplementedError("Alt sınıflar send_message metodunu implement etmeli")
    
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
        """Adapter istatistiklerini döndür"""
        return self.stats.copy()
    
    def _update_stats(self, tokens: int, cost: float):
        """İstatistikleri güncelle"""
        self.stats['requests'] += 1
        self.stats['tokens'] += tokens
        self.stats['cost'] += cost
        self.last_request_time = time.time() 