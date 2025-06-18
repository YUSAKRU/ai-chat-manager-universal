import re
import asyncio
from typing import Dict, List, Any
import logging
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from plugin_manager import BasePlugin

logger = logging.getLogger(__name__)

class DemoPlugin(BasePlugin):
    """
    Demo Plugin - Demonstrates the plugin system with simple triggers.
    
    Triggers:
    - [demo: "message"]
    - [test: "message"]
    - [hello]
    """
    
    def __init__(self):
        super().__init__()
        self.demo_responses = [
            "🎯 Demo plugin başarıyla çalıştı!",
            "✨ Plugin sistemi aktif ve çalışıyor.",
            "🚀 Bu bir test mesajıdır - sistem normal.",
            "🔥 Yaşayan proje zekası plugin'ı tetiklendi!"
        ]
        
    def get_triggers(self) -> List[str]:
        """Return regex patterns that trigger demo plugin"""
        return [
            r'\[demo:\s*["\']([^"\']+)["\']\s*\]',
            r'\[test:\s*["\']([^"\']+)["\']\s*\]',
            r'\[hello\]',
            r'plugin.*test',  # Any mention of "plugin test"
            r'demo.*çalış'    # Turkish: "demo çalış"
        ]
    
    async def execute(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute demo plugin logic"""
        try:
            # Simulate some processing time
            await asyncio.sleep(0.3)
            
            # Extract demo parameters if any
            demo_params = []
            for trigger_pattern in self.get_triggers()[:2]:  # Only check parameterized triggers
                matches = re.finditer(trigger_pattern, message, re.IGNORECASE)
                for match in matches:
                    param = match.group(1).strip()
                    if param:
                        demo_params.append(param)
            
            # Generate response based on trigger type
            if demo_params:
                response_content = f"🎯 **Demo Plugin Yanıtı**\n\n"
                response_content += f"**Tetikleyici mesaj:** {message[:100]}...\n\n"
                response_content += f"**Çıkarılan parametreler:** {', '.join(demo_params)}\n\n"
                for param in demo_params:
                    response_content += f"• ✨ '{param}' parametresi işlendi\n"
                response_content += f"\n**Sistem durumu:** ✅ Plugin sistemi aktif\n"
                response_content += f"**İşlem zamanı:** {context.get('timestamp', 'Bilinmiyor')}\n"
            else:
                # Simple trigger response
                import random
                response_content = random.choice(self.demo_responses)
                response_content += f"\n\n**Mesaj analizi:**\n"
                response_content += f"- Kelime sayısı: {len(message.split())}\n"
                response_content += f"- Karakter sayısı: {len(message)}\n"
                response_content += f"- Büyük harf içeriyor: {'Evet' if any(c.isupper() for c in message) else 'Hayır'}\n"
                response_content += f"- Sayı içeriyor: {'Evet' if any(c.isdigit() for c in message) else 'Hayır'}\n"
            
            return {
                'type': 'demo_plugin_result',
                'role': '🎯 Demo Plugin',
                'content': response_content,
                'timestamp': context.get('timestamp', ''),
                'metadata': {
                    'trigger_count': len(demo_params),
                    'message_length': len(message),
                    'plugin_version': '1.0.0'
                }
            }
            
        except Exception as e:
            logger.error(f"Error in DemoPlugin: {str(e)}")
            return {
                'type': 'plugin_error',
                'role': '🎯 Demo Plugin',
                'content': f"Demo plugin hatası: {str(e)}",
                'error': str(e)
            }

# Example usage patterns that will trigger this plugin:
# AI message: "Sistemin çalışıp çalışmadığını kontrol etmek için [demo: 'test mesajı'] gönderiyorum."
# AI message: "Let me run a [test: 'plugin functionality'] to verify the system."
# AI message: "Plugin test çalıştırarak sistem durumunu kontrol edelim."
# AI message: "[hello] plugin sistemi!" 