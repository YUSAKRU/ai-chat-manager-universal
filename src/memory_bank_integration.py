"""
Memory Bank MCP entegrasyonu için Python wrapper
AI Chrome Chat Manager konuşmalarını ve proje bilgilerini Memory Bank'a kaydeder
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
import requests

class MemoryBankIntegration:
    def __init__(self, project_goal: str, location: str = None):
        """
        Memory Bank entegrasyonunu başlat
        
        Args:
            project_goal: Projenin temel amacı
            location: Memory bank klasörünün oluşturulacağı konum
        """
        self.project_goal = project_goal
        self.location = location or os.path.join(os.getcwd(), "memory-bank")
        self.initialized = False
        
        print(f"🧠 Memory Bank Integration başlatılıyor...")
        print(f"📍 Konum: {self.location}")
        print(f"🎯 Proje Hedefi: {project_goal}")

    def initialize_memory_bank(self, gemini_api_key: str = None):
        """Memory Bank'ı başlat"""
        try:
            # MCP tools kullanarak Memory Bank'ı başlat
            # Bu fonksiyon MCP araçlarını çağırır
            print("🚀 Memory Bank başlatılıyor...")
            
            # Proje klasörünü oluştur
            os.makedirs(self.location, exist_ok=True)
            
            # Memory Bank dosya yapısını oluştur
            self._create_memory_bank_structure()
            
            self.initialized = True
            print("✅ Memory Bank başarıyla başlatıldı!")
            return True
            
        except Exception as e:
            print(f"❌ Memory Bank başlatılırken hata: {str(e)}")
            return False

    def _create_memory_bank_structure(self):
        """Memory Bank dosya yapısını oluştur"""
        documents = {
            "projectbrief.md": self._generate_project_brief(),
            "productContext.md": self._generate_product_context(),
            "systemPatterns.md": self._generate_system_patterns(),
            "techContext.md": self._generate_tech_context(),
            "activeContext.md": self._generate_active_context(),
            "progress.md": self._generate_progress()
        }
        
        for filename, content in documents.items():
            filepath = os.path.join(self.location, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"📄 {filename} oluşturuldu")

    def _generate_project_brief(self) -> str:
        """Proje özeti belgesi oluştur"""
        return f"""# AI Chrome Chat Manager - Proje Özeti

## Proje Hedefi
{self.project_goal}

## Vizyon
İki farklı AI chat penceresini yöneten ve onların birbiriyle iletişim kurmasını sağlayan Python uygulaması.

## Kapsam
- Chrome tarayıcısı otomasyonu (Selenium)
- İki AI arasında mesaj köprüsü
- Rol-tabanlı iletişim (Proje Yöneticisi, Lead Developer, Boss)
- Web tabanlı kontrol paneli
- Real-time mesajlaşma sistemi

## Hedef Kullanıcılar
- Yazılım geliştirme ekipleri
- Proje yöneticileri
- AI destekli iş akışı arayanlar

## Başarı Kriterleri
- İki AI'ın sorunsuz iletişim kurması
- Kullanıcının 3. taraf olarak müdahale edebilmesi
- Web arayüzü üzerinden kontrolün sağlanması
- Konuşma geçmişinin kaydedilmesi

Oluşturulma: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""

    def _generate_product_context(self) -> str:
        """Ürün konteksti belgesi oluştur"""
        return f"""# Ürün Konteksti

## Kullanıcı Deneyimi
AI Chrome Chat Manager kullanıcılara aşağıdaki deneyimi sunar:

### Ana Özellikler
1. **Çift AI Chat Yönetimi**
   - ChatGPT ve Claude gibi AI servisleri
   - Otomatik tarayıcı kontrolü
   - Eşzamanlı pencere yönetimi

2. **Rol-Tabanlı İletişim**
   - Proje Yöneticisi rolü
   - Lead Developer rolü
   - Boss/Patron müdahale rolü

3. **Web Kontrol Paneli**
   - Real-time konuşma görüntüleme
   - Manuel müdahale butonları
   - Mesaj geçmişi
   - Görev atama arayüzü

4. **Akıllı Mesajlaşma**
   - Otomatik mesaj routingi
   - Context-aware yanıtlar
   - Mesaj formatlaması

