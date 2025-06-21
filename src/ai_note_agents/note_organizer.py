"""
Note Organizer AI Agent
======================

Notları kategorize eden, etiketleyen ve organize eden AI agent.
"""

from typing import List, Dict, Any, Optional
import json
from datetime import datetime

from ..ai_adapters.universal_adapter import UniversalAIAdapter
from ..notes.database import NotesDatabase
from ..logger import logger


class NoteOrganizerAgent:
    """Not organizasyon AI agent'ı"""
    
    def __init__(self, ai_adapter: UniversalAIAdapter, notes_db: NotesDatabase):
        self.ai_adapter = ai_adapter
        self.notes_db = notes_db
        self.agent_id = "note_organizer"
        
        # Agent prompt şablonu
        self.system_prompt = """Sen bir not organizasyon uzmanısın. Görevlerin:
1. Notları anlamlı kategorilere ayırmak
2. Uygun etiketler önermek
3. Not hiyerarşisi oluşturmak
4. Benzer notları gruplamak
5. Arama optimizasyonu için anahtar kelimeler çıkarmak

Her zaman kullanıcının not alma alışkanlıklarına uygun öneriler yap."""
    
    def analyze_note(self, note_content: str, note_title: str, 
                    existing_tags: List[str] = None) -> Dict[str, Any]:
        """Bir notu analiz et ve organizasyon önerileri sun"""
        
        prompt = f"""{self.system_prompt}

Not Başlığı: {note_title}
Not İçeriği: {note_content[:1000]}...

Mevcut Etiketler: {', '.join(existing_tags) if existing_tags else 'Yok'}

Lütfen bu not için:
1. En uygun 3-5 etiket öner
2. Kategori belirle (teknik, kişisel, proje, toplantı, fikir, vb.)
3. 5 anahtar kelime çıkar
4. Kısa bir özet oluştur (max 100 kelime)
5. İlgili olabilecek not konularını öner

Yanıtını JSON formatında ver:
{{
    "suggested_tags": ["etiket1", "etiket2"],
    "category": "kategori",
    "keywords": ["kelime1", "kelime2"],
    "summary": "özet metni",
    "related_topics": ["konu1", "konu2"]
}}"""
        
        try:
            response = self.ai_adapter.generate_response(
                prompt,
                adapter_id=self.agent_id,
                temperature=0.3  # Daha tutarlı organizasyon için düşük temperature
            )
            
            # JSON'u parse et
            result = self._parse_json_response(response)
            
            # AI metadata olarak kaydet
            ai_metadata = {
                "organizer_analysis": result,
                "analyzed_at": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
            return {
                "success": True,
                "analysis": result,
                "ai_metadata": ai_metadata
            }
            
        except Exception as e:
            logger.error(f"Note analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "analysis": None
            }
    
    def organize_workspace(self, workspace_id: str) -> Dict[str, Any]:
        """Tüm workspace'i organize et"""
        
        try:
            # Workspace'deki tüm notları al
            notes = self.notes_db.search_notes(workspace_id, limit=100)
            
            prompt = f"""{self.system_prompt}

Aşağıda bir workspace'deki notların listesi var. Bu notları organize etmek için:
1. Ana kategoriler belirle
2. Alt kategoriler oluştur
3. Her kategori için uygun etiketler öner
4. Notları kategorilere göre grupla

Notlar:
"""
            for note in notes[:20]:  # İlk 20 not ile sınırla
                prompt += f"\n- {note.title}: {note.content[:100]}..."
            
            prompt += """

Yanıtını JSON formatında ver:
{
    "main_categories": [
        {
            "name": "kategori_adı",
            "description": "açıklama",
            "suggested_tags": ["etiket1", "etiket2"],
            "note_count": 0
        }
    ],
    "organization_suggestions": ["öneri1", "öneri2"],
    "duplicate_notes": [["not1_id", "not2_id"]]
}"""
            
            response = self.ai_adapter.generate_response(
                prompt,
                adapter_id=self.agent_id,
                temperature=0.3
            )
            
            result = self._parse_json_response(response)
            
            return {
                "success": True,
                "organization": result,
                "total_notes": len(notes),
                "analyzed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Workspace organization failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def suggest_note_connections(self, note_id: str, workspace_id: str) -> Dict[str, Any]:
        """Bir not için ilgili notları öner"""
        
        try:
            # Ana notu al
            main_note = self.notes_db.get_note(note_id, increment_view=False)
            if not main_note:
                return {"success": False, "error": "Not bulunamadı"}
            
            # Workspace'deki diğer notları al
            other_notes = self.notes_db.search_notes(
                workspace_id, 
                limit=50
            )
            # Ana notu listeden çıkar
            other_notes = [n for n in other_notes if n.id != note_id]
            
            prompt = f"""{self.system_prompt}

Ana Not:
Başlık: {main_note.title}
İçerik: {main_note.content[:500]}...
Etiketler: {[tag.name for tag in main_note.tags]}

Bu notla ilgili olabilecek notları bul:
"""
            
            for i, note in enumerate(other_notes[:20]):
                prompt += f"\n{i+1}. {note.title} (ID: {note.id})"
            
            prompt += """

En ilgili 5 notu seç ve neden ilgili olduklarını açıkla.
JSON formatında yanıtla:
{
    "related_notes": [
        {
            "note_id": "id",
            "relevance_score": 0.95,
            "reason": "ilgi nedeni"
        }
    ]
}"""
            
            response = self.ai_adapter.generate_response(
                prompt,
                adapter_id=self.agent_id,
                temperature=0.2
            )
            
            result = self._parse_json_response(response)
            
            return {
                "success": True,
                "connections": result,
                "analyzed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Note connection suggestion failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def auto_tag_notes(self, workspace_id: str, apply_tags: bool = False) -> Dict[str, Any]:
        """Workspace'deki etiketlenmemiş notları otomatik etiketle"""
        
        try:
            # Etiketlenmemiş notları bul
            notes = self.notes_db.search_notes(workspace_id, tags=[], limit=50)
            
            results = []
            for note in notes:
                if not note.tags:
                    analysis = self.analyze_note(note.content, note.title)
                    
                    if analysis["success"] and analysis["analysis"]:
                        suggested_tags = analysis["analysis"].get("suggested_tags", [])
                        
                        if apply_tags and suggested_tags:
                            # Etiketleri uygula
                            self.notes_db.update_note(
                                note.id,
                                edited_by=self.agent_id,
                                tags=suggested_tags[:3],  # En fazla 3 etiket
                                ai_metadata=analysis["ai_metadata"]
                            )
                        
                        results.append({
                            "note_id": note.id,
                            "note_title": note.title,
                            "suggested_tags": suggested_tags,
                            "applied": apply_tags
                        })
            
            return {
                "success": True,
                "processed_notes": len(results),
                "results": results,
                "tags_applied": apply_tags
            }
            
        except Exception as e:
            logger.error(f"Auto-tagging failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """AI yanıtından JSON'u çıkar"""
        try:
            # JSON bloğunu bul
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end != 0:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                # Fallback
                return {}
                
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error: {e}")
            return {} 