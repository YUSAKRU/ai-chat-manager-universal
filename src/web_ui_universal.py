"""
Web UI Universal - Analytics Dashboard ile geliştirilmiş versiyon
"""
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import json
import time
import asyncio
from datetime import datetime
import threading
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Hata yönetimi sistemi
from .error_handler import central_error_handler, safe_execute, async_safe_execute, AIChromeChatError, ErrorTypes

# Document Synthesizer - AI-Powered Document Generation
from .document_synthesizer import DocumentSynthesizer

# Live Document Canvas - Real-time Collaborative Document Editing
from .live_document_canvas import (
    DocumentStateManager, 
    RealTimeSyncEngine, 
    CanvasInterface, 
    AIDocumentIntegration
)

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
        
        # Merkezi hata yönetimi sistemini entegre et
        central_error_handler.init_app(self.app)
        
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
        
        # Document Synthesizer - AI-Powered Document Generation
        self.document_synthesizer = DocumentSynthesizer(
            ai_adapter=self.ai_adapter,
            output_dir="generated_documents"
        )
        print("📄 AI Document Synthesizer başlatıldı!")
        
        # Live Document Canvas - Real-time Collaborative Document Editing
        try:
            self.document_state_manager = DocumentStateManager()
            self.real_time_sync_engine = RealTimeSyncEngine(self.socketio, self.document_state_manager)
            self.canvas_interface = CanvasInterface()
            self.ai_document_integration = AIDocumentIntegration(
                self.document_state_manager, 
                self.real_time_sync_engine
            )
            print("🎨 Live Document Canvas başlatıldı!")
        except Exception as e:
            print(f"⚠️ Live Document Canvas simplified mode: {e}")
            # Mock objects for API compatibility
            self.document_state_manager = None
            self.real_time_sync_engine = None
            self.canvas_interface = None  
            self.ai_document_integration = None
        
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
            """Analytics verilerini döndür - Gerçek performans verileri ile"""
            try:
                if not self.ai_adapter:
                    return jsonify({'error': 'AI adapter bulunamadı'}), 500
                
                # Detaylı analytics verilerini al
                detailed_analytics = self.ai_adapter.get_detailed_analytics()
                
                # Rol atamaları
                role_assignments = self.ai_adapter.get_role_assignments()
                
                # Global stats
                global_stats = detailed_analytics['global_stats']
                
                analytics_data = {
                    'summary': {
                        'total_cost': round(global_stats['total_cost'], 4),
                        'total_requests': global_stats['total_requests'],
                        'success_rate': round(global_stats.get('success_rate', 100), 1),
                        'avg_response_time': round(global_stats.get('avg_response_time', 0), 2),
                        'total_tokens': global_stats['total_tokens'],
                        'total_errors': global_stats['total_errors'],
                        'input_tokens': global_stats.get('input_tokens', 0),
                        'output_tokens': global_stats.get('output_tokens', 0)
                    },
                    'adapters': {},
                    'token_usage': {
                        'total': global_stats['total_tokens'],
                        'input': global_stats.get('input_tokens', 0),
                        'output': global_stats.get('output_tokens', 0)
                    },
                    'performance_metrics': detailed_analytics.get('performance_metrics', {}),
                    'cost_breakdown': detailed_analytics.get('cost_breakdown', {}),
                    'timestamp': datetime.now().isoformat()
                }
                
                # Her adapter için detaylı bilgi - Gerçek performans verileri ile
                adapters_data = detailed_analytics.get('adapters', {})
                for adapter_id, adapter_info in adapters_data.items():
                    # Role assignment bul
                    assigned_role = None
                    for role, aid in role_assignments.items():
                        if aid == adapter_id:
                            assigned_role = role
                            break
                    
                    # Gerçek adapter nesnesinden performans verilerini al
                    real_adapter = self.ai_adapter.adapters.get(adapter_id)
                    real_performance = {}
                    
                    if real_adapter and hasattr(real_adapter, 'get_performance_summary'):
                        real_performance = real_adapter.get_performance_summary()
                    
                    analytics_data['adapters'][adapter_id] = {
                        'id': adapter_id,
                        'type': adapter_info['type'],
                        'model': adapter_info['model'],
                        'role': assigned_role,
                        'stats': adapter_info['stats'],
                        'is_available': adapter_info.get('rate_limit', {}).get('available', True),
                        'status': adapter_info.get('status', 'active'),
                        # Gerçek performans verileri
                        'real_performance': real_performance
                    }
                
                # Cache güncelle
                self.analytics_cache = {
                    'last_update': time.time(),
                    'data': analytics_data
                }
                
                return jsonify(analytics_data)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/analytics/advanced')
        def get_advanced_analytics():
            """🚀 FAZ 2: Advanced Analytics Dashboard"""
            try:
                if not self.ai_adapter:
                    return jsonify({'error': 'AI adapter bulunamadı'}), 500
                
                # Advanced analytics verilerini al
                advanced_data = self.ai_adapter.get_advanced_analytics_dashboard()
                
                return jsonify({
                    'status': 'success',
                    'data': advanced_data,
                    'timestamp': datetime.now().isoformat(),
                    'version': '2.0',
                    'features': [
                        'Model Performance Comparison',
                        'Cost Optimization Recommendations', 
                        'Performance Trends Analysis',
                        'System Health Monitoring',
                        'Capacity Planning'
                    ]
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/analytics/model-comparison')
        def get_model_comparison():
            """Model performans karşılaştırması"""
            try:
                if not self.ai_adapter:
                    return jsonify({'error': 'AI adapter bulunamadı'}), 500
                
                comparison_data = self.ai_adapter.get_model_performance_comparison()
                
                return jsonify({
                    'status': 'success',
                    'data': comparison_data,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/analytics/recommendations')
        def get_optimization_recommendations():
            """Maliyet optimizasyonu önerileri"""
            try:
                if not self.ai_adapter:
                    return jsonify({'error': 'AI adapter bulunamadı'}), 500
                
                recommendations = self.ai_adapter.get_cost_optimization_recommendations()
                
                return jsonify({
                    'status': 'success',
                    'recommendations': recommendations,
                    'count': len(recommendations),
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/ai/send_message', methods=['POST'])
        def send_ai_message():
            """AI'ya mesaj gönder (synchronous)"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'Geçersiz JSON verisi'}), 400
                
                role_id = data.get('role', data.get('role_id', 'project_manager'))  # 'role' da kabul et
                message = data.get('message', '').strip()
                context = data.get('context', '')
                
                if not message:
                    return jsonify({'error': 'Mesaj boş olamaz'}), 400
                
                print(f"💬 Chat mesajı: role={role_id}, message={message[:50]}...")
                
                # Synchronous AI çağrısı
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    response = loop.run_until_complete(
                        self.ai_adapter.send_message(role_id, message, context)
                    )
                    
                    if response and response.content:
                        print(f"✅ AI yanıtı alındı: {len(response.content)} karakter")
                        
                        # Analytics güncellemesi tetikle (background)
                        try:
                            self.broadcast_analytics_update()
                        except:
                            pass  # Analytics hatası chat'i etkilemesin
                        
                        return jsonify({
                            'success': True,
                            'response': response.content,
                            'role_id': role_id,
                            'model': response.model,
                            'timestamp': datetime.now().isoformat()
                        })
                    else:
                        print("❌ Boş yanıt alındı")
                        return jsonify({'error': 'AI\'dan boş yanıt alındı'}), 500
                        
                except Exception as ai_error:
                    print(f"❌ AI işlem hatası: {str(ai_error)}")
                    return jsonify({'error': f'AI işlem hatası: {str(ai_error)}'}), 500
                
            except Exception as e:
                print(f"❌ Chat endpoint hatası: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/ai/send_message_async', methods=['POST'])
        def send_ai_message_async():
            """AI'ya mesaj gönder (asynchronous - WebSocket ile)"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'Geçersiz JSON verisi'}), 400
                
                role_id = data.get('role_id', 'project_manager')
                message = data.get('message', '').strip()
                context = data.get('context', '')
                
                if not message:
                    return jsonify({'error': 'Mesaj boş olamaz'}), 400
                
            except Exception as e:
                return jsonify({'error': str(e)}), 400
            
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
            # Frontend 'intervention' parametresi gönderebilir
            intervention_message = data.get('intervention', data.get('message', '')).strip()
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
        
        @self.app.route('/api/ai/conversation/continue', methods=['POST'])
        def continue_conversation():
            """Duraklayan konuşmayı devam ettir"""
            try:
                data = request.get_json()
                session_id = data.get('session_id')
                additional_turns = data.get('additional_turns', 3)
                
                if not session_id:
                    return jsonify({'error': 'Session ID gerekli'}), 400
                
                if session_id not in self.active_conversations:
                    return jsonify({'error': 'Devam ettirilebilir konuşma bulunamadı'}), 404
                
                conversation = self.active_conversations[session_id]
                if conversation['status'] != 'paused':
                    return jsonify({'error': 'Konuşma pause durumunda değil'}), 400
                
                # Continue işlemini background'da çalıştır
                def run_continue():
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(
                            self._continue_conversation(session_id, additional_turns)
                        )
                    except Exception as e:
                        self.socketio.emit('conversation_error', {
                            'error': str(e),
                            'session_id': session_id,
                            'timestamp': datetime.now().isoformat()
                        })
                
                continue_thread = threading.Thread(target=run_continue)
                continue_thread.daemon = True
                continue_thread.start()
                
                return jsonify({
                    'status': 'continuing',
                    'session_id': session_id,
                    'additional_turns': additional_turns,
                    'current_completed': conversation['completed_turns'],
                    'new_max_turns': conversation['max_turns'] + additional_turns
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/ai/conversation/<session_id>/end', methods=['POST'])
        def end_conversation_permanently(session_id):
            """Konuşmayı kalıcı olarak sonlandır"""
            try:
                if session_id not in self.active_conversations:
                    return jsonify({'error': 'Konuşma bulunamadı'}), 404
                
                self._end_conversation_permanently(session_id)
                
                return jsonify({
                    'status': 'ended',
                    'session_id': session_id,
                    'message': 'Konuşma kalıcı olarak sonlandırıldı'
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/ai/conversation/<session_id>/status', methods=['GET'])
        def get_conversation_status(session_id):
            """Konuşma durumunu getir"""
            try:
                if session_id not in self.active_conversations:
                    return jsonify({'error': 'Konuşma bulunamadı'}), 404
                
                conversation = self.active_conversations[session_id]
                
                return jsonify({
                    'session_id': session_id,
                    'status': conversation['status'],
                    'completed_turns': conversation['completed_turns'],
                    'max_turns': conversation['max_turns'],
                    'current_turn': conversation['current_turn'],
                    'can_continue': conversation['status'] == 'paused',
                    'context_summary': {
                        'project_goal': conversation['context']['project_goal'][:100] + '...',
                        'total_messages': len(conversation['context']['conversation_history'])
                    }
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # === Document Synthesizer API Endpoints ===
        
        @self.app.route('/api/documents/generate', methods=['POST'])
        def generate_document():
            """AI-powered document synthesis"""
            try:
                data = request.get_json()
                session_id = data.get('session_id')
                document_type = data.get('document_type', 'meeting_summary')
                
                if not session_id:
                    return jsonify({'error': 'Session ID gerekli'}), 400
                
                # Session'dan conversation data'sını çıkar
                conversation_data = self.document_synthesizer.get_conversation_data_from_session(
                    session_id, self.active_conversations
                )
                
                if not conversation_data:
                    return jsonify({'error': 'Konuşma verisi bulunamadı'}), 404
                
                # Background'da document generation çalıştır
                def run_document_generation():
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        if document_type == 'meeting_summary':
                            metadata = loop.run_until_complete(
                                self.document_synthesizer.synthesize_meeting_summary(conversation_data)
                            )
                        elif document_type == 'action_items':
                            metadata = loop.run_until_complete(
                                self.document_synthesizer.synthesize_action_items(conversation_data)
                            )
                        elif document_type == 'decisions_log':
                            metadata = loop.run_until_complete(
                                self.document_synthesizer.synthesize_decisions_log(conversation_data)
                            )
                        else:
                            raise ValueError(f"Desteklenmeyen belge türü: {document_type}")
                        
                        # Success notification via WebSocket
                        self.socketio.emit('document_generated', {
                            'document_id': metadata.document_id,
                            'title': metadata.title,
                            'document_type': metadata.document_type,
                            'session_id': metadata.session_id,
                            'file_paths': metadata.file_paths,
                            'insights_summary': metadata.insights_summary,
                            'timestamp': metadata.created_at
                        })
                        
                    except Exception as e:
                        self.socketio.emit('document_generation_error', {
                            'error': str(e),
                            'session_id': session_id,
                            'document_type': document_type,
                            'timestamp': datetime.now().isoformat()
                        })
                
                generation_thread = threading.Thread(target=run_document_generation)
                generation_thread.daemon = True
                generation_thread.start()
                
                return jsonify({
                    'status': 'generating',
                    'document_type': document_type,
                    'session_id': session_id,
                    'message': 'AI belge sentezi başlatıldı...'
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/documents', methods=['GET'])
        def list_documents():
            """Oluşturulmuş belgeleri listele"""
            try:
                document_type = request.args.get('type')
                documents = self.document_synthesizer.list_documents(document_type)
                
                # Serialize documents
                documents_data = []
                for doc in documents:
                    if hasattr(doc, '__dict__'):
                        documents_data.append(doc.__dict__)
                    else:
                        documents_data.append(doc)
                
                return jsonify({
                    'documents': documents_data,
                    'count': len(documents),
                    'filter': document_type
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/documents/<document_id>', methods=['GET'])
        def get_document(document_id):
            """Belge detaylarını getir"""
            try:
                metadata = self.document_synthesizer.get_document_metadata(document_id)
                
                if not metadata:
                    return jsonify({'error': 'Belge bulunamadı'}), 404
                
                # Serialize metadata
                if hasattr(metadata, '__dict__'):
                    document_data = metadata.__dict__
                else:
                    document_data = metadata
                
                return jsonify(document_data)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/documents/<document_id>/download/<file_format>')
        def download_document(document_id, file_format):
            """Belgeyi indir"""
            try:
                metadata = self.document_synthesizer.get_document_metadata(document_id)
                
                if not metadata:
                    return jsonify({'error': 'Belge bulunamadı'}), 404
                
                file_path = metadata.file_paths.get(file_format)
                if not file_path or not os.path.exists(file_path):
                    return jsonify({'error': f'{file_format} formatı bulunamadı'}), 404
                
                from flask import send_file
                return send_file(
                    file_path,
                    as_attachment=True,
                    download_name=os.path.basename(file_path)
                )
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/documents/<document_id>', methods=['DELETE'])
        def delete_document(document_id):
            """Belgeyi sil"""
            try:
                success = self.document_synthesizer.delete_document(document_id)
                
                if not success:
                    return jsonify({'error': 'Belge silinirken hata oluştu'}), 500
                
                return jsonify({
                    'status': 'deleted',
                    'document_id': document_id
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/documents/statistics')
        def get_document_statistics():
            """Document synthesis istatistikleri"""
            try:
                stats = self.document_synthesizer.get_statistics()
                return jsonify(stats)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # === Memory & Tasks API Endpoints ===
        
        @self.app.route('/api/memory/conversations', methods=['GET'])
        def get_conversation_history():
            """Konuşma geçmişini getir"""
            try:
                limit = request.args.get('limit', 10, type=int)
                
                # Mock conversation data
                mock_conversations = [
                    {
                        'id': 'conv-1',
                        'title': 'Proje Başlangıç Toplantısı',
                        'participants': ['project_manager', 'lead_developer', 'boss'],
                        'message_count': 15,
                        'created_at': '2025-06-19T18:30:00',
                        'last_message': 'Mimari tasarım onaylandı, geliştirmeye başlayabiliriz.',
                        'status': 'completed'
                    },
                    {
                        'id': 'conv-2', 
                        'title': 'API Entegrasyonu Planlaması',
                        'participants': ['project_manager', 'lead_developer'],
                        'message_count': 8,
                        'created_at': '2025-06-19T19:15:00',
                        'last_message': 'Gemini ve OpenAI entegrasyonları hazır.',
                        'status': 'active'
                    }
                ]
                
                return jsonify({
                    'success': True,
                    'conversations': mock_conversations[:limit],
                    'total': len(mock_conversations)
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/memory/conversations/<conversation_id>', methods=['GET'])
        def get_conversation_details(conversation_id):
            """Konuşma detaylarını getir"""
            try:
                # Mock conversation details
                mock_detail = {
                    'id': conversation_id,
                    'title': 'Proje Başlangıç Toplantısı',
                    'participants': ['project_manager', 'lead_developer', 'boss'],
                    'created_at': '2025-06-19T18:30:00',
                    'status': 'completed',
                    'messages': [
                        {
                            'id': 'msg-1',
                            'sender': 'project_manager',
                            'content': 'Proje hedeflerini belirleyelim.',
                            'timestamp': '2025-06-19T18:30:15'
                        },
                        {
                            'id': 'msg-2',
                            'sender': 'lead_developer', 
                            'content': 'Teknik gereksinimleri analiz ettim.',
                            'timestamp': '2025-06-19T18:31:00'
                        }
                    ]
                }
                
                return jsonify({
                    'success': True,
                    'conversation': mock_detail
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/memory/conversations', methods=['POST'])
        def save_conversation():
            """Konuşmayı kaydet"""
            try:
                data = request.get_json()
                title = data.get('title', 'Yeni Konuşma')
                messages = data.get('messages', [])
                
                # Mock save operation
                conversation_id = f"conv-{int(time.time())}"
                
                return jsonify({
                    'success': True,
                    'conversation_id': conversation_id,
                    'message': 'Konuşma başarıyla kaydedildi'
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
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
            try:
                data = request.get_json()
                title = data.get('title', 'Yeni Görev')
                assignee = data.get('assignee', 'project_manager')
                priority = data.get('priority', 'medium')
                
                # Mock task creation
                task_id = f"task-{int(time.time())}"
                
                return jsonify({
                    'success': True,
                    'task': {
                        'id': task_id,
                        'title': title,
                        'status': 'pending',
                        'priority': priority,
                        'assignee': assignee,
                        'created_at': datetime.now().isoformat()
                    },
                    'message': 'Görev başarıyla oluşturuldu'
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/memory/tasks/<task_id>/status', methods=['PATCH'])
        def update_task_status(task_id):
            """Görev durumunu güncelle"""
            try:
                data = request.get_json()
                new_status = data.get('status', 'in_progress')
                
                return jsonify({
                    'success': True,
                    'task_id': task_id,
                    'new_status': new_status,
                    'message': f'Görev durumu {new_status} olarak güncellendi'
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/memory/search', methods=['GET'])
        def search_conversations():
            """Konuşmalarda arama yap"""
            try:
                query = request.args.get('q', '').strip()
                limit = request.args.get('limit', 10, type=int)
                
                if not query:
                    return jsonify({'error': 'Arama sorgusu gerekli'}), 400
                
                # Mock search results
                mock_results = [
                    {
                        'id': 'conv-1',
                        'title': 'Proje Başlangıç Toplantısı',
                        'snippet': f'...{query} hakkında konuştuk...',
                        'relevance_score': 0.95,
                        'created_at': '2025-06-19T18:30:00'
                    }
                ]
                
                return jsonify({
                    'success': True,
                    'query': query,
                    'results': mock_results[:limit],
                    'total': len(mock_results)
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # === API Key Management Routes ===
        
        # Eski endpoint'ler (UI uyumluluğu için)
        @self.app.route('/api/load-keys', methods=['GET'])
        def load_keys_legacy():
            """Eski UI için anahtarları yükle (legacy endpoint)"""
            return get_api_keys()
        
        @self.app.route('/api/test-key', methods=['POST'])
        def test_key_legacy():
            """Eski UI için anahtar test et (legacy endpoint)"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'Geçersiz JSON verisi'}), 400
                
                provider = data.get('provider')
                api_key = data.get('key')
                
                if not provider or not api_key:
                    return jsonify({'error': 'Provider ve key gerekli'}), 400
                
                # Test işlemini çalıştır
                test_result = self._test_api_key(provider, api_key)
                return jsonify(test_result)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/save-key', methods=['POST'])
        def save_key_legacy():
            """Eski UI için anahtar kaydet (legacy endpoint)"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'Geçersiz JSON verisi'}), 400
                
                provider = data.get('provider')
                api_key = data.get('key')
                key_name = data.get('keyName', 'primary')
                
                if not provider or not api_key:
                    return jsonify({'error': 'Provider ve key gerekli'}), 400
                
                if provider not in ['gemini', 'openai']:
                    return jsonify({'error': f'Desteklenmeyen provider: {provider}'}), 400
                
                # Model seç
                model = data.get('model', '')
                if not model:
                    model = 'gemini-2.5-flash' if provider == 'gemini' else 'gpt-3.5-turbo'
                
                # API anahtarını test et
                test_result = self._test_api_key(provider, api_key, model)
                if not test_result['success']:
                    return jsonify({'error': f'API anahtarı test edilemedi: {test_result["error"]}'}), 400
                
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
                        'message': f'{provider.title()} API anahtarı başarıyla eklendi'
                    })
                    
                except Exception as adapter_error:
                    return jsonify({
                        'success': True,  # Config kaydedildi, adapter hatası olabilir
                        'warning': f'Adapter oluşturulamadı: {str(adapter_error)}',
                        'provider': provider,
                        'message': 'API anahtarı kaydedildi, ancak adapter hatası'
                    })
                    
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/delete-key', methods=['POST'])
        def delete_key_legacy():
            """Eski UI için anahtar sil (legacy endpoint)"""
            data = request.get_json()
            provider = data.get('provider')
            key_name = data.get('keyName', 'primary')
            if not provider:
                return jsonify({'error': 'Provider gerekli'}), 400
            return delete_api_key(provider, key_name)
        
        @self.app.route('/api/clear-all-keys', methods=['POST'])
        def clear_all_keys():
            """Tüm API anahtarlarını temizle"""
            try:
                print("🧹 Tüm API anahtarları temizleniyor...")
                
                # Config manager'dan tüm anahtarları temizle
                try:
                    # Doğrudan config'i sıfırla - daha güvenli
                    self.ai_adapter.config_manager.config = {}
                    self.ai_adapter.config_manager.save_config()
                    print("✅ Config dosyası temizlendi")
                except Exception as config_error:
                    print(f"⚠️ Config temizleme hatası: {config_error}")
                
                # Adapter'ları da temizle
                try:
                    if hasattr(self.ai_adapter, 'adapters'):
                        adapter_count = len(self.ai_adapter.adapters)
                        self.ai_adapter.adapters.clear()
                        print(f"✅ {adapter_count} adapter temizlendi")
                    
                    if hasattr(self.ai_adapter, 'role_assignments'):
                        role_count = len(self.ai_adapter.role_assignments)
                        self.ai_adapter.role_assignments.clear()
                        print(f"✅ {role_count} rol ataması temizlendi")
                except Exception as adapter_error:
                    print(f"⚠️ Adapter temizleme hatası: {adapter_error}")
                
                print("🎉 Tüm anahtarlar başarıyla temizlendi")
                return jsonify({'success': True, 'message': 'Tüm anahtarlar temizlendi'})
                
            except Exception as e:
                print(f"❌ Clear-all-keys hatası: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/assign-role', methods=['POST'])
        def assign_role_legacy():
            """Eski UI için rol ataması (legacy endpoint)"""
            try:
                data = request.get_json()
                print(f"🔍 Assign role request data: {data}")
                
                if not data:
                    print("❌ JSON verisi alınamadı")
                    return jsonify({'error': 'Geçersiz JSON verisi'}), 400
                
                role = data.get('role')
                adapter_id = data.get('adapter_id')  # Artık adapter_id alıyoruz
                
                # Legacy uyumluluk için provider'ı da kontrol et
                if not adapter_id:
                    provider = data.get('provider')
                    if provider:
                        # Eski format - provider'dan adapter_id bul
                        adapter_status = self.ai_adapter.get_adapter_status()
                        for aid, status in adapter_status.items():
                            if status.get('type') == provider.lower() and 'error' not in status:
                                adapter_id = aid
                                break
                        
                        if not adapter_id:
                            for aid, status in adapter_status.items():
                                if aid.startswith(provider.lower() + '-') and 'error' not in status:
                                    adapter_id = aid
                                    break
                
                print(f"🎯 Role: {role}, Adapter ID: {adapter_id}")
                
                if not role or not adapter_id:
                    print("❌ Role veya adapter_id eksik")
                    return jsonify({'error': 'Role ve adapter_id gerekli'}), 400
                
                # Adapter'ın var olduğunu kontrol et
                if adapter_id not in self.ai_adapter.adapters:
                    print(f"❌ Adapter bulunamadı: {adapter_id}")
                    print(f"📋 Mevcut adapter'lar: {list(self.ai_adapter.adapters.keys())}")
                    return jsonify({'error': f'Adapter bulunamadı: {adapter_id}'}), 404
                
                # Rol ataması yap
                try:
                    self.ai_adapter.assign_role(role, adapter_id)
                    
                    # Adapter bilgilerini al
                    adapter_info = self.ai_adapter.get_adapter_status().get(adapter_id, {})
                    
                    return jsonify({
                        'success': True, 
                        'message': f'{role} rolü {adapter_id} adapter\'ına atandı',
                        'role': role,
                        'adapter_id': adapter_id,
                        'adapter_type': adapter_info.get('type', 'unknown'),
                        'model': adapter_info.get('model', 'unknown')
                    })
                        
                except Exception as assign_error:
                    print(f"❌ Rol atama hatası: {str(assign_error)}")
                    return jsonify({'error': f'Rol atama hatası: {str(assign_error)}'}), 500
                    
            except Exception as e:
                print(f"❌ Genel hata: {str(e)}")
                return jsonify({'error': f'Genel hata: {str(e)}'}), 500
        
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
                if not data:
                    return jsonify({'error': 'Geçersiz JSON verisi'}), 400
                
                api_key = data.get('api_key', '').strip()
                key_name = data.get('key_name', 'primary').strip()
                model = data.get('model', '')
                
                if not api_key:
                    return jsonify({'error': 'API anahtarı gerekli'}), 400
                
                if provider not in ['gemini', 'openai']:
                    return jsonify({'error': f'Desteklenmeyen provider: {provider}'}), 400
                
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
                    return jsonify({'error': f'API anahtarı test edilemedi: {test_result["error"]}'}), 400
                
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
                        'success': True,  # Config kaydedildi
                        'warning': f'Adapter oluşturulamadı: {str(adapter_error)}',
                        'provider': provider,
                        'message': 'API anahtarı kaydedildi, ancak adapter hatası'
                    })
                    
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
        
        @self.app.route('/api/optimization/enable', methods=['POST'])
        def enable_auto_optimization():
            """🤖 FAZ 3: Auto-optimization etkinleştir"""
            try:
                if not self.ai_adapter:
                    return jsonify({'error': 'AI adapter bulunamadı'}), 500
                
                data = request.get_json() or {}
                config = data.get('config', {})
                
                # Auto-optimization'ı etkinleştir
                self.ai_adapter.enable_auto_optimization(config)
                
                return jsonify({
                    'status': 'success',
                    'message': 'Auto-optimization etkinleştirildi',
                    'config': getattr(self.ai_adapter, 'auto_optimization_config', {}),
                    'features': [
                        'Dynamic Model Selection',
                        'Auto Scaling',
                        'Cost Optimization',
                        'Predictive Planning'
                    ],
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/optimization/cycle', methods=['POST'])
        def run_optimization_cycle():
            """🔄 Optimization cycle çalıştır"""
            try:
                if not self.ai_adapter:
                    return jsonify({'error': 'AI adapter bulunamadı'}), 500
                
                # Optimization cycle'ı çalıştır
                results = self.ai_adapter.run_auto_optimization_cycle()
                
                return jsonify({
                    'status': 'success',
                    'results': results,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/optimization/intelligent-select', methods=['POST'])
        def intelligent_model_selection():
            """🧠 Akıllı model seçimi"""
            try:
                if not self.ai_adapter:
                    return jsonify({'error': 'AI adapter bulunamadı'}), 500
                
                data = request.get_json()
                if not data or 'message' not in data:
                    return jsonify({'error': 'Message field gerekli'}), 400
                
                message = data['message']
                context = data.get('context', 'general')
                
                # Intelligent model selection
                selected_adapter = self.ai_adapter.intelligent_load_balancing(message, context)
                
                if selected_adapter:
                    adapter = self.ai_adapter.adapters.get(selected_adapter)
                    return jsonify({
                        'status': 'success',
                        'selected_adapter': selected_adapter,
                        'model': adapter.model if adapter else 'unknown',
                        'context': context,
                        'message_complexity': self.ai_adapter._analyze_message_complexity(message),
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    return jsonify({'error': 'Uygun adapter bulunamadı'}), 404
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/optimization/capacity-planning')
        def get_capacity_planning():
            """📈 Predictive capacity planning"""
            try:
                if not self.ai_adapter:
                    return jsonify({'error': 'AI adapter bulunamadı'}), 500
                
                planning_data = self.ai_adapter.predictive_capacity_planning()
                
                return jsonify({
                    'status': 'success',
                    'data': planning_data,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # === Live Document Canvas API Endpoints ===
        
        @self.app.route('/api/canvas/documents', methods=['POST'])
        def create_canvas_document():
            """Yeni canlı belge oluştur - FIXED VERSION"""
            try:
                import time  # Import at function level for proper scope
                
                data = request.get_json()
                title = data.get('title', 'Yeni Belge')
                content = data.get('content', '')
                document_type = data.get('type', 'markdown')
                
                # FIXED: Use DocumentStateManager to create document properly
                if self.document_state_manager:
                    document_id = self.document_state_manager.create_document(title, content, document_type, "web_user")
                    window_id = f"canvas_window_{int(time.time())}"
                    
                    print(f"📄 Canvas document created via DocumentStateManager: {title} ({document_id})")
                    
                    return jsonify({
                        'status': 'success',
                        'document_id': document_id,
                        'window_id': window_id,
                        'title': title,
                        'document_type': document_type,
                        'timestamp': datetime.now().isoformat(),
                        'method': 'document_state_manager'
                    })
                else:
                    # Fallback if DocumentStateManager is None
                    document_id = f"doc_{int(time.time())}"
                    window_id = f"canvas_window_{int(time.time())}"
                    
                    print(f"⚠️ Canvas document created in fallback mode: {title} ({document_id})")
                    
                    return jsonify({
                        'status': 'success',
                        'document_id': document_id,
                        'window_id': window_id,
                        'title': title,
                        'document_type': document_type,
                        'timestamp': datetime.now().isoformat(),
                        'method': 'fallback'
                    })
                
            except Exception as e:
                print(f"❌ Canvas document creation error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/canvas/documents/<document_id>')
        def get_canvas_document(document_id):
            """Canlı belge bilgilerini getir"""
            try:
                document_info = self.document_state_manager.get_document_info(document_id)
                
                if not document_info:
                    return jsonify({'error': 'Belge bulunamadı'}), 404
                
                return jsonify({
                    'status': 'success',
                    'document': document_info,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/canvas/windows', methods=['GET'])
        def list_canvas_windows():
            """Aktif canvas window'larını listele"""
            try:
                windows = self.canvas_interface.list_active_windows()
                room_info = self.real_time_sync_engine.list_active_rooms()
                
                return jsonify({
                    'status': 'success',
                    'windows': windows,
                    'rooms': room_info,
                    'total_windows': len(windows),
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/canvas/documents/<document_id>', methods=['PUT'])
        def update_canvas_document(document_id):
            """Canvas belgesi içeriğini güncelle"""
            try:
                data = request.get_json()
                content = data.get('content', '')
                
                print(f"💾 Canvas document updated: {document_id}")
                
                return jsonify({
                    'status': 'success',
                    'document_id': document_id,
                    'content': content,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                print(f"❌ Canvas document update error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/canvas/ai-assist', methods=['POST'])
        def canvas_ai_assist():
            """Canvas belge için AI yardımı"""
            try:
                data = request.get_json()
                document_id = data.get('document_id')
                action = data.get('action', '')
                content = data.get('content', '')
                
                print(f"🤖 AI assistance requested for document {document_id}: {action}")
                
                # Mock AI processing for now
                processed_content = content
                if 'özet' in action.lower():
                    processed_content = f"<h3>Özet</h3><p>Bu belgenin ana konuları özetlenmiştir.</p>{content}"
                elif 'devam' in action.lower():
                    processed_content = f"{content}<p>Belge AI tarafından devam ettirilmiştir...</p>"
                elif 'düzelt' in action.lower():
                    processed_content = content  # Grammar correction would go here
                elif 'çevir' in action.lower():
                    processed_content = f"<p><em>Translated content:</em></p>{content}"
                
                return jsonify({
                    'status': 'success',
                    'content': processed_content,
                    'action': action,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                print(f"❌ Canvas AI assist error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/canvas/statistics')
        def get_canvas_statistics():
            """Canvas istatistiklerini getir - SIMPLIFIED VERSION"""
            try:
                # Mock statistics for now
                combined_stats = {
                    'canvas': {
                        'active_windows': 0,
                        'total_documents': 0,
                        'users_online': 1
                    },
                    'documents': {
                        'total_created': 0,
                        'last_modified': datetime.now().isoformat()
                    },
                    'total_active_documents': 0,
                    'timestamp': datetime.now().isoformat()
                }
                
                return jsonify({
                    'status': 'success',
                    'statistics': combined_stats
                })
                
            except Exception as e:
                print(f"❌ Canvas statistics error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/node_modules/<path:filename>')
        def serve_node_modules(filename):
            """Serve local node_modules files for frontend dependencies"""
            try:
                node_modules_path = os.path.join(os.getcwd(), 'node_modules')
                return send_from_directory(node_modules_path, filename)
            except Exception as e:
                print(f"❌ Error serving node_modules file {filename}: {e}")
                return jsonify({'error': 'File not found'}), 404
    
    def setup_socketio_events(self):
        """SocketIO event'lerini ayarla"""
        
        # Document rooms için user tracking
        self.document_rooms = {}  # {document_id: {user_sessions: {...}, users: [...]}}
        self.user_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F']
        
        @self.socketio.on('connect')
        def handle_connect():
            print('🌐 Web client bağlandı')
            emit('status', {'message': 'Universal AI sistem bağlandı'})
            # İlk bağlantıda analytics verilerini gönder
            self.broadcast_analytics_update()
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print('🌐 Web client bağlantısı kesildi')
            # User'ı tüm document room'larından çıkar
            for document_id in list(self.document_rooms.keys()):
                self._remove_user_from_room(request.sid, document_id)
        
        @self.socketio.on('request_analytics')
        def handle_analytics_request():
            """Analytics verilerini iste"""
            self.broadcast_analytics_update()
        
        # PHASE 6.1: Multi-user Collaboration Events
        @self.socketio.on('join_document')
        def handle_join_document(data):
            """Kullanıcı bir dokümana katıl"""
            try:
                document_id = data.get('document_id')
                user_name = data.get('user_name', f'User_{request.sid[:6]}')
                
                if not document_id:
                    emit('error', {'message': 'Document ID gerekli'})
                    return
                
                # Room'a katıl
                join_room(document_id)
                
                # Document room'u yoksa oluştur
                if document_id not in self.document_rooms:
                    self.document_rooms[document_id] = {
                        'user_sessions': {},
                        'users': []
                    }
                
                room = self.document_rooms[document_id]
                
                # Kullanıcıya renk ata
                used_colors = [user['color'] for user in room['users']]
                available_colors = [c for c in self.user_colors if c not in used_colors]
                user_color = available_colors[0] if available_colors else self.user_colors[0]
                
                # Kullanıcı bilgilerini kaydet
                user_info = {
                    'session_id': request.sid,
                    'name': user_name,
                    'color': user_color,
                    'cursor_position': {'x': 0, 'y': 0},
                    'joined_at': datetime.now().isoformat()
                }
                
                room['user_sessions'][request.sid] = user_info
                room['users'].append(user_info)
                
                # Kullanıcıya kendi bilgilerini gönder
                emit('user_joined', {
                    'user': user_info,
                    'users_in_room': room['users']
                })
                
                # Room'daki diğer kullanıcılara yeni katılımı bildir
                emit('user_joined_room', {
                    'user': user_info,
                    'users_in_room': room['users']
                }, room=document_id, include_self=False)
                
                print(f"👥 User {user_name} joined document {document_id}")
                
            except Exception as e:
                print(f"❌ Join document error: {e}")
                emit('error', {'message': str(e)})
        
        @self.socketio.on('leave_document')
        def handle_leave_document(data):
            """Kullanıcı dokümandan ayrıl"""
            try:
                document_id = data.get('document_id')
                
                if document_id and document_id in self.document_rooms:
                    self._remove_user_from_room(request.sid, document_id)
                    
            except Exception as e:
                print(f"❌ Leave document error: {e}")
        
        @self.socketio.on('cursor_moved')
        def handle_cursor_moved(data):
            """Kullanıcı cursor pozisyonu güncellendi"""
            try:
                document_id = data.get('document_id')
                cursor_pos = data.get('position', {})
                
                if not document_id or document_id not in self.document_rooms:
                    return
                
                room = self.document_rooms[document_id]
                
                # Kullanıcının cursor pozisyonunu güncelle
                if request.sid in room['user_sessions']:
                    user_info = room['user_sessions'][request.sid]
                    user_info['cursor_position'] = cursor_pos
                    
                    # Diğer kullanıcılara cursor pozisyonunu broadcast et
                    emit('cursor_updated', {
                        'user_id': request.sid,
                        'user_name': user_info['name'],
                        'user_color': user_info['color'],
                        'position': cursor_pos
                    }, room=document_id, include_self=False)
                    
            except Exception as e:
                print(f"❌ Cursor move error: {e}")
        
        @self.socketio.on('selection_changed')
        def handle_selection_changed(data):
            """Kullanıcı text seçimi değişti"""
            try:
                document_id = data.get('document_id')
                selection = data.get('selection', {})
                
                if not document_id or document_id not in self.document_rooms:
                    return
                
                room = self.document_rooms[document_id]
                
                if request.sid in room['user_sessions']:
                    user_info = room['user_sessions'][request.sid]
                    
                    # Diğer kullanıcılara selection'ı broadcast et
                    emit('selection_updated', {
                        'user_id': request.sid,
                        'user_name': user_info['name'],
                        'user_color': user_info['color'],
                        'selection': selection
                    }, room=document_id, include_self=False)
                    
            except Exception as e:
                print(f"❌ Selection change error: {e}")

        # PHASE 6.2: Document Conflict Resolution WebSocket Events
        @self.socketio.on('document_operation')
        def handle_document_operation(data):
            """Handle OT document operations"""
            try:
                document_id = data.get('document_id')
                operation = data.get('operation')
                user_id = data.get('user_id')
                user_name = data.get('user_name')
                
                if not document_id or not operation:
                    emit('error', {'message': 'Document ID and operation required'})
                    return
                
                if document_id not in self.document_rooms:
                    emit('error', {'message': 'Document room not found'})
                    return
                
                print(f"📝 Document operation received: {operation['type']} from {user_name}")
                
                # Store operation for conflict detection
                room = self.document_rooms[document_id]
                if 'operations' not in room:
                    room['operations'] = []
                
                # Add timestamp and user info to operation
                operation_with_metadata = {
                    **operation,
                    'user_id': user_id,
                    'user_name': user_name,
                    'server_timestamp': datetime.now().isoformat(),
                    'session_id': request.sid
                }
                
                room['operations'].append(operation_with_metadata)
                
                # Detect conflicts with recent operations
                conflict = self._detect_operation_conflict(room['operations'], operation_with_metadata)
                
                if conflict:
                    print(f"🔥 Conflict detected: {conflict['type']}")
                    # Notify all users about the conflict
                    emit('conflict_detected', {
                        'document_id': document_id,
                        'conflict': conflict
                    }, room=document_id)
                
                # Broadcast operation to other users in the room
                emit('remote_operation', {
                    'document_id': document_id,
                    'operation': operation_with_metadata,
                    'user_id': user_id,
                    'user_name': user_name
                }, room=document_id, include_self=False)
                
                # Send acknowledgment to sender
                emit('operation_ack', {
                    'operation_id': operation.get('id'),
                    'status': 'processed',
                    'timestamp': datetime.now().isoformat()
                })
                
                print(f"✅ Operation {operation.get('id')} processed and broadcasted")
                
            except Exception as e:
                print(f"❌ Document operation error: {e}")
                emit('error', {'message': f'Operation failed: {str(e)}'})

        def _detect_operation_conflict(self, operations, new_operation):
            """Detect conflicts between operations"""
            if len(operations) < 2:
                return None
            
            # Check last few operations for conflicts
            recent_ops = operations[-5:]  # Check last 5 operations
            
            for op in recent_ops[:-1]:  # Exclude the new operation itself
                if self._operations_conflict(op, new_operation):
                    return {
                        'type': 'concurrent_edit',
                        'description': f"Concurrent {op['type']} and {new_operation['type']} operations",
                        'operations': [op, new_operation],
                        'users': [op['user_name'], new_operation['user_name']],
                        'timestamp': datetime.now().isoformat()
                    }
            
            return None
        
        def _operations_conflict(self, op1, op2):
            """Check if two operations conflict"""
            # Same position operations within 1 second
            time_diff = abs(
                datetime.fromisoformat(op1.get('server_timestamp', '1970-01-01')).timestamp() - 
                datetime.fromisoformat(op2.get('server_timestamp', '1970-01-01')).timestamp()
            )
            
            if time_diff > 1.0:  # Operations more than 1 second apart are less likely to conflict
                return False
            
            # Check position conflicts
            pos1 = op1.get('position', -1)
            pos2 = op2.get('position', -1)
            
            # Same position operations
            if pos1 == pos2 and pos1 != -1:
                return True
            
            # Overlapping delete operations
            if (op1.get('type') == 'delete' and op2.get('type') == 'delete'):
                len1 = op1.get('length', 0)
                len2 = op2.get('length', 0)
                
                # Check if ranges overlap
                end1 = pos1 + len1
                end2 = pos2 + len2
                
                if not (end1 <= pos2 or end2 <= pos1):  # Ranges overlap
                    return True
            
            return False
        
        def _remove_user_from_room(self, session_id, document_id):
            """Kullanıcıyı room'dan çıkar"""
            if document_id not in self.document_rooms:
                return
                
            room = self.document_rooms[document_id]
            
            # Kullanıcıyı bul ve çıkar
            if session_id in room['user_sessions']:
                user_info = room['user_sessions'][session_id]
                
                # Session'dan çıkar
                del room['user_sessions'][session_id]
                
                # Users listesinden çıkar
                room['users'] = [u for u in room['users'] if u['session_id'] != session_id]
                
                # Diğer kullanıcılara ayrılmayı bildir
                emit('user_left_room', {
                    'user_id': session_id,
                    'user_name': user_info['name'],
                    'users_in_room': room['users']
                }, room=document_id)
                
                print(f"👋 User {user_info['name']} left document {document_id}")
                
                # Room boşsa temizle
                if not room['users']:
                    del self.document_rooms[document_id]
    
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
                'max_turns': max_turns,
                'context': conversation_context,  # Context'i sakla
                'completed_turns': 0
            }
            
            self.socketio.emit('conversation_started', {
                'prompt': initial_prompt,
                'max_turns': max_turns,
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            })
            
            await self._execute_conversation_turns(session_id, max_turns)
            
        except Exception as e:
            # Hata durumunda temizlik
            if session_id in self.active_conversations:
                del self.active_conversations[session_id]
                
            self.socketio.emit('conversation_error', {
                'error': str(e),
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            })
    
    async def _execute_conversation_turns(self, session_id: str, turns_to_execute: int):
        """Belirtilen sayıda conversation turn'ü execute et"""
        if session_id not in self.active_conversations:
            return
        
        conversation = self.active_conversations[session_id]
        conversation_context = conversation['context']
        starting_turn = conversation['completed_turns']
        
        for turn in range(starting_turn, starting_turn + turns_to_execute):
            # Müdahale kontrolü
            intervention_context = self._check_interventions(session_id)
            
            # Turn counter güncelle
            conversation['current_turn'] = turn + 1
            
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
        
        # Tamamlanan turn sayısını güncelle
        conversation['completed_turns'] = starting_turn + turns_to_execute
        conversation['status'] = 'paused'  # Pause durumuna geç
        
        # Konuşma durakladı (tamamen bitmedi)
        self.socketio.emit('conversation_paused', {
            'total_turns': conversation['completed_turns'],
            'max_turns': conversation['max_turns'],
            'session_id': session_id,
            'can_continue': True,
            'timestamp': datetime.now().isoformat()
        })
        
        # Memory'ye kaydet
        await self._save_conversation_to_memory(session_id, conversation_context['project_goal'], conversation['completed_turns'])
    
    async def _continue_conversation(self, session_id: str, additional_turns: int):
        """Mevcut konuşmayı devam ettir"""
        if session_id not in self.active_conversations:
            raise ValueError("Devam ettirilebilir konuşma bulunamadı")
        
        conversation = self.active_conversations[session_id]
        if conversation['status'] != 'paused':
            raise ValueError("Konuşma aktif durumda değil")
        
        # Durumu aktif yap
        conversation['status'] = 'active'
        conversation['max_turns'] += additional_turns
        
        # Devam bildirimi gönder
        self.socketio.emit('conversation_continued', {
            'session_id': session_id,
            'additional_turns': additional_turns,
            'total_max_turns': conversation['max_turns'],
            'current_completed': conversation['completed_turns'],
            'timestamp': datetime.now().isoformat()
        })
        
        # Ek turn'leri execute et
        await self._execute_conversation_turns(session_id, additional_turns)
    
    def _end_conversation_permanently(self, session_id: str):
        """Konuşmayı kalıcı olarak sonlandır"""
        if session_id in self.active_conversations:
            conversation = self.active_conversations[session_id]
            del self.active_conversations[session_id]
            
            self.socketio.emit('conversation_completed', {
                'total_turns': conversation['completed_turns'],
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