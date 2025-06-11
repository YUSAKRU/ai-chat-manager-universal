"""
Chrome Profil Yönetimi
Mevcut Chrome profillerini tespit eder ve kullanıcının seçim yapmasını sağlar
"""
import os
import json
import platform
from typing import List, Dict, Optional
from logger import logger

class ChromeProfileManager:
    def __init__(self):
        self.chrome_user_data_path = self._get_chrome_user_data_path()
        self.available_profiles = self._discover_profiles()
        logger.info(f"Chrome User Data Path: {self.chrome_user_data_path}", "CHROME_PROFILES")
        logger.info(f"Bulunan profil sayısı: {len(self.available_profiles)}", "CHROME_PROFILES")

    def _get_chrome_user_data_path(self) -> str:
        """İşletim sistemine göre Chrome User Data klasörünü bul"""
        system = platform.system()
        
        if system == "Windows":
            # Windows için yaygın Chrome konumları
            possible_paths = [
                os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data"),
                os.path.expanduser("~\\AppData\\Local\\Google\\Chrome Beta\\User Data"),
                os.path.expanduser("~\\AppData\\Local\\Google\\Chrome Dev\\User Data"),
                os.path.expanduser("~\\AppData\\Local\\Chromium\\User Data"),
            ]
        elif system == "Darwin":  # macOS
            possible_paths = [
                os.path.expanduser("~/Library/Application Support/Google/Chrome"),
                os.path.expanduser("~/Library/Application Support/Google/Chrome Beta"),
                os.path.expanduser("~/Library/Application Support/Chromium"),
            ]
        else:  # Linux
            possible_paths = [
                os.path.expanduser("~/.config/google-chrome"),
                os.path.expanduser("~/.config/google-chrome-beta"),
                os.path.expanduser("~/.config/chromium"),
            ]
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Chrome User Data klasörü bulundu: {path}", "CHROME_PROFILES")
                return path
        
        logger.warning("Chrome User Data klasörü bulunamadı!", "CHROME_PROFILES")
        return ""

    def _discover_profiles(self) -> List[Dict]:
        """Mevcut Chrome profillerini keşfet"""
        profiles = []
        
        if not self.chrome_user_data_path or not os.path.exists(self.chrome_user_data_path):
            logger.warning("Chrome User Data klasörü mevcut değil", "CHROME_PROFILES")
            return profiles

        try:
            # Default profil
            default_path = os.path.join(self.chrome_user_data_path, "Default")
            if os.path.exists(default_path):
                profile_info = self._get_profile_info(default_path, "Default")
                if profile_info:
                    profiles.append(profile_info)

            # Profile klasörlerini tara
            for item in os.listdir(self.chrome_user_data_path):
                item_path = os.path.join(self.chrome_user_data_path, item)
                
                if os.path.isdir(item_path) and item.startswith("Profile "):
                    profile_info = self._get_profile_info(item_path, item)
                    if profile_info:
                        profiles.append(profile_info)

        except Exception as e:
            logger.error(f"Profil keşfi sırasında hata: {str(e)}", "CHROME_PROFILES", e)

        return profiles

    def _get_profile_info(self, profile_path: str, profile_name: str) -> Optional[Dict]:
        """Belirli bir profilin bilgilerini al"""
        try:
            preferences_file = os.path.join(profile_path, "Preferences")
            
            if not os.path.exists(preferences_file):
                return None

            # Preferences dosyasından profil bilgilerini oku
            with open(preferences_file, 'r', encoding='utf-8') as f:
                prefs = json.load(f)

            # Profil adını al
            profile_display_name = prefs.get('profile', {}).get('name', profile_name)
            
            # Son kullanım zamanı
            local_state_file = os.path.join(self.chrome_user_data_path, "Local State")
            last_used = "Bilinmiyor"
            
            if os.path.exists(local_state_file):
                try:
                    with open(local_state_file, 'r', encoding='utf-8') as f:
                        local_state = json.load(f)
                    
                    profile_info = local_state.get('profile', {}).get('info_cache', {}).get(profile_name, {})
                    last_used_time = profile_info.get('last_downloaded_gaia_picture_url_with_size', 'N/A')
                    if last_used_time != 'N/A':
                        last_used = "Yakın zamanda"
                except:
                    pass

            profile_info = {
                'name': profile_name,
                'display_name': profile_display_name,
                'path': profile_path,
                'last_used': last_used,
                'is_default': profile_name == "Default"
            }

            logger.debug(f"Profil bulundu: {profile_display_name} ({profile_name})", "CHROME_PROFILES")
            return profile_info

        except Exception as e:
            logger.warning(f"Profil bilgisi alınamadı ({profile_name}): {str(e)}", "CHROME_PROFILES")
            return None

    def list_profiles(self) -> List[Dict]:
        """Mevcut profilleri listele"""
        return self.available_profiles

    def get_profile_path(self, profile_name: str) -> Optional[str]:
        """Profil adına göre profil yolunu al"""
        for profile in self.available_profiles:
            if profile['name'] == profile_name:
                return profile['path']
        return None

    def select_profile_interactive(self, purpose: str = "AI Chat") -> Optional[str]:
        """Kullanıcıdan profil seçimini etkileşimli olarak al"""
        if not self.available_profiles:
            print("❌ Hiç Chrome profili bulunamadı!")
            print("💡 Lütfen önce Chrome'u açıp en az bir profil oluşturun.")
            return None

        print(f"\n🔍 {purpose} için Chrome profili seçin:")
        print("=" * 50)
        
        for i, profile in enumerate(self.available_profiles, 1):
            default_marker = " 👑" if profile['is_default'] else ""
            print(f"{i}. {profile['display_name']}{default_marker}")
            print(f"   📁 {profile['name']}")
            print(f"   🕒 Son kullanım: {profile['last_used']}")
            print()

        while True:
            try:
                choice = input(f"Seçiminizi yapın (1-{len(self.available_profiles)}) veya 'q' ile çıkış: ").strip()
                
                if choice.lower() == 'q':
                    return None
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(self.available_profiles):
                    selected_profile = self.available_profiles[choice_num - 1]
                    print(f"✅ Seçilen profil: {selected_profile['display_name']}")
                    return selected_profile['name']
                else:
                    print(f"❌ Geçersiz seçim! 1-{len(self.available_profiles)} arasında bir sayı girin.")
            
            except ValueError:
                print("❌ Geçersiz giriş! Lütfen bir sayı girin.")
            except KeyboardInterrupt:
                print("\n⚠️ İşlem iptal edildi.")
                return None

    def create_minimal_chrome_options(self, profile_name: str = None):
        """Minimal kısıtlamalarla Chrome seçenekleri oluştur"""
        from selenium.webdriver.chrome.options import Options
        
        chrome_options = Options()
        
        # Profil belirtilmişse kullan
        if profile_name and self.chrome_user_data_path:
            if profile_name == "Default":
                user_data_dir = self.chrome_user_data_path
                chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
            else:
                user_data_dir = self.chrome_user_data_path
                chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
                chrome_options.add_argument(f"--profile-directory={profile_name}")
          # Minimal kısıtlamalar - sadece automation detection'ı engelle
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Kararlılık iyileştirmeleri
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--no-default-browser-check")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        
        # Chrome policy hatalarını azalt
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        
        # DevTools uyarısını düzelt - sabit debugging port kullan
        chrome_options.add_argument("--remote-debugging-port=9222")
        
        # Sessiz modda çalışma seçenekleri
        chrome_options.add_argument("--log-level=3")  # Sadece FATAL logları göster
        chrome_options.add_argument("--silent")
        
        return chrome_options

    def get_profile_summary(self) -> str:
        """Profil özetini döndür"""
        if not self.available_profiles:
            return "❌ Hiç Chrome profili bulunamadı"
        
        summary = f"📊 Chrome Profil Özeti:\n"
        summary += f"🏠 User Data: {self.chrome_user_data_path}\n"
        summary += f"📄 Toplam Profil: {len(self.available_profiles)}\n\n"
        
        for profile in self.available_profiles:
            marker = "👑" if profile['is_default'] else "👤"
            summary += f"{marker} {profile['display_name']} ({profile['name']})\n"
        
        return summary
