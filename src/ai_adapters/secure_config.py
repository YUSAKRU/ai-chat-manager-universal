"""
Güvenli Konfigürasyon Yönetimi - API Key Şifreleme
"""
import os
import json
import base64
from typing import Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import load_dotenv
import asyncio
from logger import logger

class SecureConfigManager:
    """API anahtarlarını güvenli şekilde yöneten sınıf"""
    
    def __init__(self):
        self.key_file = ".key"
        self.encrypted_config_file = "config.enc"
        self.cipher = None
        
    def _generate_key(self, password: str = None) -> bytes:
        """Şifreleme anahtarı oluştur"""
        if not password:
            # Ortam değişkeninden veya varsayılan
            password = os.getenv('CONFIG_PASSWORD', 'AI-Chrome-Chat-Manager-2025')
        
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
    
    def _get_or_create_cipher(self) -> Fernet:
        """Cipher nesnesini al veya oluştur"""
        if self.cipher:
            return self.cipher
        
        # Key dosyası var mı?
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            # Yeni key oluştur
            key = self._generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            os.chmod(self.key_file, 0o600)  # Sadece owner okuyabilir
        
        self.cipher = Fernet(key)
        return self.cipher
    
    def encrypt_config(self, config_data: Dict[str, Any]) -> None:
        """Konfigürasyonu şifrele ve kaydet"""
        try:
            cipher = self._get_or_create_cipher()
            
            # JSON'a çevir ve şifrele
            json_data = json.dumps(config_data, indent=2)
            encrypted_data = cipher.encrypt(json_data.encode())
            
            # Şifreli dosyaya yaz
            with open(self.encrypted_config_file, 'wb') as f:
                f.write(encrypted_data)
            
            os.chmod(self.encrypted_config_file, 0o600)
            logger.info("✅ Konfigürasyon güvenli şekilde şifrelendi", "SECURE_CONFIG")
            
        except Exception as e:
            logger.error(f"Şifreleme hatası: {str(e)}", "SECURE_CONFIG", e)
            raise
    
    def decrypt_config(self) -> Dict[str, Any]:
        """Şifreli konfigürasyonu çöz"""
        try:
            if not os.path.exists(self.encrypted_config_file):
                return {}
            
            cipher = self._get_or_create_cipher()
            
            # Şifreli veriyi oku
            with open(self.encrypted_config_file, 'rb') as f:
                encrypted_data = f.read()
            
            # Çöz ve JSON'a dönüştür
            decrypted_data = cipher.decrypt(encrypted_data)
            config_data = json.loads(decrypted_data.decode())
            
            return config_data
            
        except Exception as e:
            logger.error(f"Deşifre hatası: {str(e)}", "SECURE_CONFIG", e)
            return {}
    
    async def load_secure_configs(self, env_file: str = ".env") -> Dict[str, Any]:
        """Güvenli konfigürasyonları yükle (.env veya şifreli dosyadan)"""
        
        # .env dosyasını yükle
        load_dotenv(env_file)
        
        # Şifreli config varsa önce onu dene
        encrypted_configs = self.decrypt_config()
        if encrypted_configs:
            logger.info("🔐 Şifreli konfigürasyon yüklendi", "SECURE_CONFIG")
            return encrypted_configs
        
        # .env'den yükle ve şifrele
        configs = {}
        
        # Gemini PM
        if os.getenv('GEMINI_PM_API_KEY'):
            configs['gemini_pm'] = {
                'type': 'gemini',
                'api_key': os.getenv('GEMINI_PM_API_KEY'),
                'model': os.getenv('GEMINI_PM_MODEL', 'gemini-2.0-flash'),
                'max_tokens': int(os.getenv('GEMINI_PM_MAX_TOKENS', '2000')),
                'temperature': float(os.getenv('GEMINI_PM_TEMPERATURE', '0.7'))
            }
        
        # Gemini LD
        if os.getenv('GEMINI_LD_API_KEY'):
            configs['gemini_ld'] = {
                'type': 'gemini',
                'api_key': os.getenv('GEMINI_LD_API_KEY'),
                'model': os.getenv('GEMINI_LD_MODEL', 'gemini-2.0-flash'),
                'max_tokens': int(os.getenv('GEMINI_LD_MAX_TOKENS', '2000')),
                'temperature': float(os.getenv('GEMINI_LD_TEMPERATURE', '0.9'))
            }
        
        # OpenAI PM
        if os.getenv('OPENAI_PM_API_KEY'):
            configs['openai_pm'] = {
                'type': 'openai',
                'api_key': os.getenv('OPENAI_PM_API_KEY'),
                'model': os.getenv('OPENAI_PM_MODEL', 'gpt-4o-mini'),
                'max_tokens': int(os.getenv('OPENAI_PM_MAX_TOKENS', '2000')),
                'temperature': float(os.getenv('OPENAI_PM_TEMPERATURE', '0.7'))
            }
        
        # OpenAI LD
        if os.getenv('OPENAI_LD_API_KEY'):
            configs['openai_ld'] = {
                'type': 'openai',
                'api_key': os.getenv('OPENAI_LD_API_KEY'),
                'model': os.getenv('OPENAI_LD_MODEL', 'gpt-4o-mini'),
                'max_tokens': int(os.getenv('OPENAI_LD_MAX_TOKENS', '2000')),
                'temperature': float(os.getenv('OPENAI_LD_TEMPERATURE', '0.9'))
            }
        
        # Konfigürasyonları şifrele
        if configs:
            self.encrypt_config(configs)
            logger.info("🔒 .env konfigürasyonları şifrelenerek kaydedildi", "SECURE_CONFIG")
        
        return configs
    
    def add_api_key(self, adapter_id: str, api_key: str, adapter_type: str = 'gemini', **kwargs):
        """Yeni API anahtarı ekle"""
        try:
            # Mevcut konfigürasyonları yükle
            configs = self.decrypt_config()
            
            # Yeni konfigürasyon ekle
            configs[adapter_id] = {
                'type': adapter_type,
                'api_key': api_key,
                'model': kwargs.get('model', 'gemini-2.0-flash'),
                'max_tokens': kwargs.get('max_tokens', 2000),
                'temperature': kwargs.get('temperature', 0.7)
            }
            
            # Şifreleyerek kaydet
            self.encrypt_config(configs)
            
            logger.info(f"✅ {adapter_id} API anahtarı güvenli şekilde eklendi", "SECURE_CONFIG")
            return True
            
        except Exception as e:
            logger.error(f"API anahtarı ekleme hatası: {str(e)}", "SECURE_CONFIG", e)
            return False
    
    def remove_api_key(self, adapter_id: str):
        """API anahtarını kaldır"""
        try:
            configs = self.decrypt_config()
            
            if adapter_id in configs:
                del configs[adapter_id]
                self.encrypt_config(configs)
                logger.info(f"🗑️ {adapter_id} API anahtarı kaldırıldı", "SECURE_CONFIG")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"API anahtarı kaldırma hatası: {str(e)}", "SECURE_CONFIG", e)
            return False 