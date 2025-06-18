"""
Web UI Universal - Analytics Dashboard ile geliştirilmiş versiyon
"""
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import json
import time
import asyncio
from datetime import datetime
import threading
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from project_memory import ProjectMemory
from plugin_manager import plugin_manager

class WebUIUniversal:
    """Universal AI Adapter ile uyumlu Web UI"""
    
    def __init__(self, host, port, message_broker, memory_bank, ai_adapter):
        self.app = Flask(__name__, 
                        template_folder='../templates',
                        static_folder='../static')
        self.app.config['SECRET_KEY'] = 'ai-chrome-chat-manager-universal-secret'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Sistem bileşenleri
        self.host = host
        self.port = port
        self.message_broker = message_broker
        self.memory_bank = memory_bank
        self.ai_adapter = ai_adapter
        
        # Müdahale sistemi için durum
        self.active_conversations = {}
        self.intervention_queue = {}
        
        # Proje hafızası
        self.project_memory = ProjectMemory()
        
        # Plugin sistemi
        plugin_manager.load_plugins()
        print(f"🔌 Loaded plugins: {list(plugin_manager.plugins.keys())}")
        
        # Analytics verileri için cache
        self.analytics_cache = {
            'last_update': None,
            'data': None
        }
        
        self.setup_routes()
        self.setup_socketio_events()
        self.setup_message_subscriptions()
    
    def setup_routes(self):
        """Web rotalarını ayarla"""
        
        @self.app.route('/')
        def index():
            return render_template('index_universal.html')
        
        @self.app.route('/api/status')
        def get_status():
            return jsonify({
                'status': 'running',
                'ai_adapter_ready': self.ai_adapter is not None,
                'memory_bank_ready': self.memory_bank is not None,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/analytics')
        def get_analytics():
            """Analytics verilerini döndür"""
            try:
                # Toplam istatistikler
                total_stats = self.ai_adapter.get_total_stats()
                
                # Her adapter için detaylı durum
                adapter_status = self.ai_adapter.get_adapter_status()
                
                # Rol atamaları
                role_assignments = self.ai_adapter.get_role_assignments()
                
                # Başarı oranı hesapla
                total_requests = total_stats['total_requests']
                total_errors = total_stats['total_errors']
                success_rate = ((total_requests - total_errors) / total_requests * 100) if total_requests > 0 else 100
                
                # Response time (şimdilik mock, ileride gerçek veri eklenecek)
                avg_response_time = 1.8
                
                analytics_data = {
                    'summary': {
                        'total_cost': total_stats['total_cost'],
                        'total_requests': total_requests,
                        'success_rate': round(success_rate, 1),
                        'avg_response_time': avg_response_time,
                        'total_tokens': total_stats['total_tokens'],
                        'total_errors': total_errors
                    },
                    'adapters': {},
                    'token_usage': {
                        'total': total_stats['total_tokens'],
                        'input': 0,  # Detaylı token bilgisi için güncelleme gerekecek
                        'output': 0
                    },
                    'timestamp': datetime.now().isoformat()
                }
                
                # Her adapter için detaylı bilgi
                for adapter_id, status in adapter_status.items():
                    if 'error' not in status:
                        # Role assignment bul
                        assigned_role = None
                        for role, aid in role_assignments.items():
                            if aid == adapter_id:
                                assigned_role = role
                                break
                        
                        analytics_data['adapters'][adapter_id] = {
                            'id': adapter_id,
                            'type': status['type'],
                            'model': status['model'],
                            'role': assigned_role,
                            'stats': status['stats'],
                            'is_available': status['rate_limit']['available']
                        }
                        
                        # Token usage güncelle
                        analytics_data['token_usage']['input'] += status['stats'].get('input_tokens', 0)
                        analytics_data['token_usage']['output'] += status['stats'].get('output_tokens', 0)
                
                # Cache güncelle
                self.analytics_cache = {
                    'last_update': time.time(),
                    'data': analytics_data
                }
                
                return jsonify(analytics_data)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/ai/send_message', methods=['POST'])
        def send_ai_message():
            """AI'ya mesaj gönder"""
            data = request.get_json()
            role_id = data.get('role_id', 'project_manager')
            message = data.get('message', '')
            context = data.get('context', '')
            
            if not message:
                return jsonify({'error': 'Mesaj gerekli'}), 400
            
            # Async mesajı background'da çalıştır
            def run_async():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    response = loop.run_until_complete(
                        self.ai_adapter.send_message(role_id, message, context)
                    )
                    
                    if response:
                        # WebSocket üzerinden sonucu gönder
                        self.socketio.emit('ai_response', {
                            'role_id': role_id,
                            'user_message': message,
                            'ai_response': response.content,
                            'model': response.model,
                            'usage': response.usage,
                            'timestamp': datetime.now().isoformat()
                        })
                        
                        # Analytics güncellemesi tetikle
                        self.broadcast_analytics_update()
                        
                except Exception as e:
                    self.socketio.emit('ai_error', {
                        'error': str(e),
                        'role_id': role_id,
                        'timestamp': datetime.now().isoformat()
                    })
            
            thread = threading.Thread(target=run_async)
            thread.daemon = True
            thread.start()
            
            return jsonify({'status': 'processing', 'role_id': role_id})
        
        @self.app.route('/api/ai/conversation', methods=['POST'])
        def start_conversation():
            """İki AI arasında konuşma başlat"""
            data = request.get_json()
            initial_prompt = data.get('prompt', '')
            max_turns = data.get('max_turns', 3)
            
            if not initial_prompt:
                return jsonify({'error': 'İlk prompt gerekli'}), 400
            
            # Konuşmayı background'da başlat
            def run_conversation():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(
                        self._run_ai_conversation(initial_prompt, max_turns)
                    )
                except Exception as e:
                    self.socketio.emit('conversation_error', {
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
            
            conversation_thread = threading.Thread(target=run_conversation)
            conversation_thread.daemon = True
            conversation_thread.start()
            
            return jsonify({
                'status': 'started',
                'prompt': initial_prompt,
                'max_turns': max_turns
            })
        
        @self.app.route('/api/ai/intervention', methods=['POST'])
        def director_intervention():
            """Yönetici müdahalesi gönder"""
            data = request.get_json()
            intervention_message = data.get('message', '').strip()
            session_id = data.get('session_id', 'default')
            
            if not intervention_message:
                return jsonify({'error': 'Müdahale mesajı gerekli'}), 400
            
            # Müdahaleyi sıraya ekle
            if session_id not in self.intervention_queue:
                self.intervention_queue[session_id] = []
            
            intervention_data = {
                'message': intervention_message,
                'timestamp': datetime.now().isoformat(),
                'applied': False
            }
            
            self.intervention_queue[session_id].append(intervention_data)
            
            # WebSocket üzerinden bilgilendirme
            self.socketio.emit('intervention_received', {
                'session_id': session_id,
                'message': intervention_message,
                'timestamp': intervention_data['timestamp']
            })
            
            return jsonify({
                'status': 'received',
                'message': intervention_message,
                'session_id': session_id,
                'queue_position': len(self.intervention_queue[session_id])
            })
        
        # === Memory & Tasks API Endpoints ===
        
        @self.app.route('/api/memory/conversations', methods=['GET'])
        def get_conversation_history():
            """Konuşma geçmişini getir"""
            try:
                limit = request.args.get('limit', 10, type=int)
                conversations = self.project_memory.get_conversation_history(limit)
                return jsonify(conversations)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/memory/conversations/<conversation_id>', methods=['GET'])
        def get_conversation_details(conversation_id):
            """Konuşma detaylarını getir"""
            try:
                conversation = self.project_memory.get_conversation_details(conversation_id)
                if conversation:
                    return jsonify(conversation)
                else:
                    return jsonify({'error': 'Konuşma bulunamadı'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/memory/conversations', methods=['POST'])
        def save_conversation():
            """Konuşmayı kaydet"""
            try:
                data = request.get_json()
                conversation_id = self.project_memory.save_conversation(data)
                return jsonify({'id': conversation_id, 'status': 'saved'})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/memory/tasks', methods=['GET'])
        def get_project_tasks():
            """Proje görevlerini getir"""
            try:
                tasks = self.project_memory.get_active_tasks()
                return jsonify(tasks)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/memory/tasks', methods=['POST'])
        def create_task():
            """Yeni görev oluştur"""
            try:
                data = request.get_json()
                task_id = self.project_memory.create_task_from_message(
                    data.get('message_id', ''),
                    data
                )
                return jsonify({'id': task_id, 'status': 'created'})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/memory/tasks/<task_id>/status', methods=['PATCH'])
        def update_task_status(task_id):
            """Görev durumunu güncelle"""
            try:
                data = request.get_json()
                new_status = data.get('status')
                success = self.project_memory.update_task_status(task_id, new_status)
                if success:
                    return jsonify({'status': 'updated'})
                else:
                    return jsonify({'error': 'Görev bulunamadı'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/memory/search', methods=['GET'])
        def search_conversations():
            """Konuşmalarda arama yap"""
            try:
                query = request.args.get('q', '')
                limit = request.args.get('limit', 5, type=int)
                results = self.project_memory.search_conversations(query, limit)
                return jsonify(results)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def setup_socketio_events(self):
        """SocketIO event'lerini ayarla"""
        
        @self.socketio.on('connect')
        def handle_connect():
            print('🌐 Web client bağlandı')
            emit('status', {'message': 'Universal AI sistem bağlandı'})
            # İlk bağlantıda analytics verilerini gönder
            self.broadcast_analytics_update()
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print('🌐 Web client bağlantısı kesildi')
        
        @self.socketio.on('request_analytics')
        def handle_analytics_request():
            """Analytics verilerini iste"""
            self.broadcast_analytics_update()
    
    def setup_message_subscriptions(self):
        """Message broker aboneliklerini kur"""
        if self.message_broker:
            # AI yanıtlarını dinle
            def on_ai_response(message):
                self.socketio.emit('new_message', message)
                # Analytics güncellemesi tetikle
                self.broadcast_analytics_update()
            
            self.message_broker.subscribe('system_to_webui', on_ai_response)
    
    def broadcast_analytics_update(self):
        """Analytics güncellemelerini broadcast et"""
        try:
            # Yeni analytics verilerini al
            analytics_data = self._get_analytics_data()
            
            # WebSocket üzerinden gönder
            self.socketio.emit('analytics_update', analytics_data)
            
        except Exception as e:
            print(f"Analytics broadcast hatası: {e}")
    
    def _get_analytics_data(self):
        """Analytics verilerini hazırla"""
        # Cache kontrolü (1 saniyeden eski değilse cache'den dön)
        if (self.analytics_cache['last_update'] and 
            time.time() - self.analytics_cache['last_update'] < 1 and
            self.analytics_cache['data']):
            return self.analytics_cache['data']
        
        # Yeni veri çek
        total_stats = self.ai_adapter.get_total_stats()
        adapter_status = self.ai_adapter.get_adapter_status()
        role_assignments = self.ai_adapter.get_role_assignments()
        
        # Başarı oranı
        total_requests = total_stats['total_requests']
        total_errors = total_stats['total_errors']
        success_rate = ((total_requests - total_errors) / total_requests * 100) if total_requests > 0 else 100
        
        analytics_data = {
            'summary': {
                'total_cost': total_stats['total_cost'],
                'total_requests': total_requests,
                'success_rate': round(success_rate, 1),
                'avg_response_time': 1.8,  # Mock veri
                'total_tokens': total_stats['total_tokens'],
                'total_errors': total_errors
            },
            'adapters': {},
            'token_usage': {
                'total': total_stats['total_tokens'],
                'input': 0,
                'output': 0
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Adapter detayları
        for adapter_id, status in adapter_status.items():
            if 'error' not in status:
                assigned_role = None
                for role, aid in role_assignments.items():
                    if aid == adapter_id:
                        assigned_role = role
                        break
                
                analytics_data['adapters'][adapter_id] = {
                    'id': adapter_id,
                    'type': status['type'],
                    'model': status['model'],
                    'role': assigned_role,
                    'stats': status['stats'],
                    'is_available': status['rate_limit']['available']
                }
        
        # Cache güncelle
        self.analytics_cache = {
            'last_update': time.time(),
            'data': analytics_data
        }
        
        return analytics_data
    
    async def _run_ai_conversation(self, initial_prompt: str, max_turns: int):
        """İki AI arasında konuşma köprüsü çalıştır"""
        try:
            current_message = initial_prompt
            session_id = str(int(time.time()))
            
            # Aktif konuşmayı kaydet
            self.active_conversations[session_id] = {
                'status': 'active',
                'current_turn': 0,
                'max_turns': max_turns
            }
            
            self.socketio.emit('conversation_started', {
                'prompt': initial_prompt,
                'max_turns': max_turns,
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            })
            
            for turn in range(max_turns):
                # Müdahale kontrolü
                intervention_context = self._check_interventions(session_id)
                
                # PM'den yanıt al
                self.socketio.emit('conversation_turn', {
                    'turn': turn + 1,
                    'phase': 'pm_thinking',
                    'session_id': session_id,
                    'timestamp': datetime.now().isoformat()
                })
                
                pm_prompt = current_message
                if intervention_context:
                    pm_prompt = f"{current_message}\n\n[YÖNETİCİ MÜDAHALESİ]: {intervention_context}"
                
                pm_response = await self.ai_adapter.send_message(
                    "project_manager", 
                    pm_prompt,
                    f"Konuşma turu: {turn + 1}"
                )
                
                if pm_response:
                    self.socketio.emit('conversation_message', {
                        'speaker': 'project_manager',
                        'speaker_name': '👔 Proje Yöneticisi',
                        'message': pm_response.content,
                        'turn': turn + 1,
                        'model': pm_response.model,
                        'usage': pm_response.usage,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Plugin'ları çalıştır
                    await self._process_plugins(pm_response.content, session_id)
                    
                    # Analytics güncellemesi
                    self.broadcast_analytics_update()
                
                await asyncio.sleep(1)
                
                # LD'den yanıt al
                self.socketio.emit('conversation_turn', {
                    'turn': turn + 1,
                    'phase': 'ld_thinking',
                    'session_id': session_id,
                    'timestamp': datetime.now().isoformat()
                })
                
                ld_prompt = pm_response.content if pm_response else current_message
                if intervention_context:
                    ld_prompt = f"{ld_prompt}\n\n[YÖNETİCİ MÜDAHALESİ]: {intervention_context}"
                
                ld_response = await self.ai_adapter.send_message(
                    "lead_developer",
                    ld_prompt,
                    f"PM'den gelen yanıt - Tur {turn + 1}"
                )
                
                if ld_response:
                    self.socketio.emit('conversation_message', {
                        'speaker': 'lead_developer',
                        'speaker_name': '👨‍💻 Lead Developer',
                        'message': ld_response.content,
                        'turn': turn + 1,
                        'model': ld_response.model,
                        'usage': ld_response.usage,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Plugin'ları çalıştır
                    await self._process_plugins(ld_response.content, session_id)
                    
                    # Analytics güncellemesi
                    self.broadcast_analytics_update()
                
                current_message = ld_response.content if ld_response else pm_response.content
                await asyncio.sleep(2)
            
            # Konuşmayı hafızaya kaydet
            await self._save_conversation_to_memory(session_id, initial_prompt, max_turns)
            
            # Konuşma tamamlandı
            if session_id in self.active_conversations:
                del self.active_conversations[session_id]
            
            self.socketio.emit('conversation_completed', {
                'total_turns': max_turns,
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            # Hata durumunda temizlik
            if session_id in self.active_conversations:
                del self.active_conversations[session_id]
                
            self.socketio.emit('conversation_error', {
                'error': str(e),
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            })
    
    def _check_interventions(self, session_id: str) -> str:
        """Bekleyen müdahaleleri kontrol et ve uygula"""
        if session_id not in self.intervention_queue:
            return ""
        
        interventions = self.intervention_queue[session_id]
        pending_interventions = [i for i in interventions if not i['applied']]
        
        if not pending_interventions:
            return ""
        
        # En son müdahaleyi al ve işaretle
        latest_intervention = pending_interventions[-1]
        latest_intervention['applied'] = True
        
        # WebSocket bildirim gönder
        self.socketio.emit('intervention_applied', {
            'session_id': session_id,
            'message': latest_intervention['message'],
            'affected_ai': 'both',
            'timestamp': datetime.now().isoformat()
        })
        
        return latest_intervention['message']
    
    async def _process_plugins(self, message: str, session_id: str):
        """AI mesajını plugin'lar ile işle"""
        try:
            context = {
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                'source': 'ai_conversation',
                'mcp_tools': {}  # MCP tools can be added here when available
            }
            
            # Plugin'ları çalıştır
            plugin_results = await plugin_manager.process_message(message, context)
            
            # Her plugin sonucu için WebSocket mesajı gönder
            for result in plugin_results:
                if result and result.get('type') in ['web_search_result', 'document_analysis_result', 'demo_plugin_result']:
                    self.socketio.emit('plugin_result', {
                        'plugin_name': result.get('plugin_name', 'Unknown Plugin'),
                        'role': result.get('role', '🔌 Plugin'),
                        'content': result.get('content', 'No content'),
                        'type': result.get('type', 'plugin_result'),
                        'session_id': session_id,
                        'timestamp': datetime.now().isoformat(),
                        'metadata': result.get('metadata', {})
                    })
                    
                    print(f"🔌 Plugin {result.get('plugin_name')} executed for session {session_id}")
                
                elif result and result.get('type') == 'plugin_error':
                    self.socketio.emit('plugin_error', {
                        'plugin_name': result.get('plugin_name', 'Unknown Plugin'),
                        'error': result.get('error', 'Unknown error'),
                        'session_id': session_id,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    print(f"⚠️ Plugin {result.get('plugin_name')} error: {result.get('error')}")
            
        except Exception as e:
            print(f"🚨 Plugin processing error: {e}")
            self.socketio.emit('plugin_error', {
                'error': str(e),
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            })
    
    async def _save_conversation_to_memory(self, session_id: str, initial_prompt: str, max_turns: int):
        """Konuşmayı proje hafızasına kaydet"""
        try:
            # Session mesajlarını topla (gerçek implementasyonda bu veriler session'dan gelecek)
            # Şimdilik bu fonksiyon temel yapıyı kuruyor
            
            conversation_data = {
                'title': f"AI Konuşması - {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                'initial_prompt': initial_prompt,
                'status': 'completed',
                'total_turns': max_turns,
                'total_interventions': len(self.intervention_queue.get(session_id, [])),
                'messages': [],  # Gerçek implementasyonda session'dan toplanacak
                'metadata': {
                    'session_id': session_id,
                    'created_via': 'web_interface'
                }
            }
            
            # Konuşmayı kaydet
            saved_id = self.project_memory.save_conversation(conversation_data)
            
            # WebSocket bildirimi
            self.socketio.emit('conversation_saved', {
                'conversation_id': saved_id,
                'session_id': session_id,
                'title': conversation_data['title'],
                'timestamp': datetime.now().isoformat()
            })
            
            print(f"💾 Konuşma hafızaya kaydedildi: {saved_id}")
            
        except Exception as e:
            print(f"⚠️ Konuşma kayıt hatası: {e}")
    
    def start_background(self):
        """Web arayüzünü arka planda başlat"""
        def run_server():
            self.socketio.run(self.app, host=self.host, port=self.port, debug=False)
        
        self.server_thread = threading.Thread(target=run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        print(f"🌐 Universal Web arayüzü başlatıldı: http://{self.host}:{self.port}") 