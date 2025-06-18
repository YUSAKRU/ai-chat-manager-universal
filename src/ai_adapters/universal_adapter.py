"""
Universal AI Adapter - Tüm AI servislerini yöneten ana sınıf
"""
from typing import Dict, List, Optional, Any
import asyncio
from dataclasses import dataclass
from .base_adapter import BaseAIAdapter, AIConfig, AIResponse
from .gemini_adapter import GeminiAdapter
from .openai_adapter import OpenAIAdapter
from .secure_config import SecureConfigManager
from logger import logger

@dataclass
class AdapterStats:
    """Adapter istatistikleri"""
    total_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    error_count: int = 0
    
class UniversalAIAdapter:
    """Tüm AI adaptörlerini yöneten merkezi sınıf"""
    
    def __init__(self):
        self.adapters: Dict[str, BaseAIAdapter] = {}
        self.active_adapters: Dict[str, str] = {}  # role_id -> adapter_key
        self.stats: Dict[str, AdapterStats] = {}
        self.config_manager = SecureConfigManager()
        
        # Desteklenen adaptörler
        self.adapter_classes = {
            'gemini': GeminiAdapter,
            'openai': OpenAIAdapter,
            # Future: 'claude': ClaudeAdapter,
            # Future: 'mistral': MistralAdapter
        }
        
    async def initialize_from_config(self, config_file: str = ".env"):
        """Konfigürasyon dosyasından adaptörleri başlat"""
        try:
            # Güvenli config yükle
            configs = await self.config_manager.load_secure_configs(config_file)
            
            for adapter_id, config_data in configs.items():
                adapter_type = config_data.get('type', 'gemini')
                
                if adapter_type in self.adapter_classes:
                    ai_config = AIConfig(
                        api_key=config_data['api_key'],
                        model_name=config_data.get('model', 'gemini-2.0-flash'),
                        max_tokens=config_data.get('max_tokens', 2000),
                        temperature=config_data.get('temperature', 0.7),
                        rate_limit_rpm=config_data.get('rate_limit_rpm', 60),
                        rate_limit_tpm=config_data.get('rate_limit_tpm', 1000000)
                    )
                    
                    # Adapter oluştur
                    adapter_class = self.adapter_classes[adapter_type]
                    adapter = adapter_class(ai_config)
                    
                    # Kaydet
                    self.adapters[adapter_id] = adapter
                    self.stats[adapter_id] = AdapterStats()
                    
                    logger.info(f"✅ {adapter_id} adaptörü başlatıldı ({adapter_type})", "UNIVERSAL_ADAPTER")
            
            # Varsayılan rol atamaları
            self._setup_default_roles()
            
            return True
            
        except Exception as e:
            logger.error(f"Adaptör başlatma hatası: {str(e)}", "UNIVERSAL_ADAPTER", e)
            return False
    
    def _setup_default_roles(self):
        """Varsayılan rol-adapter eşleşmeleri"""
        # Gemini varsa PM olarak kullan
        if 'gemini_pm' in self.adapters:
            self.active_adapters['project_manager'] = 'gemini_pm'
        
        # OpenAI varsa LD olarak kullan  
        if 'openai_ld' in self.adapters:
            self.active_adapters['lead_developer'] = 'openai_ld'
        elif 'gemini_ld' in self.adapters:
            self.active_adapters['lead_developer'] = 'gemini_ld'
    
    def add_adapter(self, adapter_id: str, adapter_type: str, config: AIConfig):
        """Manuel adapter ekleme"""
        if adapter_type not in self.adapter_classes:
            raise ValueError(f"Desteklenmeyen adapter tipi: {adapter_type}")
        
        adapter_class = self.adapter_classes[adapter_type]
        adapter = adapter_class(config)
        
        self.adapters[adapter_id] = adapter
        self.stats[adapter_id] = AdapterStats()
        
        logger.info(f"✅ {adapter_id} adaptörü eklendi ({adapter_type})", "UNIVERSAL_ADAPTER")
    
    def assign_role(self, role_id: str, adapter_id: str):
        """Bir role adapter ata"""
        if adapter_id not in self.adapters:
            raise ValueError(f"Adapter bulunamadı: {adapter_id}")
        
        self.active_adapters[role_id] = adapter_id
        logger.info(f"📌 {role_id} rolü -> {adapter_id} adaptörüne atandı", "UNIVERSAL_ADAPTER")
    
    async def send_message(
        self, 
        role_id: str, 
        message: str, 
        context: Optional[str] = None
    ) -> Optional[AIResponse]:
        """Role göre mesaj gönder"""
        
        # Role atanmış adapter var mı?
        if role_id not in self.active_adapters:
            logger.error(f"Role atanmamış: {role_id}", "UNIVERSAL_ADAPTER")
            return None
        
        adapter_id = self.active_adapters[role_id]
        adapter = self.adapters[adapter_id]
        
        try:
            # Role göre context oluştur
            role_context = self._get_role_context(role_id)
            
            # Mesajı gönder
            response = await adapter.send_message(
                message=message,
                context=context,
                role_context=role_context
            )
            
            # İstatistikleri güncelle
            stats = self.stats[adapter_id]
            stats.total_requests += 1
            stats.total_tokens += response.usage['total_tokens']
            stats.total_cost += adapter.estimate_cost(
                response.usage['input_tokens'],
                response.usage['output_tokens']
            )
            
            logger.info(
                f"✅ {role_id} yanıt verdi ({adapter_id}: {response.model})",
                "UNIVERSAL_ADAPTER"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"❌ {role_id} mesaj hatası: {str(e)}", "UNIVERSAL_ADAPTER", e)
            self.stats[adapter_id].error_count += 1
            return None
    
    def _get_role_context(self, role_id: str) -> str:
        """Role göre system prompt"""
        contexts = {
            "project_manager": """Sen bir Proje Yöneticisisin. Görevlerin:
- Projeleri planlama ve organize etme
- Ekip koordinasyonu sağlama  
- İlerleme takibi yapma
- Karar verme ve yönlendirme
- Risk analizi ve çözüm önerme

Profesyonel, yapıcı ve sonuç odaklı ol.""",

            "lead_developer": """Sen bir Uzman Geliştiricissin. Görevlerin:
- Teknik problemleri analiz etme ve çözme
- Kod kalitesi ve mimari kararları verme
- Teknik dokümantasyon hazırlama
- Yeni teknolojileri araştırma
- Best practice'leri uygulama

Teknik detayları açık ve anlaşılır şekilde açıkla.""",

            "boss": """Sen şirketin patronusun. Görevlerin:
- Stratejik kararlar verme
- Proje önceliklerini belirleme
- Kaynak tahsisi yapma
- Performans değerlendirme
- Vizyon ve hedef belirleme

Otoriter ama adil, sonuç odaklı ve stratejik düşün."""
        }
        
        return contexts.get(role_id, "Sen yardımcı bir AI asistanısın.")
    
    def get_adapter_status(self, adapter_id: str = None) -> Dict[str, Any]:
        """Adapter durumu"""
        if adapter_id:
            if adapter_id not in self.adapters:
                return {"error": "Adapter bulunamadı"}
            
            adapter = self.adapters[adapter_id]
            stats = self.stats[adapter_id]
            
            return {
                "id": adapter_id,
                "type": adapter.__class__.__name__,
                "model": adapter.config.model_name,
                "stats": {
                    "requests": stats.total_requests,
                    "tokens": stats.total_tokens,
                    "cost": f"${stats.total_cost:.4f}",
                    "errors": stats.error_count
                },
                "rate_limit": {
                    "available": adapter.check_rate_limit()
                }
            }
        else:
            # Tüm adaptörlerin durumu
            return {
                adapter_id: self.get_adapter_status(adapter_id)
                for adapter_id in self.adapters
            }
    
    def get_role_assignments(self) -> Dict[str, str]:
        """Rol atamalarını döndür"""
        return self.active_adapters.copy()
    
    def get_total_stats(self) -> Dict[str, Any]:
        """Toplam istatistikler"""
        total_requests = sum(s.total_requests for s in self.stats.values())
        total_tokens = sum(s.total_tokens for s in self.stats.values())
        total_cost = sum(s.total_cost for s in self.stats.values())
        total_errors = sum(s.error_count for s in self.stats.values())
        
        return {
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "total_cost": f"${total_cost:.4f}",
            "total_errors": total_errors,
            "adapters_count": len(self.adapters),
            "active_roles": len(self.active_adapters)
        }
    
    def clear_conversation_history(self, role_id: str = None):
        """Konuşma geçmişini temizle"""
        if role_id and role_id in self.active_adapters:
            adapter_id = self.active_adapters[role_id]
            self.adapters[adapter_id].clear_history()
            logger.info(f"🗑️ {role_id} konuşma geçmişi temizlendi", "UNIVERSAL_ADAPTER")
        else:
            for adapter in self.adapters.values():
                adapter.clear_history()
            logger.info("🗑️ Tüm konuşma geçmişleri temizlendi", "UNIVERSAL_ADAPTER") 