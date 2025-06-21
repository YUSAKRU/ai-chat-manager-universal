"""
AI Integration for Notes
========================

Not sistemi için AI entegrasyon özellikleri.
"""

import re
from typing import List, Dict, Any, Optional
from ..universal_ai_adapter import UniversalAIAdapter
from ..logger import logger


class NotesAIIntegration:
    """Not sistemi için AI entegrasyonu"""
    
    def __init__(self, ai_adapter: UniversalAIAdapter):
        self.ai_adapter = ai_adapter
    
    async def analyze_note(self, content: str) -> Dict[str, Any]:
        """Not içeriğini AI ile analiz et"""
        if not self.ai_adapter:
            return {'success': False, 'error': 'AI adapter mevcut değil'}
        
        try:
            prompt = f"""Not içeriğini analiz et ve aşağıdaki bilgileri sağla:
1. Ana konu/tema
2. Anahtar noktalar (bullet points)
3. Duygu analizi (pozitif/nötr/negatif)
4. Önerilen etiketler
5. İçerik kalitesi skoru (1-10)

Not içeriği:
{content[:1000]}"""  # İlk 1000 karakter
            
            # Use the correct method name
            response = await self.ai_adapter.send_message(
                role_id='general',  # Use role_id
                message=prompt
            )
            
            if response:
                return {
                    'success': True,
                    'analysis': response.content
                }
            else:
                return {
                    'success': False,
                    'error': 'AI yanıt vermedi'
                }
                
        except Exception as e:
            logger.error(f"Note analysis failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def suggest_tags(self, title: str, content: str, existing_tags: List[str] = None) -> List[str]:
        """Etiket önerileri al"""
        try:
            existing_str = f"Mevcut etiketler: {', '.join(existing_tags)}" if existing_tags else ""
            
            prompt = f"""
Bu not için en uygun 3-5 etiket öner:

Başlık: {title}
İçerik: {content}
{existing_str}

Kurallar:
- Türkçe veya İngilizce olabilir
- Kısa ve öz olsun (1-2 kelime)
- Teknik terimler kullanabilirsin
- Sadece etiket listesini ver, virgülle ayır

Örnek: python, web-development, flask, backend, api
            """
            
            response = await self.ai_adapter.send_message(
                role_id="general",
                message=prompt
            )
            
            if response and response.content:
                # Virgülle ayrılmış etiketleri parse et
                tags = [tag.strip().lower() for tag in response.content.split(',')]
                # Temizle ve filtrele
                tags = [tag for tag in tags if tag and len(tag) > 1 and len(tag) < 30]
                return tags[:5]  # Maksimum 5 etiket
            
            return self._fallback_tags(title, content)
            
        except Exception as e:
            logger.error(f"Tag suggestion failed: {e}")
            return self._fallback_tags(title, content)
    
    async def summarize_content(self, title: str, content: str, target_length: str = "short") -> str:
        """İçerik özetleme"""
        try:
            length_map = {
                "short": "1-2 cümle",
                "medium": "1 paragraf (3-5 cümle)", 
                "long": "2-3 paragraf"
            }
            
            length_desc = length_map.get(target_length, "1-2 cümle")
            
            prompt = f"""
Aşağıdaki notu özetle:

Başlık: {title}
İçerik: {content}

Özet uzunluğu: {length_desc}

Özetleme kuralları:
- Ana noktaları koru
- Anlaşılır ve akıcı olsun
- Türkçe yaz
- Gereksiz detayları çıkar
- Sadece özeti ver, başka açıklama yapma
            """
            
            response = await self.ai_adapter.send_message(
                role_id="general",
                message=prompt
            )
            
            if response and response.content:
                return response.content.strip()
            
            return self._fallback_summary(content, target_length)
            
        except Exception as e:
            logger.error(f"Content summarization failed: {e}")
            return self._fallback_summary(content, target_length)
    
    async def improve_writing(self, content: str) -> Dict[str, Any]:
        """Yazım ve stil iyileştirme"""
        try:
            prompt = f"""
Aşağıdaki metni yazım ve stil açısından iyileştir:

{content}

Lütfen şu formatta yanıt ver:
{{
    "improved_text": "iyileştirilmiş metin",
    "changes": [
        {{"type": "grammar", "description": "Dilbilgisi düzeltmesi"}},
        {{"type": "style", "description": "Stil iyileştirmesi"}}
    ],
    "suggestions": ["genel öneri 1", "genel öneri 2"]
}}

Sadece geçerli JSON formatında yanıt ver.
            """
            
            response = await self.ai_adapter.send_message(
                role_id="general",
                message=prompt
            )
            
            if response and response.content:
                import json
                try:
                    improvements = json.loads(response.content)
                    return improvements
                except json.JSONDecodeError:
                    return {
                        "improved_text": response.content,
                        "changes": [],
                        "suggestions": ["AI tarafından genel iyileştirmeler yapıldı"]
                    }
            
            return {
                "improved_text": content,
                "changes": [],
                "suggestions": ["Iyileştirme önerisi alınamadı"]
            }
            
        except Exception as e:
            logger.error(f"Writing improvement failed: {e}")
            # Fallback: basic grammar check
            logger.info("Using fallback writing improvement system")
            return self._fallback_writing_improvement(content)
    
    async def find_related_notes(self, title: str, content: str, all_notes: List[Dict]) -> List[Dict]:
        """İlgili notları bul"""
        try:
            # Basit keyword matching ile başla
            keywords = self._extract_keywords(content)
            related = []
            
            for note in all_notes[:20]:  # İlk 20 notu kontrol et
                note_keywords = self._extract_keywords(note.get('content', ''))
                
                # Ortak keyword sayısı
                common_keywords = set(keywords) & set(note_keywords)
                if len(common_keywords) > 1:
                    related.append({
                        'note': note,
                        'similarity_score': len(common_keywords) / max(len(keywords), 1),
                        'common_keywords': list(common_keywords)
                    })
            
            # Benzerlik skoruna göre sırala
            related.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            return related[:5]  # En benzer 5 not
            
        except Exception as e:
            logger.error(f"Related notes search failed: {e}")
            return []
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Basit keyword extraction"""
        if not text:
            return []
        
        # HTML etiketlerini temizle
        clean_text = re.sub(r'<[^>]+>', ' ', text)
        
        # Küçük harfe çevir ve kelimeleri ayır
        words = re.findall(r'\b\w{3,}\b', clean_text.lower())
        
        # Türkçe stop words (basit liste)
        stop_words = {
            'bir', 'bu', 'şu', 'olan', 'olan', 'için', 'ile', 've', 'ya', 'da',
            'ama', 'fakat', 'çünkü', 'eğer', 'when', 'where', 'what', 'how',
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
            'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during'
        }
        
        # Stop words'leri filtrele ve frekans hesapla
        word_freq = {}
        for word in words:
            if word not in stop_words and len(word) > 2:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # En sık kullanılan kelimeleri döndür
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in keywords[:10]]
    
    def _fallback_analysis(self, title: str, content: str) -> Dict[str, Any]:
        """AI çalışmadığında fallback analiz"""
        keywords = self._extract_keywords(content)
        
        # Basit kategori tespiti
        tech_keywords = {'python', 'javascript', 'html', 'css', 'react', 'vue', 'flask', 'api', 'database', 'sql'}
        if any(keyword in tech_keywords for keyword in keywords):
            category = "teknik"
        elif any(word in title.lower() for word in ['proje', 'plan', 'roadmap', 'goal']):
            category = "proje"
        else:
            category = "genel"
        
        return {
            "category": category,
            "sentiment": "neutral",
            "keywords": keywords[:5],
            "difficulty": "intermediate",
            "estimated_read_time": max(1, len(content.split()) // 200),
            "summary": f"{title} - {len(content)} karakter içerik",
            "confidence": 0.6,
            "ai_model": "fallback"
        }
    
    def _fallback_tags(self, title: str, content: str) -> List[str]:
        """AI çalışmadığında fallback etiketler"""
        keywords = self._extract_keywords(content)
        
        # Basit etiket önerileri
        suggested_tags = []
        
        # Başlıktan etiket çıkar
        title_words = re.findall(r'\b\w{3,}\b', title.lower())
        suggested_tags.extend(title_words[:2])
        
        # En sık kullanılan keyword'lerden etiket
        suggested_tags.extend(keywords[:3])
        
        # Temizle ve benzersiz yap
        tags = list(set(tag for tag in suggested_tags if len(tag) > 2))
        return tags[:5]
    
    def _fallback_summary(self, content: str, target_length: str) -> str:
        """AI çalışmadığında fallback özet"""
        if not content:
            return "İçerik bulunamadı."
        
        # HTML etiketlerini temizle
        clean_content = re.sub(r'<[^>]+>', ' ', content)
        sentences = re.split(r'[.!?]+', clean_content.strip())
        
        if target_length == "short":
            return sentences[0] + "." if sentences else "Özet oluşturulamadı."
        elif target_length == "medium":
            return " ".join(sentences[:3]) + "."
        else:
            return " ".join(sentences[:5]) + "."
    
    def _fallback_writing_improvement(self, content: str) -> Dict[str, Any]:
        """AI çalışmadığında fallback yazım iyileştirme"""
        if not content:
            return {
                "improved_text": "İçerik bulunamadı.",
                "changes": [],
                "suggestions": ["İçerik ekleyin ve tekrar deneyin"]
            }
        
        # Basit yazım kontrolü
        suggestions = []
        changes = []
        improved_text = content
        
        # Çift boşluk kontrolü
        if '  ' in content:
            improved_text = re.sub(r' +', ' ', improved_text)
            changes.append({
                "type": "spacing",
                "description": "Çift boşluklar düzeltildi"
            })
        
        # Başlık büyük harf kontrolü
        lines = improved_text.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if line and not line[0].isupper() and len(line) > 3:
                suggestions.append("Cümle başlarını büyük harfle başlatın")
                break
        
        # Noktalama kontrolü
        if not any(punct in content for punct in '.!?'):
            suggestions.append("Cümle sonlarında noktalama işareti kullanın")
        
        # Paragraf uzunluğu kontrolü  
        if len(content) > 500 and '\n\n' not in content:
            suggestions.append("Uzun metinleri paragraflara bölün")
        
        # Genel öneriler
        if len(suggestions) == 0:
            suggestions.extend([
                "Metniniz iyi görünüyor",
                "Daha detaylı kontrol için AI yazım iyileştirme özelliğini kullanın"
            ])
        
        return {
            "improved_text": improved_text,
            "changes": changes,
            "suggestions": suggestions[:3]  # En fazla 3 öneri
        }
