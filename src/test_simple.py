"""
Basit test sürümü - sadece browser yönetimi ve mesajlaşma
"""
import os
import time
from browser_handler import BrowserHandler
from message_broker import MessageBroker
from roles.project_manager import ProjectManager
from roles.lead_developer import LeadDeveloper
from roles.boss import Boss
from config import Config

def test_simple():
    print("🧪 Basit Test Başlatılıyor...")
    
    # Konfigürasyon
    Config.ensure_directories()
    
    # Bileşenleri başlat
    message_broker = MessageBroker()
    browser_handler = BrowserHandler()
    
    # Rolleri oluştur
    pm = ProjectManager(message_broker, browser_handler)
    ld = LeadDeveloper(message_broker, browser_handler)
    boss = Boss(message_broker, browser_handler)
    
    print("✅ Sistem bileşenleri hazır!")
    
    # Browser test
    print("\n🌐 Browser test başlatılsın mı? (y/n): ", end="")
    if input().lower() == 'y':
        
        # Tek pencere test
        print("📱 ChatGPT penceresi açılıyor...")
        pm_driver = browser_handler.open_window("project_manager", "https://chatgpt.com")
        
        if pm_driver:
            print("✅ Pencere açıldı! Giriş yapın ve hazır olduğunuzda ENTER'a basın...")
            input()
            
            # Rol tanımlaması gönder
            role_msg = Config.ROLE_DESCRIPTIONS['project_manager']
            print("📝 Rol tanımlaması gönderiliyor...")
            browser_handler.send_message("project_manager", role_msg)
            
            print("⏱️ 5 saniye bekleyin...")
            time.sleep(5)
            
            # Test mesajı
            print("📨 Test mesajı gönderiliyor...")
            test_msg = "Merhaba! Sistem testi yapıyorum. Bu mesajı aldıysan sistem çalışıyor demektir. Kısa bir yanıt verebilir misin?"
            browser_handler.send_message("project_manager", test_msg)
            
            print("✅ Test tamamlandı!")
            print("❌ Çıkmak için ENTER'a basın...")
            input()
            
            browser_handler.close_all_windows()
        else:
            print("❌ Pencere açılamadı!")
    
    # Mesaj sistemi test
    print("\n💬 Mesaj sistemi test başlatılsın mı? (y/n): ", end="")
    if input().lower() == 'y':
        print("📢 Test mesajları gönderiliyor...")
        
        # Boss konuşmaya katıl
        boss.join_conversation()
        time.sleep(2)
        
        # PM görev atasın
        pm.assign_task("Test görevi: Basit bir web uygulaması prototipi oluştur")
        time.sleep(2)
        
        # LD yanıt versin
        ld.acknowledge_task("Test görevi alındı")
        time.sleep(2)
        
        # Boss müdahale etsin
        boss.send_directive("Bu test görevini öncelik haline getirin!")
        
        print("✅ Mesaj sistemi test tamamlandı!")
        
        # Mesaj geçmişi göster
        print("\n📜 Mesaj geçmişi:")
        for msg in message_broker.get_message_history(limit=10):
            print(f"[{msg['timestamp'][:19]}] {msg['sender']}: {msg['content'][:80]}...")
    
    print("\n🎉 Test tamamlandı!")

if __name__ == "__main__":
    test_simple()
