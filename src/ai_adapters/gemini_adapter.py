"""
Gemini AI Adapter
"""
import google.generativeai as genai
import asyncio
from typing import List, Optional
from .base_adapter import BaseAIAdapter, AIResponse, AIConfig
from logger import logger

class GeminiAdapter(BaseAIAdapter):
    """Google Gemini API adaptörü"""
    
    def __init__(self, config: AIConfig):
        super().__init__(config)
        genai.configure(api_key=config.api_key)
        self.model = genai.GenerativeModel(config.model_name)
        
    async def send_message(
        self, 
        message: str, 
        context: Optional[str] = None,
        role_context: Optional[str] = None
    ) -> AIResponse:
        """Gemini'ye mesaj gönder"""
        
        if not self.check_rate_limit():
            raise Exception("Rate limit aşıldı")
        
        try:
            # Prompt oluştur
            full_prompt = ""
            if role_context:
                full_prompt += f"{role_context}\n\n"
            
            if context:
                full_prompt += f"Kontext: {context}\n\n"
            
            # Conversation history ekle
            if self.conversation_history:
                full_prompt += "Geçmiş konuşma:\n"
                for conv in self.conversation_history[-5:]:
                    full_prompt += f"Kullanıcı: {conv['user']}\n"
                    full_prompt += f"Asistan: {conv['assistant']}\n"
                full_prompt += "\n"
            
            full_prompt += f"Kullanıcı: {message}\n\nAsistan:"
            
            # API çağrısı
            response = await asyncio.to_thread(
                self.model.generate_content,
                full_prompt,
                generation_config={
                    "max_output_tokens": self.config.max_tokens,
                    "temperature": self.config.temperature,
                }
            )
            
            # Token kullanımını hesapla (yaklaşık)
            input_tokens = len(full_prompt.split()) * 1.3
            output_tokens = len(response.text.split()) * 1.3
            total_tokens = int(input_tokens + output_tokens)
            
            # Rate limiter güncelle
            self.rate_limiter.record_usage(total_tokens)
            
            # History'e ekle
            self.add_to_history(message, response.text)
            
            return AIResponse(
                content=response.text,
                model=self.config.model_name,
                usage={
                    "input_tokens": int(input_tokens),
                    "output_tokens": int(output_tokens),
                    "total_tokens": total_tokens
                },
                metadata={
                    "finish_reason": "stop",
                    "safety_ratings": getattr(response, 'safety_ratings', [])
                },
                timestamp=asyncio.get_event_loop().time()
            )
            
        except Exception as e:
            logger.error(f"Gemini API hatası: {str(e)}", "GEMINI_ADAPTER", e)
            raise
    
    def get_available_models(self) -> List[str]:
        """Kullanılabilir Gemini modelleri"""
        return [
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b", 
            "gemini-1.5-pro",
            "gemini-2.0-flash",
            "gemini-2.0-flash-thinking"
        ]
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Gemini maliyet tahmini (Free tier için 0)"""
        # Gemini free tier limitler içinde ise maliyet 0
        if self.config.model_name in ["gemini-1.5-flash", "gemini-2.0-flash"]:
            return 0.0
        
        # Pro modeller için yaklaşık fiyatlar
        costs = {
            "gemini-1.5-pro": {
                "input": 0.00125,  # $1.25 per 1M tokens
                "output": 0.00375  # $3.75 per 1M tokens
            }
        }
        
        if self.config.model_name in costs:
            cost_config = costs[self.config.model_name]
            input_cost = (input_tokens / 1_000_000) * cost_config["input"]
            output_cost = (output_tokens / 1_000_000) * cost_config["output"]
            return input_cost + output_cost
        
        return 0.0 