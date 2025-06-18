"""
Gemini AI Adapter
"""
import google.generativeai as genai
import asyncio
from typing import List, Optional, Dict, Any
from .base_adapter import BaseAIAdapter, AIResponse

class GeminiAdapter(BaseAIAdapter):
    """Google Gemini API adapter"""
    
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        super().__init__(api_key, model)
        genai.configure(api_key=api_key)
        self.genai_model = genai.GenerativeModel(model)
        
    async def send_message(self, message: str, context: Optional[str] = None) -> AIResponse:
        """Gemini'ye mesaj gönder"""
        
        # Rate limit kontrolü
        rate_limit = self.check_rate_limit()
        if not rate_limit['available']:
            raise Exception(f"Rate limit aşıldı. {rate_limit['retry_after']} saniye bekleyin.")
        
        try:
            # Basit ve güvenli prompt formatı
            full_prompt = message
            
            if context:
                full_prompt = f"{context}\n\n{message}"
            
            # API çağrısı - güvenlik filtresi tamamen kapatıldı
            response = await asyncio.to_thread(
                self.genai_model.generate_content,
                full_prompt,
                generation_config={
                    "max_output_tokens": 2048,
                    "temperature": 0.9,
                    "top_p": 0.95,
                    "top_k": 40,
                    "candidate_count": 1,
                }
                # safety_settings parametresi tamamen kaldırıldı
            )
            
            # Response kontrolü ve güvenli metin çıkarma
            response_text = ""
            finish_reason = None
            
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                finish_reason = candidate.finish_reason if hasattr(candidate, 'finish_reason') else None
                
                # Finish reason kontrolleri
                if finish_reason == 1:  # STOP - Normal sonlanma
                    if hasattr(candidate, 'content') and candidate.content.parts:
                        response_text = candidate.content.parts[0].text
                elif finish_reason == 2:  # SAFETY - Güvenlik filtresi
                    # Debug bilgisi için candidate'i incele
                    safety_info = ""
                    if hasattr(candidate, 'safety_ratings'):
                        ratings = candidate.safety_ratings
                        for rating in ratings:
                            if hasattr(rating, 'category') and hasattr(rating, 'probability'):
                                safety_info += f"{rating.category.name}: {rating.probability.name} "
                    
                    raise Exception(f"Gemini güvenlik filtresi tetiklendi. Lütfen mesajınızı farklı kelimelerle tekrar deneyin. [Debug: {safety_info}]")
                elif finish_reason == 3:  # RECITATION - Telif hakkı
                    raise Exception("İçerik telif hakkı koruması nedeniyle bloklandı.")
                elif finish_reason == 4:  # OTHER - Diğer nedenler
                    raise Exception("İçerik diğer nedenlerle bloklandı.")
                else:
                    # Finish reason belirtilmemiş ama text varsa al
                    try:
                        response_text = response.text if hasattr(response, 'text') else ""
                    except:
                        response_text = ""
            else:
                # Fallback: Direkt response.text dene
                try:
                    response_text = response.text if hasattr(response, 'text') else ""
                except:
                    raise Exception("Gemini API'den geçerli bir yanıt alınamadı.")
            
            if not response_text.strip():
                raise Exception(f"Boş yanıt alındı. Finish reason: {finish_reason}")
            
            # Token kullanımını hesapla (yaklaşık)
            input_tokens = len(full_prompt.split()) * 1.3
            output_tokens = len(response_text.split()) * 1.3
            total_tokens = int(input_tokens + output_tokens)
            
            # Maliyet hesapla
            cost = self._calculate_cost(int(input_tokens), int(output_tokens))
            
            # İstatistikleri güncelle
            self._update_stats(total_tokens, cost)
            
            return AIResponse(
                content=response_text,
                model=self.model,
                usage={
                    "input_tokens": int(input_tokens),
                    "output_tokens": int(output_tokens),
                    "total_tokens": total_tokens,
                    "cost": cost,
                    "finish_reason": finish_reason
                }
            )
            
        except Exception as e:
            self.stats['errors'] += 1
            raise Exception(f"Gemini API hatası: {str(e)}")
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Gemini maliyet hesaplama"""
        # Gemini free tier modeller için maliyet 0
        if self.model in ["gemini-pro", "gemini-1.5-flash", "gemini-2.5-flash"]:
            return 0.0
        
        # Pro modeller için fiyatlandırma
        costs = {
            "gemini-1.5-pro": {
                "input": 0.00125,  # $1.25 per 1M tokens
                "output": 0.00375  # $3.75 per 1M tokens
            },
            "gemini-2.5-pro": {
                "input": 0.00125,  # Yaklaşık fiyat (güncel olmayabilir)
                "output": 0.00375  # Yaklaşık fiyat (güncel olmayabilir)
            }
        }
        
        if self.model in costs:
            cost_config = costs[self.model]
            input_cost = (input_tokens / 1_000_000) * cost_config["input"]
            output_cost = (output_tokens / 1_000_000) * cost_config["output"]
            return input_cost + output_cost
        
        return 0.0 