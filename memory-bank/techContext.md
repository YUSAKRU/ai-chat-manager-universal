# Teknoloji Konteksti

## Teknoloji Stack

### Backend
- **Python 3.x**: Ana programlama dili
- **Selenium WebDriver**: Tarayıcı otomasyonu
- **Flask**: Web framework
- **Flask-SocketIO**: Real-time iletişim
- **Threading**: Eşzamanlı işlemler

### Frontend
- **HTML5/CSS3**: Web arayüzü
- **JavaScript**: Client-side logic
- **Socket.IO**: Real-time updates
- **Bootstrap**: UI framework

### Altyapı
- **Chrome WebDriver**: Tarayıcı kontrolü
- **WebDriver Manager**: Driver yönetimi
- **JSON**: Konfigürasyon ve veri

## Harici Bağımlılıklar
```
selenium==4.33.0
flask==3.1.1
flask-socketio==5.5.1
eventlet==0.40.0
requests==2.32.4
webdriver-manager==4.0.2
```

## Klasör Yapısı
```
ai-chrome-chat-manager/
├── src/
│   ├── main.py                 # Ana uygulama
│   ├── browser_handler.py      # Chrome otomasyonu
│   ├── message_broker.py       # Mesajlaşma sistemi
│   ├── web_ui.py              # Web arayüzü
│   ├── config.py              # Konfigürasyon
│   └── roles/                 # Rol sınıfları
├── templates/                 # HTML şablonları
├── static/                    # CSS/JS dosyaları
├── chrome_profiles/          # Chrome profilleri
└── logs/                     # Log dosyaları
```

## Konfigürasyon
- **Config sınıfı**: Merkezi ayar yönetimi
- **Chrome options**: Tarayıcı konfigürasyonu
- **Flask settings**: Web sunucu ayarları

Güncelleme: 2025-06-11 12:11
