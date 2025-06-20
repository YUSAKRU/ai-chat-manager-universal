"""
🤖 AI Document Integration - AI-Aware Document Collaboration
=========================================================

AI'ların belgeleri anlayıp düzenleyebilmesi için:
- AI prompt enhancement with document context
- Intelligent document editing commands
- AI collaboration coordination
- Context-aware AI responses
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from .document_state_manager import DocumentStateManager, DocumentChange
from .real_time_sync_engine import RealTimeSyncEngine


class AIDocumentCommand:
    """AI belge düzenleme komutu"""
    
    def __init__(self, command_type: str, target: str, content: str, position: Optional[int] = None):
        self.command_type = command_type  # append, prepend, replace_section, insert_at
        self.target = target  # section_name, line_number, "end", "beginning"
        self.content = content
        self.position = position
        self.timestamp = datetime.now().isoformat()


class AIDocumentIntegration:
    """AI-Document Collaboration Intelligence Layer"""
    
    def __init__(self, document_manager: DocumentStateManager, sync_engine: RealTimeSyncEngine):
        self.document_manager = document_manager
        self.sync_engine = sync_engine
        
        # AI command patterns
        self.command_patterns = {
            'append_to_document': r'(?i)belgeye\s+ekle[:\s]+(.+)',
            'prepend_to_document': r'(?i)belgenin\s+başına\s+ekle[:\s]+(.+)',
            'replace_section': r'(?i)(\w+)\s+bölümünü\s+değiştir[:\s]+(.+)',
            'insert_at_position': r'(?i)(\d+)\.\s+satıra\s+ekle[:\s]+(.+)',
            'create_new_section': r'(?i)yeni\s+bölüm\s+oluştur[:\s]+(.+)',
            'update_section': r'(?i)(.+)\s+bölümünü\s+güncelle[:\s]+(.+)'
        }
        
        print("🤖 AI Document Integration başlatıldı!")
    
    def enhance_ai_prompt_with_document_context(self, base_prompt: str, document_id: str, ai_role: str) -> str:
        """AI prompt'una belge context'ini ekle"""
        document = self.document_manager.get_document(document_id)
        
        if not document:
            return base_prompt
        
        # Belge bilgilerini hazırla
        document_context = f"""
📄 CANLI BELGE CONTEXT:
======================

Belge Başlığı: {document.title}
Belge Türü: {document.document_type}
Güncel Sürüm: v{document.version}
Aktif Kullanıcılar: {', '.join(document.active_users)}
Son Güncelleme: {document.last_modified}

📝 GÜNCEL BELGE İÇERİĞİ:
========================
{document.content}

🎯 BELGE DÜZENLEME YETKİLERİNİZ:
===============================
Aşağıdaki komutları kullanarak belgeyi güncelleyebilirsiniz:

1. "Belgeye ekle: [içerik]" - Belgenin sonuna içerik ekler
2. "Belgenin başına ekle: [içerik]" - Belgenin başına içerik ekler  
3. "[Bölüm] bölümünü değiştir: [yeni içerik]" - Belirli bölümü değiştirir
4. "[Satır no]. satıra ekle: [içerik]" - Belirli satıra içerik ekler
5. "Yeni bölüm oluştur: [başlık ve içerik]" - Yeni bölüm oluşturur

💡 ÖNEMLİ: Belge düzenleme komutlarınız gerçek zamanlı olarak uygulanacak ve diğer kullanıcılar tarafından görülecektir.

📋 MEVCUT GÖREV:
===============
"""
        
        # Role-specific instructions
        role_instructions = {
            'project_manager': """
Proje yöneticisi olarak:
- Proje planları ve görev listeleri oluşturun
- Karar noktalarını belgelendirin
- Milestone'ları takip edin
- Toplantı notları ve eylem maddeleri ekleyin
            """,
            'lead_developer': """
Teknik lider olarak:
- Teknik spesifikasyonları yazın
- Kod yapısı ve mimari kararları belgelendirin
- API dokümantasyonu oluşturun
- Teknik görevleri detaylandırın
            """,
            'boss': """
