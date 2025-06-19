"""
AI Chrome Chat Manager - Universal Edition
Ana yürütme dosyası
"""
import asyncio
import sys
import os
import argparse
from colorama import init, Fore, Style

# Projeyi path'e ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.universal_ai_adapter import UniversalAIAdapter, SecureConfigManager
from src.message_broker import MessageBroker
from src.memory_bank_integration import MemoryBankIntegration
from src.web_ui_universal import WebUIUniversal
from src.logger import setup_logger

# Colorama'yı başlat
init(autoreset=True)

logger = setup_logger("main_universal")

class UniversalChatManager:
    """Universal AI Chat Manager - Ana sınıf"""
    
    def __init__(self):
        logger.info("🚀 Universal AI Chat Manager başlatılıyor...")
        
        # Temel bileşenler
        self.message_broker = MessageBroker()
        self.memory_bank = None
        self.ai_adapter = None
        self.web_ui = None
        
        # Sistem durumu
        self.is_running = False
        
    async def initialize_components(self, args):
        """Sistem bileşenlerini başlat"""
        try:
            # Memory Bank başlat
            logger.info("📚 Memory Bank başlatılıyor...")
            project_goal = "AI Chrome Chat Manager - Universal AI destekli proje yönetimi ve chat sistemi"
            self.memory_bank = MemoryBankIntegration(project_goal)
            await self.memory_bank.initialize()
            
            # Secure Config Manager
            logger.info("🔐 Secure Config Manager başlatılıyor...")
            config_manager = SecureConfigManager("config/api_keys.enc")
            
            # UniversalAIAdapter başlat
            logger.info("🤖 Universal AI Adapter başlatılıyor...")
            self.ai_adapter = UniversalAIAdapter(config_manager)
            
            # Mevcut API anahtarlarını yükle (web arayüzünden eklenmiş olanlar)
            await self._configure_adapters(config_manager)
            
            # Rolleri ata
            self._assign_roles()
            
            # Web UI başlat
            logger.info("🌐 Web UI başlatılıyor...")
            self.web_ui = WebUIUniversal(
                host="0.0.0.0",
                port=5000,
                message_broker=self.message_broker,
                memory_bank=self.memory_bank,
                ai_adapter=self.ai_adapter
            )
            self.web_ui.start_background()
            
            logger.info(f"{Fore.GREEN}✅ Tüm bileşenler başarıyla başlatıldı!{Style.RESET_ALL}")
            
        except Exception as e:
            logger.error(f"❌ Başlatma hatası: {e}")
            raise
    
    async def _configure_adapters(self, config_manager: SecureConfigManager):
        """AI adapter'larını yapılandır (web arayüzünden gelen anahtarlar)"""
        
        # Web arayüzünden eklenen tüm API anahtarlarını yükle
        config_data = config_manager.get_config()
        adapter_count = 0
        
        # Gemini anahtarları
        if 'gemini' in config_data:
            for key_name, api_key in config_data['gemini'].items():
                if api_key and api_key.strip():
                    adapter_id = f"gemini-{key_name}"
                    self.ai_adapter.add_adapter("gemini", adapter_id, api_key=api_key, model="gemini-2.5-flash")
                    logger.info(f"✓ Gemini adapter eklendi: {adapter_id}")
                    adapter_count += 1
        
        # OpenAI anahtarları
        if 'openai' in config_data:
            for key_name, api_key in config_data['openai'].items():
                if api_key and api_key.strip():
                    adapter_id = f"openai-{key_name}"
                    self.ai_adapter.add_adapter("openai", adapter_id, api_key=api_key, model="gpt-4o-mini")
                    logger.info(f"✓ OpenAI adapter eklendi: {adapter_id}")
                    adapter_count += 1
        
        # Varsayılan adapter'ları ekle (backward compatibility)
        if adapter_count == 0:
            # Eski .env tarzı anahtarları da kontrol et
            gemini_key = config_manager.get_api_key("gemini")
            if gemini_key:
                self.ai_adapter.add_adapter("gemini", "gemini-pm", api_key=gemini_key, model="gemini-2.5-flash")
                logger.info("✓ Gemini PM adapter eklendi: gemini-pm")
                adapter_count += 1
                
                # İkinci Gemini adapter (aynı key ile)
                self.ai_adapter.add_adapter("gemini", "gemini-ld", api_key=gemini_key, model="gemini-2.5-flash")
                logger.info("✓ Gemini LD adapter eklendi: gemini-ld")
                adapter_count += 1
            
            openai_key = config_manager.get_api_key("openai")
            if openai_key:
                self.ai_adapter.add_adapter("openai", "openai-boss", api_key=openai_key, model="gpt-4o-mini")
                logger.info("✓ OpenAI Boss adapter eklendi: openai-boss")
                adapter_count += 1
        
        logger.info(f"🎯 Toplam {adapter_count} AI adapter yapılandırıldı")
        
        if adapter_count == 0:
            logger.warning("⚠️ Hiçbir API anahtarı bulunamadı.")
            logger.warning("🌐 Web arayüzünden API anahtarlarınızı ekleyin: http://localhost:5000/api-management")
    
    def _assign_roles(self):
        """Rolleri AI adapter'larına ata"""
        # Mevcut adapter'ları kontrol et
        adapters = list(self.ai_adapter.adapters.keys())
        logger.info(f"Mevcut adapter'lar: {adapters}")
        
        if len(adapters) >= 1:
            # Önce belirli isimleri ara
            pm_adapter = None
            if "gemini-pm" in adapters:
                pm_adapter = "gemini-pm"
            elif any("gemini" in a for a in adapters):
                pm_adapter = next(a for a in adapters if "gemini" in a)
            else:
                pm_adapter = adapters[0]
            
            self.ai_adapter.assign_role("project_manager", pm_adapter)
            logger.info(f"📋 Project Manager rolü atandı: {pm_adapter}")
        
        if len(adapters) >= 2:
            # Lead Developer için ikinci adapter
            ld_adapter = None
            if "gemini-ld" in adapters:
                ld_adapter = "gemini-ld"
            elif len([a for a in adapters if "gemini" in a]) >= 2:
                gemini_adapters = [a for a in adapters if "gemini" in a]
                ld_adapter = gemini_adapters[1] if len(gemini_adapters) > 1 else gemini_adapters[0]
            else:
                ld_adapter = adapters[1]
            
            self.ai_adapter.assign_role("lead_developer", ld_adapter)
            logger.info(f"💻 Lead Developer rolü atandı: {ld_adapter}")
        
        if len(adapters) >= 3:
            # Boss için üçüncü adapter (tercihen OpenAI)
            boss_adapter = None
            if "openai-boss" in adapters:
                boss_adapter = "openai-boss"
            elif any("openai" in a for a in adapters):
                boss_adapter = next(a for a in adapters if "openai" in a)
            else:
                # OpenAI yoksa ilk adapter'ı kullan
                boss_adapter = adapters[0]
            
            self.ai_adapter.assign_role("boss", boss_adapter)
            logger.info(f"👔 Boss rolü atandı: {boss_adapter}")
        
        # Rol atamalarını göster
        role_assignments = self.ai_adapter.get_role_assignments()
        if role_assignments:
            print(f"\n🎭 Rol Atamaları:")
            for role, adapter_id in role_assignments.items():
                role_icons = {
                    'project_manager': '📋',
                    'lead_developer': '💻', 
                    'boss': '👔'
                }
                icon = role_icons.get(role, '🤖')
                print(f"  {icon} {role}: {adapter_id}")
        else:
            logger.warning("⚠️ Hiçbir rol atanamadı - API anahtarı eksik olabilir")
    
    async def run(self):
        """Ana döngüyü çalıştır"""
        self.is_running = True
        
        print(f"\n{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🎯 AI Chrome Chat Manager Universal Edition{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🌐 Web arayüzü: http://localhost:5000{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}\n")
        
        print(f"{Fore.YELLOW}Komutlar:{Style.RESET_ALL}")
        print("  - 'chat' : AI'lar arası konuşma başlat")
        print("  - 'status' : Sistem durumunu göster")
        print("  - 'analytics' : Analytics özeti göster")
        print("  - 'exit' : Çıkış yap\n")
        
        try:
            while self.is_running:
                try:
                    # Kullanıcı girişini bekle
                    command = await asyncio.get_event_loop().run_in_executor(
                        None, input, f"{Fore.BLUE}Komut > {Style.RESET_ALL}"
                    )
                    
                    if command.lower() == 'exit':
                        break
                    elif command.lower() == 'chat':
                        await self._start_ai_chat()
                    elif command.lower() == 'status':
                        self._show_status()
                    elif command.lower() == 'analytics':
                        self._show_analytics()
                    else:
                        print(f"{Fore.RED}Geçersiz komut. 'exit', 'chat', 'status' veya 'analytics' yazın.{Style.RESET_ALL}")
                
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.error(f"Komut işleme hatası: {e}")
        
        finally:
            await self.shutdown()
    
    async def _start_ai_chat(self):
        """AI'lar arası konuşma başlat"""
        print(f"\n{Fore.CYAN}=== AI Konuşması Başlatılıyor ==={Style.RESET_ALL}")
        
        prompt = input("İlk mesaj: ").strip()
        if not prompt:
            print(f"{Fore.RED}Mesaj boş olamaz!{Style.RESET_ALL}")
            return
        
        max_turns = 3
        current_message = prompt
        
        for turn in range(max_turns):
            print(f"\n{Fore.YELLOW}--- Tur {turn + 1}/{max_turns} ---{Style.RESET_ALL}")
            
            # PM'den yanıt al
            print(f"{Fore.BLUE}👔 Project Manager düşünüyor...{Style.RESET_ALL}")
            pm_response = await self.ai_adapter.send_message(
                "project_manager", 
                current_message,
                f"Konuşma turu: {turn + 1}"
            )
            
            if pm_response:
                print(f"{Fore.GREEN}👔 PM:{Style.RESET_ALL} {pm_response.content[:200]}...")
                
                # LD'den yanıt al
                print(f"\n{Fore.BLUE}💻 Lead Developer düşünüyor...{Style.RESET_ALL}")
                ld_response = await self.ai_adapter.send_message(
                    "lead_developer",
                    pm_response.content,
                    f"PM'den gelen yanıt - Tur {turn + 1}"
                )
                
                if ld_response:
                    print(f"{Fore.GREEN}💻 LD:{Style.RESET_ALL} {ld_response.content[:200]}...")
                    current_message = ld_response.content
                else:
                    print(f"{Fore.RED}LD yanıt veremedi!{Style.RESET_ALL}")
                    break
            else:
                print(f"{Fore.RED}PM yanıt veremedi!{Style.RESET_ALL}")
                break
        
        print(f"\n{Fore.CYAN}=== Konuşma Tamamlandı ==={Style.RESET_ALL}")
    
    def _show_status(self):
        """Sistem durumunu göster"""
        print(f"\n{Fore.CYAN}=== Sistem Durumu ==={Style.RESET_ALL}")
        
        # Adapter durumları
        status = self.ai_adapter.get_adapter_status()
        for adapter_id, info in status.items():
            if "error" not in info:
                print(f"\n{Fore.YELLOW}{adapter_id}:{Style.RESET_ALL}")
                print(f"  Tip: {info['type']}")
                print(f"  Model: {info['model']}")
                print(f"  Durum: {'✅ Aktif' if info['rate_limit']['available'] else '⏳ Rate limit'}")
                print(f"  İstatistikler: {info['stats']['requests']} istek, ${info['stats']['cost']:.4f} maliyet")
        
        # Rol atamaları
        roles = self.ai_adapter.get_role_assignments()
        print(f"\n{Fore.YELLOW}Rol Atamaları:{Style.RESET_ALL}")
        for role, adapter in roles.items():
            print(f"  {role}: {adapter}")
    
    def _show_analytics(self):
        """Analytics özetini göster"""
        print(f"\n{Fore.CYAN}=== Analytics Özeti ==={Style.RESET_ALL}")
        
        stats = self.ai_adapter.get_total_stats()
        
        print(f"\n{Fore.YELLOW}Toplam İstatistikler:{Style.RESET_ALL}")
        print(f"  📊 Toplam İstek: {stats['total_requests']}")
        print(f"  💰 Toplam Maliyet: ${stats['total_cost']:.4f}")
        print(f"  🔤 Toplam Token: {stats['total_tokens']:,}")
        print(f"  ❌ Toplam Hata: {stats['total_errors']}")
        
        if stats['total_requests'] > 0:
            success_rate = ((stats['total_requests'] - stats['total_errors']) / stats['total_requests']) * 100
            print(f"  ✅ Başarı Oranı: %{success_rate:.1f}")
    
    async def shutdown(self):
        """Sistemi kapat"""
        logger.info("🛑 Sistem kapatılıyor...")
        self.is_running = False
        
        # Bileşenleri temizle
        if self.memory_bank:
            # Memory Bank'i kaydet
            await self.memory_bank.update_document("progress", """
            Son oturum kapatıldı.
            Sistem başarıyla sonlandırıldı.
            """)
        
        logger.info("👋 Sistem kapatıldı. Görüşmek üzere!")


async def main():
    """Ana giriş noktası"""
    parser = argparse.ArgumentParser(description="AI Chrome Chat Manager - Universal Edition")
    parser.add_argument("--setup", action="store_true", help="API anahtarlarını yapılandır")
    parser.add_argument("--reset", action="store_true", help="Tüm yapılandırmaları sıfırla")
    
    args = parser.parse_args()
    
    # Reset işlemi
    if args.reset:
        config_path = "config/api_keys.enc"
        if os.path.exists(config_path):
            os.remove(config_path)
            print(f"{Fore.GREEN}✓ Yapılandırma sıfırlandı{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠️ Sıfırlanacak yapılandırma bulunamadı{Style.RESET_ALL}")
        return
    
    # Ana uygulamayı başlat
    manager = UniversalChatManager()
    
    try:
        await manager.initialize_components(args)
        await manager.run()
    except KeyboardInterrupt:
        logger.info("⌨️ Klavye kesintisi algılandı")
    except Exception as e:
        logger.error(f"❌ Kritik hata: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await manager.shutdown()


if __name__ == "__main__":
    asyncio.run(main()) 