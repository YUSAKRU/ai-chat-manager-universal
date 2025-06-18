"""
Project Memory System - Konuşma Hafızası ve Görev Yönetimi
"""
import json
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid

class ProjectMemory:
    """Proje hafızası ve görev yönetimi sistemi"""
    
    def __init__(self, db_path: str = "data/project_memory.db"):
        self.db_path = db_path
        self.ensure_directory()
        self.init_database()
    
    def ensure_directory(self):
        """Veritabanı dizinini oluştur"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def init_database(self):
        """Veritabanı tablolarını oluştur"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Konuşmalar tablosu
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    initial_prompt TEXT NOT NULL,
                    status TEXT DEFAULT 'completed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    total_turns INTEGER DEFAULT 0,
                    total_interventions INTEGER DEFAULT 0,
                    metadata TEXT -- JSON format
                )
            ''')
            
            # Mesajlar tablosu
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    speaker TEXT NOT NULL, -- 'project_manager', 'lead_developer', 'director'
                    content TEXT NOT NULL,
                    turn_number INTEGER,
                    message_type TEXT DEFAULT 'response', -- 'response', 'intervention', 'system'
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT, -- JSON format
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                )
            ''')
            
            # Görevler tablosu  
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    message_id TEXT,
                    title TEXT NOT NULL,
                    description TEXT,
                    priority TEXT DEFAULT 'medium', -- 'low', 'medium', 'high', 'urgent'
                    status TEXT DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'cancelled'
                    assigned_to TEXT, -- 'project_manager', 'lead_developer', 'human'
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    due_date TIMESTAMP,
                    completed_at TIMESTAMP,
                    metadata TEXT, -- JSON format
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id),
                    FOREIGN KEY (message_id) REFERENCES messages (id)
                )
            ''')
            
            # Proje bağlamları tablosu
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS project_contexts (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    conversation_ids TEXT, -- JSON array of conversation IDs
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT -- JSON format
                )
            ''')
            
            conn.commit()
    
    def save_conversation(self, conversation_data: Dict[str, Any]) -> str:
        """Konuşmayı kaydet"""
        conversation_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Konuşma kaydı
            cursor.execute('''
                INSERT INTO conversations 
                (id, title, initial_prompt, status, completed_at, total_turns, total_interventions, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                conversation_id,
                conversation_data.get('title', 'AI Konuşması'),
                conversation_data.get('initial_prompt', ''),
                conversation_data.get('status', 'completed'),
                datetime.now() if conversation_data.get('status') == 'completed' else None,
                conversation_data.get('total_turns', 0),
                conversation_data.get('total_interventions', 0),
                json.dumps(conversation_data.get('metadata', {}))
            ))
            
            # Mesajları kaydet
            for message in conversation_data.get('messages', []):
                message_id = str(uuid.uuid4())
                cursor.execute('''
                    INSERT INTO messages 
                    (id, conversation_id, speaker, content, turn_number, message_type, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    message_id,
                    conversation_id,
                    message['speaker'],
                    message['content'],
                    message.get('turn_number'),
                    message.get('message_type', 'response'),
                    json.dumps(message.get('metadata', {}))
                ))
            
            conn.commit()
        
        return conversation_id
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Konuşma geçmişini getir"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, title, initial_prompt, status, created_at, completed_at, 
                       total_turns, total_interventions, metadata
                FROM conversations 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            conversations = []
            for row in cursor.fetchall():
                conversations.append({
                    'id': row[0],
                    'title': row[1],
                    'initial_prompt': row[2],
                    'status': row[3],
                    'created_at': row[4],
                    'completed_at': row[5],
                    'total_turns': row[6],
                    'total_interventions': row[7],
                    'metadata': json.loads(row[8]) if row[8] else {}
                })
            
            return conversations
    
    def get_conversation_details(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Konuşma detaylarını getir"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Konuşma bilgisi
            cursor.execute('''
                SELECT id, title, initial_prompt, status, created_at, completed_at,
                       total_turns, total_interventions, metadata
                FROM conversations WHERE id = ?
            ''', (conversation_id,))
            
            conversation_row = cursor.fetchone()
            if not conversation_row:
                return None
            
            conversation = {
                'id': conversation_row[0],
                'title': conversation_row[1],
                'initial_prompt': conversation_row[2],
                'status': conversation_row[3],
                'created_at': conversation_row[4],
                'completed_at': conversation_row[5],
                'total_turns': conversation_row[6],
                'total_interventions': conversation_row[7],
                'metadata': json.loads(conversation_row[8]) if conversation_row[8] else {}
            }
            
            # Mesajları getir
            cursor.execute('''
                SELECT id, speaker, content, turn_number, message_type, created_at, metadata
                FROM messages WHERE conversation_id = ?
                ORDER BY created_at ASC
            ''', (conversation_id,))
            
            messages = []
            for msg_row in cursor.fetchall():
                messages.append({
                    'id': msg_row[0],
                    'speaker': msg_row[1],
                    'content': msg_row[2],
                    'turn_number': msg_row[3],
                    'message_type': msg_row[4],
                    'created_at': msg_row[5],
                    'metadata': json.loads(msg_row[6]) if msg_row[6] else {}
                })
            
            conversation['messages'] = messages
            return conversation
    
    def create_task_from_message(self, message_id: str, task_data: Dict[str, Any]) -> str:
        """Mesajdan görev oluştur"""
        task_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tasks 
                (id, message_id, title, description, priority, assigned_to, due_date, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task_id,
                message_id,
                task_data.get('title', ''),
                task_data.get('description', ''),
                task_data.get('priority', 'medium'),
                task_data.get('assigned_to'),
                task_data.get('due_date'),
                json.dumps(task_data.get('metadata', {}))
            ))
            conn.commit()
        
        return task_id
    
    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Aktif görevleri getir"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT t.id, t.title, t.description, t.priority, t.status, t.assigned_to,
                       t.created_at, t.due_date, t.metadata, c.title as conversation_title
                FROM tasks t
                LEFT JOIN messages m ON t.message_id = m.id
                LEFT JOIN conversations c ON m.conversation_id = c.id
                WHERE t.status IN ('pending', 'in_progress')
                ORDER BY 
                    CASE t.priority 
                        WHEN 'urgent' THEN 1 
                        WHEN 'high' THEN 2 
                        WHEN 'medium' THEN 3 
                        WHEN 'low' THEN 4 
                    END,
                    t.created_at ASC
            ''')
            
            tasks = []
            for row in cursor.fetchall():
                tasks.append({
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'priority': row[3],
                    'status': row[4],
                    'assigned_to': row[5],
                    'created_at': row[6],
                    'due_date': row[7],
                    'metadata': json.loads(row[8]) if row[8] else {},
                    'conversation_title': row[9]
                })
            
            return tasks
    
    def update_task_status(self, task_id: str, status: str) -> bool:
        """Görev durumunu güncelle"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            completed_at = datetime.now() if status == 'completed' else None
            cursor.execute('''
                UPDATE tasks 
                SET status = ?, completed_at = ?
                WHERE id = ?
            ''', (status, completed_at, task_id))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def get_conversation_summary_for_context(self, conversation_id: str) -> str:
        """Konuşma özeti oluştur (yeni konuşmalarda bağlam için)"""
        conversation = self.get_conversation_details(conversation_id)
        if not conversation:
            return ""
        
        summary_parts = [
            f"Önceki Konuşma: {conversation['title']}",
            f"Başlangıç Konusu: {conversation['initial_prompt'][:200]}...",
            f"Toplam Tur: {conversation['total_turns']}"
        ]
        
        # Son birkaç mesajı ekle
        recent_messages = conversation['messages'][-4:] if len(conversation['messages']) > 4 else conversation['messages']
        for msg in recent_messages:
            speaker_name = {
                'project_manager': 'PM',
                'lead_developer': 'LD', 
                'director': 'YÖNETİCİ'
            }.get(msg['speaker'], msg['speaker'])
            
            summary_parts.append(f"{speaker_name}: {msg['content'][:150]}...")
        
        return "\n".join(summary_parts)
    
    def search_conversations(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Konuşmalarda arama yap"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT c.id, c.title, c.initial_prompt, c.created_at
                FROM conversations c
                LEFT JOIN messages m ON c.id = m.conversation_id
                WHERE c.title LIKE ? OR c.initial_prompt LIKE ? OR m.content LIKE ?
                ORDER BY c.created_at DESC
                LIMIT ?
            ''', (f'%{query}%', f'%{query}%', f'%{query}%', limit))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'title': row[1],
                    'initial_prompt': row[2],
                    'created_at': row[3]
                })
            
            return results 