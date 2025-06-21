"""
Notes Database Layer
====================

Not veritabanı işlemleri için katman.
"""

import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import create_engine, and_, or_, desc, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError

from .models import Base, Note, NoteWorkspace, NoteTag
from ..logger import logger


class NotesDatabase:
    """Not veritabanı yönetimi"""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection"""
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), '../../data/notes.db')
            
        # Dizin yoksa oluştur
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        Base.metadata.create_all(self.engine)
        
        self.SessionLocal = sessionmaker(bind=self.engine)
        logger.info(f"Notes database initialized at: {db_path}")
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    # Workspace Operations
    def create_workspace(self, name: str, owner_id: str, description: str = "") -> NoteWorkspace:
        """Yeni workspace oluştur"""
        with self.get_session() as session:
            workspace = NoteWorkspace(
                name=name,
                owner_id=owner_id,
                description=description
            )
            session.add(workspace)
            session.commit()
            session.refresh(workspace)
            logger.info(f"Workspace created: {workspace.id}")
            return workspace
    
    def get_workspace(self, workspace_id: str) -> Optional[NoteWorkspace]:
        """Workspace getir"""
        with self.get_session() as session:
            return session.query(NoteWorkspace).filter_by(id=workspace_id).first()
    
    def list_workspaces(self, owner_id: str) -> List[NoteWorkspace]:
        """Kullanıcının workspace'lerini listele"""
        with self.get_session() as session:
            return session.query(NoteWorkspace).filter_by(owner_id=owner_id).all()
    
    def get_user_workspaces(self, user_id: str) -> List[NoteWorkspace]:
        """Kullanıcının workspace'lerini getir (backward compatibility)"""
        return self.list_workspaces(user_id)
    
    def get_notes(self, workspace_id: str, limit: int = 50) -> List[Note]:
        """Workspace'deki notları getir"""
        with self.get_session() as session:
            from sqlalchemy.orm import joinedload
            
            return session.query(Note)\
                .options(joinedload(Note.tags))\
                .filter_by(workspace_id=workspace_id, is_archived=False)\
                .order_by(desc(Note.updated_at))\
                .limit(limit)\
                .all()
    
    # Note Operations
    def create_note(self, 
                   title: str,
                   workspace_id: str,
                   created_by: str,
                   content: str = "",
                   parent_id: Optional[str] = None,
                   tags: Optional[List[str]] = None) -> Note:
        """Yeni not oluştur"""
        with self.get_session() as session:
            note = Note(
                title=title,
                content=content,
                workspace_id=workspace_id,
                created_by=created_by,
                parent_id=parent_id,
                last_edited_by=created_by
            )
            
            # Etiketleri ekle
            if tags:
                for tag_name in tags:
                    tag = self._get_or_create_tag(session, tag_name, workspace_id)
                    note.tags.append(tag)
            
            session.add(note)
            session.commit()
            session.refresh(note)
            logger.info(f"Note created: {note.id} by {created_by}")
            return note
    
    def get_note(self, note_id: str, increment_view: bool = True) -> Optional[Note]:
        """Not getir"""
        with self.get_session() as session:
            from sqlalchemy.orm import joinedload
            
            # Eager load tags to prevent DetachedInstanceError
            note = session.query(Note)\
                .options(joinedload(Note.tags))\
                .filter_by(id=note_id)\
                .first()
            
            if note and increment_view:
                note.view_count += 1
                session.commit()
                session.refresh(note)
                
            return note
    
    def update_note(self,
                   note_id: str,
                   edited_by: str,
                   title: Optional[str] = None,
                   content: Optional[str] = None,
                   tags: Optional[List[str]] = None,
                   ai_metadata: Optional[Dict[str, Any]] = None,
                   is_pinned: Optional[bool] = None) -> Optional[Note]:
        """Notu güncelle"""
        with self.get_session() as session:
            from sqlalchemy.orm import joinedload
            
            note = session.query(Note)\
                .options(joinedload(Note.tags))\
                .filter_by(id=note_id)\
                .first()
            
            if not note:
                return None
            
            # Güncellemeleri uygula
            if title is not None:
                note.title = title
            if content is not None:
                note.content = content
                note.edit_count += 1
            if is_pinned is not None:
                note.is_pinned = is_pinned

            note.last_edited_by = edited_by
            note.updated_at = datetime.now()
            note.version += 1
            
            # AI metadata güncelle
            if ai_metadata:
                current_metadata = note.ai_metadata or {}
                current_metadata.update(ai_metadata)
                note.ai_metadata = current_metadata
            
            # Etiketleri güncelle
            if tags is not None:
                note.tags.clear()
                for tag_name in tags:
                    tag = self._get_or_create_tag(session, tag_name, note.workspace_id)
                    note.tags.append(tag)
            
            session.commit()
            session.refresh(note)
            logger.info(f"Note updated: {note.id} by {edited_by}")
            return note
    
    def delete_note(self, note_id: str) -> bool:
        """Notu sil"""
        with self.get_session() as session:
            note = session.query(Note).filter_by(id=note_id).first()
            
            if not note:
                return False
            
            # Alt notları da sil
            session.delete(note)
            session.commit()
            logger.info(f"Note deleted: {note_id}")
            return True
    
    def archive_note(self, note_id: str) -> bool:
        """Notu arşivle"""
        with self.get_session() as session:
            note = session.query(Note).filter_by(id=note_id).first()
            
            if not note:
                return False
                
            note.is_archived = True
            session.commit()
            return True
    
    # Search Operations
    def search_notes(self,
                    workspace_id: str,
                    query: Optional[str] = None,
                    tags: Optional[List[str]] = None,
                    parent_id: Optional[str] = None,
                    created_by: Optional[str] = None,
                    include_archived: bool = False,
                    limit: int = 50,
                    offset: int = 0) -> List[Note]:
        """Notları ara"""
        with self.get_session() as session:
            from sqlalchemy.orm import joinedload
            
            q = session.query(Note)\
                .options(joinedload(Note.tags))\
                .filter_by(workspace_id=workspace_id)
            
            # Arşivlenmiş notları dahil etme
            if not include_archived:
                q = q.filter_by(is_archived=False)
            
            # Metin araması
            if query:
                search_filter = or_(
                    Note.title.ilike(f'%{query}%'),
                    Note.content.ilike(f'%{query}%')
                )
                q = q.filter(search_filter)
            
            # Etiket filtresi
            if tags:
                q = q.join(Note.tags).filter(NoteTag.name.in_(tags))
            
            # Parent filtresi
            if parent_id is not None:
                q = q.filter_by(parent_id=parent_id)
            
            # Oluşturan filtresi
            if created_by:
                q = q.filter_by(created_by=created_by)
            
            # Sıralama ve limit
            q = q.order_by(desc(Note.updated_at))
            q = q.offset(offset).limit(limit)
            
            return q.all()
    
    def get_recent_notes(self, workspace_id: str, limit: int = 10) -> List[Note]:
        """Son güncellenen notları getir"""
        with self.get_session() as session:
            from sqlalchemy.orm import joinedload
            
            return session.query(Note)\
                .options(joinedload(Note.tags))\
                .filter_by(workspace_id=workspace_id, is_archived=False)\
                .order_by(desc(Note.updated_at))\
                .limit(limit)\
                .all()
    
    def get_pinned_notes(self, workspace_id: str) -> List[Note]:
        """Sabitlenmiş notları getir"""
        with self.get_session() as session:
            from sqlalchemy.orm import joinedload
            
            return session.query(Note)\
                .options(joinedload(Note.tags))\
                .filter_by(workspace_id=workspace_id, is_pinned=True, is_archived=False)\
                .order_by(desc(Note.updated_at))\
                .all()
    
    def get_note_tree(self, workspace_id: str, parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Not hiyerarşisini getir"""
        with self.get_session() as session:
            notes = session.query(Note)\
                .filter_by(workspace_id=workspace_id, parent_id=parent_id, is_archived=False)\
                .order_by(Note.title)\
                .all()
            
            result = []
            for note in notes:
                note_dict = note.to_dict()
                # Alt notları recursive olarak getir
                note_dict['children'] = self.get_note_tree(workspace_id, note.id)
                result.append(note_dict)
                
            return result
    
    # Tag Operations
    def _get_or_create_tag(self, session: Session, tag_name: str, workspace_id: str) -> NoteTag:
        """Etiketi getir veya oluştur"""
        tag = session.query(NoteTag).filter_by(name=tag_name, workspace_id=workspace_id).first()
        
        if not tag:
            tag = NoteTag(name=tag_name, workspace_id=workspace_id)
            session.add(tag)
            
        return tag
    
    def list_tags(self, workspace_id: str) -> List[NoteTag]:
        """Workspace'deki tüm etiketleri listele"""
        with self.get_session() as session:
            return session.query(NoteTag)\
                .filter_by(workspace_id=workspace_id)\
                .order_by(NoteTag.name)\
                .all()
    
    def get_popular_tags(self, workspace_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """En çok kullanılan etiketleri getir"""
        with self.get_session() as session:
            result = session.query(
                NoteTag.name,
                NoteTag.color,
                func.count(Note.id).label('note_count')
            )\
            .join(NoteTag.notes)\
            .filter(NoteTag.workspace_id == workspace_id)\
            .group_by(NoteTag.name, NoteTag.color)\
            .order_by(desc('note_count'))\
            .limit(limit)\
            .all()
            
            return [
                {
                    'name': tag.name,
                    'color': tag.color,
                    'note_count': tag.note_count
                }
                for tag in result
            ]
    
    # Statistics
    def get_workspace_stats(self, workspace_id: str) -> Dict[str, Any]:
        """Workspace istatistiklerini getir"""
        with self.get_session() as session:
            total_notes = session.query(func.count(Note.id))\
                .filter_by(workspace_id=workspace_id)\
                .scalar()
                
            archived_notes = session.query(func.count(Note.id))\
                .filter_by(workspace_id=workspace_id, is_archived=True)\
                .scalar()
                
            total_tags = session.query(func.count(NoteTag.id))\
                .filter_by(workspace_id=workspace_id)\
                .scalar()
                
            return {
                'total_notes': total_notes,
                'active_notes': total_notes - archived_notes,
                'archived_notes': archived_notes,
                'total_tags': total_tags
            } 