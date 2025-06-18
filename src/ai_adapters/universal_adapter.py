"""
Universal AI Adapter - Çoklu AI desteği sağlayan merkezi yönetim sistemi
"""
from typing import Dict, Optional, List, Any, Union
from dataclasses import dataclass
import asyncio
import time
from datetime import datetime
import uuid

from .base_adapter import BaseAIAdapter, AIResponse
from .gemini_adapter import GeminiAdapter
from .openai_adapter import OpenAIAdapter
from .secure_config import SecureConfigManager


class UniversalAIAdapter:
    """Birden fazla AI adapter'ını yöneten merkezi sistem"""
    
    def __init__(self, config_manager: SecureConfigManager):
        self.config_manager = config_manager
        self.adapters: Dict[str, BaseAIAdapter] = {}
        self.role_assignments: Dict[str, str] = {}  # role_id -> adapter_id
        self.conversation_history: List[Dict[str, Any]] = []
        self.total_stats = {
            'total_requests': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'total_errors': 0
        }
    
    def add_adapter(self, adapter_type: str, adapter_id: Optional[str] = None, **kwargs) -> str:
        """Yeni bir AI adapter ekle"""
        # Otomatik ID oluştur
        if not adapter_id:
            adapter_id = f"{adapter_type}-{str(uuid.uuid4())[:8]}"
        
        # Adapter tipine göre oluştur
        if adapter_type == "gemini":
            adapter = GeminiAdapter(
                api_key=kwargs.get('api_key'),
                model=kwargs.get('model', 'gemini-pro')
            )
        elif adapter_type == "openai":
            adapter = OpenAIAdapter(
                api_key=kwargs.get('api_key'),
                model=kwargs.get('model', 'gpt-3.5-turbo')
            )
        else:
            raise ValueError(f"Desteklenmeyen adapter tipi: {adapter_type}")
        
        self.adapters[adapter_id] = adapter
        return adapter_id
    
    def remove_adapter(self, adapter_id: str):
        """Bir adapter'ı kaldır"""
        if adapter_id in self.adapters:
            del self.adapters[adapter_id]
            # Rol atamalarını temizle
            for role, assigned_id in list(self.role_assignments.items()):
                if assigned_id == adapter_id:
                    del self.role_assignments[role]
    
    def assign_role(self, role_id: str, adapter_id: str):
        """Bir role adapter ata"""
        if adapter_id not in self.adapters:
            raise ValueError(f"Adapter bulunamadı: {adapter_id}")
        self.role_assignments[role_id] = adapter_id
    
    async def send_message(self, role_id: str, message: str, context: Optional[str] = None) -> Optional[AIResponse]:
        """Belirli bir rol üzerinden mesaj gönder"""
        # Role atanmış adapter'ı bul
        adapter_id = self.role_assignments.get(role_id)
        if not adapter_id or adapter_id not in self.adapters:
            # Varsayılan olarak ilk adapter'ı kullan
            if self.adapters:
                adapter_id = list(self.adapters.keys())[0]
            else:
                raise ValueError("Kullanılabilir adapter yok")
        
        adapter = self.adapters[adapter_id]
        
        try:
            # Mesajı gönder
            response = await adapter.send_message(message, context)
            
            if response:
                # İstatistikleri güncelle
                self.total_stats['total_requests'] += 1
                self.total_stats['total_tokens'] += response.usage.get('total_tokens', 0)
                self.total_stats['total_cost'] += response.usage.get('cost', 0)
                
                # Konuşma geçmişine ekle
                self.conversation_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'role_id': role_id,
                    'adapter_id': adapter_id,
                    'message': message,
                    'response': response.content,
                    'usage': response.usage
                })
                
                return response
                
        except Exception as e:
            self.total_stats['total_errors'] += 1
            raise e
    
    async def send_message_to_adapter(self, adapter_id: str, message: str, context: Optional[str] = None) -> Optional[AIResponse]:
        """Doğrudan belirli bir adapter'a mesaj gönder"""
        if adapter_id not in self.adapters:
            raise ValueError(f"Adapter bulunamadı: {adapter_id}")
        
        adapter = self.adapters[adapter_id]
        return await adapter.send_message(message, context)
    
    def get_adapter_status(self) -> Dict[str, Any]:
        """Tüm adapter'ların durumunu al"""
        status = {}
        for adapter_id, adapter in self.adapters.items():
            status[adapter_id] = {
                'type': adapter.__class__.__name__.replace('Adapter', '').lower(),
                'model': adapter.model,
                'rate_limit': adapter.check_rate_limit(),
                'stats': adapter.get_stats()
            }
        return status
    
    def get_role_assignments(self) -> Dict[str, str]:
        """Rol atamalarını döndür"""
        return self.role_assignments.copy()
    
    def get_total_stats(self) -> Dict[str, Any]:
        """Toplam istatistikleri döndür"""
        stats = self.total_stats.copy()
        stats['adapters_count'] = len(self.adapters)
        stats['active_roles'] = len(self.role_assignments)
        return stats
    
    def clear_conversation_history(self):
        """Konuşma geçmişini temizle"""
        self.conversation_history.clear()
    
    def get_conversation_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Konuşma geçmişini al"""
        if limit:
            return self.conversation_history[-limit:]
        return self.conversation_history.copy()
    
    async def balance_load(self, message: str, context: Optional[str] = None) -> Optional[AIResponse]:
        """Yük dengeleme ile mesaj gönder (en az kullanılan adapter'ı seç)"""
        if not self.adapters:
            raise ValueError("Kullanılabilir adapter yok")
        
        # En az istek alan adapter'ı bul
        min_requests = float('inf')
        selected_adapter_id = None
        
        for adapter_id, adapter in self.adapters.items():
            stats = adapter.get_stats()
            if stats['requests'] < min_requests and adapter.check_rate_limit()['available']:
                min_requests = stats['requests']
                selected_adapter_id = adapter_id
        
        if not selected_adapter_id:
            # Tüm adapter'lar rate limit'te, ilk uygun olanı bekle
            for adapter_id, adapter in self.adapters.items():
                if adapter.check_rate_limit()['retry_after'] == 0:
                    selected_adapter_id = adapter_id
                    break
        
        if selected_adapter_id:
            return await self.send_message_to_adapter(selected_adapter_id, message, context)
        
        raise Exception("Tüm adapter'lar meşgul")
    
    async def parallel_query(self, message: str, context: Optional[str] = None) -> Dict[str, AIResponse]:
        """Tüm adapter'lara paralel sorgu gönder"""
        tasks = []
        adapter_ids = []
        
        for adapter_id, adapter in self.adapters.items():
            if adapter.check_rate_limit()['available']:
                task = self.send_message_to_adapter(adapter_id, message, context)
                tasks.append(task)
                adapter_ids.append(adapter_id)
        
        if not tasks:
            return {}
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        results = {}
        for adapter_id, response in zip(adapter_ids, responses):
            if isinstance(response, Exception):
                results[adapter_id] = None
            else:
                results[adapter_id] = response
        
        return results 