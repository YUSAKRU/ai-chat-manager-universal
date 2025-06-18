# AI Chrome Chat Manager - Docker Image
FROM python:3.11-slim

# Sistem bağımlılıkları
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Çalışma dizini
WORKDIR /app

# Bağımlılıkları kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodunu kopyala
COPY src/ ./src/
COPY templates/ ./templates/
COPY static/ ./static/

# Güvenlik için non-root kullanıcı
RUN useradd -m -u 1000 aimanager && \
    chown -R aimanager:aimanager /app

USER aimanager

# Ortam değişkenleri
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Web UI portu
EXPOSE 5000

# Varsayılan komut
CMD ["python", "src/main_universal.py"] 