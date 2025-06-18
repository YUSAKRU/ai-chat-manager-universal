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


@dataclass
class TokenStats:
    """Token istatistikleri için gelişmiş veri yapısı"""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    input_cost: float = 0.0
    output_cost: float = 0.0
    total_cost: float = 0.0
    requests_count: int = 0
    errors_count: int = 0
    avg_response_time: float = 0.0
    last_request_time: Optional[str] = None
    
    def add_usage(self, usage_data: Dict[str, Any], response_time: float):
        """Yeni kullanım verisi ekle"""
        input_tokens = usage_data.get('input_tokens', 0)
        output_tokens = usage_data.get('output_tokens', 0)
        cost = usage_data.get('cost', 0.0)
        
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens += input_tokens + output_tokens
        self.total_cost += cost
        self.requests_count += 1
        
        # Ortalama yanıt süresini güncelle
        if self.requests_count == 1:
            self.avg_response_time = response_time
        else:
            self.avg_response_time = (self.avg_response_time * (self.requests_count - 1) + response_time) / self.requests_count
        
        self.last_request_time = datetime.now().isoformat()
    
    def add_error(self):
        """Hata sayısını artır"""
        self.errors_count += 1
    
    def get_success_rate(self) -> float:
        """Başarı oranını hesapla"""
        total_attempts = self.requests_count + self.errors_count
        if total_attempts == 0:
            return 100.0
        return (self.requests_count / total_attempts) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Dictionary'ye dönüştür"""
        return {
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'total_tokens': self.total_tokens,
            'input_cost': round(self.input_cost, 4),
            'output_cost': round(self.output_cost, 4),
            'total_cost': round(self.total_cost, 4),
            'requests_count': self.requests_count,
            'errors_count': self.errors_count,
            'success_rate': round(self.get_success_rate(), 2),
            'avg_response_time': round(self.avg_response_time, 3),
            'last_request_time': self.last_request_time
        }


