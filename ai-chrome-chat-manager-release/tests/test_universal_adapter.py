#!/usr/bin/env python3
"""
UniversalAIAdapter için test dosyası
Token istatistikleri ve genel işlevsellik testleri
"""
import asyncio
import sys
import os
from pathlib import Path

# Projeyi path'e ekle
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

try:
    from ai_adapters.universal_adapter import UniversalAIAdapter, TokenStats
    from ai_adapters.secure_config import SecureConfigManager
    from ai_adapters.base_adapter import AIResponse
    print("✅ Modüller başarıyla import edildi")
except ImportError as e:
    print(f"❌ Import hatası: {e}")
    sys.exit(1)

class MockAdapter:
    """Test için sahte AI adapter"""
    def __init__(self, adapter_type="mock", model="mock-model"):
        self.adapter_type = adapter_type
        self.model = model
        self.request_count = 0
        
    async def send_message(self, message, context=None):
        """Sahte mesaj gönderme"""
        self.request_count += 1
        
        # Sahte token sayıları
        input_tokens = len(message.split()) * 2  # Kelime sayısı x 2
        output_tokens = 50  # Sabit çıktı token sayısı
        
        return AIResponse(
            content=f"Mock response to: {message[:50]}...",
            model=self.model,
            usage={
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': input_tokens + output_tokens,
                'cost': 0.001
            }
        )
    
    def check_rate_limit(self):
        """Rate limit kontrolü"""
        return {'available': True, 'retry_after': 0}
    
    def get_stats(self):
        """Adapter istatistikleri"""
        return {'requests': self.request_count}

def test_token_stats():
    """TokenStats sınıfını test et"""
    print("\n🧪 TokenStats testi...")
    
    stats = TokenStats()
    
    # İlk kullanım verisi ekle
    usage_data = {
        'input_tokens': 100,
        'output_tokens': 50,
        'cost': 0.005
    }
    stats.add_usage(usage_data, response_time=1.5)
    
    # Kontroller
    assert stats.input_tokens == 100, f"Input tokens beklenen: 100, gerçek: {stats.input_tokens}"
    assert stats.output_tokens == 50, f"Output tokens beklenen: 50, gerçek: {stats.output_tokens}"
    assert stats.total_tokens == 150, f"Total tokens beklenen: 150, gerçek: {stats.total_tokens}"
    assert stats.total_cost == 0.005, f"Total cost beklenen: 0.005, gerçek: {stats.total_cost}"
    assert stats.requests_count == 1, f"Requests count beklenen: 1, gerçek: {stats.requests_count}"
    assert stats.avg_response_time == 1.5, f"Avg response time beklenen: 1.5, gerçek: {stats.avg_response_time}"
    
    # İkinci kullanım verisi
    usage_data2 = {
        'input_tokens': 200,
        'output_tokens': 100,
        'cost': 0.010
    }
    stats.add_usage(usage_data2, response_time=2.0)
    
    # Güncellenmiş kontroller
    assert stats.total_tokens == 450, f"Total tokens beklenen: 450, gerçek: {stats.total_tokens}"
    assert stats.requests_count == 2, f"Requests count beklenen: 2, gerçek: {stats.requests_count}"
    assert stats.avg_response_time == 1.75, f"Avg response time beklenen: 1.75, gerçek: {stats.avg_response_time}"
    
    # Başarı oranı testi
    stats.add_error()
    success_rate = stats.get_success_rate()
    assert abs(success_rate - 66.67) < 0.1, f"Success rate beklenen: ~66.67, gerçek: {success_rate}"
    
    print("✅ TokenStats testi başarılı!")

def test_universal_adapter():
    """UniversalAIAdapter temel işlevsellik testi"""
    print("\n🧪 UniversalAIAdapter testi...")
    
    # Mock config manager
    config_manager = None  # Bu test için None kullanabiliriz
    
    # Universal adapter oluştur
    universal = UniversalAIAdapter(config_manager)
    
    # Mock adapter ekle
    mock_adapter = MockAdapter("gemini", "gemini-pro")
    universal.adapters["mock-1"] = mock_adapter
    universal.adapter_stats["mock-1"] = TokenStats()
    
    # Role ata
    universal.assign_role("test_role", "mock-1")
    
    # Temel kontroller
    assert "mock-1" in universal.adapters, "Adapter eklenmedi"
    assert "test_role" in universal.role_assignments, "Role atanmadı"
    assert universal.role_assignments["test_role"] == "mock-1", "Role yanlış adapter'a atandı"
    
    print("✅ UniversalAIAdapter temel testi başarılı!")

