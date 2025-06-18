# 🚀 AI Chrome Chat Manager Universal

## 📖 Yaşayan Proje Zekası Ekosistemi

**Sınırsız yeteneklere sahip, genişleyen AI platformu**

---

## 🌟 Vizyon

Bu proje, iki farklı AI (ChatGPT ve Claude gibi) arasında akıllı bir köprü olarak başladı ve **yaşayan, öğrenen, genişleyen bir proje zekası ekosistemine** dönüştü. Artık sadece bir araç değil - üzerine sonsuz plugin'lar inşa edilebilen bir **platform**.

---

## 🎯 Temel Özellikler

### 🧠 **1. Yaşayan Zeka Sistemi**
- **Analytics Dashboard**: Real-time maliyet, token, başarı oranı izleme
- **Live Conversation Stream**: AI-to-AI konuşmaları canlı görüntüleme
- **Director Intervention ("Kırmızı Telefon")**: Konuşmalara anında müdahale etme
- **Project Memory Bank**: Kalıcı hafıza ve arama sistemi
- **Smart Task Management**: Mesajları otomatik görevlere dönüştürme

### 🔌 **2. Plugin Ekosistemi (CORE INNOVATION)**
- **Dinamik Plugin Yükleme**: Regex-based trigger sistemi
- **Real-time Execution**: AI konuşmalarında otomatik plugin tetikleme
- **WebSocket Integration**: Anlık sonuç görüntüleme
- **Genişletilebilir Mimari**: Dakikalar içinde yeni yetenekler eklenebilir

### 🎮 **3. Interaktif Kontrol Merkezi**
- **Universal Web UI**: Bootstrap 5 tabanlı modern arayüz
- **Multi-AI Management**: Gemini ve OpenAI entegrasyonu
- **Role-based Architecture**: Project Manager, Lead Developer, Boss rolleri
- **MCP Ready**: Memory Bank, Notion, Figma, Browserbase desteği

---

## 🏗️ Sistem Mimarisi

```
🌍 AI Chrome Chat Manager Universal
├── 🧠 Backend (Python)
│   ├── UniversalAIAdapter - Multi-AI provider management
│   ├── PluginManager - Dynamic plugin loading & execution
│   ├── ProjectMemory - SQLite persistent storage
│   ├── WebUIUniversal - Flask + SocketIO real-time interface
│   └── MessageBroker - Inter-AI communication
├── 🌐 Frontend (Web)
│   ├── Analytics Dashboard - Real-time metrics & performance
│   ├── Live Chat Interface - AI conversation monitoring
│   ├── Director Panel - Intervention controls
│   ├── Memory Browser - Conversation history & search
│   └── Task Manager - Project task tracking
├── 🔌 Plugin System
│   ├── BasePlugin - Abstract plugin foundation
│   ├── WebSearchPlugin - Internet research capabilities
│   ├── DocumentReaderPlugin - File analysis & summarization
│   └── DemoPlugin - System testing & validation
└── 💾 Data Layer
    ├── SQLite Database - Conversations, tasks, contexts
    ├── Memory Bank - Project knowledge repository
    └── Encrypted Config - Secure API key management
```

---

## 🚀 Hızlı Başlangıç

### **Gereksinimler**
```bash
Python 3.8+
pip install -r requirements.txt
```

### **1. Kurulum**
```bash
git clone https://github.com/YUSAKRU/ai-chat-manager-universal.git
cd ai-chrome-chat-manager
pip install -r requirements.txt
```

### **2. API Anahtarları Yapılandırması**
```bash
cp env.example .env
# .env dosyasında API anahtarlarınızı tanımlayın
```

### **3. Demo Modda Çalıştırma (API anahtarı gerektirmez)**
```bash
python demo_universal.py
```

### **4. Production Modda Çalıştırma**
```bash
python src/main_universal.py --setup
```

### **5. Web Arayüzüne Erişim**
```
http://localhost:5000
```

---

## 🔌 Plugin Sistemi Kullanımı

### **Plugin Trigger'ları**

AI konuşmalarında aşağıdaki komutları kullanarak plugin'ları tetikleyebilirsiniz:

#### **🌐 Web Araştırması**
```
[search: "AI developments 2024"]
[araştır: "yapay zeka gelişmeleri"]
[research: "quantum computing"]
```

