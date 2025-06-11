import os
import time
import threading
import signal
import sys
from browser_handler import BrowserHandler
from message_broker import MessageBroker
from roles.project_manager import ProjectManager
from roles.lead_developer import LeadDeveloper
from roles.boss import Boss
from web_ui import WebUI
from config import Config
from memory_bank_integration import MemoryBankIntegration
from logger import logger, safe_execute, validate_config

class AIChromeChatManager:
    def __init__(self):
        logger.info("AI Chrome Chat Manager başlatılıyor...", "SYSTEM")
        
        # Konfigürasyon ve klasörleri hazırla
        Config.ensure_directories()
        
        # Ana bileşenleri başlat
        self.message_broker = MessageBroker()
        self.browser_handler = BrowserHandler()
        
        # Rolleri oluştur
        self.project_manager = ProjectManager(self.message_broker, self.browser_handler)
        self.lead_developer = LeadDeveloper(self.message_broker, self.browser_handler)
        self.boss = Boss(self.message_broker, self.browser_handler)
        
        # Web UI'ı başlat
        self.web_ui = WebUI(self)
        
        # Memory Bank'ı başlat
        self.memory_bank = MemoryBankIntegration(
            project_goal="İki AI chat penceresi arasında akıllı köprü sistemi geliştirmek",
            location=os.path.join(os.getcwd(), "memory-bank")
        )
        self.memory_bank.initialize_memory_bank()
        
        # Mesajları Web UI'a yayınla (broadcast)
        for channel in [
            'pm_to_ld', 'ld_to_pm', 'boss_to_pm', 'boss_to_ld'
        ]:
            self.message_broker.subscribe(channel, self.web_ui.broadcast_message)
            # Memory Bank'a da mesajları kaydet
            self.message_broker.subscribe(channel, self._save_to_memory_bank)
        self.web_server_thread = None
        
        # Shutdown handler
        signal.signal(signal.SIGINT, self.signal_handler)
        
        print("✅ Sistem hazır!")

    def _save_to_memory_bank(self, message_obj):
        """Mesajları Memory Bank'a kaydet"""
        try:
            # Mesajları topla ve belirli aralıklarla kaydet
            if hasattr(self, '_pending_messages'):
                self._pending_messages.append(message_obj)
            else:
                self._pending_messages = [message_obj]
            
            # Her 5 mesajda bir kaydet
            if len(self._pending_messages) >= 5:
                self.memory_bank.save_conversation(self._pending_messages)
                self._pending_messages = []
        except Exception as e:
            print(f"⚠️ Memory Bank'a kayıt sırasında hata: {str(e)}")

    def signal_handler(self, signum, frame):
        """Sistem kapatma sinyali yakaladığında"""
        print("\n⚠️ Sistem kapatılıyor...")
        self.cleanup()
        sys.exit(0)

    def start_web_ui(self):
        """Web arayüzünü başlat"""
        try:
            self.web_server_thread = self.web_ui.run_in_background(
                host=Config.WEB_HOST, 
                port=Config.WEB_PORT
            )
            return True
        except Exception as e:
            print(f"❌ Web arayüzü başlatılamadı: {str(e)}")
            return False

    def create_profile_directories(self):
        """Chrome profil klasörlerini oluştur"""
        os.makedirs("chrome_profiles/project_manager", exist_ok=True)
        os.makedirs("chrome_profiles/lead_developer", exist_ok=True)
        print("📁 Chrome profil klasörleri oluşturuldu")

    def start_browser_sessions(self):
        """Browser oturumlarını başlat"""
        print("\n🌐 Chrome pencereleri açılıyor...")
        
        # Proje Yöneticisi penceresi
        pm_driver = self.browser_handler.open_window(
            "project_manager", 
            Config.DEFAULT_URLS['project_manager']
        )
        if pm_driver:
            print("✅ Proje Yöneticisi penceresi açıldı")
            print("📝 Lütfen ChatGPT'ye giriş yapın ve hazır olduğunuzda ENTER'a basın...")
            input()
        
        # Lead Developer penceresi  
        ld_driver = self.browser_handler.open_window(
            "lead_developer", 
            Config.DEFAULT_URLS['lead_developer']
        )
        if ld_driver:
            print("✅ Lead Developer penceresi açıldı")
            print("📝 Lütfen Claude'a giriş yapın ve hazır olduğunuzda ENTER'a basın...")
            input()
        
        return pm_driver is not None and ld_driver is not None

    def initialize_roles(self):
        """Rolleri başlat ve tanımla"""
        print("\n🎭 Roller tanımlanıyor...")
        
        # Proje Yöneticisi'ni tanımla
        self.browser_handler.send_message("project_manager", Config.ROLE_DESCRIPTIONS['project_manager'])
        time.sleep(2)
        
        # Lead Developer'ı tanımla
        self.browser_handler.send_message("lead_developer", Config.ROLE_DESCRIPTIONS['lead_developer'])
        
        print("✅ Roller tanımlandı!")

    def start_demo_conversation(self):
        """Demo konuşma başlat"""
        print("\n🎬 Demo konuşma başlatılıyor...")
        
        # İlk görev ataması
        time.sleep(3)
        self.project_manager.assign_task(
            "E-ticaret sitesi için kullanıcı yönetim sistemi geliştirmek. "
            "Kullanıcı kaydı, giriş, profil yönetimi ve yetkilendirme modülleri gerekli."
        )
        
        # Boss'u konuşmaya dahil et
        time.sleep(5)
        self.boss.join_conversation()
        
        # Durum raporu iste
        time.sleep(8)
        self.boss.request_status_report()

    def interactive_mode(self):
        """İnteraktif mod - kullanıcı kontrolü"""
        print("\n🎮 İNTERAKTİF MOD")
        print("Komutlar:")
        print("1 - PM'den görev ata")
        print("2 - Boss müdahalesi")
        print("3 - Durum raporu iste")
        print("4 - Conversation history")
        print("5 - Konuşmayı kaydet")
        print("6 - Memory Bank sorgusu")
        print("7 - Proje özeti (Memory Bank)")
        print("q - Çıkış")
        
        while True:
            try:
                command = input("\n🎯 Komut girin: ").strip()
                
                if command == "1":
                    task = input("📋 Atanacak görev: ")
                    self.project_manager.assign_task(task)
                    
                elif command == "2":
                    message = input("👑 Boss mesajı: ")
                    self.boss.send_directive(message)
                    
                elif command == "3":
                    self.boss.request_status_report()
                    
                elif command == "4":
                    history = self.message_broker.get_message_history(limit=5)
                    print("\n📜 Son 5 mesaj:")
                    for msg in history:
                        print(f"[{msg['timestamp'][:19]}] {msg['sender']}: {msg['content'][:100]}...")
                        
                elif command == "5":
                    filename = f"conversation_{int(time.time())}.json"
                    self.message_broker.save_conversation(filename)
                    
                elif command == "6":
                    query = input("🔍 Memory Bank sorgusu: ")
                    result = self.memory_bank.query_memory_bank(query)
                    print(f"\n📋 Sonuç:\n{result}")
                    
                elif command == "7":
                    summary = self.memory_bank.get_project_summary()
                    print(f"\n📊 Proje Özeti:\n{summary}")
                    
                elif command.lower() == "q":
                    break
                    
                else:
                    print("❌ Geçersiz komut!")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Hata: {str(e)}")

    def cleanup(self):
        """Temizlik işlemleri"""
        print("\n🧹 Sistem kapatılıyor...")
        self.browser_handler.close_all_windows()
        print("✅ Tüm Chrome pencereleri kapatıldı")

