"""
🔄 Real-time Sync Engine - WebSocket Document Synchronization
============================================================

Real-time document senkronizasyonu:
- WebSocket event broadcasting
- Change conflict resolution
- Multi-user coordination
- AI-Human collaboration sync
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from flask_socketio import emit

from .document_state_manager import DocumentStateManager, DocumentChange, LiveDocument


class RealTimeSyncEngine:
    """Real-time Document Synchronization Engine"""
    
    def __init__(self, socketio_instance, document_manager: DocumentStateManager):
        self.socketio = socketio_instance
        self.document_manager = document_manager
        self.active_rooms: Dict[str, List[str]] = {}  # document_id -> [user_ids]
        self.event_handlers: Dict[str, Callable] = {}
        
        # Setup socket event handlers
        self._setup_socket_events()
        
        print("🔄 Real-time Sync Engine başlatıldı!")
    
    def _setup_socket_events(self):
        """Socket.IO event handler'larını ayarla"""
        
        @self.socketio.on('join_document')
        def handle_join_document(data):
            """Kullanıcı belgeye katıl"""
            document_id = data.get('document_id')
            user_id = data.get('user_id', 'anonymous')
            
            if not document_id:
                emit('error', {'message': 'Document ID gerekli'})
                return
            
            # Document'a kullanıcı ekle
            success = self.document_manager.add_user_to_document(document_id, user_id)
            
            if success:
                # Socket room'a katıl
                from flask import request
                room_name = f"document_{document_id}"
                self.socketio.server.enter_room(request.sid, room_name)
                
                # Active rooms'u güncelle
                if document_id not in self.active_rooms:
                    self.active_rooms[document_id] = []
                if user_id not in self.active_rooms[document_id]:
                    self.active_rooms[document_id].append(user_id)
                
                # Belge bilgilerini gönder
                document_info = self.document_manager.get_document_info(document_id)
                emit('document_joined', {
                    'document_id': document_id,
                    'user_id': user_id,
                    'document': document_info,
                    'active_users': self.active_rooms[document_id]
                })
                
                # Diğer kullanıcılara bildir
                self.broadcast_user_joined(document_id, user_id)
                
                print(f"👤 {user_id} belgeye katıldı: {document_id[:8]}")
            else:
                emit('error', {'message': 'Belgeye katılamadı'})
        
        @self.socketio.on('leave_document')
        def handle_leave_document(data):
            """Kullanıcı belgeden ayrıl"""
            document_id = data.get('document_id')
            user_id = data.get('user_id', 'anonymous')
            
            if document_id and user_id:
                self.remove_user_from_document(document_id, user_id)
        
        @self.socketio.on('document_change')
        def handle_document_change(data):
            """Belge değişikliği al ve uygula"""
            try:
                document_id = data.get('document_id')
                user_id = data.get('user_id')
                change_data = data.get('change')
                
                if not all([document_id, user_id, change_data]):
                    emit('error', {'message': 'Eksik veri'})
                    return
                
                # DocumentChange objesi oluştur
                change = DocumentChange(
                    change_id=self.document_manager.generate_change_id(),
                    document_id=document_id,
                    user_id=user_id,
                    change_type=change_data.get('type', 'insert'),
                    position=change_data.get('position', 0),
                    old_content=change_data.get('old_content', ''),
                    new_content=change_data.get('new_content', ''),
                    timestamp=datetime.now().isoformat()
                )
                
                # Değişikliği uygula
                success = self.document_manager.apply_change(document_id, change)
                
                if success:
                    # Tüm kullanıcılara broadcast et
                    self.broadcast_document_change(document_id, change, user_id)
                    emit('change_applied', {'change_id': change.change_id, 'success': True})
                else:
                    emit('change_failed', {'change_id': change.change_id, 'reason': 'Uygulama hatası'})
                    
            except Exception as e:
                print(f"❌ Document change error: {e}")
                emit('error', {'message': str(e)})
        
        @self.socketio.on('cursor_update')
        def handle_cursor_update(data):
            """Cursor pozisyonu güncelleme"""
            document_id = data.get('document_id')
            user_id = data.get('user_id')
            cursor_data = data.get('cursor')
            
            if all([document_id, user_id, cursor_data]):
                self.broadcast_cursor_update(document_id, user_id, cursor_data)
        
        @self.socketio.on('request_document_sync')
        def handle_sync_request(data):
            """Belge senkronizasyonu talebi"""
            document_id = data.get('document_id')
            client_version = data.get('version', 0)
            
            if document_id:
                document_info = self.document_manager.get_document_info(document_id)
                if document_info:
                    emit('document_sync', {
                        'document_id': document_id,
                        'content': document_info['content'],
                        'version': document_info['version'],
                        'last_modified': document_info['last_modified']
                    })
    
    def remove_user_from_document(self, document_id: str, user_id: str):
        """Kullanıcıyı belgeden çıkar"""
        # Document manager'dan çıkar
        self.document_manager.remove_user_from_document(document_id, user_id)
        
        # Active rooms'dan çıkar
        if document_id in self.active_rooms:
            if user_id in self.active_rooms[document_id]:
                self.active_rooms[document_id].remove(user_id)
        
        # Socket room'dan çıkar
        from flask import request
        room_name = f"document_{document_id}"
        self.socketio.server.leave_room(request.sid, room_name)
        
        # Diğer kullanıcılara bildir
        self.broadcast_user_left(document_id, user_id)
        
        print(f"👋 {user_id} belgeden ayrıldı: {document_id[:8]}")
    
    def broadcast_document_change(self, document_id: str, change: DocumentChange, exclude_user: str = None):
        """Belge değişikliğini tüm kullanıcılara broadcast et"""
        room_name = f"document_{document_id}"
        
        change_data = {
            'document_id': document_id,
            'change': {
                'change_id': change.change_id,
                'user_id': change.user_id,
                'type': change.change_type,
                'position': change.position,
                'old_content': change.old_content,
                'new_content': change.new_content,
                'timestamp': change.timestamp
            },
            'document_version': self.document_manager.get_document(document_id).version
        }
        
        # Tüm room üyelerine gönder (değişikliği yapan hariç)
        self.socketio.emit('document_changed', change_data, room=room_name, skip_sid=exclude_user)
        
        print(f"📡 Değişiklik broadcast edildi: {change.user_id} → {change.change_type}")
    
    def broadcast_user_joined(self, document_id: str, user_id: str):
        """Kullanıcı katılımını broadcast et"""
        room_name = f"document_{document_id}"
        
        self.socketio.emit('user_joined_document', {
            'document_id': document_id,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'active_users': self.active_rooms.get(document_id, [])
        }, room=room_name)
    
    def broadcast_user_left(self, document_id: str, user_id: str):
        """Kullanıcı ayrılışını broadcast et"""
        room_name = f"document_{document_id}"
        
        self.socketio.emit('user_left_document', {
            'document_id': document_id,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'active_users': self.active_rooms.get(document_id, [])
        }, room=room_name)
    
    def broadcast_cursor_update(self, document_id: str, user_id: str, cursor_data: Dict):
        """Cursor güncellemesini broadcast et"""
        room_name = f"document_{document_id}"
        
        self.socketio.emit('cursor_updated', {
            'document_id': document_id,
            'user_id': user_id,
            'cursor': cursor_data,
            'timestamp': datetime.now().isoformat()
        }, room=room_name)
    
    def broadcast_ai_activity(self, document_id: str, ai_role: str, activity_type: str, details: Dict = None):
        """AI aktivitesini broadcast et"""
        room_name = f"document_{document_id}"
        
        self.socketio.emit('ai_document_activity', {
            'document_id': document_id,
            'ai_role': ai_role,
            'activity_type': activity_type,  # typing, editing, analyzing
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }, room=room_name)
    
    def ai_document_change(self, document_id: str, ai_role: str, 
                          change_type: str, position: int, 
                          old_content: str, new_content: str) -> bool:
        """AI'dan belge değişikliği uygula"""
        try:
            # DocumentChange objesi oluştur
            change = DocumentChange(
                change_id=self.document_manager.generate_change_id(),
                document_id=document_id,
                user_id=f"ai_{ai_role}",
                change_type=change_type,
                position=position,
                old_content=old_content,
                new_content=new_content,
                timestamp=datetime.now().isoformat()
            )
            
            # Değişikliği uygula
            success = self.document_manager.apply_change(document_id, change)
            
            if success:
                # Broadcast et
                self.broadcast_document_change(document_id, change)
                
                # AI activity bildir
                self.broadcast_ai_activity(document_id, ai_role, 'edited', {
                    'change_type': change_type,
                    'content_length': len(new_content)
                })
                
                print(f"🤖 AI değişikliği uygulandı: {ai_role} → {change_type}")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ AI document change error: {e}")
            return False
    
    def get_document_room_info(self, document_id: str) -> Dict[str, Any]:
        """Document room bilgilerini getir"""
        return {
            'document_id': document_id,
            'active_users': self.active_rooms.get(document_id, []),
            'user_count': len(self.active_rooms.get(document_id, [])),
            'document_info': self.document_manager.get_document_info(document_id)
        }
    
    def list_active_rooms(self) -> List[Dict[str, Any]]:
        """Aktif document room'ları listele"""
        rooms = []
        
        for document_id, users in self.active_rooms.items():
            if users:  # Aktif kullanıcı varsa
                room_info = self.get_document_room_info(document_id)
                rooms.append(room_info)
        
        return rooms 