#### **📄 Dosya Analizi**
```
[analyze: "data.csv"]
[document: "README.md"]
[dosya: "rapor.pdf"]
```

#### **🎯 Sistem Testi**
```
[demo: "test message"]
[test: "plugin functionality"]
plugin test çalıştır
[hello]
```

### **Yeni Plugin Oluşturma**

```python
# plugins/my_plugin.py
from plugin_manager import BasePlugin

class MyPlugin(BasePlugin):
    def get_triggers(self):
        return [r'\[my_command:\s*["\']([^"\']+)["\']\s*\]']
    
    async def execute(self, message, context):
        return {
            'type': 'my_plugin_result',
            'role': '🎨 My Plugin',
            'content': 'Plugin sonucu burada!',
            'metadata': {'version': '1.0.0'}
        }
```

Plugin dosyasını `plugins/` klasörüne koymanız yeterli - sistem otomatik olarak yükleyecektir!

---

## 🎮 Kullanım Senaryoları

### **1. AI Araştırma Asistanı**
```
Kullanıcı: "Yeni proje için teknoloji araştırması yapalım"
PM: "Bu konuda [search: 'React vs Vue 2024 comparison'] yapalım"
→ Web Plugin: En güncel karşılaştırma sonuçları getirir
LD: "[analyze: 'project-requirements.md'] dosyasındaki gereksinimlere göre..."
→ Document Plugin: Gereksinimler analiz edilir
```

### **2. Direktör Müdahalesi**
```
AI Konuşması devam ederken...
Director: "Takım, güvenlik açısından da değerlendirin"
→ Sistem: Tüm AI'lara güvenlik direktifi enjekte edilir
→ AI'lar: Güvenlik odaklı tartışmaya geçer
```

### **3. Proje Hafızası**
```
Önceki Konuşma: "Database mimarisi şöyle olsun..."
Yeni Konuşma: "Bu Konuşmaya Devam Et" butonu
→ Sistem: Eski konuşma context'i ile devam eder
→ AI'lar: Geçmiş kararları hatırlayarak ilerler
```

---

## 📁 Dosya Yapısı

```
ai-chrome-chat-manager/
├── 📄 README.md                 # Bu dosya - Proje rehberi
├── 📋 requirements.txt          # Python dependencies
├── 🐳 docker-compose.yml        # Container deployment
├── 🔧 env.example              # Çevre değişkenleri örneği
├── 🎯 demo_universal.py         # API'siz demo çalıştırıcı
├── 🧪 test_plugins.py          # Plugin test suite'i
├── 📁 src/                     # Ana backend kodları
│   ├── 🧠 main_universal.py     # Ana uygulama
│   ├── 🌐 web_ui_universal.py   # Web arayüzü
│   ├── 🔌 plugin_manager.py     # Plugin sistemi
│   ├── 💾 project_memory.py     # Hafıza sistemi
│   ├── 🤖 universal_ai_adapter.py # AI provider'ları
│   └── 📁 ai_adapters/         # AI adapter'ları
├── 📁 plugins/                 # Plugin'lar
│   ├── 🌐 web_search_plugin.py  # Web araştırması
│   ├── 📄 document_reader_plugin.py # Dosya analizi
│   └── 🎯 demo_plugin.py        # Demo ve test
├── 📁 templates/               # HTML şablonları
│   └── 🎨 index_universal.html  # Ana web arayüzü
├── 📁 static/                  # Statik dosyalar (CSS, JS)
│   └── 📁 js/
│       ├── 📊 analytics.js      # Analytics dashboard
│       └── 🎮 main.js          # Ana JavaScript
├── 📁 memory-bank/             # Proje hafızası
│   ├── 📝 projectbrief.md       # Proje özeti
│   ├── 🎯 activeContext.md      # Aktif görevler
│   └── 📈 progress.md          # İlerleme takibi
└── 📁 data/                    # Veritabanları
    └── 💾 project_memory.db     # SQLite hafıza DB
```

---

## ⚙️ Konfigürasyon