def main():
    """Ana fonksiyon"""
    chat_manager = None
    
    try:
        # Sistem başlat
        chat_manager = AIChromeChatManager()
        
        # Web arayüzünü başlat
        print("\n🌐 Web arayüzü başlatılıyor...")
        if chat_manager.start_web_ui():
            print(f"✅ Web arayüzü aktif: http://{Config.WEB_HOST}:{Config.WEB_PORT}")
        
        # Browser'ları aç
        print("\n📋 Browser oturumları başlatılsın mı? (y/n): ", end="")
        if input().lower() == 'y':
            if chat_manager.start_browser_sessions():
                # Rolleri tanımla
                chat_manager.initialize_roles()
                
                # Demo başlat
                print("\n📊 Demo konuşma başlatılsın mı? (y/n): ", end="")
                if input().lower() == 'y':
                    chat_manager.start_demo_conversation()
        
        print(f"\n🎮 Sistem çalışıyor!")
        print(f"🌐 Web kontrol paneli: http://{Config.WEB_HOST}:{Config.WEB_PORT}")
        print("📱 İnteraktif kontroller web arayüzünden yapılabilir")
        print("❌ Çıkmak için Ctrl+C tuşlayın\n")
        
        # Sistem çalışmaya devam etsin
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Kullanıcı tarafından iptal edildi")
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {str(e)}")
    finally:
        if chat_manager:
            chat_manager.cleanup()

if __name__ == "__main__":
    main()