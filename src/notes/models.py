"""
Note Data Models
================

Not alma sistemi için veri modelleri.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import JSON
import uuid

Base = declarative_base()

# Many-to-many relationship table for notes and tags
note_tags = Table('note_tags', Base.metadata,
    Column('note_id', String, ForeignKey('notes.id')),
    Column('tag_id', String, ForeignKey('tags.id'))
)

# Many-to-many relationship table for notes and collaborators
note_collaborators = Table('note_collaborators', Base.metadata,
    Column('note_id', String, ForeignKey('notes.id')),
    Column('user_id', String)
)


class NoteWorkspace(Base):
    """Not çalışma alanı modeli"""
    __tablename__ = 'workspaces'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    description = Column(Text)
    owner_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    settings = Column(JSON, default={})
    
    # Relationships
    notes = relationship("Note", back_populates="workspace", cascade="all, delete-orphan")


class Note(Base):
    """Not modeli"""
    __tablename__ = 'notes'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(500), nullable=False)
    content = Column(Text, default='')  # Markdown/HTML içerik
    content_type = Column(String(50), default='markdown')  # markdown, html, plaintext
    
    # Hiyerarşi
    parent_id = Column(String, ForeignKey('notes.id'), nullable=True)
    workspace_id = Column(String, ForeignKey('workspaces.id'), nullable=False)
    
    # Metadata
    created_by = Column(String, nullable=False)  # user_id veya ai_agent_id
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    last_edited_by = Column(String)
    
    # Özellikler
    is_public = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    version = Column(Integer, default=1)
    
    # AI metadata
    ai_metadata = Column(JSON, default={})
    # Örnek: {
    #   "summary": "AI tarafından oluşturulan özet",
    #   "keywords": ["anahtar1", "anahtar2"],
    #   "category": "teknik",
    #   "sentiment": "positive",
    #   "ai_suggestions": [],
    #   "last_ai_analysis": "2025-01-21T10:30:00"
    # }
    
    # İstatistikler
    view_count = Column(Integer, default=0)
    edit_count = Column(Integer, default=0)
    
    # Relationships
    workspace = relationship("NoteWorkspace", back_populates="notes")
    tags = relationship("NoteTag", secondary=note_tags, back_populates="notes")
    children = relationship("Note", backref='parent', remote_side=[id])
    
    def to_dict(self) -> Dict[str, Any]:
        """Not objesini dictionary'e çevir"""
        # Tags'i güvenli şekilde al
        try:
            tags_list = [tag.name for tag in self.tags] if self.tags else []
        except Exception:
            tags_list = []
            
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'content_type': self.content_type,
            'parent_id': self.parent_id,
            'workspace_id': self.workspace_id,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_public': self.is_public,
            'is_pinned': self.is_pinned,
            'is_archived': self.is_archived,
            'version': self.version,
            'ai_metadata': self.ai_metadata,
            'tags': tags_list,
            'view_count': self.view_count,
            'edit_count': self.edit_count
        }


class NoteTag(Base):
    """Not etiketi modeli"""
    __tablename__ = 'tags'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False)
    color = Column(String(7), default='#808080')  # Hex color
    workspace_id = Column(String, ForeignKey('workspaces.id'))
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    notes = relationship("Note", secondary=note_tags, back_populates="tags")


@dataclass
class NoteVersion:
    """Not versiyonu için dataclass (gelecek özellik)"""
    note_id: str
    version: int
    content: str
    edited_by: str
    edited_at: datetime
    change_summary: Optional[str] = None
    
    
@dataclass
class NoteActivity:
    """Not aktivitesi için dataclass"""
    note_id: str
    user_id: str
    action: str  # view, edit, share, ai_analysis, etc.
    timestamp: datetime = field(default_factory=datetime.now)
    details: Optional[Dict[str, Any]] = None 