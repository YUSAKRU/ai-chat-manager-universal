"""
OpenAI (GPT) Adapter
"""
import openai
import asyncio
from typing import List, Optional
from .base_adapter import BaseAIAdapter, AIResponse, AIConfig
from logger import logger

class OpenAIAdapter(BaseAIAdapter):
    """OpenAI API adaptörü"""
    
    def __init__(self, config: AIConfig):
        super().__init__(config)
        self.client = openai.AsyncOpenAI(api_key=config.api_key)
        
    async def send_message(
        self, 
        message: str, 
        context: Optional[str] = None,
        role_context: Optional[str] = None
    ) -> AIResponse:
        """OpenAI'ye mesaj gönder"""
        
        if not self.check_rate_limit():
            raise Exception("Rate limit aşıldı")
        
        try:
            # Mesaj listesi oluştur
            messages = []
            
            # System prompt
            if role_context:
                messages.append({
                    "role": "system",
                    "content": role_context
                })
            
            # Context varsa ekle
            if context:
                messages.append({
                    "role": "system",
                    "content": f"Kontext: {context}"
                })
            
            # Conversation history
            for conv in self.conversation_history[-5:]:
                messages.append({"role": "user", "content": conv['user']})
                messages.append({"role": "assistant", "content": conv['assistant']})
            
            # Yeni mesaj
            messages.append({"role": "user", "content": message})
            
            # API çağrısı
            response = await self.client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                stream=False
            )
            
            # Yanıt ve kullanım bilgileri
            ai_response = response.choices[0].message.content
            usage = response.usage
            
            # Rate limiter güncelle
            self.rate_limiter.record_usage(usage.total_tokens)
            
            # History'e ekle
            self.add_to_history(message, ai_response)
            
            return AIResponse(
                content=ai_response,
                model=response.model,
                usage={
                    "input_tokens": usage.prompt_tokens,
                    "output_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens
                },
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "id": response.id,
                    "created": response.created
                },
                timestamp=asyncio.get_event_loop().time()
            )
            
        except Exception as e:
            logger.error(f"OpenAI API hatası: {str(e)}", "OPENAI_ADAPTER", e)
            raise
    
    def get_available_models(self) -> List[str]:
        """Kullanılabilir OpenAI modelleri"""
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4-turbo-preview",
            "gpt-4",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k"
        ]
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """OpenAI maliyet tahmini"""
        # Model bazlı fiyatlandırma (1M token başına $)
        costs = {
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gpt-4-turbo": {"input": 10.00, "output": 30.00},
            "gpt-4": {"input": 30.00, "output": 60.00},
            "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
            "gpt-3.5-turbo-16k": {"input": 3.00, "output": 4.00}
        }
        
        model_costs = costs.get(self.config.model_name, costs["gpt-3.5-turbo"])
        
        input_cost = (input_tokens / 1_000_000) * model_costs["input"]
        output_cost = (output_tokens / 1_000_000) * model_costs["output"]
        
        return round(input_cost + output_cost, 6) 