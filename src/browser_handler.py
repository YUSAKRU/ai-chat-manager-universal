import os
import tempfile
from config import Config
from logger import logger, safe_execute
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

    def create_chrome_options(self, role_name):
        """Chrome seçeneklerini oluştur"""
        # Profil klasörünü benzersiz bir temp dizini olarak oluştur
        profile_dir = tempfile.mkdtemp(prefix=f"{role_name}_profile_")
        
        chrome_options = Options()
        # Remote debugging port atama (0 ile dinamik port)
        chrome_options.add_argument("--remote-debugging-port=0")
        # Ek güvenlik ve stabilite argümanları
        # (remove remote debugging to avoid profile errors)
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--no-default-browser-check")
        chrome_options.add_argument("--disable-background-networking")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-client-side-phishing-detection")
        chrome_options.add_argument("--disable-default-apps")
        chrome_options.add_argument("--disable-hang-monitor")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-prompt-on-repost")
        chrome_options.add_argument("--disable-sync")
        chrome_options.add_argument("--metrics-recording-only")
        chrome_options.add_argument("--safebrowsing-disable-auto-update")
        chrome_options.add_argument("--password-store=basic")
        chrome_options.add_argument("--use-mock-keychain")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"--user-data-dir={profile_dir}")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        return chrome_options

    def open_window(self, role_name, url="https://chatgpt.com"):
        """Belirtilen rol için Chrome penceresi aç"""
        try:
            print(f"🚀 {role_name} için Chrome penceresi açılıyor...")
            
            # Chrome seçeneklerini ayarla
            chrome_options = self.create_chrome_options(role_name)
            
            # WebDriver'ı başlat
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Automation detection'ı engelle
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # URL'ye git
            driver.get(url)
            driver.maximize_window()
            
            # Driver'ı kaydet
            self.drivers[role_name] = driver
            self.current_windows[role_name] = driver.current_window_handle
            
            print(f"✅ {role_name} penceresi başarıyla açıldı: {url}")
            return driver
            
        except Exception as e:
            print(f"❌ {role_name} penceresi açılırken hata: {str(e)}")
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