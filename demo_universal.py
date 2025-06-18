"""
Demo Script - Universal AI Chat Manager
Analytics Dashboard'u test etmek için
"""
import asyncio
import sys
import os

# Projeyi path'e ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.universal_ai_adapter import UniversalAIAdapter, SecureConfigManager
from src.message_broker import MessageBroker
from src.memory_bank_integration import MemoryBankIntegration
from src.web_ui_universal import WebUIUniversal

async def setup_demo():
    """Demo için sistemi kur"""
    print("🚀 Demo başlatılıyor...")
    
    # Temel bileşenler
    message_broker = MessageBroker()
    
    # Memory Bank (demo için basit başlatma)
    memory_bank = MemoryBankIntegration(
        project_goal="AI Chrome Chat Manager - Universal Edition Demo",
        location="./demo-memory-bank"
    )
    memory_bank.initialize_memory_bank()
    
    # Config Manager (demo için)
    config_manager = SecureConfigManager("config/api_keys_demo.enc")
    
    # Demo API anahtarları (gerçek değilse bile adapter oluşturmak için)
    config_manager.save_api_key("gemini", "demo-gemini-key")
    config_manager.save_api_key("openai", "demo-openai-key")
    
    # UniversalAIAdapter
    ai_adapter = UniversalAIAdapter(config_manager)
    
    # Demo adapter'ları ekle
    gemini_id = ai_adapter.add_adapter("gemini", api_key="demo-gemini-key")
    openai_id = ai_adapter.add_adapter("openai", api_key="demo-openai-key")
    
    # Rolleri ata
    ai_adapter.assign_role("project_manager", gemini_id)
    ai_adapter.assign_role("lead_developer", openai_id)
    
    # Demo istatistikleri ekle (gerçek API çağrısı yapmadan)
    # Bu kısım normalde API çağrıları sonrası otomatik güncellenir
    gemini_adapter = ai_adapter.adapters.get(gemini_id)
    if gemini_adapter:
        gemini_adapter.stats = {
            'requests': 15,
            'tokens': 12500,
            'cost': 0.125,
            'errors': 1,
            'input_tokens': 7500,
            'output_tokens': 5000
        }
    
    openai_adapter = ai_adapter.adapters.get(openai_id)
    if openai_adapter:
        openai_adapter.stats = {
            'requests': 23,
            'tokens': 18700,
            'cost': 0.374,
            'errors': 0,
            'input_tokens': 10200,
            'output_tokens': 8500
        }
    
    # Web UI başlat
    web_ui = WebUIUniversal(
        host="0.0.0.0",
        port=5000,
        message_broker=message_broker,
        memory_bank=memory_bank,
        ai_adapter=ai_adapter
    )
    
    print("✅ Demo bileşenleri hazır!")
    return web_ui

async def main():
    """Ana demo fonksiyonu"""
    print("="*60)
    print("🎯 AI Chrome Chat Manager - Universal Edition Demo")
    print("="*60)
    
    # Demo'yu kur
    web_ui = await setup_demo()
    
    # Web UI'yı başlat
    web_ui.start_background()
    
    print("\n🌐 Web arayüzü başlatıldı: http://localhost:5000")
    print("📊 Analytics Dashboard'u görüntülemek için tarayıcınızı açın")
    print("\n✨ Demo Özellikleri:")
    print("  - Canlı analytics metrikleri")
    print("  - AI adapter performans kartları")
    print("  - Token kullanım görselleştirmesi")
    print("  - Real-time SocketIO güncellemeleri")
    print("\n❌ Çıkmak için Ctrl+C")
    
    try:
        # Sürekli çalışmasını sağla
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n👋 Demo sonlandırılıyor...")
    finally:
        print("✅ Demo tamamlandı!")

if __name__ == "__main__":
    asyncio.run(main()) 