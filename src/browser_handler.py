import os
import tempfile
from config import Config
from logger import logger, safe_execute
from chrome_profile_manager import ChromeProfileManager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
import threading

class BrowserHandler:
    def __init__(self):
        self.drivers = {}
        self.current_windows = {}
        self.profile_manager = ChromeProfileManager()
        self.selected_profiles = {}  # role_name -> profile_name mapping

    def setup_profiles_interactive(self):
        """Kullanıcıdan her rol için profil seçimi al"""
        print("\n🎭 AI Rolleri için Chrome Profil Kurulumu")
        print("=" * 50)
        
        if not self.profile_manager.available_profiles:
            print("❌ Chrome profili bulunamadı! Lütfen önce Chrome'u açıp profil oluşturun.")
            return False
        
        # Profil özeti göster
        print(self.profile_manager.get_profile_summary())
        
        roles = [
            ("project_manager", "👔 Proje Yöneticisi (ChatGPT)"),
            ("lead_developer", "👨‍💻 Lead Developer (Claude)")
        ]
        
        for role_key, role_description in roles:
            print(f"\n{role_description} için profil seçimi:")
            selected_profile = self.profile_manager.select_profile_interactive(role_description)
            
            if selected_profile:
                self.selected_profiles[role_key] = selected_profile
                logger.info(f"{role_description} -> {selected_profile} profili atandı", "BROWSER_SETUP")
            else:
                print(f"❌ {role_description} için profil seçilmedi!")
                return False
        
        print(f"\n✅ Profil kurulumu tamamlandı!")
        print(f"👔 PM: {self.selected_profiles.get('project_manager', 'N/A')}")
        print(f"👨‍💻 LD: {self.selected_profiles.get('lead_developer', 'N/A')}")
        return True

    def create_chrome_options(self, role_name):
        """Seçilen profile göre Chrome seçenekleri oluştur"""
        profile_name = self.selected_profiles.get(role_name)
        
        if profile_name:
            logger.info(f"{role_name} için {profile_name} profili kullanılıyor", "BROWSER_HANDLER")
            return self.profile_manager.create_minimal_chrome_options(profile_name)
        else:
            logger.warning(f"{role_name} için profil seçilmemiş, varsayılan kullanılıyor", "BROWSER_HANDLER")
            return self.profile_manager.create_minimal_chrome_options()

    def open_window(self, role_name, url="https://chatgpt.com"):
        """Belirtilen rol için Chrome penceresi aç"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                profile_name = self.selected_profiles.get(role_name, "Profil seçilmemiş")
                logger.info(f"{role_name} için Chrome penceresi açılıyor (Profil: {profile_name})...", "BROWSER_HANDLER")
                
                # Chrome seçeneklerini ayarla
                chrome_options = self.create_chrome_options(role_name)
                
                # WebDriver'ı başlat
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
                
                # Automation detection'ı engelle
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                # URL'ye git
                driver.get(url)
                
                # Sayfanın yüklenmesini bekle
                WebDriverWait(driver, 10).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                
                driver.maximize_window()
                
                # Driver'ı kaydet
                self.drivers[role_name] = driver
                self.current_windows[role_name] = driver.current_window_handle
                
                logger.info(f"{role_name} penceresi başarıyla açıldı: {url}", "BROWSER_HANDLER")
                return driver
                
            except Exception as e:
                retry_count += 1
                logger.warning(f"{role_name} penceresi açılırken hata (Deneme {retry_count}/{max_retries}): {str(e)}", "BROWSER_HANDLER")
                
                # Eğer driver açıldıysa kapat
                try:
                    if 'driver' in locals():
                        driver.quit()
                except:
                    pass
                
                if retry_count < max_retries:
                    logger.info(f"5 saniye bekleyip tekrar denenecek...", "BROWSER_HANDLER")
                    time.sleep(5)
                else:
                    logger.error(f"{role_name} penceresi {max_retries} denemeden sonra açılamadı", "BROWSER_HANDLER")
                    return None

    def send_message(self, role_name, message, input_selector=None):
        """Belirtilen pencereye mesaj gönder"""
        if role_name not in self.drivers:
            print(f"❌ {role_name} penceresi bulunamadı!")
            return False
            
        driver = self.drivers[role_name]
        
        try:
            print(f"📤 {role_name} penceresine mesaj gönderiliyor: {message[:50]}...")
            
            # Yaygın chat input selectors
            possible_selectors = [
                input_selector if input_selector else None,
                'textarea[placeholder*="message"]',
                'textarea[data-id="root"]',
                'textarea[placeholder*="Message"]',
                'div[contenteditable="true"]',
                'textarea',
                'input[type="text"]'
            ]
            
            message_input = None
            for selector in possible_selectors:
                if selector:
                    try:
                        message_input = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        break
                    except:
                        continue
            
            if message_input:
                # Mesajı gönder
                message_input.clear()
                message_input.send_keys(message)
                time.sleep(0.5)
                message_input.send_keys(Keys.RETURN)
                
                print(f"✅ {role_name} penceresine mesaj gönderildi!")
                return True
            else:
                print(f"❌ {role_name} penceresinde mesaj input alanı bulunamadı!")
                return False
                
        except Exception as e:
            print(f"❌ {role_name} penceresine mesaj gönderilirken hata: {str(e)}")
            return False

    def get_last_message(self, role_name, message_selector=None):
        """Son mesajı al"""
        if role_name not in self.drivers:
            return None
            
        driver = self.drivers[role_name]
        
        try:
            # Yaygın mesaj selectors
            possible_selectors = [
                message_selector if message_selector else None,
                'div[data-message-author-role="assistant"]',
                '.bot-message',
                '.assistant-message',
                'div[class*="message"]',
                'div[class*="response"]'
            ]
            
            for selector in possible_selectors:
                if selector:
                    try:
                        messages = driver.find_elements(By.CSS_SELECTOR, selector)
                        if messages:
                            return messages[-1].text
                    except:
                        continue
            
            return None
            
        except Exception as e:
            print(f"❌ {role_name} penceresinden mesaj okunurken hata: {str(e)}")
            return None

    def close_window(self, role_name):
        """Belirtilen pencereyi kapat"""
        if role_name in self.drivers:
            try:
                self.drivers[role_name].quit()
                del self.drivers[role_name]
                if role_name in self.current_windows:
                    del self.current_windows[role_name]
                print(f"🔒 {role_name} penceresi kapatıldı")
            except Exception as e:
                print(f"❌ {role_name} penceresi kapatılırken hata: {str(e)}")

    def close_all_windows(self):
        """Tüm pencereleri kapat"""
        for role_name in list(self.drivers.keys()):
            self.close_window(role_name)

    # ------------------------------------------------------------------
    # 🌐 WEB UI PROFIL KURULUMU
    # ------------------------------------------------------------------
    def setup_profiles_web(self, mapping: dict) -> bool:
        """Web UI üzerinden gelen profil eşlemesini doğrula ve uygula.

        Args:
            mapping: {"project_manager": "Profile X", "lead_developer": "Default", ...}

        Returns:
            bool: Başarılıysa True, aksi halde False.
        """
        required_roles = ["project_manager", "lead_developer"]

        # 1. Gerekli rollerin sunulduğunu kontrol et
        if not all(role in mapping for role in required_roles):
            logger.error("Eksik rol anahtarları: mapping tam değil", "BROWSER_SETUP")
            return False

        # 2. Profil isimlerinin geçerli olduğunu kontrol et
        valid_profile_names = {p["name"] for p in self.profile_manager.available_profiles}

        for role, profile_name in mapping.items():
            if profile_name not in valid_profile_names:
                logger.error(f"Geçersiz profil adı alındı: {profile_name}", "BROWSER_SETUP")
                return False

        # 3. Sözlüğü güncelle
        self.selected_profiles.update(mapping)

        logger.info(
            f"Web üzerinden profiller atandı: PM -> {mapping['project_manager']} | LD -> {mapping['lead_developer']}",
            "BROWSER_SETUP",
        )

        return True