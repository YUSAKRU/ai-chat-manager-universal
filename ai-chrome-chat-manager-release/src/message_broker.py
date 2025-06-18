import json
import time
from datetime import datetime
from typing import Dict, List, Callable
import threading

class MessageBroker:
    def __init__(self):
        self.subscribers = {}
        self.message_history = []
        self.lock = threading.Lock()
        self.web_broadcast_callback = None

    def subscribe(self, channel, callback):
        """Belirtilen kanala mesaj dinleyicisi ekle"""
        with self.lock:
            if channel not in self.subscribers:
                self.subscribers[channel] = []
                print(f"📢 {channel} kanalı oluşturuldu")
            
            # Aynı callback'in tekrar eklenmesini önle
            if callback not in self.subscribers[channel]:
                self.subscribers[channel].append(callback)
                callback_name = getattr(callback, '__self__', {})
                callback_name = getattr(callback_name, '__class__', {})
                callback_name = getattr(callback_name, '__name__', 'Unknown')
                print(f"  ↳ {callback_name} artık {channel} kanalını dinliyor")

    def unsubscribe(self, channel, callback):
        """Mesaj dinlemeyi durdur"""
        with self.lock:
            if channel in self.subscribers and callback in self.subscribers[channel]:
                self.subscribers[channel].remove(callback)
                print(f"🔇 {channel} kanalından dinleme durduruldu")

    def publish(self, channel, message, sender=None):
        """Mesaj yayınla"""
        with self.lock:
            # Mesaj objesi oluştur
            message_obj = {
                "id": f"msg_{int(time.time() * 1000)}",
                "channel": channel,
                "sender": sender,
                "content": message,
                "timestamp": datetime.now().isoformat(),
                "type": "text"
            }
            
            # Mesaj geçmişine ekle
            self.message_history.append(message_obj)
            
            # Log
            content_preview = str(message)[:100] if isinstance(message, str) else str(message.get('content', message))[:100]
            print(f"📢 [{channel}] {sender}: {content_preview}...")
            
            # Web UI'ya broadcast et
            if self.web_broadcast_callback:
                try:
                    self.web_broadcast_callback(message_obj)
                except Exception as e:
                    print(f"⚠️ Web broadcast hatası: {str(e)}")
            
            # Abonelere gönder
            if channel in self.subscribers:
                for callback in self.subscribers[channel]:
                    try:
                        callback(message_obj)
                    except Exception as e:
                        print(f"❌ Mesaj gönderilirken hata: {str(e)}")
            
            # Web UI'a da broadcast et
            if self.web_broadcast_callback:
                try:
                    self.web_broadcast_callback(message_obj)
                except Exception as e:
                    print(f"❌ Web broadcast hatası: {str(e)}")

    def set_web_broadcast_callback(self, callback):
        """Web broadcast callback'ini ayarla"""
        self.web_broadcast_callback = callback

    def get_message_history(self, channel=None, limit=10):
        """Mesaj geçmişini getir"""
        with self.lock:
            if channel:
                filtered_messages = [msg for msg in self.message_history if msg["channel"] == channel]
                return filtered_messages[-limit:] if limit else filtered_messages
            else:
                return self.message_history[-limit:] if limit else self.message_history

    def clear_history(self):
        """Mesaj geçmişini temizle"""
        with self.lock:
            self.message_history.clear()
            print("🧹 Mesaj geçmişi temizlendi")

    def get_active_channels(self):
        """Aktif kanalları getir"""
        with self.lock:
            return list(self.subscribers.keys())

    def save_conversation(self, filename):
        """Konuşmayı dosyaya kaydet"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.message_history, f, indent=2, ensure_ascii=False)
            print(f"💾 Konuşma kaydedildi: {filename}")
        except Exception as e:
            print(f"❌ Konuşma kaydedilirken hata: {str(e)}")

    def load_conversation(self, filename):
        """Konuşmayı dosyadan yükle"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.message_history = json.load(f)
            print(f"📂 Konuşma yüklendi: {filename}")
        except Exception as e:
            print(f"❌ Konuşma yüklenirken hata: {str(e)}")

    def set_web_broadcast_callback(self, callback):
        """Web UI için yayın callback'ini ayarla"""
        self.web_broadcast_callback = callback
        print("🌐 Web arayüzü mesaj dinleme sistemi aktif")