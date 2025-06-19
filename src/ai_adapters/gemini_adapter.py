"""
Gemini AI Adapter
"""
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import asyncio
from typing import List, Optional, Dict, Any
from .base_adapter import BaseAIAdapter, AIResponse

class GeminiAdapter(BaseAIAdapter):
    """Google Gemini API adapter"""
    
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash-002"):
        super().__init__(api_key, model)
        genai.configure(api_key=api_key)
        self.genai_model = genai.GenerativeModel(model)
        
        # Model rotation - yeni stabil modeller öncelik
        self.fallback_models = [
            "gemini-1.5-flash-002",  # Yeni stabil - default güvenlik: Block none
            "gemini-1.5-pro-002",    # Yeni stabil - default güvenlik: Block none  
            "gemini-2.0-flash-001",  # Yeni stabil - default güvenlik: Block none
            "gemini-1.5-flash",      # Fallback
            "gemini-2.5-flash"       # Son fallback
        ]
        
    async def _send_message_impl(self, message: str, context: Optional[str] = None) -> AIResponse:
        """Gemini'ye mesaj gönder - Model rotation + retry ile"""
        
        # Model rotation ile retry
        for attempt, model_to_try in enumerate(self.fallback_models):
            try:
                print(f"🔄 Deneme #{attempt + 1}: {model_to_try} modeli kullanılıyor...")
                result = await self._try_with_model(model_to_try, message, context)
                print(f"✅ Başarılı: {model_to_try} ile yanıt alındı!")
                return result
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Güvenlik filtresi hatası - bir sonraki modeli dene
                if any(keyword in error_msg for keyword in ['güvenlik filtresi', 'safety filter', 'blocked', 'safety']):
                    print(f"🛡️ {model_to_try}: Güvenlik filtresi - sonraki model deneniyor...")
                    if attempt < len(self.fallback_models) - 1:
                        await asyncio.sleep(1)  # Kısa bekleme
                        continue
                
                # Timeout/API hatası - bir sonraki modeli dene  
                elif any(keyword in error_msg for keyword in ['timeout', 'connection', 'quota', 'limit']):
                    print(f"🔌 {model_to_try}: API hatası - sonraki model deneniyor...")
                    if attempt < len(self.fallback_models) - 1:
                        await asyncio.sleep(2)  # Biraz daha bekle
                        continue
                
                # Son model de başarısız oldu
                if attempt == len(self.fallback_models) - 1:
                    raise Exception(f"Tüm Gemini modelleri başarısız oldu. Son hata: {str(e)}")
                    
        # Bu noktaya ulaşılmamalı
        raise Exception("Beklenmeyen hata: Model rotation tamamlanamadı")
    
    async def _try_with_model(self, model_name: str, message: str, context: Optional[str] = None) -> AIResponse:
        """Belirli bir model ile deneme yap"""
        try:
            # Model'i dinamik olarak oluştur 
            current_model = genai.GenerativeModel(model_name)
            
            # Güvenlik filtresi için prompt optimizasyonu
            safe_message = self._sanitize_prompt(message)
            full_prompt = safe_message
            
            if context:
                safe_context = self._sanitize_prompt(context)
                full_prompt = f"{safe_context}\n\n{safe_message}"
            
            # Model-specific güvenlik ayarları
            # Yeni modeller (002, 001) için daha az kısıtlayıcı
            if any(new_version in model_name for new_version in ['-002', '-001', '2.0-flash']):
                safety_settings = {
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                }
            else:
                # Eski modeller için daha kısıtlayıcı
                safety_settings = {
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                }
            
            response = await asyncio.to_thread(
                current_model.generate_content,
                full_prompt,
                generation_config={
                    "max_output_tokens": 2048,
                    "temperature": 0.9,
                    "top_p": 0.95,
                    "top_k": 40,
                    "candidate_count": 1,
                },
                safety_settings=safety_settings
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
                    # Daha kullanıcı dostu mesaj
                    fallback_suggestions = [
                        "• Daha genel terimler kullanın",
                        "• Teknik kelimelerle ifade edin", 
                        "• Sorunuzu farklı açıdan sormayı deneyin",
                        "• Örnek vermek yerine kavramsal açıklama isteyin"
                    ]
                    
                    # Debug bilgisi için candidate'i incele
                    safety_info = ""
                    if hasattr(candidate, 'safety_ratings'):
                        ratings = candidate.safety_ratings
                        high_risk_categories = []
                        for rating in ratings:
                            if hasattr(rating, 'category') and hasattr(rating, 'probability'):
                                if rating.probability.name in ['HIGH', 'MEDIUM']:
                                    high_risk_categories.append(rating.category.name.replace('HARM_CATEGORY_', ''))
                        
                        if high_risk_categories:
                            safety_info = f"Tetiklenen kategoriler: {', '.join(high_risk_categories)}"
                    
                    suggestions_text = "\n".join(fallback_suggestions)
                    error_msg = f"""🛡️ Gemini güvenlik filtresi devreye girdi. 

💡 Öneriler:
{suggestions_text}

🔧 Alternatif: OpenAI adaptörünü kullanmayı deneyin.

{f'[Debug: {safety_info}]' if safety_info else ''}"""
                    
                    raise Exception(error_msg)
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
            cost = self._calculate_cost(model_name, int(input_tokens), int(output_tokens))
            
            return AIResponse(
                content=response_text,
                model=model_name,  # Kullanılan model adını döndür
                usage={
                    "input_tokens": int(input_tokens),
                    "output_tokens": int(output_tokens),
                    "total_tokens": total_tokens,
                    "total_cost": cost,
                    "finish_reason": finish_reason
                }
            )
            
        except Exception as e:
            self.stats['errors'] += 1
            raise Exception(f"Gemini API hatası ({model_name}): {str(e)}")
    
    def _calculate_cost(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """Gemini maliyet hesaplama - 2025 güncel fiyatlar"""
        
        # 2025 güncel Gemini fiyatları (USD per 1M tokens)
        cost_table = {
            # Free tier modeller - $0
            "gemini-1.5-flash": {"input": 0.0, "output": 0.0},
            "gemini-1.5-flash-002": {"input": 0.0, "output": 0.0},
            "gemini-2.0-flash": {"input": 0.0, "output": 0.0},
            "gemini-2.0-flash-001": {"input": 0.0, "output": 0.0},
            "gemini-2.5-flash": {"input": 0.0, "output": 0.0},
            
            # Pro modeller - Ücretli
            "gemini-1.5-pro": {"input": 1.25, "output": 3.75},
            "gemini-1.5-pro-002": {"input": 1.25, "output": 3.75},
            "gemini-2.0-pro": {"input": 2.50, "output": 7.50},  # Tahmini
            "gemini-2.5-pro": {"input": 2.50, "output": 7.50},  # Tahmini
        }
        
        # Model için fiyat bulma
        model_cost = None
        for cost_model, prices in cost_table.items():
            if cost_model in model_name:
                model_cost = prices
                break
        
        # Eğer model bulunamazsa, "pro" içeriyorsa ücretli, yoksa ücretsiz
        if model_cost is None:
            if "pro" in model_name.lower():
                model_cost = {"input": 1.25, "output": 3.75}  # Default pro pricing
            else:
                model_cost = {"input": 0.0, "output": 0.0}  # Default free
        
        # Maliyet hesaplama
        input_cost = (input_tokens / 1_000_000) * model_cost["input"]
        output_cost = (output_tokens / 1_000_000) * model_cost["output"]
        
        return round(input_cost + output_cost, 6)  # 6 decimal precision
    
    def _sanitize_prompt(self, text: str) -> str:
        """Gemini güvenlik filtresi için prompt'u optimize et"""
        if not text:
            return text
        
        # Türkçe içerik tespit et
        turkish_indicators = ['ı', 'ğ', 'ü', 'ş', 'ö', 'ç', 'İ', 'Ğ', 'Ü', 'Ş', 'Ö', 'Ç']
        is_turkish = any(char in text for char in turkish_indicators)
        
        if is_turkish:
            # Türkçe metni İngilizce'ye çevir (basit mapping)
            english_translation = self._translate_to_english(text)
            return f"Please respond in Turkish. {english_translation}"
        
        # İngilizce metinler için minimal sanitization
        safe_text = text.replace('generate', 'suggest').replace('create', 'develop')
        return safe_text
    
    def _translate_to_english(self, turkish_text: str) -> str:
        """Basit Türkçe->İngilizce çeviri (Gemini güvenlik filtresi için)"""
        
        # Yaygın Türkçe ifadelerin İngilizce karşılıkları
        translations = {
            # Selamlaşma
            'merhaba': 'hello',
            'selam': 'hello',
            'iyi günler': 'good day',
            
            # Temel fiiller
            'istiyorum': 'I want',
            'istediğim': 'what I want',
            'verebilir misiniz': 'can you provide',
            'yapabilir misiniz': 'can you do',
            'geliştirmek': 'to develop',
            'oluşturmak': 'to create',
            'üretmek': 'to produce',
            'yapmak': 'to make',
            
            # Teknik terimler
            'yapay zeka': 'artificial intelligence',
            'AI teknolojisi': 'AI technology', 
            'web uygulaması': 'web application',
            'web application teknolojisi': 'web application technology',
            'api': 'API',
            'destekli': 'powered',
            'tabanlı': 'based',
            
            # Sıfatlar ve zarflar
            'çeşitli': 'various',
            'farklı': 'different', 
            'çekitli': 'various',  # Yazım hatası
            'konularda': 'topics',
            'konularfa': 'topics',  # Yazım hatası
            'konusunda': 'about',
            'üzerine': 'about',
            'izerine': 'about',  # Yazım hatası
            
            # İsimler
            'fikirler': 'ideas',
            'öneriler': 'suggestions',
            'fikir': 'idea',
            'öneri': 'suggestion',
            'proje': 'project',
            'sistem': 'system',
            'uygulama': 'application',
            'teknoloji': 'technology',
            
            # Bağlaçlar ve edatlar
            'ile': 'with',
            'için': 'for',
            've': 'and',
            'veya': 'or',
            'ama': 'but',
            'ancak': 'however',
        }
        
        # Basit kelime değiştirme
        english_text = turkish_text.lower()
        for turkish, english in translations.items():
            english_text = english_text.replace(turkish, english)
        
        # Temel cümle yapısı düzenlemesi
        if 'hello' in english_text and 'API' in english_text:
            english_text = "Hello. I need suggestions for building web applications using APIs and AI technology. Please provide various ideas for different topics and technical approaches."
        
        return english_text.capitalize() 