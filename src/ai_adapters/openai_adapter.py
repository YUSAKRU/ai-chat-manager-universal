"""
OpenAI (GPT) Adapter
"""
import openai
import asyncio
from typing import Optional, Dict, Any
from .base_adapter import BaseAIAdapter, AIResponse


class OpenAIAdapter(BaseAIAdapter):
    """OpenAI API adapter"""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        super().__init__(api_key, model)
        self.client = openai.AsyncOpenAI(api_key=api_key)
        
    async def send_message(self, message: str, context: Optional[str] = None) -> AIResponse:
        """OpenAI'ye mesaj gönder"""
        
        # Rate limit kontrolü
        rate_limit = self.check_rate_limit()
        if not rate_limit['available']:
            raise Exception(f"Rate limit aşıldı. {rate_limit['retry_after']} saniye bekleyin.")
        
        try:
            # Mesaj listesi oluştur
            messages = []
            
            # Context varsa ekle
            if context:
                messages.append({
                    "role": "system",
                    "content": context
                })
            
            # Kullanıcı mesajı
            messages.append({"role": "user", "content": message})
            
            # API çağrısı
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=2048,
                temperature=0.7,
                stream=False
            )
            
            # Yanıt ve kullanım bilgileri
            ai_response = response.choices[0].message.content
            usage = response.usage
            
            # Maliyet hesapla
            cost = self._calculate_cost(usage.prompt_tokens, usage.completion_tokens)
            
            # İstatistikleri güncelle
            self._update_stats(usage.total_tokens, cost)
            
            return AIResponse(
                content=ai_response,
                model=response.model,
                usage={
                    "input_tokens": usage.prompt_tokens,
                    "output_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                    "cost": cost
                }
            )
            
        except Exception as e:
            self.stats['errors'] += 1
            raise Exception(f"OpenAI API hatası: {str(e)}")
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """OpenAI maliyet hesaplama"""
        # Model bazlı fiyatlandırma (1M token başına $)
        costs = {
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gpt-4-turbo": {"input": 10.00, "output": 30.00},
            "gpt-4": {"input": 30.00, "output": 60.00},
            "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
            "gpt-3.5-turbo-16k": {"input": 3.00, "output": 4.00}
        }
        
        model_costs = costs.get(self.model, costs["gpt-3.5-turbo"])
        
        input_cost = (input_tokens / 1_000_000) * model_costs["input"]
        output_cost = (output_tokens / 1_000_000) * model_costs["output"]
        
        return round(input_cost + output_cost, 6) 