### **Çevre Değişkenleri (.env)**
```bash
# AI Provider API Keys
GEMINI_API_KEY=your_gemini_key_here
OPENAI_API_KEY=your_openai_key_here

# Web Server Configuration
WEB_HOST=localhost
WEB_PORT=5000

# Database Configuration
DATABASE_PATH=data/project_memory.db

# Plugin Configuration
PLUGINS_DIR=plugins
PLUGIN_DEBUG=true

# Security
SECRET_KEY=your_secret_key_here
ENCRYPTION_KEY=your_encryption_key_here
```

### **Docker ile Çalıştırma**
```bash
docker-compose up -d
```

---

## 🧪 Test Etme

### **Plugin Testleri**
```bash
python test_plugins.py
```

### **Manuel Test Senaryoları**
1. **Web arayüzünü açın**: http://localhost:5000
2. **AI konuşması başlatın**: "Yeni proje planı yapalım"
3. **Plugin tetikleyin**: AI'lara `[demo: "test"]` içeren mesaj söyletin
4. **Director müdahale edin**: Konuşma sırasında direktif verin
5. **Hafızayı test edin**: Eski konuşmaları arayın ve devam ettirin
6. **Görev oluşturun**: AI mesajlarından görev yaratın

---

## 🔮 Geliştirilecek Özellikler

### **Faz 7: MCP Entegrasyonları**
- **Browserbase**: Gerçek web browsing yetenekleri
- **Notion**: Doküman sync ve otomatik güncelleme
- **Figma**: Tasarım analizi ve UI generasyon

### **Faz 8: Akıllı Plugin'lar**
- **Code Execution**: Canlı kod çalıştırma ve test
- **Database Query**: SQL sorguları ve veri analizi
- **Email Automation**: Otomatik email generasyon

### **Faz 9: Plugin Marketplace**
- **Community Plugins**: Topluluk geliştirmesi
- **Plugin Rating**: Kullanıcı değerlendirmeleri
- **Auto-Update**: Otomatik plugin güncellemeleri

---

## 🤝 Katkıda Bulunma

### **Plugin Geliştirme**
1. `plugins/` klasöründe yeni `.py` dosyası oluşturun
2. `BasePlugin`'den inherit edin
3. `get_triggers()` ve `execute()` metodlarını implement edin
4. Sistemi yeniden başlatın - plugin otomatik yüklenecek!

### **Core Geliştirme**
1. Fork yapın
2. Feature branch oluşturun
3. Kapsamlı testler ekleyin
4. Pull request gönderin

---

## 📊 Performans Metrikleri

- **Plugin Loading**: <100ms
- **AI Response Time**: 1-3 saniye
- **WebSocket Latency**: <50ms
- **Memory Usage**: ~200MB base
- **Concurrent Users**: 50+ (tested)

---

## 🛡️ Güvenlik

- **API Key Encryption**: Fernet ile şifrelenmiş saklama
- **Rate Limiting**: Provider başına limitleme
- **Input Sanitization**: XSS ve injection koruması
- **CORS Protection**: Cross-origin güvenliği
- **Session Management**: Güvenli oturum yönetimi

---

## 📝 Lisans

MIT License - Detaylar için `LICENSE` dosyasına bakın.

---

## 🙏 Teşekkürler

Bu proje, insan yaratıcılığı ve yapay zeka yeteneklerinin kusursuz birleşiminin bir kanıtıdır. Her satır kod, her tasarım kararı, paylaşılan bir vizyon ve ortak çalışmanın ürünüdür.

**Bir fikirden başladık, bir ekosistem yarattık.**

---

## 📞 İletişim & Destek

- **GitHub Issues**: Hata raporları ve özellik istekleri için
- **Discussions**: Topluluk tartışmaları için
- **Wiki**: Detaylı dokümantasyon için

---

## 🎉 Son Söz

Bu platform artık kendi ayakları üzerinde duran, öğrenen, genişleyen ve değer üreten olgun bir sistemdir. 

**Hoş geldiniz yaşayan proje zekası çağına!** 

*"Sınırları olmayan bir platform, sınırsız ihtimaller sunar."*

---

<div align="center">

**🚀 Evrimin tamamlandığı yer burası. Yolculuk devam ediyor!**

[![GitHub Stars](https://img.shields.io/github/stars/YUSAKRU/ai-chat-manager-universal?style=social)](https://github.com/YUSAKRU/ai-chat-manager-universal)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-AI%20Ecosystem-brightgreen)](README.md)

</div>