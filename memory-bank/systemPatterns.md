# Sistem Mimarisi ve Desenler

## Genel Mimari
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web UI        │    │  Message Broker  │    │ Browser Handler │
│   (Flask)       │◄──►│   (Pub/Sub)     │◄──►│   (Selenium)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                       ┌────────▼────────┐
                       │  Role Manager   │
                       │ PM/LD/Boss     │
                       └─────────────────┘
```

## Temel Bileşenler

### 1. BrowserHandler
- Chrome WebDriver yönetimi
- Sayfa otomasyonu
- Mesaj gönderme/alma

### 2. MessageBroker
- Pub/Sub mesajlaşma sistemi
- Mesaj geçmişi
- Real-time broadcasting

### 3. Role System
- ProjectManager sınıfı
- LeadDeveloper sınıfı
- Boss sınıfı

### 4. Web UI
- Flask backend
- SocketIO real-time
- Control panel

## Tasarım Desenleri
- **Observer Pattern**: MessageBroker pub/sub sistemi
- **Strategy Pattern**: Role-based message handling
- **Singleton Pattern**: Configuration management
- **Factory Pattern**: Browser driver creation

## Veri Akışı
1. Kullanıcı input → Web UI
2. Web UI → MessageBroker
3. MessageBroker → Role handlers
4. Role handlers → BrowserHandler
5. BrowserHandler → AI platforms
6. Response → MessageBroker → Web UI

Güncelleme: 2025-06-21 10:51
