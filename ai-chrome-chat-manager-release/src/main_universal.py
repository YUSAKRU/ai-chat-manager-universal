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
            self.memory_bank = MemoryBankIntegration()
            await self.memory_bank.initialize()
            
            # Secure Config Manager
            logger.info("🔐 Secure Config Manager başlatılıyor...")
            config_manager = SecureConfigManager("config/api_keys.enc")
            
            # API anahtarlarını kontrol et
            if args.setup:
                await self._setup_api_keys(config_manager)
            
            # UniversalAIAdapter başlat
            logger.info("🤖 Universal AI Adapter başlatılıyor...")
            self.ai_adapter = UniversalAIAdapter(config_manager)
            
            # Örnek adapter'ları ekle (eğer yapılandırılmışsa)
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
    
    async def _setup_api_keys(self, config_manager: SecureConfigManager):
        """API anahtarlarını yapılandır"""
        print(f"\n{Fore.CYAN}=== API Anahtarı Kurulumu ==={Style.RESET_ALL}")
        
        # Gemini API Key
        print(f"\n{Fore.YELLOW}Gemini API anahtarı:{Style.RESET_ALL}")
        gemini_key = input("API anahtarınızı girin (boş bırakılırsa atlanır): ").strip()
        if gemini_key:
            config_manager.save_api_key("gemini", gemini_key)
            print(f"{Fore.GREEN}✓ Gemini API anahtarı kaydedildi{Style.RESET_ALL}")
        
        # OpenAI API Key
        print(f"\n{Fore.YELLOW}OpenAI API anahtarı:{Style.RESET_ALL}")
        openai_key = input("API anahtarınızı girin (boş bırakılırsa atlanır): ").strip()
        if openai_key:
            config_manager.save_api_key("openai", openai_key)
            print(f"{Fore.GREEN}✓ OpenAI API anahtarı kaydedildi{Style.RESET_ALL}")
        
        print(f"\n{Fore.GREEN}API anahtarları güvenli bir şekilde şifrelendi ve kaydedildi!{Style.RESET_ALL}")
    
    async def _configure_adapters(self, config_manager: SecureConfigManager):
        """AI adapter'larını yapılandır"""
        # Gemini adapter ekle
        gemini_key = config_manager.get_api_key("gemini")
        if gemini_key:
            self.ai_adapter.add_adapter("gemini", api_key=gemini_key)
            logger.info("✓ Gemini adapter eklendi")
        
        # OpenAI adapter ekle
        openai_key = config_manager.get_api_key("openai")
        if openai_key:
            self.ai_adapter.add_adapter("openai", api_key=openai_key)
            logger.info("✓ OpenAI adapter eklendi")
        
        if not gemini_key and not openai_key:
            logger.warning("⚠️ Hiçbir API anahtarı yapılandırılmadı. --setup ile kurulum yapın.")
    
    def _assign_roles(self):
        """Rolleri AI adapter'larına ata"""
        # Mevcut adapter'ları kontrol et
        adapters = list(self.ai_adapter.adapters.keys())
        
        if len(adapters) >= 1:
            self.ai_adapter.assign_role("project_manager", adapters[0])
            logger.info(f"📋 Project Manager rolü atandı: {adapters[0]}")
        
        if len(adapters) >= 2:
            self.ai_adapter.assign_role("lead_developer", adapters[1])
            logger.info(f"💻 Lead Developer rolü atandı: {adapters[1]}")
        
        if len(adapters) >= 3:
            self.ai_adapter.assign_role("boss", adapters[2])
            logger.info(f"👔 Boss rolü atandı: {adapters[2]}")
    
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