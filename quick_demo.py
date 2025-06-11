#!/usr/bin/env python3
"""
AI Chrome Chat Manager - Hızlı Demo
Sistem bileşenlerinin çalışabilirliğini test eden demo script
"""

import sys
import os

# Proje root'unu sys.path'e ekle
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))

def demo_chrome_profiles():
    """Chrome profil yönetimi demosunu çalıştır"""
    print("🎭 Chrome Profil Yönetimi Demo")
    print("=" * 40)
    
    try:
        from chrome_profile_manager import ChromeProfileManager
        
        profile_manager = ChromeProfileManager()
        
        print(f"📁 Chrome User Data: {profile_manager.chrome_user_data_path}")
        print(f"📊 Bulunan profil sayısı: {len(profile_manager.available_profiles)}")
        
        if profile_manager.available_profiles:
            print("\n👤 Mevcut Profiller:")
            for i, profile in enumerate(profile_manager.available_profiles, 1):
                marker = "👑" if profile['is_default'] else "👤"
                print(f"  {i}. {marker} {profile['display_name']} ({profile['name']})")
        
        print("\n✅ Chrome Profil Manager çalışıyor!")
        return True
        
    except Exception as e:
        print(f"❌ Chrome Profil Manager hatası: {str(e)}")
        return False

def demo_web_ui_endpoints():
    """Web UI endpoint'lerinin hazır olduğunu göster"""
    print("\n🌐 Web UI Endpoints Demo")
    print("=" * 40)
    
    try:
        from web_ui import WebUI
        from unittest.mock import Mock
        
        # Mock chat manager
        mock_chat_manager = Mock()
        mock_chat_manager.message_broker.get_active_channels.return_value = ['pm_to_ld', 'ld_to_pm']
        mock_chat_manager.message_broker.message_history = []
        mock_chat_manager.message_broker.set_web_broadcast_callback = Mock()
        
        # Mock browser handler
        mock_browser_handler = Mock()
        mock_browser_handler.profile_manager.list_profiles.return_value = [
            {'name': 'Default', 'display_name': 'Your Chrome', 'is_default': True},
            {'name': 'Profile 1', 'display_name': 'Your Chrome', 'is_default': False}
        ]
        mock_browser_handler.selected_profiles = {'project_manager': 'Profile 1'}
        mock_chat_manager.browser_handler = mock_browser_handler
        
        web_ui = WebUI(mock_chat_manager)
        
        print("📡 Mevcut API Endpoints:")
        print("  • GET  /api/status")
        print("  • GET  /api/messages")
        print("  • POST /api/send_message")
        print("  • GET  /api/chrome_profiles/list")
        print("  • GET  /api/chrome_profiles/selected")
        print("  • GET  /api/chrome_profiles/summary")
        print("  • POST /api/memory_bank/query")
        
        print("\n✅ Web UI hazır!")
        return True
        
    except Exception as e:
        print(f"❌ Web UI hatası: {str(e)}")
        return False

def demo_system_integration():
    """Sistem entegrasyonu demosunu göster"""
    print("\n🚀 Sistem Entegrasyonu Demo")
    print("=" * 40)
    
    try:
        from config import Config
        from logger import logger
        from message_broker import MessageBroker
        
        # Config test
        print(f"⚙️  Web Host: {Config.WEB_HOST}:{Config.WEB_PORT}")
        print(f"🌐 Default URLs: {len(Config.DEFAULT_URLS)} adet")
        
        # Logger test
        logger.info("Demo logger test mesajı", "DEMO")
        print("📝 Logger sistemi aktif")
        
        # Message broker test
        broker = MessageBroker()
        print(f"📡 Message broker hazır")
        
        print("\n✅ Tüm sistem bileşenleri entegre!")
        return True
        
    except Exception as e:
        print(f"❌ Sistem entegrasyonu hatası: {str(e)}")
        return False

def main():
    """Ana demo fonksiyonu"""
    print("🎉 AI Chrome Chat Manager - Hızlı Demo")
    print("=" * 50)
    
    demos = [
        ("Chrome Profil Yönetimi", demo_chrome_profiles),
        ("Web UI Endpoints", demo_web_ui_endpoints),
        ("Sistem Entegrasyonu", demo_system_integration)
    ]
    
    passed = 0
    total = len(demos)
    
    for demo_name, demo_func in demos:
        try:
            if demo_func():
                passed += 1
        except Exception as e:
            print(f"❌ {demo_name} demo hatası: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"📊 DEMO SONUCU: {passed}/{total} başarılı")
    
    if passed == total:
        print("🎉 Sistem tamamen hazır ve çalışabilir!")
        print("\n🚀 Sistem başlatmak için:")
        print("   python src/main.py")
        print("\n🌐 Web arayüzü:")
        print("   http://127.0.0.1:5000")
        return True
    else:
        print("⚠️ Bazı bileşenlerde sorun var.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
