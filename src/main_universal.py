"""
AI Chrome Chat Manager - Universal AI Adapter Version
Çoklu AI desteği ile geliştirilmiş versiyon
"""
import asyncio
import os
from ai_adapters import UniversalAIAdapter
from message_broker import MessageBroker
from memory_bank_integration import MemoryBankIntegration
from web_ui_universal import WebUIUniversal
from config import Config
from logger import logger

class AIChromeChatManagerUniversal:
    """Universal AI Adapter kullanan gelişmiş sistem"""
    
    def __init__(self):
        self.config = Config()
        self.message_broker = MessageBroker()
        self.ai_adapter = UniversalAIAdapter()
        self.memory_bank = None
        self.web_ui = None
        
    async def initialize(self):
        """Sistemi başlat"""
        try:
            logger.info("🚀 AI Chrome Chat Manager Universal başlatılıyor...", "SYSTEM")
            
            # 1. AI Adapterleri yükle
            logger.info("🤖 AI Adapterleri yükleniyor...", "SYSTEM")
            success = await self.ai_adapter.initialize_from_config()
            if not success:
                raise Exception("AI Adapterleri yüklenemedi!")
            
            # 2. Memory Bank başlat
            logger.info("🧠 Memory Bank başlatılıyor...", "SYSTEM")
            self.setup_memory_bank()
            
            # 3. Mesaj kanalları
            logger.info("📡 Mesaj kanalları oluşturuluyor...", "SYSTEM")
            self.setup_message_channels()
            
            # 4. Web UI başlat
            logger.info("🌐 Web arayüzü başlatılıyor...", "SYSTEM")
            self.start_web_ui()
            
            logger.info("✅ Sistem başarıyla başlatıldı!", "SYSTEM")
            
            # Sistem durumunu göster
            self.show_system_status()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Sistem başlatma hatası: {str(e)}", "SYSTEM", e)
            return False
    
    def setup_memory_bank(self):
        """Memory Bank sistemini kur"""
        try:
            memory_bank_path = os.getenv('MEMORY_BANK_PATH', './memory-bank')
            project_goal = os.getenv('PROJECT_GOAL', 'Çoklu AI köprü sistemi')
            
            self.memory_bank = MemoryBankIntegration(memory_bank_path, project_goal)
            self.memory_bank.initialize()
            
        except Exception as e:
            logger.error(f"Memory Bank hatası: {str(e)}", "MEMORY_BANK", e)
    
    def setup_message_channels(self):
        """Mesaj kanallarını oluştur"""
        channels = [
            "pm_to_ld",
            "ld_to_pm", 
            "boss_to_pm",
            "boss_to_ld",
            "webui_to_system",
            "system_to_webui"
        ]
        
        for channel in channels:
            self.message_broker.create_channel(channel)
    
    def start_web_ui(self):
        """Web UI'yı başlat"""
        try:
            self.web_ui = WebUIUniversal(
                self.config.get_web_host(),
                self.config.get_web_port(),
                self.message_broker,
                self.memory_bank,
                self.ai_adapter
            )
            
            self.web_ui.start_background()
            
        except Exception as e:
            logger.error(f"Web UI hatası: {str(e)}", "WEB_UI", e)
    
    def show_system_status(self):
        """Sistem durumunu göster"""
        print("\n" + "="*60)
        print("📊 SISTEM DURUMU")
        print("="*60)
        
        # AI Adapter durumu
        adapter_status = self.ai_adapter.get_adapter_status()
        print("\n🤖 AI Adapterleri:")
        for adapter_id, status in adapter_status.items():
            if 'error' not in status:
                print(f"   • {adapter_id}: {status['type']} ({status['model']})")
                print(f"     └─ Durum: {'✅ Hazır' if status['rate_limit']['available'] else '⚠️ Rate Limit'}")
        
        # Rol atamaları
        roles = self.ai_adapter.get_role_assignments()
        print("\n🎭 Rol Atamaları:")
        for role, adapter in roles.items():
            print(f"   • {role} → {adapter}")
        
        # Toplam istatistikler
        stats = self.ai_adapter.get_total_stats()
        print("\n📈 İstatistikler:")
        print(f"   • Toplam İstek: {stats['total_requests']}")
        print(f"   • Toplam Token: {stats['total_tokens']:,}")
        print(f"   • Toplam Maliyet: {stats['total_cost']}")
        print(f"   • Aktif Adapter: {stats['adapters_count']}")
        
        # Web UI
        if self.web_ui:
            web_url = f"http://{self.config.get_web_host()}:{self.config.get_web_port()}"
            print(f"\n🌐 Web Arayüzü: {web_url}")
        
        print("="*60 + "\n")
    
    async def start_conversation_bridge(self, initial_prompt: str, max_turns: int = 5):
        """AI'lar arasında konuşma köprüsü başlat"""
        try:
            logger.info(f"🌉 Konuşma köprüsü başlatılıyor ({max_turns} tur)", "CONVERSATION")
            
            current_message = initial_prompt
            conversation_log = []
            
            for turn in range(max_turns):
                print(f"\n{'='*50}")
                print(f"🔄 Tur {turn + 1}/{max_turns}")
                print('='*50)
                
                # PM'den yanıt al
                pm_response = await self.ai_adapter.send_message(
                    "project_manager",
                    current_message,
                    f"Konuşma turu: {turn + 1}"
                )
                
                if pm_response:
                    print(f"\n👔 Proje Yöneticisi:")
                    print(f"{pm_response.content[:300]}...")
                    
                    conversation_log.append({
                        'speaker': 'Project Manager',
                        'content': pm_response.content,
                        'turn': turn + 1
                    })
                
                # LD'den yanıt al
                ld_response = await self.ai_adapter.send_message(
                    "lead_developer",
                    pm_response.content if pm_response else current_message,
                    f"PM'den gelen yanıt - Tur {turn + 1}"
                )
                
                if ld_response:
                    print(f"\n👨‍💻 Lead Developer:")
                    print(f"{ld_response.content[:300]}...")
                    
                    conversation_log.append({
                        'speaker': 'Lead Developer',
                        'content': ld_response.content,
                        'turn': turn + 1
                    })
                
                # Sonraki tur için mesaj
                current_message = ld_response.content if ld_response else pm_response.content
                
                # Rate limit için bekle
                await asyncio.sleep(2)
            
            # Memory Bank'e kaydet
            if self.memory_bank and conversation_log:
                self.memory_bank.save_conversation(conversation_log, f"bridge_{int(asyncio.get_event_loop().time())}")
            
            # Final istatistikler
            self.show_conversation_summary()
            
        except Exception as e:
            logger.error(f"Konuşma köprüsü hatası: {str(e)}", "CONVERSATION", e)
    
    def show_conversation_summary(self):
        """Konuşma özetini göster"""
        stats = self.ai_adapter.get_total_stats()
        print(f"\n{'='*50}")
        print("📊 KONUŞMA ÖZETİ")
        print('='*50)
        print(f"• Toplam Mesaj: {stats['total_requests']}")
        print(f"• Kullanılan Token: {stats['total_tokens']:,}")
        print(f"• Maliyet: {stats['total_cost']}")
        print('='*50)

