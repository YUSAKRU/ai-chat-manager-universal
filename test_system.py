#!/usr/bin/env python3
"""
AI Chrome Chat Manager Test Script
Sistem test ve doğrulama için hızlı script
"""

import os
import sys
import traceback
from datetime import datetime

# Proje root'unu sys.path'e ekle
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))

def test_imports():
    """Tüm modüllerin import edilebilirliğini test et"""
    print("🔍 Import testleri...")
    
    modules = [
        'config',
        'logger',
        'message_broker',
        'browser_handler',
        'memory_bank_integration',
        'web_ui',
        'roles.project_manager',
        'roles.lead_developer',
        'roles.boss'
    ]
    
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except Exception as e:
            print(f"❌ {module}: {str(e)}")
            return False
    
    return True

def test_config():
    """Konfigürasyon ayarlarını test et"""
    print("\n🔧 Konfigürasyon testleri...")
    
    try:
        from config import Config
        
        # Gerekli klasörleri oluştur
        Config.ensure_directories()
        
        # Web ayarları kontrolü
        print(f"✅ Web Host: {Config.WEB_HOST}")
        print(f"✅ Web Port: {Config.WEB_PORT}")
        print(f"✅ Default URLs tanımlı: {len(Config.DEFAULT_URLS)} adet")
        
        return True
    except Exception as e:
        print(f"❌ Config hatası: {str(e)}")
        return False

def test_logger():
    """Logger sistemini test et"""
    print("\n📝 Logger testleri...")
    
    try:
        from logger import logger
        
        logger.info("Test info mesajı", "TEST")
        logger.warning("Test uyarı mesajı", "TEST")
        logger.debug("Test debug mesajı", "TEST")
        
        print("✅ Logger çalışıyor")
        return True
    except Exception as e:
        print(f"❌ Logger hatası: {str(e)}")
        return False

def test_message_broker():
    """Message broker sistemini test et"""
    print("\n📡 Message Broker testleri...")
    
    try:
        from message_broker import MessageBroker
        
        broker = MessageBroker()
        
        # Test callback
        received_messages = []
        def test_callback(message):
            received_messages.append(message)
          # Subscribe ve publish test
        broker.subscribe("test_channel", test_callback)
        broker.publish("test_channel", "Test mesajı", sender="TestSender")
        
        if len(received_messages) > 0:
            print("✅ Message Broker çalışıyor")
            return True
        else:
            print("❌ Message Broker: Mesaj alınamadı")
            return False
            
    except Exception as e:
        print(f"❌ Message Broker hatası: {str(e)}")
        traceback.print_exc()
        return False

def test_memory_bank():
    """Memory Bank entegrasyonunu test et"""
    print("\n🧠 Memory Bank testleri...")
    
    try:
        from memory_bank_integration import MemoryBankIntegration
          # Test memory bank instance
        memory_bank = MemoryBankIntegration(
            project_goal="Test projesi",
            location=os.path.join(project_root, "test_memory_bank")
        )
        
        # Klasör kontrol
        if os.path.exists(memory_bank.location):
            print("✅ Memory Bank klasörü mevcut")
        else:
            print("⚠️ Memory Bank klasörü oluşturulacak")
            
        print("✅ Memory Bank integration çalışıyor")
        return True
        
    except Exception as e:
        print(f"❌ Memory Bank hatası: {str(e)}")
        return False

def test_web_ui():
    """Web UI bileşenini test et (import only)"""
    print("\n🌐 Web UI testleri...")
    
    try:
        from web_ui import WebUI
        print("✅ Web UI import edildi")
        return True
        
    except Exception as e:
        print(f"❌ Web UI hatası: {str(e)}")
        return False

def test_roles():
    """Role sınıflarını test et"""
    print("\n🎭 Role testleri...")
    
    try:
        from message_broker import MessageBroker
        from browser_handler import BrowserHandler
        from roles.project_manager import ProjectManager
        from roles.lead_developer import LeadDeveloper
        from roles.boss import Boss
        
        # Mock objeler oluştur
        broker = MessageBroker()
        browser = BrowserHandler()
        
        # Role instanceları oluştur
        pm = ProjectManager(broker, browser)
        ld = LeadDeveloper(broker, browser)
        boss = Boss(broker, browser)
        
        print("✅ Project Manager role")
        print("✅ Lead Developer role")
        print("✅ Boss role")
        
        return True
        
    except Exception as e:
        print(f"❌ Roles hatası: {str(e)}")
        return False

def main():
    """Ana test fonksiyonu"""
    print("🚀 AI Chrome Chat Manager Test Sistemi")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("Config Tests", test_config),
        ("Logger Tests", test_logger),
        ("Message Broker Tests", test_message_broker),
        ("Memory Bank Tests", test_memory_bank),
        ("Web UI Tests", test_web_ui),
        ("Roles Tests", test_roles)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} başarısız!")
        except Exception as e:
            print(f"❌ {test_name} kritik hata: {str(e)}")
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print(f"📊 TEST SONUCU: {passed}/{total} başarılı")
    
    if passed == total:
        print("🎉 Tüm testler başarılı! Sistem çalıştırılabilir.")
        return True
    else:
        print("⚠️ Bazı testler başarısız. Lütfen hataları düzeltin.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