### Kullanım Senaryoları
- **Brainstorming Sessiyonları**: İki AI'ın farklı perspektiflerden fikir üretmesi
- **Kod Riview**: Bir AI'ın kod yazması, diğerinin review yapması
- **Proje Planlaması**: PM ve Developer rolleriyle proje planlaması

Güncelleme: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""

    def _generate_system_patterns(self) -> str:
        """Sistem mimarisi belgesi oluştur"""
        return f"""# Sistem Mimarisi ve Desenler

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

Güncelleme: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""

    def _generate_tech_context(self) -> str:
        """Teknoloji konteksti belgesi oluştur"""
        return f"""# Teknoloji Konteksti

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

Güncelleme: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""

    def _generate_active_context(self) -> str:
        """Aktif kontekst belgesi oluştur"""
        return f"""# Aktif Geliştirme Konteksti

## Şu Anki Durum
Proje temel MVP (Minimum Viable Product) aşamasını tamamlamıştır.

## Aktif Görevler
- [ ] Web UI HTML template'lerinin tamamlanması
- [ ] Memory Bank MCP entegrasyonu
- [ ] Hata yönetiminin iyileştirilmesi
- [ ] Logging sisteminin eklenmesi
- [ ] Konfigürasyon dosyası desteği

## Son Çalışmalar
- ✅ Chrome browser otomasyonu
- ✅ Mesaj broker sistemi
- ✅ Rol-tabanlı mimari
- ✅ Flask web sunucusu
- ✅ SocketIO entegrasyonu

## Teknik Borçlar
1. **Template Dosyaları**: index.html boş, doldurulması gerek
2. **Hata Yakalama**: Try/catch blokları eksik
3. **Config Yönetimi**: JSON config dosyası eklenebilir
4. **Test Coverage**: Unit testler yazılmalı

## Öncelikli İyileştirmeler
1. Web UI'nin tamamlanması
2. Memory Bank entegrasyonu
3. Comprehensive error handling
4. Logging infrastructure

## Gelecek Özellikler
- Conversation analytics
- Custom AI prompt templates
- Multi-language support
- Plugin system

Son Güncelleme: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""

    def _generate_progress(self) -> str:
        """İlerleme belgesi oluştur"""
        return f"""# Proje İlerlemesi

## Milestone 1: Temel Sistem ✅
**Tamamlanma: %95**
- [x] Proje yapısı oluşturuldu
- [x] Chrome WebDriver entegrasyonu
- [x] Message Broker sistemi
- [x] Rol-tabanlı mimari
- [x] Flask web sunucusu
- [x] SocketIO real-time iletişim
- [ ] Web UI templates (in progress)

## Milestone 2: Memory Bank Entegrasyonu 🔄
**Tamamlanma: %10**
- [x] Memory Bank MCP araştırması
- [ ] MCP entegrasyon modülü
- [ ] Konuşma kaydetme sistemi
- [ ] Proje dokümantasyon otomasyonu

## Milestone 3: Gelişmiş Özellikler ⏳
**Tamamlanma: %0**
- [ ] Advanced error handling
- [ ] Comprehensive logging
- [ ] Configuration management
- [ ] Unit testing framework

## Tamamlanan İşler

### 2025-06-11: Temel Sistem Kurulumu
- Proje klasör yapısı oluşturuldu
- requirements.txt hazırlandı
- Ana sınıflar implement edildi
- Chrome otomasyonu çalışır hale getirildi

### Karşılaşılan Sorunlar ve Çözümler
1. **Chrome Profile Conflicts**: 
   - Sorun: Aynı profil birden fazla kullanım
   - Çözüm: Dinamik profil klasörleri

2. **SocketIO Import Errors**:
   - Sorun: Flask-SocketIO eksik
   - Çözüm: requirements.txt güncellendi

3. **Message Broadcasting**:
   - Sorun: Web UI broadcast eksik
   - Çözüm: Callback sistemi eklendi

## Metrics
- **Code Lines**: ~1500
- **Files Created**: 15+
- **Dependencies**: 6 main packages
- **Test Coverage**: 0% (TODO)

