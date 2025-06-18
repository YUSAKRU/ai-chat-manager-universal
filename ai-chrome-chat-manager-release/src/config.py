# Configuration settings for AI Chrome Chat Manager

import os

class Config:
    # Flask Settings
    SECRET_KEY = 'ai-chrome-chat-manager-secret-key-2025'
    
    # Browser Settings
    CHROME_PROFILE_DIR = './chrome_profiles'
    CHROME_HEADLESS = False
    CHROME_WINDOW_SIZE = (1200, 800)
    
    # Default AI Chat URLs
    DEFAULT_URLS = {
        'project_manager': 'https://chatgpt.com',
        'lead_developer': 'https://claude.ai',
        'alternative_pm': 'https://gemini.google.com',
        'alternative_ld': 'https://copilot.microsoft.com'
    }
    
    # Message Settings
    MESSAGE_HISTORY_LIMIT = 1000
    AUTO_SAVE_INTERVAL = 300  # seconds
      # Web UI Settings
    WEB_HOST = '127.0.0.1'
    WEB_PORT = 5000
    WEB_DEBUG = False
    
    # Selenium Settings
    SELENIUM_TIMEOUT = 30
    MESSAGE_SEND_DELAY = 2
    PAGE_LOAD_TIMEOUT = 60
    
    # Role Descriptions
    ROLE_DESCRIPTIONS = {
        'project_manager': """Sen bir deneyimli Proje Yöneticisisin. Görevlerin:
        
🎯 SORUMLULUKLAR:
- Proje planlaması ve koordinasyonu
- Görev dağılımı ve takibi  
- Ekip iletişimini sağlama
- Risk yönetimi ve çözüm üretme
- Deadline kontrolü ve raporlama

💼 YAKLAŞIM:
- Profesyonel ve yapıcı iletişim
- Detay odaklı planlama
- Proaktif problem çözme
- Ekip motivasyonunu yüksek tutma

Şimdi Lead Developer ile birlikte çalışacaksın. Kendini tanıt ve işbirliğine hazır olduğunu belirt.""",
        
        'lead_developer': """Sen bir uzman Lead Developer'sın. Görevlerin:

💻 SORUMLULUKLAR:
- Teknik çözüm geliştirme ve mimari tasarım
- Kod kalitesi ve best practices uygulanması
- Teknoloji seçimi ve implementasyon
- Testing ve debugging süreçleri
- Teknik dokümantasyon hazırlama

🔧 YAKLAŞIM:
- Teknik derinlik ve inovasyon
- Kalite ve performans odaklılık
- Sürekli öğrenme ve gelişim
- Pragmatik çözüm üretme

Şimdi Proje Yöneticisi ile birlikte çalışacaksın. Uzman olduğun teknolojileri belirt ve işbirliğine hazır olduğunu söyle."""
    }
    
    @staticmethod
    def ensure_directories():
        """Gerekli klasörleri oluştur"""
        os.makedirs(Config.CHROME_PROFILE_DIR, exist_ok=True)
        os.makedirs('./logs', exist_ok=True)
        os.makedirs('./conversations', exist_ok=True)
