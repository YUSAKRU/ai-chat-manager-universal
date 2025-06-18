#!/usr/bin/env python3
"""
🚀 AI Chrome Chat Manager - Production Mode Runner
Gerçek API anahtarları ile tam özellikli çalıştırıcı
"""

import os
import sys
import asyncio
import webbrowser
import time
from pathlib import Path

# Projeyi path'e ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def print_welcome():
    """Karşılama mesajı"""
    print("="*70)
    print("🎯 AI CHROME CHAT MANAGER - PRODUCTION MODE")
    print("="*70)
    print()
    print("🆕 YENİ! Web Tabanlı API Yönetimi:")
    print("   ✅ Grafik arayüzde API anahtarı ekleme")
    print("   ✅ Real-time API anahtarı test etme")
    print("   ✅ Rol bazlı API ataması")
    print("   ✅ Güvenli şifrelenmiş saklama")
    print()

def print_instructions():
    """Kullanım talimatları"""
    print("📋 KULLANIM TALİMATLARI:")
    print("="*30)
    print("1️⃣  Web arayüzü otomatik açılacak")
    print("2️⃣  'API Yönetimi' linkine tıklayın")
    print("3️⃣  API anahtarlarınızı ekleyin:")
    print("     🤖 Gemini: https://makersuite.google.com/app/apikey")
    print("     🧠 OpenAI: https://platform.openai.com/api-keys")
    print("4️⃣  Test edin ve kaydedin")
    print("5️⃣  Rolleri atayın ve sistemi kullanın!")
    print()

async def main():
    """Ana production fonksiyonu"""
    print_welcome()
    print_instructions()
    
    try:
        # Production modüllerini import et
        from src.main_universal import main as run_universal
        
        print("🚀 Production mode başlatılıyor...")
        print("📊 Tüm özellikler aktif:")
        print("  ✅ Web-based API management")
        print("  ✅ Role-based AI architecture")
        print("  ✅ Memory Bank sistemi")
        print("  ✅ Plugin ecosystem")
        print("  ✅ Analytics dashboard")
        print("  ✅ Director intervention system")
        print()
        print("🌐 Web arayüzü: http://localhost:5000")
        print("🔑 API Yönetimi: http://localhost:5000/api-management")
        print("❌ Çıkmak için: Ctrl+C")
        print("="*70)
        
        # 2 saniye bekle sonra tarayıcıyı aç
        def open_browser():
            time.sleep(2)
            try:
                webbrowser.open('http://localhost:5000')
                print("🌐 Tarayıcı açıldı!")
            except:
                print("🌐 Tarayıcı açılamadı, manuel olarak açın: http://localhost:5000")
        
        # Background'da tarayıcıyı aç
        import threading
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Universal sistem başlat
        await run_universal()
        
    except ImportError as e:
        print(f"❌ Modül import hatası: {e}")
        print("📦 Gerekli modülleri yüklemek için: pip install -r requirements.txt")
    except KeyboardInterrupt:
        print("\n👋 Production mode sonlandırılıyor...")
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("✅ Production mode tamamlandı!")

if __name__ == "__main__":
    asyncio.run(main()) 