class UniversalAIAdapter:
    """Birden fazla AI adapter'ını yöneten merkezi sistem"""
    
    def __init__(self, config_manager: SecureConfigManager):
        self.config_manager = config_manager
        self.adapters: Dict[str, BaseAIAdapter] = {}
        self.role_assignments: Dict[str, str] = {}  # role_id -> adapter_id
        self.conversation_history: List[Dict[str, Any]] = []
        
        # Gelişmiş istatistik takibi
        self.adapter_stats: Dict[str, TokenStats] = {}  # adapter_id -> TokenStats
        self.role_stats: Dict[str, TokenStats] = {}     # role_id -> TokenStats
        self.global_stats = TokenStats()
        
        # Token fiyatları (model bazında)
        self.token_prices = {
            'gemini-pro': {'input': 0.00025, 'output': 0.0005},
            'gemini-1.5-pro': {'input': 0.00125, 'output': 0.005},
            'gemini-2.0-flash': {'input': 0.0001, 'output': 0.0003},
            'gpt-3.5-turbo': {'input': 0.0015, 'output': 0.002},
            'gpt-4': {'input': 0.03, 'output': 0.06},
            'gpt-4-turbo': {'input': 0.01, 'output': 0.03},
            'gpt-4o': {'input': 0.005, 'output': 0.015},
            'gpt-4o-mini': {'input': 0.00015, 'output': 0.0006},
        }
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> Dict[str, float]:
        """Model bazında maliyet hesapla"""
        prices = self.token_prices.get(model, {'input': 0.001, 'output': 0.002})
        
        input_cost = (input_tokens / 1000) * prices['input']
        output_cost = (output_tokens / 1000) * prices['output']
        total_cost = input_cost + output_cost
        
        return {
            'input_cost': input_cost,
            'output_cost': output_cost,
            'total_cost': total_cost
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
        self.adapter_stats[adapter_id] = TokenStats()
        return adapter_id
    
    def remove_adapter(self, adapter_id: str):
        """Bir adapter'ı kaldır"""
        if adapter_id in self.adapters:
            del self.adapters[adapter_id]
            del self.adapter_stats[adapter_id]
            # Rol atamalarını temizle
            for role, assigned_id in list(self.role_assignments.items()):
                if assigned_id == adapter_id:
                    del self.role_assignments[role]
    
    def assign_role(self, role_id: str, adapter_id: str):
        """Bir role adapter ata"""
        if adapter_id not in self.adapters:
            raise ValueError(f"Adapter bulunamadı: {adapter_id}")
        self.role_assignments[role_id] = adapter_id
        
        # Role istatistikleri başlat
        if role_id not in self.role_stats:
            self.role_stats[role_id] = TokenStats()
    
    async def send_message(self, role_id: str, message: str, context: Optional[str] = None) -> Optional[AIResponse]:
        """Belirli bir rol üzerinden mesaj gönder"""
        start_time = time.time()
        
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
            response_time = time.time() - start_time
            
            if response:
                # Token sayılarını normalize et
                input_tokens = response.usage.get('input_tokens', response.usage.get('prompt_tokens', 0))
                output_tokens = response.usage.get('output_tokens', response.usage.get('completion_tokens', 0))
                
                # Maliyet hesapla
                cost_info = self._calculate_cost(adapter.model, input_tokens, output_tokens)
                
                # Enhanced usage data
                enhanced_usage = {
                    'input_tokens': input_tokens,
                    'output_tokens': output_tokens,
                    'total_tokens': input_tokens + output_tokens,
                    'cost': cost_info['total_cost'],
                    'input_cost': cost_info['input_cost'],
                    'output_cost': cost_info['output_cost'],
                    'model': adapter.model,
                    'response_time': response_time
                }
                
                # İstatistikleri güncelle
                self.adapter_stats[adapter_id].add_usage(enhanced_usage, response_time)
                self.role_stats[role_id].add_usage(enhanced_usage, response_time)
                self.global_stats.add_usage(enhanced_usage, response_time)
                
                # Response'u güncelle
                response.usage.update(enhanced_usage)
                
                # Konuşma geçmişine ekle
                self.conversation_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'role_id': role_id,
                    'adapter_id': adapter_id,
                    'message': message,
                    'response': response.content,
                    'usage': enhanced_usage
                })
                
                return response
                
        except Exception as e:
            response_time = time.time() - start_time
            # Hata istatistiklerini güncelle
            self.adapter_stats[adapter_id].add_error()
            if role_id in self.role_stats:
                self.role_stats[role_id].add_error()
            self.global_stats.add_error()
            raise e
    
    async def send_message_to_adapter(self, adapter_id: str, message: str, context: Optional[str] = None) -> Optional[AIResponse]:
        """Doğrudan belirli bir adapter'a mesaj gönder"""
        if adapter_id not in self.adapters:
            raise ValueError(f"Adapter bulunamadı: {adapter_id}")
        
        start_time = time.time()
        adapter = self.adapters[adapter_id]
        
        try:
            response = await adapter.send_message(message, context)
            response_time = time.time() - start_time
            
            if response:
                # Token sayılarını normalize et
                input_tokens = response.usage.get('input_tokens', response.usage.get('prompt_tokens', 0))
                output_tokens = response.usage.get('output_tokens', response.usage.get('completion_tokens', 0))
                
                # Maliyet hesapla
                cost_info = self._calculate_cost(adapter.model, input_tokens, output_tokens)
                
                # Enhanced usage data
                enhanced_usage = {
                    'input_tokens': input_tokens,
                    'output_tokens': output_tokens,
                    'total_tokens': input_tokens + output_tokens,
                    'cost': cost_info['total_cost'],
                    'input_cost': cost_info['input_cost'],
                    'output_cost': cost_info['output_cost'],
                    'model': adapter.model,
                    'response_time': response_time
                }
                
                # İstatistikleri güncelle
                self.adapter_stats[adapter_id].add_usage(enhanced_usage, response_time)
                self.global_stats.add_usage(enhanced_usage, response_time)
                
                # Response'u güncelle
                response.usage.update(enhanced_usage)
            
            return response
            
        except Exception as e:
            response_time = time.time() - start_time
            self.adapter_stats[adapter_id].add_error()
            self.global_stats.add_error()
            raise e
    
    def get_adapter_status(self) -> Dict[str, Any]:
        """Tüm adapter'ların durumunu al - gelişmiş istatistikler ile"""
        status = {}
        for adapter_id, adapter in self.adapters.items():
            adapter_stats = self.adapter_stats.get(adapter_id, TokenStats())
            
            status[adapter_id] = {
                'id': adapter_id,
                'type': adapter.__class__.__name__.replace('Adapter', '').lower(),
                'model': adapter.model,
                'rate_limit': adapter.check_rate_limit(),
                'stats': adapter_stats.to_dict(),
                'status': 'active' if adapter.check_rate_limit()['available'] else 'rate_limited'
            }
        return status
    
    def get_role_status(self) -> Dict[str, Any]:
        """Rol bazında istatistikleri al"""
        status = {}
        for role_id, adapter_id in self.role_assignments.items():
            role_stats = self.role_stats.get(role_id, TokenStats())
            adapter = self.adapters.get(adapter_id)
            
            status[role_id] = {
                'role_id': role_id,
                'adapter_id': adapter_id,
                'adapter_type': adapter.__class__.__name__.replace('Adapter', '').lower() if adapter else 'unknown',
                'model': adapter.model if adapter else 'unknown',
                'stats': role_stats.to_dict()
            }
        return status
    
    def get_role_assignments(self) -> Dict[str, str]:
        """Rol atamalarını döndür"""
        return self.role_assignments.copy()
    
    def get_total_stats(self) -> Dict[str, Any]:
        """Toplam istatistikleri döndür - gelişmiş sürüm"""
        stats = self.global_stats.to_dict()
        stats.update({
            'adapters_count': len(self.adapters),
            'active_roles': len(self.role_assignments),
            'conversation_entries': len(self.conversation_history),
            'uptime': self._get_uptime()
        })
        return stats
    
    def get_detailed_analytics(self) -> Dict[str, Any]:
        """Detaylı analytics verisi döndür"""
        return {
            'global_stats': self.get_total_stats(),
            'adapter_stats': {
                adapter_id: stats.to_dict() 
                for adapter_id, stats in self.adapter_stats.items()
            },
            'role_stats': {
                role_id: stats.to_dict() 
                for role_id, stats in self.role_stats.items()
            },
            'adapters': self.get_adapter_status(),
            'roles': self.get_role_status(),
            'token_usage_breakdown': self._get_token_breakdown(),
            'cost_breakdown': self._get_cost_breakdown(),
            'performance_metrics': self._get_performance_metrics()
        }
    
    def _get_token_breakdown(self) -> Dict[str, Any]:
        """Token kullanım dağılımı"""
        total_tokens = self.global_stats.total_tokens
        if total_tokens == 0:
            return {'input_percentage': 0, 'output_percentage': 0}
        
        input_percentage = (self.global_stats.input_tokens / total_tokens) * 100
        output_percentage = (self.global_stats.output_tokens / total_tokens) * 100
        
        return {
            'input_tokens': self.global_stats.input_tokens,
            'output_tokens': self.global_stats.output_tokens,
            'total_tokens': total_tokens,
            'input_percentage': round(input_percentage, 2),
            'output_percentage': round(output_percentage, 2)
        }
    
    def _get_cost_breakdown(self) -> Dict[str, Any]:
        """Maliyet dağılımı"""
        adapter_costs = {}
        role_costs = {}
        
        for adapter_id, stats in self.adapter_stats.items():
            if stats.total_cost > 0:
                adapter_costs[adapter_id] = {
                    'total_cost': round(stats.total_cost, 4),
                    'requests': stats.requests_count,
                    'cost_per_request': round(stats.total_cost / stats.requests_count, 4) if stats.requests_count > 0 else 0
                }
        
        for role_id, stats in self.role_stats.items():
            if stats.total_cost > 0:
                role_costs[role_id] = {
                    'total_cost': round(stats.total_cost, 4),
                    'requests': stats.requests_count,
                    'cost_per_request': round(stats.total_cost / stats.requests_count, 4) if stats.requests_count > 0 else 0
                }
        
        return {
            'total_cost': round(self.global_stats.total_cost, 4),
            'adapter_costs': adapter_costs,
            'role_costs': role_costs
        }
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Performans metrikleri"""
        fastest_adapter = None
        slowest_adapter = None
        min_time = float('inf')
        max_time = 0
        
        for adapter_id, stats in self.adapter_stats.items():
            if stats.requests_count > 0:
                if stats.avg_response_time < min_time:
                    min_time = stats.avg_response_time
                    fastest_adapter = adapter_id
                if stats.avg_response_time > max_time:
                    max_time = stats.avg_response_time
                    slowest_adapter = adapter_id
        
        return {
            'global_avg_response_time': round(self.global_stats.avg_response_time, 3),
            'fastest_adapter': fastest_adapter,
            'slowest_adapter': slowest_adapter,
            'fastest_time': round(min_time, 3) if min_time != float('inf') else 0,
            'slowest_time': round(max_time, 3),
            'global_success_rate': round(self.global_stats.get_success_rate(), 2)
        }
    
    def _get_uptime(self) -> str:
        """Sistem çalışma süresi (basit versiyon)"""
        # Bu örnekte basit bir implementasyon
        # Gerçek implementasyonda başlangıç zamanı saklanabilir
        return "session_based"
    
    def reset_stats(self, scope: str = 'all'):
        """İstatistikleri sıfırla"""
        if scope == 'all' or scope == 'global':
            self.global_stats = TokenStats()
        
        if scope == 'all' or scope == 'adapters':
            for adapter_id in self.adapter_stats:
                self.adapter_stats[adapter_id] = TokenStats()
        
        if scope == 'all' or scope == 'roles':
            for role_id in self.role_stats:
                self.role_stats[role_id] = TokenStats()
        
        if scope == 'all' or scope == 'conversations':
            self.conversation_history.clear()
    
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
        
        # En az istek alan ve en hızlı adapter'ı bul
        best_adapter_id = None
        best_score = float('inf')  # Düşük skor daha iyi
        
        for adapter_id, adapter in self.adapters.items():
            if not adapter.check_rate_limit()['available']:
                continue
                
            stats = self.adapter_stats.get(adapter_id, TokenStats())
            
            # Scoring: requests_count + avg_response_time
            score = stats.requests_count + (stats.avg_response_time * 10)
            
            if score < best_score:
                best_score = score
                best_adapter_id = adapter_id
        
        if best_adapter_id:
            return await self.send_message_to_adapter(best_adapter_id, message, context)
        
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