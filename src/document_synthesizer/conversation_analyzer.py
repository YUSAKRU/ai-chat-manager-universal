"""
🧠 ConversationAnalyzer - AI-Powered Conversation Intelligence
============================================================

Yapay zeka ile konuşmaları analiz eder ve temel bilgileri çıkarır:
- Toplantı konusu ve amacı
- Katılımcı rolleri ve katkıları
- Ana tartışma noktaları
- Alınan kararlar 
- Eylem maddeleri ve sorumlular
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class ConversationParticipant:
    """Konuşma katılımcısı bilgileri"""
    role: str
    display_name: str
    message_count: int
    key_contributions: List[str]


@dataclass 
class DecisionItem:
    """Alınan karar bilgileri"""
    decision: str
    context: str
    participants_involved: List[str]
    confidence_level: float  # 0.0-1.0


@dataclass
class ActionItem:
    """Eylem maddesi bilgileri"""
    action: str
    assignee: str
    priority: str  # high, medium, low
    deadline: Optional[str]
    context: str


@dataclass
class ConversationInsights:
    """Konuşma analiz sonuçları"""
    session_id: str
    title: str
    purpose: str
    participants: List[ConversationParticipant]
    key_points: List[str]
    decisions: List[DecisionItem]
    action_items: List[ActionItem]
    total_turns: int
    duration_summary: str
    created_at: str


class ConversationAnalyzer:
    """AI-Powered Conversation Analysis Engine"""
    
    def __init__(self, ai_adapter=None):
        self.ai_adapter = ai_adapter
        self.analysis_model = "gemini-2.5-flash"  # Default analysis model
        
    async def analyze_conversation(self, conversation_data: Dict[str, Any]) -> ConversationInsights:
        """
        Konuşmayı AI ile analiz et ve yapılandırılmış insights çıkar
        """
        try:
            # Conversation verilerini hazırla
            messages = conversation_data.get('messages', [])
            session_id = conversation_data.get('session_id', 'unknown')
            context = conversation_data.get('context', {})
            
            if not messages:
                return self._create_empty_insights(session_id)
            
            # AI ile analiz yap
            conversation_text = self._prepare_conversation_text(messages)
            
            # Multi-step AI analysis
            insights = await self._perform_ai_analysis(conversation_text, context)
            
            # Structured data oluştur
            return ConversationInsights(
                session_id=session_id,
                title=insights.get('title', 'AI Konuşması'),
                purpose=insights.get('purpose', 'Proje planlaması ve tartışması'),
                participants=self._extract_participants(messages, insights),
                key_points=insights.get('key_points', []),
                decisions=self._extract_decisions(insights),
                action_items=self._extract_action_items(insights),
                total_turns=len(messages),
                duration_summary=self._calculate_duration_summary(messages),
                created_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            print(f"🚨 Conversation analysis error: {e}")
            return self._create_empty_insights(session_id)
    
    async def _perform_ai_analysis(self, conversation_text: str, context: Dict) -> Dict[str, Any]:
        """AI ile konuşma analizi yap"""
        
        analysis_prompt = f"""Sen uzman bir toplantı analisti ve belge sentezleyicisisin. Aşağıdaki AI konuşmasını analiz et:

🎯 PROJE CONTEXT: {context.get('project_goal', 'AI destekli proje geliştirme')}

📋 KONUŞMA İÇERİĞİ:
{conversation_text}

Lütfen bu konuşmayı analiz et ve aşağıdaki JSON formatında yanıt ver:

{{
    "title": "Konuşmanın özetleyici başlığı (maksimum 8 kelime)",
    "purpose": "Konuşmanın ana amacı ve hedefi (2-3 cümle)",
    "key_points": [
        "İlk ana tartışma noktası",
        "İkinci önemli nokta", 
        "Üçüncü kritik konu",
        "Dördüncü kilit fikir",
        "Beşinci öne çıkan nokta"
    ],
    "decisions_raw": [
        {{
            "decision": "Alınan net karar açıklaması",
            "context": "Kararın alınma sebebi ve bağlamı",
            "participants": ["project_manager", "lead_developer"],
            "confidence": 0.9
        }}
    ],
    "action_items_raw": [
        {{
            "action": "Yapılacak iş tanımı",
            "assignee": "project_manager",
            "priority": "high",
            "context": "Bu işin yapılma sebebi"
        }}
    ],
    "participant_insights": {{
        "project_manager": {{
            "contribution": "PM'in ana katkıları özeti",
            "key_points": ["PM'in 1. önemli noktası", "PM'in 2. önemli noktası"]
        }},
        "lead_developer": {{
            "contribution": "Developer'ın ana katkıları özeti", 
            "key_points": ["Dev'in 1. teknik noktası", "Dev'in 2. teknik noktası"]
        }}
    }}
}}

