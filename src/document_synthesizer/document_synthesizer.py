"""
🎯 DocumentSynthesizer - AI-Powered Document Generation Orchestrator
==================================================================

Ana orchestrator sınıfı:
- ConversationAnalyzer ile AI analizi yapar
- TemplateEngine ile profesyonel belgeler oluşturur
- ExportEngine ile çoklu format desteği
- Document management ve metadata tracking
"""

import os
import uuid
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .conversation_analyzer import ConversationAnalyzer, ConversationInsights
from .template_engine import TemplateEngine
from .export_engine import ExportEngine


@dataclass
class DocumentMetadata:
    """Belge metadata bilgileri"""
    document_id: str
    title: str
    document_type: str  # meeting_summary, action_items, decisions_log
    session_id: str
    created_at: str
    file_paths: Dict[str, str]  # format -> file_path
    insights_summary: Dict[str, Any]


class DocumentSynthesizer:
    """AI-Powered Document Generation Orchestrator"""
    
    def __init__(self, ai_adapter=None, output_dir="generated_documents"):
        self.ai_adapter = ai_adapter
        self.output_dir = output_dir
        self.metadata_file = os.path.join(output_dir, "documents_metadata.json")
        
        # Initialize components
        self.analyzer = ConversationAnalyzer(ai_adapter)
        self.template_engine = TemplateEngine()
        self.export_engine = ExportEngine()
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Load existing metadata
        self.metadata_db = self._load_metadata()
    
    async def synthesize_meeting_summary(self, conversation_data: Dict[str, Any]) -> DocumentMetadata:
        """
        Meeting Summary belgesi oluştur
        """
        try:
            print("🧠 AI analizi başlatılıyor...")
            
            # AI ile conversation analizi
            insights = await self.analyzer.analyze_conversation(conversation_data)
            
            print(f"✅ Analiz tamamlandı: {insights.title}")
            
            # Document ID oluştur
            doc_id = self._generate_document_id("meeting_summary")
            
            # Template ile belgeler oluştur
            print("📄 Belgeler oluşturuluyor...")
            
            markdown_content = self.template_engine.generate_meeting_summary_markdown(insights)
            html_content = self.template_engine.generate_meeting_summary_html(insights)
            
            # Dosyaları kaydet
            file_paths = {}
            
            # Markdown dosyası
            md_filename = f"{doc_id}_meeting_summary.md"
            md_path = os.path.join(self.output_dir, md_filename)
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            file_paths['markdown'] = md_path
            
            # HTML dosyası  
            html_filename = f"{doc_id}_meeting_summary.html"
            html_path = os.path.join(self.output_dir, html_filename)
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            file_paths['html'] = html_path
            
            # PDF oluştur (opsiyonel)
            try:
                pdf_path = await self.export_engine.html_to_pdf(html_content, doc_id + "_meeting_summary")
                if pdf_path:
                    file_paths['pdf'] = pdf_path
            except Exception as e:
                print(f"⚠️ PDF oluşturulamadı: {e}")
            
            # Metadata oluştur
            metadata = DocumentMetadata(
                document_id=doc_id,
                title=insights.title,
                document_type="meeting_summary",
                session_id=insights.session_id,
                created_at=insights.created_at,
                file_paths=file_paths,
                insights_summary={
                    'participants_count': len(insights.participants),
                    'key_points_count': len(insights.key_points),
                    'decisions_count': len(insights.decisions),
                    'action_items_count': len(insights.action_items),
                    'total_turns': insights.total_turns,
                    'duration': insights.duration_summary
                }
            )
            
            # Metadata'yı kaydet
            self._save_document_metadata(metadata)
            
            print(f"✅ Meeting Summary oluşturuldu: {doc_id}")
            print(f"📁 Dosyalar: {list(file_paths.keys())}")
            
            return metadata
            
        except Exception as e:
            print(f"🚨 Document synthesis error: {e}")
            raise
    
    async def synthesize_action_items(self, conversation_data: Dict[str, Any]) -> DocumentMetadata:
        """
        Action Items belgesi oluştur
        """
        try:
            print("🧠 Action Items analizi başlatılıyor...")
            
            # AI analizi
            insights = await self.analyzer.analyze_conversation(conversation_data)
            
            # Document ID
            doc_id = self._generate_document_id("action_items")
            
            # Action Items template
            markdown_content = self.template_engine.generate_action_items_markdown(insights)
            
            # Dosyayı kaydet
            file_paths = {}
            md_filename = f"{doc_id}_action_items.md"
            md_path = os.path.join(self.output_dir, md_filename)
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            file_paths['markdown'] = md_path
            
            # Metadata
            metadata = DocumentMetadata(
                document_id=doc_id,
                title=f"Eylem Planı - {insights.title}",
                document_type="action_items",
                session_id=insights.session_id,
                created_at=insights.created_at,
                file_paths=file_paths,
                insights_summary={
                    'action_items_count': len(insights.action_items),
                    'high_priority': len([a for a in insights.action_items if a.priority == 'high']),
                    'medium_priority': len([a for a in insights.action_items if a.priority == 'medium']),
                    'low_priority': len([a for a in insights.action_items if a.priority == 'low'])
                }
            )
            
            self._save_document_metadata(metadata)
            
            print(f"✅ Action Items oluşturuldu: {doc_id}")
            
            return metadata
            
        except Exception as e:
            print(f"🚨 Action Items synthesis error: {e}")
            raise
    
    async def synthesize_decisions_log(self, conversation_data: Dict[str, Any]) -> DocumentMetadata:
        """
        Decisions Log belgesi oluştur
        """
        try:
            print("🧠 Decisions Log analizi başlatılıyor...")
            
            # AI analizi
            insights = await self.analyzer.analyze_conversation(conversation_data)
            
            # Document ID
            doc_id = self._generate_document_id("decisions_log")
            
            # Decisions Log template
            markdown_content = self.template_engine.generate_decisions_log_markdown(insights)
            
            # Dosyayı kaydet
            file_paths = {}
            md_filename = f"{doc_id}_decisions_log.md"
            md_path = os.path.join(self.output_dir, md_filename)
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            file_paths['markdown'] = md_path
            
            # Metadata
            metadata = DocumentMetadata(
                document_id=doc_id,
                title=f"Karar Defteri - {insights.title}",
                document_type="decisions_log",
                session_id=insights.session_id,
                created_at=insights.created_at,
                file_paths=file_paths,
                insights_summary={
                    'decisions_count': len(insights.decisions),
                    'high_confidence': len([d for d in insights.decisions if d.confidence_level > 0.8]),
                    'medium_confidence': len([d for d in insights.decisions if 0.5 <= d.confidence_level <= 0.8]),
                    'low_confidence': len([d for d in insights.decisions if d.confidence_level < 0.5])
                }
            )
            
            self._save_document_metadata(metadata)
            
            print(f"✅ Decisions Log oluşturuldu: {doc_id}")
            
            return metadata
            
        except Exception as e:
            print(f"🚨 Decisions Log synthesis error: {e}")
            raise
    
    def get_document_metadata(self, document_id: str) -> Optional[DocumentMetadata]:
        """Belge metadata'sını getir"""
        return self.metadata_db.get(document_id)
    
    def list_documents(self, document_type: Optional[str] = None) -> List[DocumentMetadata]:
        """Belgeleri listele"""
        documents = list(self.metadata_db.values())
        
        if document_type:
            documents = [doc for doc in documents if doc.document_type == document_type]
        
        # En yeni belgeler önce
        documents.sort(key=lambda x: x.created_at, reverse=True)
        
        return documents
    
    def delete_document(self, document_id: str) -> bool:
        """Belgeyi sil"""
        try:
            metadata = self.metadata_db.get(document_id)
            if not metadata:
                return False
            
            # Dosyaları sil
            for file_path in metadata.file_paths.values():
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            # Metadata'dan çıkar
            del self.metadata_db[document_id]
            self._save_metadata_db()
            
            print(f"🗑️ Belge silindi: {document_id}")
            return True
            
        except Exception as e:
            print(f"🚨 Belge silme hatası: {e}")
            return False
    
    def get_conversation_data_from_session(self, session_id: str, active_conversations: Dict) -> Optional[Dict[str, Any]]:
        """Session'dan conversation verilerini çıkar"""
        try:
            conversation = active_conversations.get(session_id)
            if not conversation:
                return None
            
            # Messages'i çıkar
            messages = conversation.get('messages', [])
            context = conversation.get('context', {})
            
            conversation_data = {
                'session_id': session_id,
                'messages': messages,
                'context': context,
                'status': conversation.get('status', 'unknown')
            }
            
            return conversation_data
            
        except Exception as e:
            print(f"🚨 Session data extraction error: {e}")
            return None
    
    # Private Methods
    
    def _generate_document_id(self, doc_type: str) -> str:
        """Unique document ID oluştur"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{doc_type}_{timestamp}_{unique_id}"
    
    def _load_metadata(self) -> Dict[str, DocumentMetadata]:
        """Metadata veritabanını yükle"""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                metadata_db = {}
                for doc_id, doc_data in data.items():
                    # JSON'dan DocumentMetadata'ya çevir
                    metadata = DocumentMetadata(**doc_data)
                    metadata_db[doc_id] = metadata
                
                return metadata_db
            else:
                return {}
                
        except Exception as e:
            print(f"⚠️ Metadata yükleme hatası: {e}")
            return {}
    
    def _save_document_metadata(self, metadata: DocumentMetadata):
        """Yeni belge metadata'sını kaydet"""
        self.metadata_db[metadata.document_id] = metadata
        self._save_metadata_db()
    
    def _save_metadata_db(self):
        """Metadata veritabanını kaydet"""
        try:
            # DocumentMetadata'yı dict'e çevir
            data = {}
            for doc_id, metadata in self.metadata_db.items():
                if hasattr(metadata, '__dict__'):
                    data[doc_id] = metadata.__dict__
                else:
                    # If it's already a dict
                    data[doc_id] = metadata
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"🚨 Metadata kaydetme hatası: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Document synthesis istatistikleri"""
        documents = list(self.metadata_db.values())
        
        stats = {
            'total_documents': len(documents),
            'document_types': {
                'meeting_summary': len([d for d in documents if getattr(d, 'document_type', None) == 'meeting_summary']),
                'action_items': len([d for d in documents if getattr(d, 'document_type', None) == 'action_items']),
                'decisions_log': len([d for d in documents if getattr(d, 'document_type', None) == 'decisions_log'])
            },
            'last_created': documents[-1].created_at if documents else None,
            'total_insights': {
                'participants': sum([getattr(d, 'insights_summary', {}).get('participants_count', 0) for d in documents]),
                'key_points': sum([getattr(d, 'insights_summary', {}).get('key_points_count', 0) for d in documents]),
                'decisions': sum([getattr(d, 'insights_summary', {}).get('decisions_count', 0) for d in documents]),
                'action_items': sum([getattr(d, 'insights_summary', {}).get('action_items_count', 0) for d in documents])
            }
        }
        
        return stats 