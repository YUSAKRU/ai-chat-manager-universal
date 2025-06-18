#!/usr/bin/env python3
"""
🚀 AI Chrome Chat Manager - Basit Demo Çalıştırıcı
Hiçbir API anahtarı gerektirmez, sadece web arayüzünü gösterir
"""

import os
import sys
from pathlib import Path

# Flask ve gerekli modülleri import et
try:
    from flask import Flask, render_template, jsonify
    from flask_socketio import SocketIO, emit
    import threading
    import time
    import webbrowser
    print("✅ Tüm modüller başarıyla yüklendi!")
except ImportError as e:
    print(f"❌ Modül yükleme hatası: {e}")
    print("📦 Gerekli modülleri yüklemek için: pip install -r requirements.txt")
    sys.exit(1)

# Demo uygulaması
app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')
app.config['SECRET_KEY'] = 'demo-secret-key'
# Python 3.13 uyumluluğu için threading mode kullan
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Demo verileri
demo_stats = {
    "ai_adapters": [
        {
            "id": "gemini-1",
            "type": "Gemini Pro",
            "status": "active",
            "requests": 47,
            "tokens": 28450,
            "cost": 0.28,
            "success_rate": 98.2,
            "avg_response_time": 1.24
        },
        {
            "id": "openai-1", 
            "type": "GPT-4",
            "status": "active",
            "requests": 32,
            "tokens": 19680,
            "cost": 0.59,
            "success_rate": 100.0,
            "avg_response_time": 0.89
        }
    ],
    "system_metrics": {
        "total_conversations": 15,
        "active_plugins": 3,
        "memory_entries": 127,
        "uptime": "2h 45m"
    }
}

demo_conversations = [
    {
        "id": 1,
        "timestamp": "2025-06-18 19:15:23",
        "role_from": "Project Manager",
        "role_to": "Lead Developer", 
        "ai_from": "Gemini Pro",
        "ai_to": "GPT-4",
        "message": "Yeni plugin sistemi için kod review başlatalım. DocumentReader ve WebSearch pluginleri hazır.",
        "status": "completed"
    },
    {
        "id": 2,
        "timestamp": "2025-06-18 19:16:45",
        "role_from": "Lead Developer",
        "role_to": "Boss",
        "ai_from": "GPT-4", 
        "ai_to": "Claude",
        "message": "Plugin architecture implementasyonu tamamlandı. Test sonuçları %100 başarılı.",
        "status": "completed"
    }
]

@app.route('/')
def index():
    """Ana sayfa"""
    return render_template('index_universal.html')

@app.route('/api/stats')
def get_stats():
    """Demo istatistikleri"""
    return jsonify(demo_stats)

@app.route('/api/conversations')
def get_conversations():
    """Demo konuşmaları"""
    return jsonify(demo_conversations)

@socketio.on('connect')
def handle_connect():
    """WebSocket bağlantısı"""
    emit('status', {'msg': '🔗 Demo sisteme bağlandınız!'})
    print("🔗 Yeni kullanıcı bağlandı")

@socketio.on('send_message')
def handle_message(data):
    """Demo mesaj gönderme"""
    message = data.get('message', '')
    
    # Plugin testleri
    if '[search:' in message:
        emit('plugin_result', {
            'plugin': 'WebSearch',
            'result': '🔍 Web araması tamamlandı. 5 alakalı sonuç bulundu.',
            'timestamp': time.strftime('%H:%M:%S')
        })
    elif '[analyze:' in message:
        emit('plugin_result', {
            'plugin': 'DocumentReader', 
            'result': '📄 Doküman analizi tamamlandı. 3 sayfa işlendi.',
            'timestamp': time.strftime('%H:%M:%S')
        })
    elif '[demo:' in message:
        emit('plugin_result', {
            'plugin': 'DemoPlugin',
            'result': '🎯 Demo plugin çalıştırıldı başarıyla!',
            'timestamp': time.strftime('%H:%M:%S')
        })
    
    # Konuşma simülasyonu
    emit('conversation_update', {
        'role_from': 'User',
        'role_to': 'AI Assistant',
        'message': message,
        'timestamp': time.strftime('%H:%M:%S'),
        'status': 'processing'
    })

def open_browser():
    """Tarayıcıyı otomatik aç"""
    time.sleep(2)
    webbrowser.open('http://localhost:5000')

def main():
    """Ana fonksiyon"""
    print("="*70)
    print("🎯 AI CHROME CHAT MANAGER - UNIVERSAL EDITION DEMO")
    print("="*70)
    print("🚀 Web Server başlatılıyor...")
    print("📊 Analytics Dashboard hazırlanıyor...")
    print("🔌 Plugin sistemi simüle ediliyor...")
    print()
    print("✨ DEMO ÖZELLİKLERİ:")
    print("  🎨 Modern Bootstrap 5 UI")
    print("  📊 Canlı Analytics Dashboard")
    print("  🤖 AI Adapter Performance Kartları")
    print("  💬 Real-time Conversation Stream")
    print("  🔌 Plugin Test Interface")
    print("  📈 Token ve Maliyet Grafikleri")
    print()
    print("🌐 Demo çalışacak adres: http://localhost:5000")
    print("❌ Çıkmak için: Ctrl+C")
    print("="*70)
    
    # Tarayıcıyı background'da aç
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Flask uygulamasını başlat
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n👋 Demo sonlandırılıyor...")
    except Exception as e:
        print(f"❌ Hata: {e}")
    finally:
        print("✅ Demo tamamlandı!")

if __name__ == "__main__":
    main() 