from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import json
import time
from datetime import datetime
import threading

class WebUI:
    def __init__(self, chat_manager):
        self.app = Flask(__name__, 
                        template_folder='../templates',
                        static_folder='../static')
        self.app.config['SECRET_KEY'] = 'ai-chrome-chat-manager-secret'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.chat_manager = chat_manager
        
        # Web UI için broadcast aboneliği (main.py içinde yapıldı)
        # Mesaj broker'dan gelen tüm kanallar için yayın callback'i main.py'de abone edildi
        
        self.setup_routes()
        self.setup_socketio_events()

    def setup_routes(self):
        """Web route'larını ayarla"""
        
        @self.app.route('/')
        def index():
            return render_template('index.html')
        
        @self.app.route('/api/status')
        def get_status():
            return jsonify({
                'status': 'running',
                'active_channels': self.chat_manager.message_broker.get_active_channels(),
                'message_count': len(self.chat_manager.message_broker.message_history),
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/messages')
        def get_messages():
            limit = request.args.get('limit', 50, type=int)
            channel = request.args.get('channel', None)
            messages = self.chat_manager.message_broker.get_message_history(channel, limit)
            return jsonify(messages)
        
        @self.app.route('/api/send_message', methods=['POST'])
        def send_message():
            data = request.get_json()
            sender = data.get('sender', 'Web User')
            channel = data.get('channel', 'boss_to_pm')
            message = data.get('message', '')
            
            # Boss üzerinden mesaj gönder
            if channel == 'boss_to_pm':
                self.chat_manager.boss.send_directive(message, target='pm')
            elif channel == 'boss_to_ld':
                self.chat_manager.boss.send_directive(message, target='ld')
            elif channel == 'boss_to_both':
                self.chat_manager.boss.send_directive(message, target='both')
            
            return jsonify({'status': 'sent', 'message': message})
        
        @self.app.route('/api/assign_task', methods=['POST'])
        def assign_task():
            data = request.get_json()
            task = data.get('task', '')
            
            self.chat_manager.project_manager.assign_task(task)
            return jsonify({'status': 'assigned', 'task': task})
        
        @self.app.route('/api/request_status', methods=['POST'])
        def request_status():
            self.chat_manager.boss.request_status_report()
            return jsonify({'status': 'requested'})

    def setup_socketio_events(self):
        """SocketIO event'lerini ayarla"""
        
        @self.socketio.on('connect')
        def handle_connect():
            print('🌐 Web client bağlandı')
            emit('status', {'message': 'Bağlantı başarılı'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print('🌐 Web client bağlantısı kesildi')
        
        @self.socketio.on('send_message')
        def handle_message(data):
            channel = data.get('channel', 'boss_to_both')
            message = data.get('message', '')
            sender = data.get('sender', 'Web User')
            
            # Boss üzerinden mesaj gönder
            if channel == 'boss_to_pm':
                self.chat_manager.boss.send_directive(message, target='pm')
            elif channel == 'boss_to_ld':
                self.chat_manager.boss.send_directive(message, target='ld')
            else:
                self.chat_manager.boss.send_directive(message, target='both')
        
        @self.socketio.on('assign_task')
        def handle_task_assignment(data):
            task = data.get('task', '')
            self.chat_manager.project_manager.assign_task(task)
        
        @self.socketio.on('request_status')
        def handle_status_request():
            self.chat_manager.boss.request_status_report()

    def broadcast_message(self, message_obj):
        """Mesajı web client'lara yayınla"""
        self.socketio.emit('new_message', message_obj)

    def run(self, host='localhost', port=5000, debug=False):
        """Web sunucusunu başlat"""
        print(f"🌐 Web arayüzü başlatılıyor: http://{host}:{port}")
        self.socketio.run(self.app, host=host, port=port, debug=debug)

    def run_in_background(self, host='localhost', port=5000):
        """Web sunucusunu arka planda çalıştır"""
        def run_server():
            self.socketio.run(self.app, host=host, port=port, debug=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        print(f"🌐 Web arayüzü arka planda başlatıldı: http://{host}:{port}")
        return server_thread