Director olarak:
- Stratejik kararları onaylayın
- Proje yönünü belirleyin
- Kaynak planlaması yapın
- Kalite kontrolü sağlayın
            """
        }
        
        enhanced_prompt = f"""
{base_prompt}

{document_context}

{role_instructions.get(ai_role, '')}

📌 Şimdi yukarıdaki görevinizi yerine getirirken, aynı zamanda canlı belgeyi uygun şekilde güncelleyin.
"""
        
        return enhanced_prompt
    
    def parse_ai_response_for_document_commands(self, ai_response: str, ai_role: str) -> List[AIDocumentCommand]:
        """AI yanıtından belge düzenleme komutlarını çıkar"""
        commands = []
        
        # Her pattern için kontrol et
        for command_type, pattern in self.command_patterns.items():
            matches = re.finditer(pattern, ai_response, re.MULTILINE)
            
            for match in matches:
                if command_type == 'append_to_document':
                    content = match.group(1).strip()
                    commands.append(AIDocumentCommand('append', 'end', content))
                    
                elif command_type == 'prepend_to_document':
                    content = match.group(1).strip()
                    commands.append(AIDocumentCommand('prepend', 'beginning', content))
                    
                elif command_type == 'replace_section':
                    section = match.group(1).strip()
                    content = match.group(2).strip()
                    commands.append(AIDocumentCommand('replace_section', section, content))
                    
                elif command_type == 'insert_at_position':
                    line_number = int(match.group(1))
                    content = match.group(2).strip()
                    commands.append(AIDocumentCommand('insert_at', str(line_number), content, line_number))
                    
                elif command_type == 'create_new_section':
                    content = match.group(1).strip()
                    commands.append(AIDocumentCommand('append', 'end', f"\n\n## {content}\n\n"))
                    
                elif command_type == 'update_section':
                    section = match.group(1).strip()
                    content = match.group(2).strip()
                    commands.append(AIDocumentCommand('replace_section', section, content))
        
        if commands:
            print(f"🎯 {len(commands)} belge komutu bulundu: {ai_role}")
            
        return commands
    
    def execute_ai_document_commands(self, document_id: str, ai_role: str, commands: List[AIDocumentCommand]) -> List[bool]:
        """AI belge komutlarını uygula"""
        results = []
        
        for command in commands:
            try:
                success = self._execute_single_command(document_id, ai_role, command)
                results.append(success)
                
                if success:
                    print(f"✅ AI komutu uygulandı: {ai_role} → {command.command_type}")
                else:
                    print(f"❌ AI komutu başarısız: {ai_role} → {command.command_type}")
                    
            except Exception as e:
                print(f"❌ AI komut hatası: {e}")
                results.append(False)
        
        return results
    
    def _execute_single_command(self, document_id: str, ai_role: str, command: AIDocumentCommand) -> bool:
        """Tek bir AI komutunu uygula"""
        document = self.document_manager.get_document(document_id)
        if not document:
            return False
        
        current_content = document.content
        
        # Command type'a göre pozisyon ve content'i belirle
        if command.command_type == 'append':
            position = len(current_content)
            new_content = f"\n{command.content}"
            old_content = ""
            
        elif command.command_type == 'prepend':
            position = 0
            new_content = f"{command.content}\n"
            old_content = ""
            
        elif command.command_type == 'insert_at':
            lines = current_content.split('\n')
            line_number = command.position - 1  # 0-based index
            
            if 0 <= line_number <= len(lines):
                position = sum(len(line) + 1 for line in lines[:line_number])
                new_content = f"{command.content}\n"
                old_content = ""
            else:
                return False
                
        elif command.command_type == 'replace_section':
            # Section'ı bul ve değiştir
            section_pattern = rf'(?i)#+\s*{re.escape(command.target)}.*?(?=\n#+|\Z)'
            match = re.search(section_pattern, current_content, re.DOTALL)
            
            if match:
                position = match.start()
                old_content = match.group(0)
                new_content = f"## {command.target}\n\n{command.content}"
            else:
                # Section bulunamadı, sona ekle
                position = len(current_content)
                old_content = ""
                new_content = f"\n\n## {command.target}\n\n{command.content}"
        else:
            return False
        
        # Real-time sync engine ile değişikliği uygula
        success = self.sync_engine.ai_document_change(
            document_id=document_id,
            ai_role=ai_role,
            change_type='insert' if not old_content else 'replace',
            position=position,
            old_content=old_content,
            new_content=new_content
        )
        
        return success
    
    def process_ai_conversation_message(self, document_id: str, ai_role: str, 
                                      ai_message: str, conversation_context: Dict) -> Dict[str, Any]:
        """AI konuşma mesajını işle ve belge komutlarını uygula"""
        result = {
            'ai_role': ai_role,
            'message': ai_message,
            'document_commands_found': 0,
            'document_commands_executed': 0,
            'document_updated': False,
            'timestamp': datetime.now().isoformat()
        }
        
        # AI yanıtından belge komutlarını çıkar
        commands = self.parse_ai_response_for_document_commands(ai_message, ai_role)
        result['document_commands_found'] = len(commands)
        
        if commands:
            # Komutları uygula
            execution_results = self.execute_ai_document_commands(document_id, ai_role, commands)
            successful_commands = sum(execution_results)
            
            result['document_commands_executed'] = successful_commands
            result['document_updated'] = successful_commands > 0
            
            if successful_commands > 0:
                # Document güncellendiğini bildir
                self.sync_engine.broadcast_ai_activity(
                    document_id, ai_role, 'document_updated', 
                    {
                        'commands_executed': successful_commands,
                        'total_commands': len(commands)
                    }
                )
        
        return result
    
    def get_document_summary_for_ai(self, document_id: str) -> str:
        """AI için belge özeti oluştur"""
        document = self.document_manager.get_document(document_id)
        
        if not document:
            return "Belge bulunamadı."
        
        content_lines = document.content.split('\n')
        content_length = len(document.content)
        word_count = len(document.content.split())
        
        # Başlıkları çıkar
        headers = [line for line in content_lines if line.startswith('#')]
        
        summary = f"""