async def interactive_menu(system: AIChromeChatManagerUniversal):
    """İnteraktif menü"""
    while True:
        print("\n" + "="*50)
        print("🎮 AI CHROME CHAT MANAGER - MENÜ")
        print("="*50)
        print("1. 🌉 Konuşma Köprüsü Başlat")
        print("2. 🔄 Rol Değiştir")
        print("3. 📊 İstatistikleri Göster")
        print("4. 🗑️  Konuşma Geçmişini Temizle")
        print("5. 🚪 Çıkış")
        print("="*50)
        
        choice = input("Seçiminiz (1-5): ").strip()
        
        if choice == '1':
            prompt = input("\n💬 İlk mesaj: ").strip()
            if prompt:
                turns = input("🔢 Kaç tur konuşsunlar? (varsayılan: 3): ").strip()
                turns = int(turns) if turns.isdigit() else 3
                await system.start_conversation_bridge(prompt, turns)
        
        elif choice == '2':
            # Rol değiştirme
            roles = system.ai_adapter.get_role_assignments()
            print("\n🎭 Mevcut Roller:")
            for role, adapter in roles.items():
                print(f"   • {role} → {adapter}")
            
            role_id = input("\n📝 Değiştirilecek rol: ").strip()
            adapter_id = input("🤖 Yeni adapter ID: ").strip()
            
            try:
                system.ai_adapter.assign_role(role_id, adapter_id)
                print("✅ Rol ataması güncellendi!")
            except Exception as e:
                print(f"❌ Hata: {e}")
        
        elif choice == '3':
            system.show_system_status()
        
        elif choice == '4':
            system.ai_adapter.clear_conversation_history()
            print("✅ Konuşma geçmişi temizlendi!")
        
        elif choice == '5':
            print("👋 Güle güle!")
            break
        
        else:
            print("❌ Geçersiz seçim!")

async def main():
    """Ana fonksiyon"""
    print("🚀 AI Chrome Chat Manager - Universal Version")
    print("="*60)
    
    # Sistem oluştur ve başlat
    system = AIChromeChatManagerUniversal()
    
    if await system.initialize():
        # İnteraktif menü
        await interactive_menu(system)
    else:
        print("❌ Sistem başlatılamadı!")

if __name__ == "__main__":
    asyncio.run(main()) 