ÖNEMLİ: Sadece JSON formatında yanıt ver, başka açıklama ekleme."""

        try:
            if not self.ai_adapter:
                return self._get_fallback_analysis()
                
            # AI'dan analiz al
            response = await self.ai_adapter.send_message(
                "boss",  # Analysis için boss role kullan
                analysis_prompt,
                "Conversation Analysis"
            )
            
            if response and response.content:
                # JSON parse et
                clean_json = self._extract_json_from_response(response.content)
                return json.loads(clean_json)
            else:
                return self._get_fallback_analysis()
                
        except Exception as e:
            print(f"⚠️ AI analysis failed: {e}")
            return self._get_fallback_analysis()
    
    def _prepare_conversation_text(self, messages: List[Dict]) -> str:
        """Konuşma mesajlarını AI analizi için hazırla"""
        formatted_messages = []
        
        for i, msg in enumerate(messages, 1):
            speaker = msg.get('speaker', 'Unknown')
            content = msg.get('content', msg.get('message', ''))
            turn = msg.get('turn', i)
            
            # Speaker name'i temizle
            speaker_name = self._clean_speaker_name(speaker)
            
            formatted_messages.append(f"TUR {turn} - {speaker_name}:\n{content}\n")
        
        return "\n".join(formatted_messages)
    
    def _clean_speaker_name(self, speaker: str) -> str:
        """Speaker adını temizle ve düzenle"""
        role_mapping = {
            'project_manager': 'Proje Yöneticisi',
            'lead_developer': 'Lead Developer',
            'boss': 'Director',
            'pm': 'Proje Yöneticisi',
            'dev': 'Lead Developer',
            'director': 'Director'
        }
        return role_mapping.get(speaker.lower(), speaker)
    
    def _extract_participants(self, messages: List[Dict], insights: Dict) -> List[ConversationParticipant]:
        """Katılımcı bilgilerini çıkar"""
        participants = {}
        
        # Mesajlardan katılımcıları say
        for msg in messages:
            speaker = msg.get('speaker', 'Unknown')
            if speaker not in participants:
                participants[speaker] = {
                    'message_count': 0,
                    'contributions': []
                }
            participants[speaker]['message_count'] += 1
        
        # AI insights'tan katkıları al
        participant_insights = insights.get('participant_insights', {})
        
        result = []
        for speaker, data in participants.items():
            speaker_insights = participant_insights.get(speaker, {})
            
            participant = ConversationParticipant(
                role=speaker,
                display_name=self._clean_speaker_name(speaker),
                message_count=data['message_count'],
                key_contributions=speaker_insights.get('key_points', [])
            )
            result.append(participant)
        
        return result
    
    def _extract_decisions(self, insights: Dict) -> List[DecisionItem]:
        """Karar maddelerini çıkar"""
        decisions_raw = insights.get('decisions_raw', [])
        decisions = []
        
        for decision_data in decisions_raw:
            decision = DecisionItem(
                decision=decision_data.get('decision', ''),
                context=decision_data.get('context', ''),
                participants_involved=decision_data.get('participants', []),
                confidence_level=decision_data.get('confidence', 0.8)
            )
            decisions.append(decision)
        
        return decisions
    
    def _extract_action_items(self, insights: Dict) -> List[ActionItem]:
        """Eylem maddelerini çıkar"""
        action_items_raw = insights.get('action_items_raw', [])
        action_items = []
        
        for item_data in action_items_raw:
            action_item = ActionItem(
                action=item_data.get('action', ''),
                assignee=self._clean_speaker_name(item_data.get('assignee', '')),
                priority=item_data.get('priority', 'medium'),
                deadline=item_data.get('deadline'),
                context=item_data.get('context', '')
            )
            action_items.append(action_item)
        
        return action_items
    
    def _calculate_duration_summary(self, messages: List[Dict]) -> str:
        """Konuşma süresini hesapla"""
        if not messages:
            return "Bilinmiyor"
        
        try:
            first_time = messages[0].get('timestamp')
            last_time = messages[-1].get('timestamp')
            
            if first_time and last_time:
                # Timestamp parse et
                first_dt = datetime.fromisoformat(first_time.replace('Z', '+00:00'))
                last_dt = datetime.fromisoformat(last_time.replace('Z', '+00:00'))
                
                duration = last_dt - first_dt
                minutes = int(duration.total_seconds() / 60)
                
                if minutes < 1:
                    return "1 dakikadan az"
                elif minutes < 60:
                    return f"{minutes} dakika"
                else:
                    hours = minutes // 60
                    remaining_minutes = minutes % 60
                    return f"{hours} saat {remaining_minutes} dakika"
            
        except Exception as e:
            print(f"⚠️ Duration calculation error: {e}")
        
        return f"Yaklaşık {len(messages)} tur konuşma"
    
    def _extract_json_from_response(self, response_text: str) -> str:
        """AI yanıtından JSON'u çıkar"""
        # JSON code block'u ara
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            return json_match.group(1).strip()
        
        # Direk JSON ara
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            return json_match.group(0).strip()
        
        # Fallback
        return "{}"
    
    def _get_fallback_analysis(self) -> Dict[str, Any]:
        """AI analizi başarısız olduğunda kullanılacak fallback"""
        return {
            "title": "AI Konuşması",
            "purpose": "Proje planlaması ve teknik tartışma",
            "key_points": [
                "Proje gereksinimleri tartışıldı",
                "Teknik yaklaşım belirlendi", 
                "Gelişim planı oluşturuldu"
            ],
            "decisions_raw": [],
            "action_items_raw": [],
            "participant_insights": {}
        }
    
    def _create_empty_insights(self, session_id: str) -> ConversationInsights:
        """Boş insights oluştur"""
        return ConversationInsights(
            session_id=session_id,
            title="Boş Konuşma",
            purpose="Henüz analiz edilemeyen konuşma",
            participants=[],
            key_points=[],
            decisions=[],
            action_items=[],
            total_turns=0,
            duration_summary="Bilinmiyor",
            created_at=datetime.now().isoformat()
        )
    
    def to_dict(self, insights: ConversationInsights) -> Dict[str, Any]:
        """Insights'ı dictionary'e çevir"""
        return asdict(insights) 