📄 BELGE ÖZETİ: {document.title}
===============================

📊 İstatistikler:
- Toplam karakter: {content_length}
- Toplam kelime: {word_count}
- Toplam satır: {len(content_lines)}
- Sürüm: v{document.version}

📋 Başlıklar ({len(headers)}):
{chr(10).join(f"  • {header}" for header in headers[:10])}
{('...' if len(headers) > 10 else '')}

👥 Aktif Kullanıcılar: {', '.join(document.active_users) if document.active_users else 'Kimse aktif değil'}

⏰ Son Güncelleme: {document.last_modified}
"""
        
        return summary.strip()
    
    def create_collaborative_document(self, title: str, initial_content: str, 
                                    document_type: str = "markdown", 
                                    session_id: str = None) -> str:
        """İş birlikçi belge oluştur"""
        document_id = self.document_manager.create_document(
            title=title,
            content=initial_content,
            document_type=document_type,
            created_by=f"session_{session_id}" if session_id else "system"
        )
        
        print(f"🎨 İş birlikçi belge oluşturuldu: {title}")
        
        return document_id
    
    def get_ai_collaboration_status(self, document_id: str) -> Dict[str, Any]:
        """AI iş birliği durumunu getir"""
        document = self.document_manager.get_document(document_id)
        room_info = self.sync_engine.get_document_room_info(document_id)
        
        if not document:
            return {'error': 'Belge bulunamadı'}
        
        ai_users = [user for user in document.active_users if user.startswith('ai_')]
        human_users = [user for user in document.active_users if not user.startswith('ai_')]
        
        return {
            'document_id': document_id,
            'title': document.title,
            'total_active_users': len(document.active_users),
            'ai_collaborators': len(ai_users),
            'human_collaborators': len(human_users),
            'document_version': document.version,
            'last_ai_change': self._get_last_ai_change_time(document),
            'collaboration_active': len(document.active_users) > 1,
            'document_locked': document.is_locked
        }
    
    def _get_last_ai_change_time(self, document) -> Optional[str]:
        """Son AI değişiklik zamanını getir"""
        ai_changes = [
            change for change in document.changes_history 
            if change.user_id.startswith('ai_') and change.applied
        ]
        
        if ai_changes:
            return ai_changes[-1].timestamp
        
        return None 