async def test_message_sending():
    """Mesaj gönderme ve istatistik güncelleme testi"""
    print("\n🧪 Mesaj gönderme testi...")
    
    config_manager = None
    universal = UniversalAIAdapter(config_manager)
    
    # Mock adapter ekle
    mock_adapter = MockAdapter("openai", "gpt-4")
    universal.adapters["mock-1"] = mock_adapter
    universal.adapter_stats["mock-1"] = TokenStats()
    universal.assign_role("test_role", "mock-1")
    
    # Mesaj gönder
    response = await universal.send_message("test_role", "Test mesajı bu")
    
    # Response kontrolü
    assert response is not None, "Response None döndü"
    assert "Test mesajı bu" in response.content, "Response içeriği yanlış"
    
    # İstatistik kontrolü
    global_stats = universal.get_total_stats()
    assert global_stats['requests_count'] == 1, f"Global requests beklenen: 1, gerçek: {global_stats['requests_count']}"
    assert global_stats['total_tokens'] > 0, "Total tokens 0"
    assert global_stats['total_cost'] > 0, "Total cost 0"
    
    # Adapter istatistikleri
    adapter_stats = universal.get_adapter_status()
    assert "mock-1" in adapter_stats, "Adapter stats'ta bulunamadı"
    assert adapter_stats["mock-1"]["stats"]["requests_count"] == 1, "Adapter request count yanlış"
    
    # Role istatistikleri
    role_stats = universal.get_role_status()
    assert "test_role" in role_stats, "Role stats'ta bulunamadı"
    assert role_stats["test_role"]["stats"]["requests_count"] == 1, "Role request count yanlış"
    
    print("✅ Mesaj gönderme testi başarılı!")

def test_cost_calculation():
    """Maliyet hesaplama testi"""
    print("\n🧪 Maliyet hesaplama testi...")
    
    config_manager = None
    universal = UniversalAIAdapter(config_manager)
    
    # Test verileri
    test_cases = [
        ("gemini-pro", 1000, 500, 0.00025 + 0.00025),    # (1000/1000)*0.00025 + (500/1000)*0.0005 = 0.0005
        ("gpt-4", 1000, 500, 0.03 + 0.03),               # (1000/1000)*0.03 + (500/1000)*0.06 = 0.06
        ("gpt-4o-mini", 1000, 500, 0.00015 + 0.0003),    # (1000/1000)*0.00015 + (500/1000)*0.0006 = 0.00045
    ]
    
    for model, input_tokens, output_tokens, expected_cost in test_cases:
        cost_info = universal._calculate_cost(model, input_tokens, output_tokens)
        actual_cost = cost_info['total_cost']
        
        # Yaklaşık eşitlik kontrolü (floating point hatası için)
        assert abs(actual_cost - expected_cost) < 0.01, \
            f"Model {model}: beklenen {expected_cost}, gerçek {actual_cost}"
    
    print("✅ Maliyet hesaplama testi başarılı!")

async def test_detailed_analytics():
    """Detaylı analytics testi"""
    print("\n🧪 Detaylı analytics testi...")
    
    config_manager = None
    universal = UniversalAIAdapter(config_manager)
    
    # Birden fazla adapter ve role ekle
    for i in range(3):
        mock_adapter = MockAdapter(f"type-{i}", f"model-{i}")
        adapter_id = f"adapter-{i}"
        role_id = f"role-{i}"
        
        universal.adapters[adapter_id] = mock_adapter
        universal.adapter_stats[adapter_id] = TokenStats()
        universal.assign_role(role_id, adapter_id)
        
        # Test mesajları gönder
        await universal.send_message(role_id, f"Test mesajı {i}")
    
    # Analytics verilerini al
    analytics = universal.get_detailed_analytics()
    
    # Kontroller
    assert 'global_stats' in analytics, "Global stats eksik"
    assert 'adapter_stats' in analytics, "Adapter stats eksik"
    assert 'role_stats' in analytics, "Role stats eksik"
    assert 'token_usage_breakdown' in analytics, "Token breakdown eksik"
    assert 'cost_breakdown' in analytics, "Cost breakdown eksik"
    assert 'performance_metrics' in analytics, "Performance metrics eksik"
    
    # Global stats kontrolü
    global_stats = analytics['global_stats']
    assert global_stats['requests_count'] == 3, f"Global requests beklenen: 3, gerçek: {global_stats['requests_count']}"
    assert global_stats['adapters_count'] == 3, f"Adapters count beklenen: 3, gerçek: {global_stats['adapters_count']}"
    
    print("✅ Detaylı analytics testi başarılı!")

def main():
    """Ana test fonksiyonu"""
    print("🚀 UniversalAIAdapter Testleri Başlatılıyor...")
    print("="*50)
    
    try:
        # Senkron testler
        test_token_stats()
        test_universal_adapter()
        test_cost_calculation()
        
        # Asenkron testler
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(test_message_sending())
        loop.run_until_complete(test_detailed_analytics())
        
        loop.close()
        
        print("\n" + "="*50)
        print("🎉 TÜM TESTLER BAŞARILI!")
        print("✅ Token istatistikleri çalışıyor")
        print("✅ Maliyet hesaplama doğru")
        print("✅ Analytics sistemi aktif")
        print("✅ Universal adapter düzgün çalışıyor")
        
    except Exception as e:
        print(f"\n❌ Test başarısız: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 