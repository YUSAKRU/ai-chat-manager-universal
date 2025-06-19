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
        self.adapter_stats: Dict[str, TokenStats] = {}
        self.role_assignments: Dict[str, str] = {}  # role_id -> adapter_id
        self.role_stats: Dict[str, TokenStats] = {}
        self.global_stats = TokenStats()
        self.conversation_history: List[Dict[str, Any]] = []
        
        # 2025 Güncel Gemini model fiyatları - Yeni modeller eklendi
        self.token_prices = {
            # Gemini 2025 - Ücretsiz modeller
            'gemini-1.5-flash': {'input': 0.0, 'output': 0.0},
            'gemini-1.5-flash-002': {'input': 0.0, 'output': 0.0},
            'gemini-2.0-flash': {'input': 0.0, 'output': 0.0},        # 🚀 YENİ - Ultra high throughput
            'gemini-2.0-flash-001': {'input': 0.0, 'output': 0.0},
            'gemini-2.0-flash-lite': {'input': 0.0, 'output': 0.0},   # 🚀 YENİ - Ultra performance
            'gemini-2.5-flash': {'input': 0.0, 'output': 0.0},
            'gemini-2.5-flash-lite-preview': {'input': 0.0, 'output': 0.0},  # 🚀 YENİ - 30K RPM
            
            # Gemini 2025 - Ücretli modeller
            'gemini-1.5-pro': {'input': 0.00125, 'output': 0.005},
            'gemini-1.5-pro-002': {'input': 0.00125, 'output': 0.005},
            'gemini-2.5-pro': {'input': 0.00125, 'output': 0.005},    # Enterprise model
            
            # OpenAI modelleri (karşılaştırma için)
            'gpt-3.5-turbo': {'input': 0.0015, 'output': 0.002},
            'gpt-4': {'input': 0.03, 'output': 0.06},
            'gpt-4-turbo': {'input': 0.01, 'output': 0.03},
            'gpt-4o': {'input': 0.005, 'output': 0.015},
            'gpt-4o-mini': {'input': 0.00015, 'output': 0.0006},
        }
        
        # Model rate limits - 2025 güncel veriler
        self.model_rate_limits = {
            'gemini-2.0-flash': {'rpm': 30000, 'tpm': 30000000},       # 🚀 Ultra high
            'gemini-2.0-flash-lite': {'rpm': 30000, 'tpm': 30000000},  # 🚀 Ultra high  
            'gemini-2.5-flash-lite-preview': {'rpm': 30000, 'tpm': 30000000},  # 🚀 Ultra high
            'gemini-2.5-flash': {'rpm': 10000, 'tpm': 8000000},
            'gemini-2.5-pro': {'rpm': 2000, 'tpm': 8000000},
            'gemini-1.5-flash': {'rpm': 15000, 'tpm': 1000000},
            'gemini-1.5-pro': {'rpm': 2000, 'tpm': 32000},
        }
        
        # Performance analytics için yeni özellikler
        self.model_performance_history = {}  # model -> [performance_snapshots]
        self.cost_optimization_recommendations = []
        self.performance_alerts = []
    
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
        
        # Eğer ID zaten mevcutsa, unique hale getir
        original_id = adapter_id
        counter = 1
        while adapter_id in self.adapters:
            adapter_id = f"{original_id}-{counter}"
            counter += 1
        
        # Adapter tipine göre oluştur
        if adapter_type == "gemini":
            adapter = GeminiAdapter(
                api_key=kwargs.get('api_key'),
                model=kwargs.get('model', 'gemini-1.5-flash-002')  # Yeni stabil model
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
        
        # Gemini güvenlik filtresi için fallback sistemi
        primary_adapter_id = adapter_id
        fallback_attempted = False
        
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
            error_message = str(e)
            
            # Gemini güvenlik filtresi hatası için OpenAI fallback
            if ("güvenlik filtresi" in error_message.lower() or 
                "safety filter" in error_message.lower() or
                "blocked" in error_message.lower()) and not fallback_attempted:
                
                print(f"🔄 Gemini güvenlik filtresi tetiklendi, OpenAI fallback deneniyor...")
                
                # OpenAI adapter'ı bul
                openai_adapter_id = None
                for aid, adapter in self.adapters.items():
                    if adapter.__class__.__name__ == 'OpenAIAdapter':
                        openai_adapter_id = aid
                        break
                
                if openai_adapter_id:
                    try:
                        fallback_attempted = True
                        print(f"🤖 OpenAI fallback: {openai_adapter_id}")
                        
                        # OpenAI ile dene
                        openai_adapter = self.adapters[openai_adapter_id]
                        response = await openai_adapter.send_message(message, context)
                        response_time = time.time() - start_time
                        
                        if response:
                            # Token sayılarını normalize et
                            input_tokens = response.usage.get('input_tokens', response.usage.get('prompt_tokens', 0))
                            output_tokens = response.usage.get('output_tokens', response.usage.get('completion_tokens', 0))
                            
                            # Maliyet hesapla
                            cost_info = self._calculate_cost(openai_adapter.model, input_tokens, output_tokens)
                            
                            # Enhanced usage data
                            enhanced_usage = {
                                'input_tokens': input_tokens,
                                'output_tokens': output_tokens,
                                'total_tokens': input_tokens + output_tokens,
                                'cost': cost_info['total_cost'],
                                'input_cost': cost_info['input_cost'],
                                'output_cost': cost_info['output_cost'],
                                'model': openai_adapter.model,
                                'response_time': response_time,
                                'fallback_used': True,
                                'original_adapter': primary_adapter_id,
                                'fallback_adapter': openai_adapter_id
                            }
                            
                            # İstatistikleri güncelle (fallback adapter için)
                            self.adapter_stats[openai_adapter_id].add_usage(enhanced_usage, response_time)
                            self.role_stats[role_id].add_usage(enhanced_usage, response_time)
                            self.global_stats.add_usage(enhanced_usage, response_time)
                            
                            # Response'u güncelle
                            response.usage.update(enhanced_usage)
                            
                            # Konuşma geçmişine ekle (fallback bilgisi ile)
                            self.conversation_history.append({
                                'timestamp': datetime.now().isoformat(),
                                'role_id': role_id,
                                'adapter_id': openai_adapter_id,
                                'message': message,
                                'response': response.content,
                                'usage': enhanced_usage,
                                'fallback_used': True,
                                'original_adapter': primary_adapter_id,
                                'fallback_reason': 'Gemini security filter'
                            })
                            
                            print(f"✅ OpenAI fallback başarılı!")
                            return response
                            
                    except Exception as fallback_error:
                        print(f"❌ OpenAI fallback da başarısız: {str(fallback_error)}")
                        # OpenAI de başarısız olursa orijinal Gemini hatasını fırlat
                        pass
                else:
                    print("⚠️ OpenAI adapter bulunamadı, fallback yapılamıyor")
            
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
            'total_requests': self.global_stats.requests_count,  # Backward compatibility
            'total_errors': self.global_stats.errors_count,    # Backward compatibility
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
    
    # 🚀 FAZ 2: ADVANCED ANALYTICS METODLARI
    
    def get_model_performance_comparison(self) -> Dict[str, Any]:
        """Model performans karşılaştırması - 2025 Advanced Analytics"""
        comparison = {
            'models': {},
            'recommendations': [],
            'best_performers': {},
            'cost_efficiency': {},
            'throughput_analysis': {}
        }
        
        # Her model için performans analizi
        for adapter_id, adapter in self.adapters.items():
            stats = self.adapter_stats.get(adapter_id, TokenStats())
            model_name = adapter.model
            
            # Rate limit bilgilerini al
            rate_limits = self.model_rate_limits.get(model_name, {'rpm': 1000, 'tpm': 100000})
            
            # Cost per request hesapla
            cost_per_request = stats.total_cost / stats.requests_count if stats.requests_count > 0 else 0
            
            # Throughput efficiency (actual vs theoretical)
            theoretical_capacity = rate_limits['rpm'] * 60  # per hour
            actual_throughput = stats.requests_count / max(1, (time.time() - stats.last_request_time) / 3600) if stats.last_request_time else 0
            throughput_efficiency = min(100, (actual_throughput / theoretical_capacity) * 100) if theoretical_capacity > 0 else 0
            
            comparison['models'][adapter_id] = {
                'model_name': model_name,
                'total_requests': stats.requests_count,
                'avg_response_time': round(stats.avg_response_time, 3),
                'success_rate': round(stats.get_success_rate(), 2),
                'total_cost': round(stats.total_cost, 4),
                'cost_per_request': round(cost_per_request, 6),
                'tokens_per_second': round(stats.total_tokens / max(1, stats.avg_response_time), 2),
                'throughput_efficiency': round(throughput_efficiency, 2),
                'rate_limits': rate_limits,
                'cost_category': 'FREE' if stats.total_cost == 0 else 'PAID'
            }
        
        # En iyi performans gösterenleri belirle
        if comparison['models']:
            # En hızlı model
            fastest = min(comparison['models'].items(), 
                         key=lambda x: x[1]['avg_response_time'] if x[1]['avg_response_time'] > 0 else float('inf'))
            comparison['best_performers']['fastest'] = fastest[0]
            
            # En ekonomik model
            cheapest = min(comparison['models'].items(),
                          key=lambda x: x[1]['cost_per_request'])
            comparison['best_performers']['most_economical'] = cheapest[0]
            
            # En yüksek throughput
            highest_throughput = max(comparison['models'].items(),
                                   key=lambda x: x[1]['throughput_efficiency'])
            comparison['best_performers']['highest_throughput'] = highest_throughput[0]
        
        return comparison
    
    def get_cost_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Maliyet optimizasyonu önerileri"""
        recommendations = []
        
        performance_data = self.get_model_performance_comparison()
        
        # 1. Ücretsiz modellere geçiş önerisi
        free_models = [model for model, data in performance_data['models'].items() 
                      if data['cost_category'] == 'FREE']
        paid_models = [model for model, data in performance_data['models'].items() 
                      if data['cost_category'] == 'PAID']
        
        if free_models and paid_models:
            best_free = max(free_models, 
                          key=lambda x: performance_data['models'][x]['throughput_efficiency'])
            
            recommendations.append({
                'type': 'COST_REDUCTION',
                'priority': 'HIGH',
                'title': 'Ücretsiz Model Kullanımı',
                'description': f'{best_free} modeli ücretsiz olup yüksek performans sunuyor.',
                'estimated_savings': f'~%{self._calculate_potential_savings(paid_models, best_free)}',
                'action': f'Paid modellerden {best_free} modeline geçiş yapın'
            })
        
        # 2. Ultra-high throughput modelleri önerisi
        ultra_models = ['gemini-2.0-flash', 'gemini-2.0-flash-lite', 'gemini-2.5-flash-lite-preview']
        available_ultra = [model for model in ultra_models 
                          if any(model in adapter.model for adapter in self.adapters.values())]
        
        if not available_ultra:
            recommendations.append({
                'type': 'PERFORMANCE_BOOST',
                'priority': 'MEDIUM',
                'title': '2025 Ultra-High Throughput Modelleri',
                'description': 'Gemini 2.0 Flash ve 2.5 Flash-Lite 30,000 RPM kapasitesi sunuyor.',
                'estimated_improvement': '+200% throughput capacity',
                'action': 'Ultra modelleri sisteme ekleyin'
            })
        
        # 3. Load balancing önerisi
        model_usage = {model: data['total_requests'] 
                      for model, data in performance_data['models'].items()}
        if model_usage:
            max_usage = max(model_usage.values())
            min_usage = min(model_usage.values())
            imbalance_ratio = max_usage / max(1, min_usage)
            
            if imbalance_ratio > 3:  # %300'den fazla dengesizlik
                recommendations.append({
                    'type': 'LOAD_BALANCING',
                    'priority': 'MEDIUM',
                    'title': 'Yük Dağılımı Optimizasyonu',
                    'description': f'Model kullanımında %{int(imbalance_ratio*100)}\'lük dengesizlik tespit edildi.',
                    'estimated_improvement': '+25% overall efficiency',
                    'action': 'Load balancing algoritması uygulayın'
                })
        
        return recommendations
    
    def _calculate_potential_savings(self, paid_models: List[str], alternative_model: str) -> int:
        """Potansiyel maliyet tasarrufu hesapla"""
        total_paid_cost = sum(self.adapter_stats.get(model, TokenStats()).total_cost 
                             for model in paid_models)
        if total_paid_cost > 0:
            return min(90, int((total_paid_cost * 100) / max(total_paid_cost, 0.01)))
        return 0
    
    def get_performance_trends(self) -> Dict[str, Any]:
        """Performans trend analizi"""
        trends = {
            'response_time_trend': 'stable',  # stable, improving, degrading
            'cost_trend': 'stable',
            'throughput_trend': 'stable',
            'error_rate_trend': 'stable',
            'predictions': {
                'next_hour_cost': 0.0,
                'bottleneck_risk': 'low',  # low, medium, high
                'capacity_warning': None
            }
        }
        
        # Basit trend analizi (gerçek uygulamada daha karmaşık olabilir)
        current_avg_response = self.global_stats.avg_response_time
        
        if current_avg_response > 3.0:
            trends['response_time_trend'] = 'degrading'
            trends['predictions']['bottleneck_risk'] = 'high'
        elif current_avg_response < 1.0:
            trends['response_time_trend'] = 'improving'
        
        # Maliyet trend analizi
        hourly_cost_rate = self.global_stats.total_cost
        trends['predictions']['next_hour_cost'] = round(hourly_cost_rate, 4)
        
        # Kapasite uyarıları
        for adapter_id, adapter in self.adapters.items():
            stats = self.adapter_stats.get(adapter_id, TokenStats())
            rate_limits = self.model_rate_limits.get(adapter.model, {'rpm': 1000})
            
            if stats.requests_count > (rate_limits['rpm'] * 0.8):  # %80 kapasiteye yakın
                trends['predictions']['capacity_warning'] = f'{adapter_id} kapasitesinin %80\'ine yaklaştı'
                break
        
        return trends
    
    def get_advanced_analytics_dashboard(self) -> Dict[str, Any]:
        """Gelişmiş analytics dashboard verisi"""
        return {
            'model_comparison': self.get_model_performance_comparison(),
            'cost_optimization': self.get_cost_optimization_recommendations(),
            'performance_trends': self.get_performance_trends(),
            'system_health': {
                'overall_score': self._calculate_system_health_score(),
                'critical_alerts': self._get_critical_alerts(),
                'recommendations_count': len(self.get_cost_optimization_recommendations())
            },
            'capacity_planning': {
                'current_utilization': self._get_current_utilization(),
                'growth_projection': self._get_growth_projection(),
                'scaling_recommendations': self._get_scaling_recommendations()
            }
        }
    
    def _calculate_system_health_score(self) -> int:
        """Sistem sağlık skoru hesapla (0-100)"""
        score = 100
        
        # Error rate penalty
        if self.global_stats.errors_count > 0:
            error_rate = self.global_stats.errors_count / max(1, self.global_stats.requests_count)
            score -= min(30, error_rate * 100)
        
        # Response time penalty
        if self.global_stats.avg_response_time > 2.0:
            score -= min(20, (self.global_stats.avg_response_time - 2.0) * 10)
        
        # Low usage penalty
        if self.global_stats.requests_count < 10:
            score -= 10
        
        return max(0, int(score))
    
    def _get_critical_alerts(self) -> List[str]:
        """Kritik uyarıları al"""
        alerts = []
        
        if self.global_stats.avg_response_time > 5.0:
            alerts.append('Yüksek yanıt süresi tespit edildi')
        
        error_rate = self.global_stats.errors_count / max(1, self.global_stats.requests_count)
        if error_rate > 0.1:  # %10'dan fazla hata
            alerts.append(f'Yüksek hata oranı: %{int(error_rate*100)}')
        
        if len(self.adapters) == 0:
            alerts.append('Hiçbir AI adapter yapılandırılmamış')
        
        return alerts
    
    def _get_current_utilization(self) -> Dict[str, float]:
        """Mevcut kapasite kullanımı"""
        utilization = {}
        
        for adapter_id, adapter in self.adapters.items():
            stats = self.adapter_stats.get(adapter_id, TokenStats())
            rate_limits = self.model_rate_limits.get(adapter.model, {'rpm': 1000})
            
            current_rpm = stats.requests_count  # Simplified calculation
            utilization[adapter_id] = min(100, (current_rpm / rate_limits['rpm']) * 100)
        
        return utilization
    
    def _get_growth_projection(self) -> str:
        """Büyüme projeksiyonu"""
        if self.global_stats.requests_count < 50:
            return 'Yetersiz veri'
        elif self.global_stats.requests_count < 500:
            return 'Düşük büyüme'
        else:
            return 'Yüksek büyüme'
    
    def _get_scaling_recommendations(self) -> List[str]:
        """Ölçeklendirme önerileri"""
        recommendations = []
        
        utilization = self._get_current_utilization()
        high_usage_adapters = [adapter for adapter, usage in utilization.items() if usage > 70]
        
        if high_usage_adapters:
            recommendations.append(f'Yüksek kullanımlı adapter\'lar için ek kapasite ekleyin: {", ".join(high_usage_adapters)}')
        
        if len(self.adapters) < 3:
            recommendations.append('Redundancy için en az 3 adapter kullanın')
        
        return recommendations
    
    # 🤖 FAZ 3: AUTO-OPTIMIZATION METODLARI
    
    def enable_auto_optimization(self, config: Dict[str, Any] = None):
        """Auto-optimization özelliklerini etkinleştir"""
        default_config = {
            'dynamic_model_selection': True,
            'auto_scaling': True,
            'cost_optimization': True,
            'predictive_planning': True,
            'optimization_interval': 300,  # 5 dakika
            'max_cost_threshold': 1.0,     # $1 limit
            'min_success_rate': 95.0,      # %95 başarı oranı
            'max_response_time': 3.0       # 3 saniye
        }
        
        self.auto_optimization_config = {**default_config, **(config or {})}
        self.auto_optimization_enabled = True
        
        print("🤖 Auto-optimization etkinleştirildi!")
        self._log_optimization_config()
    
    def _log_optimization_config(self):
        """Optimization config'ini logla"""
        config = self.auto_optimization_config
        print(f"📊 Optimization parametreleri:")
        print(f"   💰 Max maliyet: ${config['max_cost_threshold']}")
        print(f"   ✅ Min başarı oranı: %{config['min_success_rate']}")
        print(f"   ⚡ Max yanıt süresi: {config['max_response_time']}s")
        print(f"   🔄 Kontrol aralığı: {config['optimization_interval']}s")
    
    def auto_select_optimal_model(self, context: str = "general") -> str:
        """🧠 Akıllı model seçimi - Context-aware optimization"""
        if not hasattr(self, 'auto_optimization_enabled') or not self.auto_optimization_enabled:
            # Fallback to first available adapter
            return list(self.adapters.keys())[0] if self.adapters else None
        
        # Performance metrics al
        performance_data = self.get_model_performance_comparison()
        
        if not performance_data['models']:
            return None
        
        # Context-based scoring
        context_weights = self._get_context_weights(context)
        
        best_model = None
        best_score = -1
        
        for adapter_id, model_data in performance_data['models'].items():
            # Multi-criteria scoring
            score = 0
            
            # Response time score (lower is better)
            response_time = model_data['avg_response_time']
            response_score = max(0, 100 - (response_time * 20))  # 5s = 0 score
            score += response_score * context_weights['speed']
            
            # Cost efficiency score (lower cost is better)
            cost_per_request = model_data['cost_per_request']
            cost_score = 100 if cost_per_request == 0 else max(0, 100 - (cost_per_request * 10000))
            score += cost_score * context_weights['cost']
            
            # Success rate score
            success_rate = model_data['success_rate']
            score += success_rate * context_weights['reliability']
            
            # Throughput score
            throughput_efficiency = model_data['throughput_efficiency']
            score += throughput_efficiency * context_weights['throughput']
            
            # 2025 model priority bonus
            model_name = model_data['model_name']
            if any(new_model in model_name for new_model in ['2.0-flash', '2.5-flash-lite', '2.0-flash-lite']):
                score += 20  # Bonus for latest models
            
            if score > best_score:
                best_score = score
                best_model = adapter_id
        
        print(f"🧠 Auto-selected model: {best_model} (score: {best_score:.1f})")
        return best_model
    
    def _get_context_weights(self, context: str) -> Dict[str, float]:
        """Context'e göre optimization ağırlıklarını belirle"""
        weights = {
            'general': {'speed': 0.3, 'cost': 0.3, 'reliability': 0.3, 'throughput': 0.1},
            'cost_sensitive': {'speed': 0.1, 'cost': 0.6, 'reliability': 0.2, 'throughput': 0.1},
            'performance_critical': {'speed': 0.5, 'cost': 0.1, 'reliability': 0.3, 'throughput': 0.1},
            'high_volume': {'speed': 0.2, 'cost': 0.2, 'reliability': 0.2, 'throughput': 0.4},
            'enterprise': {'speed': 0.2, 'cost': 0.1, 'reliability': 0.5, 'throughput': 0.2}
        }
        
        return weights.get(context, weights['general'])
    
    def auto_scale_adapters(self) -> Dict[str, Any]:
        """🔄 Otomatik adapter scaling"""
        if not hasattr(self, 'auto_optimization_enabled') or not self.auto_optimization_enabled:
            return {'message': 'Auto-optimization devre dışı'}
        
        scaling_actions = {
            'added_adapters': [],
            'removed_adapters': [],
            'rebalanced_roles': [],
            'recommendations': []
        }
        
        # Current utilization analysis
        utilization = self._get_current_utilization()
        
        # High-usage adapter detection
        high_usage_adapters = [aid for aid, usage in utilization.items() if usage > 80]
        
        if high_usage_adapters:
            # Add ultra-high throughput models for load distribution
            ultra_models = ['gemini-2.0-flash', 'gemini-2.0-flash-lite', 'gemini-2.5-flash-lite-preview']
            
            for model in ultra_models:
                if not any(model in adapter.model for adapter in self.adapters.values()):
                    try:
                        # Auto-add high-performance model
                        new_adapter_id = self.add_adapter('gemini', model=model)
                        scaling_actions['added_adapters'].append({
                            'adapter_id': new_adapter_id,
                            'model': model,
                            'reason': 'High utilization scaling',
                            'expected_capacity': '+30,000 RPM'
                        })
                        print(f"🚀 Auto-scaling: {model} adapter eklendi")
                        break  # Only add one at a time
                    except Exception as e:
                        print(f"⚠️ Auto-scaling hatası: {e}")
        
        # Low-usage adapter cleanup
        low_usage_adapters = [aid for aid, usage in utilization.items() if usage < 5 and len(self.adapters) > 2]
        
        if low_usage_adapters:
            # Keep at least 2 adapters for redundancy
            adapter_to_remove = low_usage_adapters[0]
            scaling_actions['recommendations'].append({
                'type': 'REMOVE_ADAPTER',
                'adapter_id': adapter_to_remove,
                'reason': 'Very low utilization',
                'potential_savings': 'Resource cleanup'
            })
        
        return scaling_actions
    
    def predictive_capacity_planning(self) -> Dict[str, Any]:
        """📈 Predictive capacity planning based on usage patterns"""
        if not hasattr(self, 'auto_optimization_enabled') or not self.auto_optimization_enabled:
            return {'message': 'Auto-optimization devre dışı'}
        
        # Simplified predictive analysis
        current_requests = self.global_stats.requests_count
        current_cost = self.global_stats.total_cost
        
        # Growth prediction (simplified)
        if current_requests < 100:
            growth_rate = 'low'
            predicted_requests_24h = current_requests * 2
        elif current_requests < 1000:
            growth_rate = 'moderate'
            predicted_requests_24h = current_requests * 3
        else:
            growth_rate = 'high'
            predicted_requests_24h = current_requests * 5
        
        # Capacity recommendations
        recommendations = []
        
        if predicted_requests_24h > 10000:
            recommendations.append({
                'type': 'CAPACITY_EXPANSION',
                'priority': 'HIGH',
                'message': 'Ultra-high throughput modelleri eklemeyi düşünün',
                'models': ['gemini-2.0-flash', 'gemini-2.5-flash-lite-preview'],
                'expected_capacity': '30,000 RPM per model'
            })
        
        if current_cost > 0.5:  # $0.50+
            recommendations.append({
                'type': 'COST_OPTIMIZATION',
                'priority': 'MEDIUM',
                'message': 'Maliyet optimizasyonu için ücretsiz modelleri değerlendirin',
                'potential_savings': f'~${current_cost * 0.8:.2f}'
            })
        
        return {
            'current_metrics': {
                'requests': current_requests,
                'cost': round(current_cost, 4),
                'growth_rate': growth_rate
            },
            'predictions_24h': {
                'estimated_requests': predicted_requests_24h,
                'estimated_cost': round(current_cost * (predicted_requests_24h / max(1, current_requests)), 4)
            },
            'recommendations': recommendations,
            'confidence': 'medium'  # Basit model için
        }
    
    def intelligent_load_balancing(self, message: str, context: Optional[str] = None) -> str:
        """🎯 Akıllı load balancing - Best adapter selection"""
        if not hasattr(self, 'auto_optimization_enabled') or not self.auto_optimization_enabled:
            # Fallback to simple selection
            return list(self.adapters.keys())[0] if self.adapters else None
        
        # Message complexity analysis
        complexity = self._analyze_message_complexity(message)
        
        # Context mapping
        if complexity == 'high':
            optimal_context = 'performance_critical'
        elif 'cost' in message.lower() or 'budget' in message.lower():
            optimal_context = 'cost_sensitive'
        elif len(message) > 1000:
            optimal_context = 'high_volume'
        else:
            optimal_context = context or 'general'
        
        # Auto-select optimal model
        selected_adapter = self.auto_select_optimal_model(optimal_context)
        
        print(f"🎯 Intelligent load balancing:")
        print(f"   📝 Message complexity: {complexity}")
        print(f"   🎭 Context: {optimal_context}")
        print(f"   🤖 Selected adapter: {selected_adapter}")
        
        return selected_adapter
    
    def _analyze_message_complexity(self, message: str) -> str:
        """Mesaj karmaşıklığını analiz et"""
        if len(message) > 2000:
            return 'high'
        elif len(message) > 500:
            return 'medium'
        else:
            return 'low'
    
    def run_auto_optimization_cycle(self) -> Dict[str, Any]:
        """🔄 Tam otomatik optimization cycle"""
        if not hasattr(self, 'auto_optimization_enabled') or not self.auto_optimization_enabled:
            return {'message': 'Auto-optimization devre dışı'}
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'optimizations_applied': [],
            'recommendations': [],
            'system_health_before': self._calculate_system_health_score(),
            'system_health_after': 0
        }
        
        try:
            # 1. Performance analysis
            trends = self.get_performance_trends()
            
            # 2. Auto-scaling if needed
            scaling_results = self.auto_scale_adapters()
            if scaling_results['added_adapters']:
                results['optimizations_applied'].extend(scaling_results['added_adapters'])
            
            # 3. Cost optimization check
            config = self.auto_optimization_config
            if self.global_stats.total_cost > config['max_cost_threshold']:
                recommendations = self.get_cost_optimization_recommendations()
                high_priority = [r for r in recommendations if r['priority'] == 'HIGH']
                results['recommendations'].extend(high_priority[:2])  # Top 2 high priority
            
            # 4. Predictive planning
            capacity_planning = self.predictive_capacity_planning()
            results['capacity_predictions'] = capacity_planning
            
            # 5. Final health score
            results['system_health_after'] = self._calculate_system_health_score()
            
            # 6. Summary
            improvement = results['system_health_after'] - results['system_health_before']
            results['improvement'] = improvement
            results['status'] = 'success' if improvement >= 0 else 'needs_attention'
            
            print(f"🔄 Auto-optimization cycle completed:")
            print(f"   📊 Health improvement: +{improvement}")
            print(f"   ⚡ Optimizations applied: {len(results['optimizations_applied'])}")
            print(f"   💡 New recommendations: {len(results['recommendations'])}")
            
        except Exception as e:
            results['error'] = str(e)
            results['status'] = 'error'
            print(f"❌ Auto-optimization error: {e}")
        
        return results 