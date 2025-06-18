# 🚀 AI Chrome Chat Manager - Universal Edition
## Kurulum ve Çalıştırma Rehberi

### 📋 Sistem Gereksinimleri
- Python 3.8 veya üzeri
- Internet bağlantısı
- Windows/Linux/MacOS

### 🔧 Hızlı Kurulum

#### 1. Python Bağımlılıklarını Yükle
```bash
pip install -r requirements.txt
```

#### 2. API Anahtarlarını Yapılandır (Opsiyonel)
```bash
# env.example dosyasını .env olarak kopyala
copy env.example .env

# .env dosyasını düzenle ve API anahtarlarını ekle
```

#### 3. Sistemi Çalıştır
```bash
python quickstart.py
```

### 🎮 Çalıştırma Modları

**1️⃣ DEMO MODE**
- API anahtarı gerektirmez
- Sistemi test etmek için idealdir
- Web arayüzü simülasyonu

**2️⃣ PRODUCTION**
- Gerçek API anahtarları gerekir
- Tam özellikli sistem
- Gerçek AI entegrasyonları

**3️⃣ SETUP**
- Kurulum yardımcısı
- Bağımlılık kontrolü
- API anahtarı konfigürasyonu

### 🐳 Docker ile Çalıştırma
```bash
docker-compose up --build
```

### 🆘 Yaygın Sorunlar

**"env.example dosyası bulunamadı" Hatası:**
- Bu dosya paket içinde bulunuyor
- Eğer eksikse, manuel olarak .env dosyası oluşturun

**Bağımlılık Hataları:**
- `pip install -r requirements.txt` komutunu çalıştırın
- Python sürümünüzü kontrol edin (3.8+)

**Port Hatası:**
- Web arayüzü varsayılan olarak 5000 portunu kullanır
- Eğer port meşgulse, quickstart.py'de port numarasını değiştirin

### 📞 Destek
Sorun yaşıyorsanız, lütfen GitHub repository'sinde issue oluşturun.

### ⚡ İpuçları
- İlk kullanımda DEMO MODE'u deneyin
- Production mode için mutlaka API anahtarları gereklidir
- Test modunu kullanarak sistem sağlığını kontrol edebilirsiniz 