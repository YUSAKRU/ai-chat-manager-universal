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
        # Message broker'a web broadcast callback'ini ekle
        self.chat_manager.message_broker.set_web_broadcast_callback(self.broadcast_message)
        
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
        
        # Memory Bank API Endpoints
        @self.app.route('/api/memory_bank/query', methods=['POST'])
        def memory_bank_query():
            """Memory Bank'tan sorgu yap"""
            try:
                data = request.get_json()
                query = data.get('query', '')
                
                if not query:
                    return jsonify({'error': 'Query gerekli'}), 400
                
                result = self.chat_manager.memory_bank.query_memory_bank(query)
                return jsonify({'result': result, 'query': query})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/memory_bank/update', methods=['POST'])
        def memory_bank_update():
            """Memory Bank dokümantasyonunu güncelle"""
            try:
                data = request.get_json()
                doc_type = data.get('documentType', '')
                content = data.get('content', '')
                
                if not doc_type:
                    return jsonify({'error': 'Document type gerekli'}), 400
                
                result = self.chat_manager.memory_bank.update_document(doc_type, content)
                return jsonify({'result': result, 'documentType': doc_type})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/memory_bank/export', methods=['GET'])
        def memory_bank_export():
            """Memory Bank'ı export et"""
            try:
                export_format = request.args.get('format', 'json')
                result = self.chat_manager.memory_bank.export_memory_bank(export_format)
                return jsonify({'result': result, 'format': export_format})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/memory_bank/status')
        def memory_bank_status():
            """Memory Bank durumunu kontrol et"""
            try:
                # Memory Bank klasörünün var olup olmadığını kontrol et
                import os
                memory_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'memory-bank')
                status = {
                    'initialized': os.path.exists(memory_path),
                    'documents_count': len([f for f in os.listdir(memory_path) if f.endswith('.md')]) if os.path.exists(memory_path) else 0,
                    'path': memory_path
                }
                return jsonify(status)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # Chrome Profil Yönetimi Endpoints
        @self.app.route('/api/chrome_profiles/list')
        def list_chrome_profiles():
            """Mevcut Chrome profillerini listele"""
            try:
                profiles = self.chat_manager.browser_handler.profile_manager.list_profiles()
                return jsonify({
                    'profiles': profiles,
                    'count': len(profiles),
                    'user_data_path': self.chat_manager.browser_handler.profile_manager.chrome_user_data_path
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/chrome_profiles/selected')
        def get_selected_profiles():
            """Seçilen profilleri göster"""
            try:
                selected = self.chat_manager.browser_handler.selected_profiles
                return jsonify({
                    'selected_profiles': selected,
                    'pm_profile': selected.get('project_manager', 'Seçilmemiş'),
                    'ld_profile': selected.get('lead_developer', 'Seçilmemiş')
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/chrome_profiles/summary')
        def chrome_profiles_summary():
            """Chrome profil özetini döndür"""
            try:
                summary = self.chat_manager.browser_handler.profile_manager.get_profile_summary()
                return jsonify({'summary': summary})
            except Exception as e:
                return jsonify({'error': str(e)}), 500

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
