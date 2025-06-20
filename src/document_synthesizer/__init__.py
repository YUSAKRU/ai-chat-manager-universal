"""
🧠 AI Document Synthesizer
==========================

Yapay Zeka Destekli Belge Sentezleyici
AI konuşmalarını akıllıca analiz edip profesyonel belgeler üretir.

Modüller:
- ConversationAnalyzer: AI-powered conversation intelligence
- DocumentSynthesizer: Intelligent document generation  
- TemplateEngine: Professional document templates
- ExportEngine: Multi-format export (PDF, Word, MD)
"""

from .conversation_analyzer import ConversationAnalyzer
from .document_synthesizer import DocumentSynthesizer  
from .template_engine import TemplateEngine
from .export_engine import ExportEngine

__version__ = "1.0.0"
__author__ = "AI Chrome Chat Manager Team"

__all__ = [
    'ConversationAnalyzer',
    'DocumentSynthesizer', 
    'TemplateEngine',
    'ExportEngine'
] 