Son Güncelleme: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""

    def save_conversation(self, messages: List[Dict], session_id: str = None):
        """Konuşmayı Memory Bank'a kaydet"""
        if not self.initialized:
            print("⚠️ Memory Bank başlatılmamış!")
            return False
            
        try:
            session_id = session_id or f"session_{int(time.time())}"
            
            # Konuşmayı formatla
            conversation_content = self._format_conversation(messages, session_id)
            
            # Progress dosyasını güncelle
            self._update_progress_with_conversation(conversation_content)
            
            # Ayrı konuşma dosyası kaydet
            conversations_dir = os.path.join(self.location, "conversations")
            os.makedirs(conversations_dir, exist_ok=True)
            
            conversation_file = os.path.join(conversations_dir, f"{session_id}.md")
            with open(conversation_file, 'w', encoding='utf-8') as f:
                f.write(conversation_content)
            
            print(f"💾 Konuşma kaydedildi: {conversation_file}")
            return True
            
        except Exception as e:
            print(f"❌ Konuşma kaydedilirken hata: {str(e)}")
            return False

    def _format_conversation(self, messages: List[Dict], session_id: str) -> str:
        """Konuşmayı Markdown formatında düzenle"""
        content = f"""# AI Chat Session: {session_id}

**Tarih**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Session ID**: {session_id}
**Mesaj Sayısı**: {len(messages)}

---

## Konuşma

"""
        
        for msg in messages:
            timestamp = msg.get('timestamp', '')[:19] if msg.get('timestamp') else 'Unknown'
            sender = msg.get('sender', 'Unknown')
            content_text = msg.get('content', '')
            
            content += f"""### [{timestamp}] {sender}

{content_text}

---

"""
        
        return content

    def _update_progress_with_conversation(self, conversation_content: str):
        """Progress dosyasını konuşma ile güncelle"""
        try:
            progress_file = os.path.join(self.location, "progress.md")
            
            if os.path.exists(progress_file):
                with open(progress_file, 'r', encoding='utf-8') as f:
                    current_content = f.read()
                
                # Yeni konuşma bölümü ekle
                new_section = f"""

## Son Konuşma Sessiyonu - {datetime.now().strftime('%Y-%m-%d %H:%M')}

{conversation_content[:500]}...

[Tam konuşma için conversations/ klasörünü kontrol edin]

"""
                
                updated_content = current_content + new_section
                
                with open(progress_file, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                    
        except Exception as e:
            print(f"⚠️ Progress güncellenirken hata: {str(e)}")

    def query_memory_bank(self, query: str) -> str:
        """Memory Bank'ı sorgula"""
        if not self.initialized:
            return "Memory Bank başlatılmamış!"
            
        try:
            # Memory Bank dosyalarını tara
            results = []
            
            for root, dirs, files in os.walk(self.location):
                for file in files:
                    if file.endswith('.md'):
                        file_path = os.path.join(root, file)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if query.lower() in content.lower():
                                results.append({
                                    'file': file,
                                    'path': file_path,
                                    'snippet': self._extract_snippet(content, query)
                                })
            
            if results:
                response = f"🔍 '{query}' için {len(results)} sonuç bulundu:\n\n"
                for result in results:
                    response += f"📄 **{result['file']}**\n{result['snippet']}\n\n"
                return response
            else:
                return f"🔍 '{query}' için sonuç bulunamadı."
                
        except Exception as e:
            return f"❌ Sorgu sırasında hata: {str(e)}"

    def _extract_snippet(self, content: str, query: str, context_length: int = 150) -> str:
        """Sorgu etrafından snippet çıkar"""
        query_pos = content.lower().find(query.lower())
        if query_pos == -1:
            return content[:context_length] + "..."
        
        start = max(0, query_pos - context_length // 2)
        end = min(len(content), query_pos + len(query) + context_length // 2)
        
        snippet = content[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
            
        return snippet

    def update_active_context(self, new_tasks: List[str] = None, completed_tasks: List[str] = None):
        """Aktif konteksti güncelle"""
        if not self.initialized:
            return False
            
        try:
            active_context_file = os.path.join(self.location, "activeContext.md")
            
            if os.path.exists(active_context_file):
                with open(active_context_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Yeni görevler ekle
                if new_tasks:
                    tasks_section = "\n\n## Yeni Eklenen Görevler\n"
                    for task in new_tasks:
                        tasks_section += f"- [ ] {task}\n"
                    content += tasks_section
                
                # Tamamlanan görevler ekle
                if completed_tasks:
                    completed_section = "\n\n## Yeni Tamamlanan Görevler\n"
                    for task in completed_tasks:
                        completed_section += f"- [x] {task}\n"
                    content += completed_section
                
                # Güncelleme zamanını ekle
                content += f"\n\nSon Güncelleme: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                
                with open(active_context_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print("📝 Aktif kontekst güncellendi")
                return True
                
        except Exception as e:
            print(f"❌ Aktif kontekst güncellenirken hata: {str(e)}")
            return False

    def get_project_summary(self) -> str:
        """Proje özetini getir"""
        if not self.initialized:
            return "Memory Bank başlatılmamış!"
            
        try:
            summary = f"""# AI Chrome Chat Manager - Proje Özeti

📍 **Memory Bank Konumu**: {self.location}
🎯 **Proje Hedefi**: {self.project_goal}

"""
            
            # Her belge türünden özet çıkar
            docs = ['projectbrief.md', 'productContext.md', 'systemPatterns.md', 
                   'techContext.md', 'activeContext.md', 'progress.md']
            
            for doc in docs:
                doc_path = os.path.join(self.location, doc)
                if os.path.exists(doc_path):
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # İlk paragrafı al
                        first_para = content.split('\n\n')[1] if '\n\n' in content else content[:200]
                        summary += f"## {doc}\n{first_para[:200]}...\n\n"
            
            return summary
            
        except Exception as e:
            return f"❌ Özet oluşturulurken hata: {str(e)}"

    # -------------------------------------------------------------
    # 🔄 Doküman Güncelleme & Dışa Aktarma
    # -------------------------------------------------------------

    def update_document(self, document_type: str, content: str = "", regenerate: bool = False) -> str:
        """Belirtilen dokümanı güncelle veya yeniden üret.

        Args:
            document_type: Doküman türü anahtarı (örn. "projectbrief", "productContext").
            content: Dokümana yazılacak içerik. Boş bırakılır ve regenerate=True ise varsayılan şablonla yeniden oluşturulur.
            regenerate: True verilirse mevcut içeriği göz ardı edip ilgili _generate_ metodundan çıkan içerik kullanılır.

        Returns:
            İşlem sonucu mesajı.
        """
        if not self.initialized:
            return "Memory Bank başlatılmamış!"

        # Haritalama tablosu
        generators = {
            "projectbrief": ("projectbrief.md", self._generate_project_brief),
            "productcontext": ("productContext.md", self._generate_product_context),
            "systempatterns": ("systemPatterns.md", self._generate_system_patterns),
            "techcontext": ("techContext.md", self._generate_tech_context),
            "activecontext": ("activeContext.md", self._generate_active_context),
            "progress": ("progress.md", self._generate_progress),
        }

        key = document_type.lower()
        if key not in generators:
            return f"❌ Desteklenmeyen doküman türü: {document_type}"

        filename, generator_fn = generators[key]
        file_path = os.path.join(self.location, filename)

        try:
            # İçeriği belirle
            if regenerate or not content:
                content_to_write = generator_fn()
            else:
                content_to_write = content

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content_to_write)

            return f"✅ {filename} güncellendi"
        except Exception as e:
            return f"❌ Doküman güncellenemedi: {str(e)}"

    def export_memory_bank(self, export_format: str = "json") -> str:
        """Memory Bank klasörünü dışa aktar.

        Args:
            export_format: "json" veya "folder" (varsayılan json).

        Returns:
            Oluşturulan dosya/dizin yolu veya hata mesajı.
        """
        if not self.initialized:
            return "Memory Bank başlatılmamış!"

        try:
            export_format = export_format.lower()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if export_format == "json":
                export_data = {}
                for file in os.listdir(self.location):
                    if file.endswith(".md"):
                        with open(os.path.join(self.location, file), "r", encoding="utf-8") as f:
                            export_data[file] = f.read()

                export_path = os.path.join(self.location, f"memory_bank_export_{timestamp}.json")
                with open(export_path, "w", encoding="utf-8") as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)

                return f"✅ Dışa aktarıldı: {export_path}"

            elif export_format == "folder":
                # Basitçe klasör yolunu döndür
                return f"📁 Memory Bank klasörü: {self.location}"

            else:
                return "❌ Desteklenmeyen export formatı. Sadece 'json' veya 'folder' kullanın."

        except Exception as e:
            return f"❌ Export sırasında hata: {str(e)}"
