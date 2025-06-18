#!/usr/bin/env python3
"""
🚀 AI Chrome Chat Manager - Quick Start
Kullanıcı dostu başlatma scripti
"""

import os
import sys
import subprocess
from pathlib import Path

def print_banner():
    """Başlık banner'ı"""
    print("="*80)
    print("🎯 AI CHROME CHAT MANAGER - UNIVERSAL EDITION")
    print("   Akıllı AI-to-AI Köprü Sistemi & Plugin Ecosystem")
    print("="*80)

def print_menu():
    """Ana menü"""
    print("\n🎮 ÇALIŞTIRMA SEÇENEKLERİ:")
    print()
    print("1️⃣  DEMO MODE     - API anahtarı gerektirmez")
    print("                   ✨ Web arayüzü simülasyonu")
    print("                   ✨ Plugin test interface")
    print("                   ✨ Analytics dashboard")
    print()
    print("2️⃣  PRODUCTION    - Gerçek API anahtarları gerekir") 
    print("                   🚀 Tam özellikli sistem")
    print("                   🤖 Gerçek AI entegrasyonları")
    print("                   🔌 Aktif plugin sistemi")
    print()
    print("3️⃣  SETUP         - Kurulum yardımcısı")
    print("                   📦 Bağımlılık kontrolü")
    print("                   🔐 API anahtarı konfigürasyonu")
    print()
    print("4️⃣  TEST          - Plugin ve sistem testleri")
    print()
    print("5️⃣  DOCKER        - Docker ile çalıştır")
    print()
    print("0️⃣  ÇIKIŞ")
    print()

def check_requirements():
    """Gereksinimleri kontrol et"""
    print("📦 Gereksinimler kontrol ediliyor...")
    
    try:
        import flask, flask_socketio, requests
        print("✅ Temel modüller yüklü")
        return True
    except ImportError as e:
        print(f"❌ Eksik modül: {e}")
        print("📥 Yüklemek için: pip install -r requirements.txt")
        return False

def setup_environment():
    """Ortam kurulumu"""
    print("\n🔧 KURULUM YARDIMCISI")
    print("="*40)
    
    # Requirements kontrolü
    if not check_requirements():
        choice = input("\n📦 Gereksinimleri şimdi yüklemek ister misiniz? (y/n): ")
        if choice.lower() == 'y':
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                             check=True)
                print("✅ Gereksinimler yüklendi!")
            except subprocess.CalledProcessError:
                print("❌ Yükleme başarısız!")
                return
    
    # .env dosyası kontrolü
    env_file = Path('.env')
    if not env_file.exists():
        print("\n🔐 API Anahtarı Konfigürasyonu")
        print("env.example dosyası .env olarak kopyalanıyor...")
        
        example_file = Path('env.example')
        if example_file.exists():
            import shutil
            shutil.copy('env.example', '.env')
            print("✅ .env dosyası oluşturuldu!")
            print("📝 .env dosyasını düzenleyerek API anahtarlarınızı ekleyin:")
            print("   - GEMINI_API_KEY=your_gemini_key")
            print("   - OPENAI_API_KEY=your_openai_key")
        else:
            print("❌ env.example dosyası bulunamadı!")
    else:
        print("✅ .env dosyası mevcut")
    
    print("\n✅ Kurulum tamamlandı!")

def run_tests():
    """Testleri çalıştır"""
    print("\n🧪 TESTLER ÇALIŞTIRILIYOR")
    print("="*30)
    
    try:
        # Plugin testleri
        result = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Tüm testler başarılı!")
        else:
            print("❌ Bazı testler başarısız!")
            print(result.stdout)
    except FileNotFoundError:
        print("📝 Test framework'ü yükleniyor...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest"], check=True)
        print("✅ Testler için hazır!")

def run_docker():
    """Docker ile çalıştır"""
    print("\n🐳 DOCKER MOD")
    print("="*20)
    
    if not Path('Dockerfile').exists():
        print("❌ Dockerfile bulunamadı!")
        return
    
    try:
        print("🔨 Docker image build ediliyor...")
        subprocess.run(["docker", "build", "-t", "ai-chrome-chat-manager", "."], check=True)
        
        print("🚀 Docker container başlatılıyor...")
        subprocess.run(["docker", "run", "-p", "5000:5000", "ai-chrome-chat-manager"], check=True)
        
    except subprocess.CalledProcessError:
        print("❌ Docker komutu başarısız!")
        print("💡 Docker'ın yüklü ve çalışır durumda olduğundan emin olun")
    except FileNotFoundError:
        print("❌ Docker komutları bulunamadı!")
        print("📥 Docker'ı yükleyin: https://docker.com")

def main():
    """Ana fonksiyon"""
    print_banner()
    
    while True:
        print_menu()
        
        try:
            choice = input("🎯 Seçiminizi yapın (0-5): ").strip()
            
            if choice == "0":
                print("👋 Görüşmek üzere!")
                break
                
            elif choice == "1":
                print("\n🎮 DEMO MODE başlatılıyor...")
                print("🌐 Tarayıcınız otomatik açılacak: http://localhost:5000")
                print("❌ Çıkmak için: Ctrl+C")
                subprocess.run([sys.executable, "run_demo.py"])
                
            elif choice == "2":
                print("\n🚀 PRODUCTION MODE başlatılıyor...")
                subprocess.run([sys.executable, "run_production.py"])
                
            elif choice == "3":
                setup_environment()
                
            elif choice == "4":
                run_tests()
                
            elif choice == "5":
                run_docker()
                
            else:
                print("❌ Geçersiz seçim! Lütfen 0-5 arası bir sayı girin.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Program sonlandırıldı!")
            break
        except Exception as e:
            print(f"❌ Hata: {e}")
        
        # Devam etmek için bekle
        input("\n⏎ Devam etmek için Enter'a basın...")

if __name__ == "__main__":
    main() 