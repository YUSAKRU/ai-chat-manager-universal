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
# TODO: Implement these modules in future versions
# from project_memory import ProjectMemory
# from plugin_manager import plugin_manager

class WebUIUniversal:
    """Universal AI Adapter ile uyumlu Web UI"""
    
    def __init__(self, host, port, message_broker, memory_bank, ai_adapter):
        self.app = Flask(__name__, 
                        template_folder='../templates',
                        static_folder='../static')
        self.app.config['SECRET_KEY'] = 'ai-chrome-chat-manager-universal-secret'
        # Python 3.13 uyumluluğu için threading mode kullan
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='threading')
        
        # Sistem bileşenleri
        self.host = host
        self.port = port
        self.message_broker = message_broker
        self.memory_bank = memory_bank
        self.ai_adapter = ai_adapter
        
        # Müdahale sistemi için durum
        self.active_conversations = {}
        self.intervention_queue = {}
        
        # Proje hafızası (TODO: Implement ProjectMemory)
        # self.project_memory = ProjectMemory()
        self.project_memory = None
        
        # Plugin sistemi (TODO: Implement plugin_manager)
        # plugin_manager.load_plugins()
        # print(f"🔌 Loaded plugins: {list(plugin_manager.plugins.keys())}")
        print("🔌 Plugin system disabled for this version")
        
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
        
        @self.app.route('/api-management')
        def api_management():
            return render_template('api_management.html')
        
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
                # TODO: Implement ProjectMemory
                return jsonify({'error': 'Project memory not implemented yet'}), 501
                # limit = request.args.get('limit', 10, type=int)
                # conversations = self.project_memory.get_conversation_history(limit)
                # return jsonify(conversations)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/memory/conversations/<conversation_id>', methods=['GET'])
        def get_conversation_details(conversation_id):
            """Konuşma detaylarını getir"""
            return jsonify({'error': 'Project memory not implemented yet'}), 501
        
        @self.app.route('/api/memory/conversations', methods=['POST'])
        def save_conversation():
            """Konuşmayı kaydet"""
            return jsonify({'error': 'Project memory not implemented yet'}), 501
        
        @self.app.route('/api/memory/tasks', methods=['GET'])
        def get_project_tasks():
            """Proje görevlerini getir"""
            try:
                # Mock task data for now - TODO: implement real task management
                mock_tasks = [
                    {
                        'id': 'task-1',
                        'title': 'Proje Gereksinimlerini Belirle',
                        'status': 'in_progress',
                        'priority': 'high',
                        'assignee': 'project_manager',
                        'created_at': '2025-06-19T12:00:00'
                    },
                    {
                        'id': 'task-2', 
                        'title': 'Teknik Mimari Tasarımı',
                        'status': 'pending',
                        'priority': 'medium',
                        'assignee': 'lead_developer',
                        'created_at': '2025-06-19T12:30:00'
                    }
                ]
                
                return jsonify({
                    'success': True,
                    'tasks': mock_tasks,
                    'total': len(mock_tasks)
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/memory/tasks', methods=['POST'])
        def create_task():
            """Yeni görev oluştur"""
            return jsonify({'error': 'Project memory not implemented yet'}), 501
        
        @self.app.route('/api/memory/tasks/<task_id>/status', methods=['PATCH'])
        def update_task_status(task_id):
            """Görev durumunu güncelle"""
            return jsonify({'error': 'Project memory not implemented yet'}), 501
        
        @self.app.route('/api/memory/search', methods=['GET'])
        def search_conversations():
            """Konuşmalarda arama yap"""
            return jsonify({'error': 'Project memory not implemented yet'}), 501
        
        # === API Key Management Routes ===
        
        @self.app.route('/api/keys', methods=['GET'])
        def get_api_keys():
            """Kayıtlı API anahtarlarını listele (güvenli format)"""
            try:
                config_data = self.ai_adapter.config_manager.get_config()
                safe_keys = {}
                
                for provider, keys in config_data.items():
                    if isinstance(keys, dict):
                        safe_keys[provider] = {}
                        for key_name, key_value in keys.items():
                            # API anahtarını maskele
                            if key_value and len(key_value) > 8:
                                masked = key_value[:4] + "*" * (len(key_value) - 8) + key_value[-4:]
                            else:
                                masked = "****"
                            safe_keys[provider][key_name] = {
                                'masked_key': masked,
                                'has_key': bool(key_value),
                                'key_length': len(key_value) if key_value else 0
                            }
                
                return jsonify({
                    'success': True,
                    'keys': safe_keys,
                    'adapters': self.ai_adapter.get_adapter_status(),
                    'roles': self.ai_adapter.get_role_assignments()
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/keys/<provider>', methods=['POST'])
        def add_api_key(provider):
            """Yeni API anahtarı ekle"""
            try:
                data = request.get_json()
                api_key = data.get('api_key', '').strip()
                key_name = data.get('key_name', 'primary').strip()
                model = data.get('model', '')
                
                if not api_key:
                    return jsonify({'error': 'API anahtarı gerekli'}), 400
                
                if not model:
                    # Varsayılan modeller
                    if provider == 'gemini':
                        model = 'gemini-2.5-flash'
                    elif provider == 'openai':
                        model = 'gpt-3.5-turbo'
                    else:
                        return jsonify({'error': 'Model belirtilmeli'}), 400
                
                # API anahtarını test et
                test_result = self._test_api_key(provider, api_key, model)
                if not test_result['success']:
                    return jsonify({
                        'error': f'API anahtarı test edilemedi: {test_result["error"]}',
                        'test_result': test_result
                    }), 400
                
                # Konfigürasyona kaydet
                success = self.ai_adapter.config_manager.set_key(provider, key_name, api_key)
                if not success:
                    return jsonify({'error': 'API anahtarı kaydedilemedi'}), 500
                
                # Yeni adapter oluştur
                adapter_id = f"{provider}-{key_name}"
                try:
                    created_adapter_id = self.ai_adapter.add_adapter(
                        provider, 
                        adapter_id,
                        api_key=api_key,
                        model=model
                    )
                    
                    return jsonify({
                        'success': True,
                        'adapter_id': created_adapter_id,
                        'provider': provider,
                        'model': model,
                        'test_result': test_result,
                        'message': f'{provider.title()} API anahtarı başarıyla eklendi'
                    })
                    
                except Exception as adapter_error:
                    return jsonify({
                        'error': f'Adapter oluşturulamadı: {str(adapter_error)}',
                        'api_key_saved': True
                    }), 500
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/keys/<provider>/<key_name>', methods=['PUT'])
        def update_api_key(provider, key_name):
            """API anahtarını güncelle"""
            try:
                data = request.get_json()
                api_key = data.get('api_key', '').strip()
                model = data.get('model', '')
                
                if not api_key:
                    return jsonify({'error': 'API anahtarı gerekli'}), 400
                
                # API anahtarını test et
                test_result = self._test_api_key(provider, api_key, model)
                if not test_result['success']:
                    return jsonify({
                        'error': f'API anahtarı test edilemedi: {test_result["error"]}',
                        'test_result': test_result
                    }), 400
                
                # Konfigürasyonu güncelle
                success = self.ai_adapter.config_manager.set_key(provider, key_name, api_key)
                if not success:
                    return jsonify({'error': 'API anahtarı güncellenemedi'}), 500
                
                # İlgili adapter'ı güncelle
                adapter_id = f"{provider}-{key_name}"
                if adapter_id in self.ai_adapter.adapters:
                    # Eski adapter'ı kaldır
                    self.ai_adapter.remove_adapter(adapter_id)
                
                # Yeni adapter oluştur
                created_adapter_id = self.ai_adapter.add_adapter(
                    provider,
                    adapter_id,
                    api_key=api_key,
                    model=model
                )
                
                return jsonify({
                    'success': True,
                    'adapter_id': created_adapter_id,
                    'provider': provider,
                    'model': model,
                    'test_result': test_result,
                    'message': f'{provider.title()} API anahtarı başarıyla güncellendi'
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/keys/<provider>/<key_name>', methods=['DELETE'])
        def delete_api_key(provider, key_name):
            """API anahtarını sil"""
            try:
                # Konfigürasyondan sil
                success = self.ai_adapter.config_manager.remove_key(provider, key_name)
                if not success:
                    return jsonify({'error': 'API anahtarı silinemedi'}), 500
                
                # İlgili adapter'ı kaldır
                adapter_id = f"{provider}-{key_name}"
                if adapter_id in self.ai_adapter.adapters:
                    self.ai_adapter.remove_adapter(adapter_id)
                
                return jsonify({
                    'success': True,
                    'message': f'{provider.title()} API anahtarı başarıyla silindi'
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/keys/test', methods=['POST'])
        def test_api_key():
            """API anahtarını test et"""
            try:
                data = request.get_json()
                provider = data.get('provider')
                api_key = data.get('api_key', '').strip()
                model = data.get('model', '')
                
                if not all([provider, api_key]):
                    return jsonify({'error': 'Provider ve API anahtarı gerekli'}), 400
                
                test_result = self._test_api_key(provider, api_key, model)
                return jsonify(test_result)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/roles/<role_id>/adapter', methods=['POST'])
        def assign_adapter_to_role(role_id):
            """Bir role adapter ata"""
            try:
                print(f"🎯 Rol atama isteği: {role_id}")
                data = request.get_json()
                print(f"📤 Request data: {data}")
                
                adapter_id = data.get('adapter_id')
                print(f"🔍 Adapter ID: {adapter_id}")
                
                if not adapter_id:
                    print("❌ Adapter ID eksik")
                    return jsonify({'error': 'Adapter ID gerekli'}), 400
                
                print(f"📊 Mevcut adapter'lar: {list(self.ai_adapter.adapters.keys())}")
                if adapter_id not in self.ai_adapter.adapters:
                    print(f"❌ Adapter bulunamadı: {adapter_id}")
                    return jsonify({'error': 'Adapter bulunamadı'}), 404
                
                # Role ata
                print(f"✅ {role_id} rolüne {adapter_id} atanıyor...")
                self.ai_adapter.assign_role(role_id, adapter_id)
                print(f"📋 Mevcut rol atamaları: {self.ai_adapter.get_role_assignments()}")
                
                return jsonify({
                    'success': True,
                    'role_id': role_id,
                    'adapter_id': adapter_id,
                    'message': f'{role_id} rolüne {adapter_id} adapter\'ı atandı'
                })
                
            except Exception as e:
                print(f"❌ Rol atama hatası: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/roles/<role_id>/adapter', methods=['DELETE'])
        def remove_role_assignment(role_id):
            """Rol atamasını kaldır"""
            try:
                print(f"🗑️ Rol kaldırma isteği: {role_id}")
                print(f"📋 Mevcut rol atamaları: {self.ai_adapter.get_role_assignments()}")
                
                # Rol atamasını kaldır
                if role_id in self.ai_adapter.role_assignments:
                    removed_adapter = self.ai_adapter.role_assignments[role_id]
                    del self.ai_adapter.role_assignments[role_id]
                    print(f"✅ {role_id} rol ataması kaldırıldı: {removed_adapter}")
                    print(f"📋 Güncel rol atamaları: {self.ai_adapter.get_role_assignments()}")
                    
                    return jsonify({
                        'success': True,
                        'role_id': role_id,
                        'removed_adapter': removed_adapter,
                        'message': f'{role_id} rol ataması kaldırıldı'
                    })
                else:
                    print(f"⚠️ {role_id} zaten atanmamış")
                    return jsonify({
                        'success': True,
                        'role_id': role_id,
                        'message': f'{role_id} zaten atanmamış'
                    })
                
            except Exception as e:
                print(f"❌ Rol kaldırma hatası: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/models/<provider>')
        def get_available_models(provider):
            """Provider için mevcut modelleri listele"""
            models = {
                'gemini': [
                    {'id': 'gemini-2.5-flash', 'name': 'Gemini 2.5 Flash', 'recommended': True},
                    {'id': 'gemini-1.5-flash', 'name': 'Gemini 1.5 Flash', 'recommended': False},
                    {'id': 'gemini-1.5-pro', 'name': 'Gemini 1.5 Pro', 'recommended': False},
                    {'id': 'gemini-2.5-pro', 'name': 'Gemini 2.5 Pro', 'recommended': False}
                ],
                'openai': [
                    {'id': 'gpt-4o-mini', 'name': 'GPT-4o Mini', 'recommended': True},
                    {'id': 'gpt-3.5-turbo', 'name': 'GPT-3.5 Turbo', 'recommended': False},
                    {'id': 'gpt-4o', 'name': 'GPT-4o', 'recommended': False},
                    {'id': 'gpt-4-turbo', 'name': 'GPT-4 Turbo', 'recommended': False}
                ]
            }
            
            return jsonify({
                'provider': provider,
                'models': models.get(provider, [])
            })
        
        @self.app.route('/api/setup')
        def get_setup_status():
            """Kurulum durumunu kontrol et"""
            try:
                adapters = self.ai_adapter.get_adapter_status()
                roles = self.ai_adapter.get_role_assignments()
                
                # Temel roller tanımlı mı?
                required_roles = ['project_manager', 'lead_developer', 'boss']
                setup_complete = all(role in roles for role in required_roles)
                
                has_api_keys = len(adapters) > 0
                
                return jsonify({
                    'setup_complete': setup_complete,
                    'has_api_keys': has_api_keys,
                    'adapters_count': len(adapters),
                    'roles_assigned': len(roles),
                    'required_roles': required_roles,
                    'missing_roles': [role for role in required_roles if role not in roles]
                })
                
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
            # Conversation context - daha zengin başlangıç
            conversation_context = {
                'project_goal': initial_prompt,
                'conversation_history': [],
                'decisions_made': [],
                'next_actions': []
            }
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
                
                # Zengin PM prompt'u hazırla
                if turn == 0:
                    pm_prompt = f"""Sen deneyimli bir proje yöneticisisin. Aşağıdaki proje hakkında analiz yap:

🎯 PROJE: {conversation_context['project_goal']}

Tur {turn + 1}'de şunları yap:
• Proje hedeflerini netleştir
• Ana gereksinimleri belirle  
• İlk adımları öneri
• Lead Developer'a hangi sorular sorulmalı?

Kısa ve odaklı bir analiz sun."""
                else:
                    recent_history = ' -> '.join(conversation_context['conversation_history'][-3:])
                    pm_prompt = f"""Proje Yöneticisi Perspektifi - Tur {turn + 1}:

🎯 PROJE: {conversation_context['project_goal'][:200]}...
📋 SON GELİŞMELER: {recent_history}

Lead Developer'ın son yorumuna dayanarak:
• Teknik yaklaşımı değerlendir
• Proje planı açısından feedback ver
• Sonraki adımları belirle
• Karar alınması gereken konuları öne çıkar

Yapıcı ve yönlendirici bir yanıt ver."""
                
                if intervention_context:
                    pm_prompt += f"\n\n🔔 YÖNETİCİ NOTU: {intervention_context}"
                
                pm_response = await self.ai_adapter.send_message(
                    "project_manager", 
                    pm_prompt,
                    f"Proje Değerlendirmesi - Tur {turn + 1}"
                )
                
                if pm_response:
                    # Context'e ekle
                    conversation_context['conversation_history'].append(f"PM: {pm_response.content[:100]}...")
                    
                    self.socketio.emit('conversation_message', {
                        'speaker': 'project_manager',
                        'speaker_name': '👔 Proje Yöneticisi',
                        'message': pm_response.content,
                        'turn': turn + 1,
                        'model': pm_response.model,
                        'usage': pm_response.usage,
                        'timestamp': datetime.now().isoformat()
                    })
                    
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
                
                # Zengin LD prompt'u hazırla
                if turn == 0:
                    ld_prompt = f"""Sen deneyimli bir Lead Developer'sın. Proje Yöneticisi'nin analizini değerlendir:

🎯 PROJE: {conversation_context['project_goal']}

👔 PROJE YÖNETİCİSİ DİYOR: {pm_response.content[:400] if pm_response else "Henüz yanıt yok"}

Teknik perspektiften:
• Hangi teknolojiler uygun olur?
• Mimari nasıl olmalı?
• Gelişirme sürecindeki zorluklar neler?
• PM'e hangi teknik sorular sormalı?

Teknik ve uygulanabilir öneriler sun."""
                else:
                    ld_prompt = f"""Lead Developer Perspektifi - Tur {turn + 1}:

🎯 PROJE: {conversation_context['project_goal'][:200]}...
📋 GÖRÜŞMELER: {' -> '.join(conversation_context['conversation_history'][-4:])}

👔 PM'İN SON YORUMU: {pm_response.content[:400] if pm_response else "Yanıt yok"}

Teknik açıdan:
• PM'in önerilerine teknik feedback ver
• Implementation zorlukları belirt
• Alternatif çözümler öner
• Bir sonraki teknik adımları tanımla

Gerçekçi ve detaylı bir teknik analiz yap."""
                
                if intervention_context:
                    ld_prompt += f"\n\n🔔 YÖNETİCİ NOTU: {intervention_context}"
                
                ld_response = await self.ai_adapter.send_message(
                    "lead_developer",
                    ld_prompt,
                    f"Teknik Analiz - Tur {turn + 1}"
                )
                
                if ld_response:
                    # Context'e ekle
                    conversation_context['conversation_history'].append(f"LD: {ld_response.content[:100]}...")
                    
                    self.socketio.emit('conversation_message', {
                        'speaker': 'lead_developer',
                        'speaker_name': '👨‍💻 Lead Developer',
                        'message': ld_response.content,
                        'turn': turn + 1,
                        'model': ld_response.model,
                        'usage': ld_response.usage,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Analytics güncellemesi
                    self.broadcast_analytics_update()
                
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
            
            # Plugin'ları çalıştır (TODO: Implement plugin_manager)
            # plugin_results = await plugin_manager.process_message(message, context)
            plugin_results = []  # Empty for now
            
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
            # TODO: Implement ProjectMemory
            print(f"📝 Konuşma kaydı atlandı (Project memory not implemented): {session_id}")
            return
            
            # Session mesajlarını topla (gerçek implementasyonda bu veriler session'dan gelecek)
            # Şimdilik bu fonksiyon temel yapıyı kuruyor
            
            # conversation_data = {
            #     'title': f"AI Konuşması - {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            #     'initial_prompt': initial_prompt,
            #     'status': 'completed',
            #     'total_turns': max_turns,
            #     'total_interventions': len(self.intervention_queue.get(session_id, [])),
            #     'messages': [],  # Gerçek implementasyonda session'dan toplanacak
            #     'metadata': {
            #         'session_id': session_id,
            #         'created_via': 'web_interface'
            #     }
            # }
            
            # # Konuşmayı kaydet
            # saved_id = self.project_memory.save_conversation(conversation_data)
            
            # # WebSocket bildirimi
            # self.socketio.emit('conversation_saved', {
            #     'conversation_id': saved_id,
            #     'session_id': session_id,
            #     'title': conversation_data['title'],
            #     'timestamp': datetime.now().isoformat()
            # })
            
            # print(f"💾 Konuşma hafızaya kaydedildi: {saved_id}")
            
        except Exception as e:
            print(f"⚠️ Konuşma kayıt hatası: {e}")
    
    def _test_api_key(self, provider: str, api_key: str, model: str = "") -> dict:
        """API anahtarını gerçekten test et - GERÇEK API ÇAĞRISI"""
        try:
            import asyncio
            import concurrent.futures
            
            # Test mesajı
            test_message = "Hi"  # Minimal test mesajı
            
            # Geçici adapter oluştur
            if provider == 'gemini':
                from .ai_adapters.gemini_adapter import GeminiAdapter
                test_model = model or 'gemini-2.5-flash'
                test_adapter = GeminiAdapter(api_key=api_key, model=test_model)
            elif provider == 'openai':
                from .ai_adapters.openai_adapter import OpenAIAdapter
                test_model = model or 'gpt-4o-mini'
                test_adapter = OpenAIAdapter(api_key=api_key, model=test_model)
            else:
                return {
                    'success': False,
                    'error': f'Desteklenmeyen provider: {provider}',
                    'provider': provider
                }
            
            # GERÇEK API TESTI - Async işlemi sync wrapper ile çalıştır
            def run_real_test():
                try:
                    # Yeni event loop oluştur
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Gerçek API çağrısı yap
                    response = loop.run_until_complete(
                        test_adapter.send_message(test_message)
                    )
                    
                    loop.close()
                    return response
                    
                except Exception as e:
                    return {'error': str(e)}
            
            # Test'i thread'de çalıştır (5 saniye timeout)
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_real_test)
                try:
                    result = future.result(timeout=5.0)  # 5 saniye timeout
                    
                    if isinstance(result, dict) and 'error' in result:
                        # API hatası
                        error_msg = result['error']
                        if 'insufficient_quota' in error_msg.lower():
                            return {
                                'success': False,
                                'error': 'API quota aşıldı - Ücretli plan gerekli',
                                'provider': provider,
                                'details': 'API anahtarı geçerli ama quota sınırında'
                            }
                        elif 'invalid' in error_msg.lower() or 'unauthorized' in error_msg.lower():
                            return {
                                'success': False,
                                'error': 'Geçersiz API anahtarı',
                                'provider': provider,
                                'details': error_msg[:100]
                            }
                        else:
                            return {
                                'success': False,
                                'error': f'API hatası: {error_msg[:100]}',
                                'provider': provider
                            }
                    
                    elif result and hasattr(result, 'content'):
                        # Başarılı yanıt
                        return {
                            'success': True,
                            'message': 'API anahtarı gerçekten çalışıyor!',
                            'provider': provider,
                            'model': test_model,
                            'details': f'Test yanıtı: "{result.content[:50]}..."',
                            'test_response': result.content[:100] if result.content else 'Boş yanıt'
                        }
                    else:
                        return {
                            'success': False,
                            'error': 'API\'den geçerli yanıt alınamadı',
                            'provider': provider,
                            'details': str(result)[:100] if result else 'None response'
                        }
                        
                except concurrent.futures.TimeoutError:
                    return {
                        'success': False,
                        'error': 'API test timeout (5 saniye)',
                        'provider': provider,
                        'details': 'API çok yavaş yanıt veriyor'
                    }
                    
        except ImportError as e:
            return {
                'success': False,
                'error': f'Adapter import hatası: {str(e)[:100]}',
                'provider': provider
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Test başlatma hatası: {str(e)[:100]}',
                'provider': provider
            }
    
    def start_background(self):
        """Web sunucusunu background'da başlat"""
        def run_server():
            self.socketio.run(self.app, host=self.host, port=self.port, debug=False, allow_unsafe_werkzeug=True)
        
        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()
        
        print(f"🌐 Universal Web arayüzü başlatıldı: http://{self.host}:{self.port}")
        
        return server_thread 