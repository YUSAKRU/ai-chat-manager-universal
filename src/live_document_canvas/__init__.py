"""
🎨 Live Document Canvas - Real-time Collaborative Document Editing
===============================================================

Gerçek zamanlı, çok kullanıcılı (AI + İnsan) belge düzenleme sistemi:
- Real-time sync engine
- Interactive canvas interface  
- AI-aware document collaboration
- Floating window management
"""

from .document_state_manager import DocumentStateManager
from .real_time_sync_engine import RealTimeSyncEngine
from .canvas_interface import CanvasInterface
from .ai_document_integration import AIDocumentIntegration

__version__ = "1.0.0"
__author__ = "AI Chrome Chat Manager Team"

__all__ = [
    'DocumentStateManager',
    'RealTimeSyncEngine', 
    'CanvasInterface',
    'AIDocumentIntegration'
] 