"""
📋 DocumentStateManager - Real-time Document State Management
============================================================

Canlı belgelerin gerçek zamanlı durumunu yönetir:
- In-memory document storage
- Version control ve change tracking
- Multi-user edit conflict resolution
- Document snapshot management
"""

import uuid
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from threading import Lock
import difflib


@dataclass
class DocumentChange:
    """Belge değişiklik kaydı"""
    change_id: str
    document_id: str
    user_id: str  # AI role_id or "human_user"
    change_type: str  # insert, delete, replace, format
    position: int
    old_content: str
    new_content: str
    timestamp: str
    applied: bool = False


@dataclass
class DocumentCursor:
    """Kullanıcı/AI cursor pozisyonu"""
    user_id: str
    position: int
    selection_start: int
    selection_end: int
    timestamp: str
    is_typing: bool = False


@dataclass
class LiveDocument:
    """Canlı belge veri yapısı"""
    document_id: str
    title: str
    content: str
    document_type: str  # markdown, rich_text, structured
    created_by: str
    created_at: str
    last_modified: str
    version: int
    active_users: List[str]
    changes_history: List[DocumentChange]
    cursors: Dict[str, DocumentCursor]
    is_locked: bool = False
    metadata: Dict[str, Any] = None


class DocumentStateManager:
    """Real-time Document State Management Engine"""
    
    def __init__(self):
        self.documents: Dict[str, LiveDocument] = {}
        self.locks: Dict[str, Lock] = {}
        self.change_queue: List[DocumentChange] = []
        self.max_history_size = 1000
        
    def create_document(self, title: str, content: str = "", 
                       document_type: str = "markdown", 
                       created_by: str = "system") -> str:
        """Yeni canlı belge oluştur"""
        document_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        document = LiveDocument(
            document_id=document_id,
            title=title,
            content=content,
            document_type=document_type,
            created_by=created_by,
            created_at=now,
            last_modified=now,
            version=1,
            active_users=[],
            changes_history=[],
            cursors={},
            metadata={}
        )
        
        self.documents[document_id] = document
        self.locks[document_id] = Lock()
        
        print(f"📄 Canlı belge oluşturuldu: {title} ({document_id[:8]})")
        return document_id
    
    def get_document(self, document_id: str) -> Optional[LiveDocument]:
        """Belge bilgilerini getir"""
        return self.documents.get(document_id)
    
    def add_user_to_document(self, document_id: str, user_id: str) -> bool:
        """Kullanıcıyı belgeye ekle"""
        if document_id not in self.documents:
            return False
            
        with self.locks[document_id]:
            document = self.documents[document_id]
            if user_id not in document.active_users:
                document.active_users.append(user_id)
                document.last_modified = datetime.now().isoformat()
                print(f"👤 {user_id} belgeye katıldı: {document.title}")
            
        return True
    
    def remove_user_from_document(self, document_id: str, user_id: str) -> bool:
        """Kullanıcıyı belgeden çıkar"""
        if document_id not in self.documents:
            return False
            
        with self.locks[document_id]:
            document = self.documents[document_id]
            if user_id in document.active_users:
                document.active_users.remove(user_id)
                # Cursor'ını da temizle
                if user_id in document.cursors:
                    del document.cursors[user_id]
                document.last_modified = datetime.now().isoformat()
                print(f"👋 {user_id} belgeden ayrıldı: {document.title}")
        
        return True
    
    def apply_change(self, document_id: str, change: DocumentChange) -> bool:
        """Belge değişikliğini uygula"""
        if document_id not in self.documents:
            return False
        
        with self.locks[document_id]:
            document = self.documents[document_id]
            
            if document.is_locked:
                print(f"⚠️ Belge kilitli, değişiklik uygulanamadı: {document_id}")
                return False
            
            try:
                # Change type'a göre işlem yap
                if change.change_type == "insert":
                    new_content = (
                        document.content[:change.position] + 
                        change.new_content + 
                        document.content[change.position:]
                    )
                elif change.change_type == "delete":
                    # Metin silme
                    end_pos = change.position + len(change.old_content)
                    new_content = (
                        document.content[:change.position] + 
                        document.content[end_pos:]
                    )
                elif change.change_type == "replace":
                    end_pos = change.position + len(change.old_content)
                    new_content = (
                        document.content[:change.position] + 
                        change.new_content + 
                        document.content[end_pos:]
                    )
                else:
                    print(f"❌ Bilinmeyen change type: {change.change_type}")
                    return False
                
                # İçeriği güncelle
                document.content = new_content
                document.version += 1
                document.last_modified = datetime.now().isoformat()
                
                # Change'i history'ye ekle
                change.applied = True
                document.changes_history.append(change)
                
                # History size limitini kontrol et
                if len(document.changes_history) > self.max_history_size:
                    document.changes_history = document.changes_history[-self.max_history_size:]
                
                print(f"✅ Değişiklik uygulandı: {change.user_id} → {change.change_type}")
                return True
                
            except Exception as e:
                print(f"❌ Change uygulama hatası: {e}")
                return False
    
    def update_cursor(self, document_id: str, cursor: DocumentCursor) -> bool:
        """Kullanıcı cursor pozisyonunu güncelle"""
        if document_id not in self.documents:
            return False
        
        with self.locks[document_id]:
            document = self.documents[document_id]
            document.cursors[cursor.user_id] = cursor
            
        return True
    
    def get_document_content(self, document_id: str) -> Optional[str]:
        """Belge içeriğini getir"""
        if document_id not in self.documents:
            return None
        return self.documents[document_id].content
    
    def get_document_info(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Belge bilgilerini dict olarak getir"""
        document = self.get_document(document_id)
        if not document:
            return None
        
        return {
            'document_id': document.document_id,
            'title': document.title,
            'content': document.content,
            'document_type': document.document_type,
            'version': document.version,
            'active_users': document.active_users,
            'last_modified': document.last_modified,
            'is_locked': document.is_locked,
            'active_cursors': len(document.cursors),
            'total_changes': len(document.changes_history)
        }
    
    def lock_document(self, document_id: str, locked_by: str) -> bool:
        """Belgeyi kilitle (AI işlemi sırasında)"""
        if document_id not in self.documents:
            return False
        
        with self.locks[document_id]:
            document = self.documents[document_id]
            document.is_locked = True
            document.metadata = document.metadata or {}
            document.metadata['locked_by'] = locked_by
            document.metadata['locked_at'] = datetime.now().isoformat()
            
        print(f"🔒 Belge kilitlendi: {locked_by}")
        return True
    
    def unlock_document(self, document_id: str) -> bool:
        """Belge kilidini aç"""
        if document_id not in self.documents:
            return False
        
        with self.locks[document_id]:
            document = self.documents[document_id]
            document.is_locked = False
            if document.metadata:
                document.metadata.pop('locked_by', None)
                document.metadata.pop('locked_at', None)
        
        print(f"🔓 Belge kilidi açıldı")
        return True
    
    def get_changes_since_version(self, document_id: str, since_version: int) -> List[DocumentChange]:
        """Belirli versiyondan sonraki değişiklikleri getir"""
        if document_id not in self.documents:
            return []
        
        document = self.documents[document_id]
        return [
            change for change in document.changes_history 
            if change.applied and change.timestamp > since_version
        ]
    
    def create_document_snapshot(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Belge anlık görüntüsü oluştur"""
        document = self.get_document(document_id)
        if not document:
            return None
        
        snapshot = {
            'document_id': document.document_id,
            'title': document.title,
            'content': document.content,
            'version': document.version,
            'snapshot_time': datetime.now().isoformat(),
            'active_users': document.active_users.copy(),
            'content_length': len(document.content),
            'total_changes': len(document.changes_history)
        }
        
        return snapshot
    
    def list_active_documents(self) -> List[Dict[str, Any]]:
        """Aktif belgeleri listele"""
        documents = []
        
        for doc_id, document in self.documents.items():
            if document.active_users:  # Aktif kullanıcı varsa
                doc_info = {
                    'document_id': doc_id,
                    'title': document.title,
                    'document_type': document.document_type,
                    'active_users': len(document.active_users),
                    'version': document.version,
                    'last_modified': document.last_modified,
                    'is_locked': document.is_locked
                }
                documents.append(doc_info)
        
        return documents
    
    def generate_change_id(self) -> str:
        """Unique change ID oluştur"""
        timestamp = str(int(time.time() * 1000))
        unique_id = str(uuid.uuid4())[:8]
        return f"change_{timestamp}_{unique_id}"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Document state manager istatistikleri"""
        total_documents = len(self.documents)
        active_documents = len([d for d in self.documents.values() if d.active_users])
        total_active_users = sum(len(d.active_users) for d in self.documents.values())
        total_changes = sum(len(d.changes_history) for d in self.documents.values())
        
        return {
            'total_documents': total_documents,
            'active_documents': active_documents,
            'total_active_users': total_active_users,
            'total_changes': total_changes,
            'avg_changes_per_doc': total_changes / max(total_documents, 1)
        } 