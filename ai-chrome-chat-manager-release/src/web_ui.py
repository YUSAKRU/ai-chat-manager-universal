from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import json
import time
from datetime import datetime
import threading
import os
import re
from werkzeug.utils import secure_filename
import difflib

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

        # -----------------------------------------------
        # 🌐 Chrome Profil Seçimi (WEB UI)
        # -----------------------------------------------
        @self.app.route('/api/chrome_profiles/select', methods=['POST'])
        def select_chrome_profiles():
            """Web UI'dan gelen profil seçimlerini kaydet"""
            try:
                data = request.get_json()
                pm_profile = data.get('project_manager')
                ld_profile = data.get('lead_developer')

                mapping = {
                    'project_manager': pm_profile,
                    'lead_developer': ld_profile
                }

                # Profil isimleri boş mu?
                if not pm_profile or not ld_profile:
                    return jsonify({'error': 'Her iki rol için de profil seçilmelidir.'}), 400

                # BrowserHandler üzerinden doğrula & ata
                success = self.chat_manager.browser_handler.setup_profiles_web(mapping)

                if not success:
                    return jsonify({'error': 'Profil doğrulaması başarısız oldu.'}), 400

                return jsonify({'status': 'ok', 'selected_profiles': mapping})
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        # -------------------------------------------------
        # 🌐 Tarayıcıları Web UI üzerinden başlat
        # -------------------------------------------------
        @self.app.route('/api/browsers/start', methods=['POST'])
        def start_browsers():
            """Seçili profillerle Chrome pencerelerini arka planda başlat"""
            try:
                # Arka planda browser başlatma, UI'ı bloklamasın
                self.socketio.start_background_task(self._launch_browser_windows)
                return jsonify({'status': 'ok', 'message': 'Tarayıcı başlatma işlemi tetiklendi.'})
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        # Tarayıcıları durdur
        @self.app.route('/api/browsers/stop', methods=['POST'])
        def stop_browsers():
            """Açık pencereleri kapatmak için arka plan görevi"""
            try:
                self.socketio.start_background_task(self._shutdown_browser_windows)
                return jsonify({'status': 'ok', 'message': 'Tarayıcı durdurma işlemi tetiklendi.'})
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        # -------------------------------------------------
        # 📋 Görev Panosu - activeContext.md
        # -------------------------------------------------
        @self.app.route('/api/tasks', methods=['GET'])
        def get_tasks():
            """activeContext.md'den görev listesini JSON döndür"""
            return jsonify(self._get_tasks_from_markdown())

        # -------------------------------------------------
        # ✅ Görev durumunu güncelle
        # -------------------------------------------------
        @self.app.route('/api/tasks/update', methods=['POST'])
        def update_task():
            data = request.get_json()
            task_text = data.get('text')
            task_status = data.get('status')

            if not task_text or task_status not in ['completed', 'pending']:
                return jsonify({'error': 'Geçersiz istek verisi'}), 400

            success = self._update_task_in_markdown(task_text, task_status)
            if success:
                return jsonify({'status': 'ok'})
            return jsonify({'error': 'Görev bulunamadı'}), 404

        # -------------------------------------------------
        # 🧠 Memory Bank dosya yönetimi
        # -------------------------------------------------
        @self.app.route('/api/memory/list', methods=['GET'])
        def list_memory_files():
            memory_path = os.path.join(os.getcwd(), 'memory-bank')
            try:
                files = sorted([f for f in os.listdir(memory_path) if f.endswith('.md')])
                return jsonify(files)
            except FileNotFoundError:
                return jsonify({'error': f"'{memory_path}' klasörü bulunamadı."}), 404

        @self.app.route('/api/memory/view/<filename>', methods=['GET'])
        def view_memory_file(filename):
            memory_path = os.path.join(os.getcwd(), 'memory-bank')
            secure_name = secure_filename(filename)
            file_path = os.path.join(memory_path, secure_name)
            if not os.path.exists(file_path):
                return jsonify({'error': 'Dosya bulunamadı.'}), 404
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return jsonify({'filename': secure_name, 'content': content})
            except Exception as e:
                return jsonify({'error': f'Dosya okunurken hata: {str(e)}'}), 500

        # -----------------------------------------------
        # 📝 Memory Bank Diff & Update
        # -----------------------------------------------
        @self.app.route('/api/memory/diff', methods=['POST'])
        def memory_file_diff():
            """Yeni içerikle unified diff üret"""
            try:
                data = request.get_json()
                filename = data.get('filename')
                new_content = data.get('content', '')
                memory_path = os.path.join(os.getcwd(), 'memory-bank')
                secure_name = secure_filename(filename)
                file_path = os.path.join(memory_path, secure_name)

                if not os.path.exists(file_path):
                    return jsonify({'error': 'Orijinal dosya bulunamadı'}), 404

                with open(file_path, 'r', encoding='utf-8') as f:
                    orig_content = f.read()

                diff_lines = difflib.unified_diff(
                    orig_content.splitlines(keepends=True),
                    new_content.splitlines(keepends=True),
                    fromfile=f"a/{secure_name}", tofile=f"b/{secure_name}"
                )
                diff_text = ''.join(diff_lines)
                return jsonify({'diff': diff_text})
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/memory/update', methods=['POST'])
        def memory_file_update():
            """Dosyayı yeni içerikle güncelle"""
            try:
                data = request.get_json()
                filename = data.get('filename')
                new_content = data.get('content', '')
                if filename is None:
                    return jsonify({'error': 'filename gerekli'}), 400
                memory_path = os.path.join(os.getcwd(), 'memory-bank')
                secure_name = secure_filename(filename)
                file_path = os.path.join(memory_path, secure_name)

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return jsonify({'status': 'ok', 'message': f"{secure_name} güncellendi"})
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

    # -------------------------------------------------
    # 🚀 Tarayıcı Başlatma İş Akışı (arka plan task)
    # -------------------------------------------------
    def _launch_browser_windows(self):
        """Selected profillerle browser oturumlarını aç ve durum emit et"""
        try:
            handler = self.chat_manager.browser_handler

            # Profil doğrulaması
            pm_profile = handler.selected_profiles.get('project_manager')
            ld_profile = handler.selected_profiles.get('lead_developer')

            if not pm_profile or not ld_profile:
                self.socketio.emit('status_update', {
                    'message': '❌ Hata: Lütfen önce her iki rol için de profil seçin!',
                    'level': 'error'
                })
                return

            # Başlatma süreci
            self.socketio.emit('status_update', {'message': '▶️ Tarayıcılar başlatılıyor...', 'level': 'info'})

            # PM
            self.socketio.emit('status_update', {'message': f'🌀 AI-1 (Proje Yöneticisi) penceresi açılıyor... (Profil: {pm_profile})', 'level': 'info'})
            pm_driver = handler.open_window('project_manager')
            if pm_driver:
                self.socketio.emit('status_update', {'message': '✅ AI-1 penceresi hazır.', 'level': 'success'})
            else:
                self.socketio.emit('status_update', {'message': '❌ AI-1 penceresi açılamadı!', 'level': 'error'})
                return

            # LD
            self.socketio.emit('status_update', {'message': f'🌀 AI-2 (Lead Developer) penceresi açılıyor... (Profil: {ld_profile})', 'level': 'info'})
            ld_driver = handler.open_window('lead_developer')
            if ld_driver:
                self.socketio.emit('status_update', {'message': '✅ AI-2 penceresi hazır.', 'level': 'success'})
            else:
                self.socketio.emit('status_update', {'message': '❌ AI-2 penceresi açılamadı!', 'level': 'error'})
                return

            self.socketio.emit('status_update', {'message': '🚀 Tüm sistemler hazır! Sohbet başlayabilir.', 'level': 'final'})

        except Exception as e:
            self.socketio.emit('status_update', {
                'message': f'❌ Tarayıcı başlatılırken hata: {str(e)}',
                'level': 'error'
            })

    # -------------------------------------------------
    # 🛑 Tarayıcıları kapatma iş akışı
    # -------------------------------------------------
    def _shutdown_browser_windows(self):
        try:
            self.socketio.emit('status_update', {'message': '⏹️ Tarayıcı kapatma komutu alındı. Pencereler kapatılıyor...', 'level': 'info'})

            self.chat_manager.browser_handler.close_all_windows()

            self.socketio.emit('status_update', {'message': '🚪 Tüm tarayıcılar kapatıldı.', 'level': 'success'})

            # Sistemi resetle
            self.socketio.emit('system_reset', {'message': 'Sistem başlangıç durumuna döndü. Yeni bir oturum başlatabilirsiniz.'})

        except Exception as e:
            self.socketio.emit('status_update', {'message': f'❌ Tarayıcılar kapatılırken hata: {str(e)}', 'level': 'error'})

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

    # -------------------------------------------------
    # 📋 Markdown görev ayrıştırıcı
    # -------------------------------------------------
    def _get_tasks_from_markdown(self):
        tasks = []
        context_file = os.path.join(os.getcwd(), 'memory-bank', 'activeContext.md')
        try:
            with open(context_file, 'r', encoding='utf-8') as f:
                for line in f:
                    m = re.match(r'-\s*\[( |x)\]\s*(.*)', line)
                    if m:
                        status = 'completed' if m.group(1) == 'x' else 'pending'
                        tasks.append({'text': m.group(2).strip(), 'status': status})
        except FileNotFoundError:
            tasks.append({'text': 'activeContext.md bulunamadı', 'status': 'error'})
        except Exception as e:
            tasks.append({'text': f'Hata: {str(e)}', 'status': 'error'})
        return tasks

    def _update_task_in_markdown(self, task_text: str, new_status: str) -> bool:
        """activeContext.md içinde eşleşen görev satırını günceller"""
        context_file = os.path.join(os.getcwd(), 'memory-bank', 'activeContext.md')
        if not os.path.exists(context_file):
            return False
        try:
            with open(context_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            updated = False
            for idx, line in enumerate(lines):
                m = re.match(r'-\s*\[( |x)\]\s*(.*)', line)
                if m and m.group(2).strip() == task_text.strip():
                    char = 'x' if new_status == 'completed' else ' '
                    lines[idx] = f"- [{char}] {task_text}\n"
                    updated = True
                    break

            if updated:
                with open(context_file, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                return True
            return False
        except Exception as e:
            print(f'Görev güncelleme hatası: {str(e)}')
            return False
