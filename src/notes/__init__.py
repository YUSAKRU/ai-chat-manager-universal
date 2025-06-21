"""
AI-Powered Note Taking System
=============================

Bu modül, AI destekli not alma sisteminin temel bileşenlerini içerir.
"""

from .models import Note, NoteWorkspace, NoteTag
from .database import NotesDatabase
from .api import notes_blueprint

__version__ = "1.0.0"
__author__ = "AI Chrome Chat Manager Team"

__all__ = [
    'Note',
    'NoteWorkspace', 
    'NoteTag',
    'NotesDatabase',
    'notes_blueprint'
] 