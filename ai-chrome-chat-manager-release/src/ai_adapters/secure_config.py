"""
Güvenli Konfigürasyon Yönetimi - API Key Şifreleme
"""
import os
import json
import base64
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SecureConfigManager:
    """API anahtarlarını güvenli şekilde yöneten basit sınıf"""
    
    def __init__(self, config_file: str = "config/api_keys.enc"):
        self.config_file = config_file
        self.config_dir = os.path.dirname(config_file)
        self.cipher = None
        
        # Config dizinini oluştur
        if self.config_dir and not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir, exist_ok=True)
    
    def _generate_key(self, password: str = "AI-Chrome-Chat-Manager-2025") -> bytes:
        """Şifreleme anahtarı oluştur"""
        password_bytes = password.encode()
        salt = b'ai-chrome-chat-salt'  # Production'da random salt kullan
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        return key
    
    def _get_cipher(self) -> Fernet:
        """Cipher nesnesini al"""
        if not self.cipher:
            key = self._generate_key()
            self.cipher = Fernet(key)
        return self.cipher
    
    def save_api_key(self, provider: str, api_key: str) -> bool:
        """API anahtarını kaydet"""
        try:
            # Mevcut konfigürasyonları yükle
            configs = self.load_all_keys()
            
            # Yeni anahtarı ekle
            configs[provider] = api_key
            
            # Şifreleyerek kaydet
            cipher = self._get_cipher()
            json_data = json.dumps(configs)
            encrypted_data = cipher.encrypt(json_data.encode())
            
            with open(self.config_file, 'wb') as f:
                f.write(encrypted_data)
            
            print(f"✅ {provider} API anahtarı kaydedildi")
            return True
            
        except Exception as e:
            print(f"❌ API anahtarı kaydetme hatası: {str(e)}")
            return False
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """API anahtarını al"""
        try:
            configs = self.load_all_keys()
            return configs.get(provider)
        except:
            return None
    
    def load_all_keys(self) -> Dict[str, str]:
        """Tüm API anahtarlarını yükle"""
        try:
            if not os.path.exists(self.config_file):
                return {}
            
            cipher = self._get_cipher()
            
            with open(self.config_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = cipher.decrypt(encrypted_data)
            configs = json.loads(decrypted_data.decode())
            
            return configs
            
        except Exception as e:
            print(f"❌ API anahtarları yükleme hatası: {str(e)}")
            return {}
    
    def remove_api_key(self, provider: str) -> bool:
        """API anahtarını kaldır"""
        try:
            configs = self.load_all_keys()
            
            if provider in configs:
                del configs[provider]
                
                # Şifreleyerek kaydet
                cipher = self._get_cipher()
                json_data = json.dumps(configs)
                encrypted_data = cipher.encrypt(json_data.encode())
                
                with open(self.config_file, 'wb') as f:
                    f.write(encrypted_data)
                
                print(f"🗑️ {provider} API anahtarı kaldırıldı")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ API anahtarı kaldırma hatası: {str(e)}")
            return False 