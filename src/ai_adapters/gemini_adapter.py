"""
Gemini AI Adapter
"""
import google.generativeai as genai
import asyncio
from typing import List, Optional, Dict, Any
from .base_adapter import BaseAIAdapter, AIResponse

class GeminiAdapter(BaseAIAdapter):
    """Google Gemini API adapter"""
    
    def __init__(self, api_key: str, model: str = "gemini-pro"):
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
            # Prompt oluştur
            full_prompt = ""
            
            if context:
                full_prompt += f"Context: {context}\n\n"
            
            full_prompt += f"User: {message}\n\nAssistant:"
            
            # API çağrısı
            response = await asyncio.to_thread(
                self.genai_model.generate_content,
                full_prompt,
                generation_config={
                    "max_output_tokens": 2048,
                    "temperature": 0.7,
                }
            )
            
            # Token kullanımını hesapla (yaklaşık)
            input_tokens = len(full_prompt.split()) * 1.3
            output_tokens = len(response.text.split()) * 1.3
            total_tokens = int(input_tokens + output_tokens)
            
            # Maliyet hesapla
            cost = self._calculate_cost(int(input_tokens), int(output_tokens))
            
            # İstatistikleri güncelle
            self._update_stats(total_tokens, cost)
            
            return AIResponse(
                content=response.text,
                model=self.model,
                usage={
                    "input_tokens": int(input_tokens),
                    "output_tokens": int(output_tokens),
                    "total_tokens": total_tokens,
                    "cost": cost
                }
            )
            
        except Exception as e:
            self.stats['errors'] += 1
            raise Exception(f"Gemini API hatası: {str(e)}")
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Gemini maliyet hesaplama"""
        # Gemini free tier modeller için maliyet 0
        if self.model in ["gemini-pro", "gemini-1.5-flash"]:
            return 0.0
        
        # Pro modeller için fiyatlandırma
        costs = {
            "gemini-1.5-pro": {
                "input": 0.00125,  # $1.25 per 1M tokens
                "output": 0.00375  # $3.75 per 1M tokens
            }
        }
        
        if self.model in costs:
            cost_config = costs[self.model]
            input_cost = (input_tokens / 1_000_000) * cost_config["input"]
            output_cost = (output_tokens / 1_000_000) * cost_config["output"]
            return input_cost + output_cost
        
        return 0.0 