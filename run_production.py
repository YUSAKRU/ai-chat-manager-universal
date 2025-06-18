#!/usr/bin/env python3
"""
🚀 AI Chrome Chat Manager - Production Mode Runner
Gerçek API anahtarları ile tam özellikli çalıştırıcı
"""

import os
import sys
import asyncio
from pathlib import Path

# Projeyi path'e ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_api_keys():
    """API anahtarlarını kontrol et"""
    print("🔐 API anahtarları kontrol ediliyor...")
    
    # .env dosyasını kontrol et
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env dosyası bulunamadı!")
        print("📝 .env dosyası oluşturmak için:")
        print("   1. env.example dosyasını .env olarak kopyala")
        print("   2. Gerçek API anahtarlarınızı ekleyin")
        return False
    
    # Gerekli API anahtarlarını kontrol et
    from dotenv import load_dotenv
    load_dotenv()
    
    required_keys = ['GEMINI_API_KEY', 'OPENAI_API_KEY']
    missing_keys = []
    
    for key in required_keys:
        if not os.getenv(key):
            missing_keys.append(key)
    
    if missing_keys:
        print(f"❌ Eksik API anahtarları: {', '.join(missing_keys)}")
        print("📝 .env dosyasına ekleyin:")
        for key in missing_keys:
            print(f"   {key}=your_api_key_here")
        return False
    
    print("✅ Tüm API anahtarları mevcut!")
    return True

async def main():
    """Ana production fonksiyonu"""
    print("="*70)
    print("🎯 AI CHROME CHAT MANAGER - PRODUCTION MODE")
    print("="*70)
    
    # API anahtarlarını kontrol et
    if not check_api_keys():
        print("\n💡 Demo mode için: python run_demo.py")
        return
    
    try:
        # Production modüllerini import et
        from src.main_universal import main as run_universal
        
        print("🚀 Production mode başlatılıyor...")
        print("📊 Tüm özellikler aktif:")
        print("  ✅ Gerçek AI API entegrasyonları")
        print("  ✅ Memory Bank sistemi")
        print("  ✅ Plugin ecosystem")
        print("  ✅ Role-based AI architecture")
        print("  ✅ Analytics dashboard")
        print("  ✅ Director intervention system")
        print()
        print("🌐 Web arayüzü: http://localhost:5000")
        print("❌ Çıkmak için: Ctrl+C")
        print("="*70)
        
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