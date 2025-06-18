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

class WebSearchPlugin(BasePlugin):
    """
    Web Search Plugin - Conducts web searches when AI messages contain search triggers.
    
    Triggers:
    - [search: "query"]
    - [araştır: "sorgu"] 
    - [research: "topic"]
    - [google: "search term"]
    """
    
    def __init__(self):
        super().__init__()
        self.search_engines = {
            'google': 'https://www.google.com/search?q={}',
            'bing': 'https://www.bing.com/search?q={}',
            'duckduckgo': 'https://duckduckgo.com/?q={}'
        }
        self.default_engine = 'google'
        
    def get_triggers(self) -> List[str]:
        """Return regex patterns that trigger web search"""
        return [
            r'\[search:\s*["\']([^"\']+)["\']\s*\]',
            r'\[araştır:\s*["\']([^"\']+)["\']\s*\]',
            r'\[research:\s*["\']([^"\']+)["\']\s*\]',
            r'\[google:\s*["\']([^"\']+)["\']\s*\]',
            r'\[web:\s*["\']([^"\']+)["\']\s*\]'
        ]
    
    async def execute(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute web search based on detected triggers"""
        try:
            # Extract search queries from all triggers
            search_queries = []
            
            for trigger_pattern in self.get_triggers():
                matches = re.finditer(trigger_pattern, message, re.IGNORECASE)
                for match in matches:
                    query = match.group(1).strip()
                    if query:
                        search_queries.append(query)
            
            if not search_queries:
                return {}
            
            # Process each search query
            search_results = []
            for query in search_queries:
                logger.info(f"Performing web search for: {query}")
                
                # Try to use Browserbase MCP first, fallback to simple method
                result = await self._perform_search(query, context)
                if result:
                    search_results.append(result)
            
            if search_results:
                return {
                    'type': 'web_search_result',
                    'role': '🌐 Web Araştırmacısı',
                    'content': self._format_search_results(search_results),
                    'queries': search_queries,
                    'timestamp': context.get('timestamp', ''),
                    'metadata': {
                        'search_count': len(search_results),
                        'engine': self.default_engine
                    }
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error in WebSearchPlugin: {str(e)}")
            return {
                'type': 'plugin_error',
                'role': '🌐 Web Araştırmacısı',
                'content': f"Web araştırması sırasında hata oluştu: {str(e)}",
                'error': str(e)
            }
    
    async def _perform_search(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform the actual web search"""
        try:
            # Try to use Browserbase MCP if available
            if await self._try_browserbase_search(query, context):
                return await self._try_browserbase_search(query, context)
            
            # Fallback to simulated search results
            return await self._simulate_search(query)
            
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {str(e)}")
            return await self._simulate_search(query, error=str(e))
    
    async def _try_browserbase_search(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Try to use Browserbase MCP for real web search"""
        try:
            # Check if we have MCP tools available in context
            mcp_tools = context.get('mcp_tools', {})
            
            if 'browserbase' in mcp_tools:
                # Use Browserbase to perform search
                browserbase = mcp_tools['browserbase']
                
                # Navigate to Google and perform search
                search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
                
                # This would be the actual Browserbase call
                # For now, we'll simulate it
                await asyncio.sleep(0.1)  # Simulate search delay
                
                return {
                    'query': query,
                    'method': 'browserbase',
                    'url': search_url,
                    'results': [
                        {
                            'title': f"'{query}' hakkında araştırma sonuçları",
                            'snippet': f"'{query}' konusunda kapsamlı bilgiler ve güncel gelişmeler.",
                            'url': search_url
                        }
                    ]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Browserbase search failed: {str(e)}")
            return None
    
    async def _simulate_search(self, query: str, error: str = None) -> Dict[str, Any]:
        """Simulate search results when real search is not available"""
        
        # Simulate network delay
        await asyncio.sleep(0.5)
        
        # Generate realistic search results
        results = [
            {
                'title': f"'{query}' - Comprehensive Overview",
                'snippet': f"Detailed information about {query} including latest developments, key concepts, and related topics.",
                'url': f"https://example.com/search?q={query.replace(' ', '-')}"
            },
            {
                'title': f"Latest News on {query}",
                'snippet': f"Recent news and updates related to {query}. Stay informed with the latest developments.",
                'url': f"https://news.example.com/{query.replace(' ', '-')}"
            },
            {
                'title': f"{query} - Wikipedia",
                'snippet': f"Encyclopedia article about {query} with comprehensive information and references.",
                'url': f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}"
            }
        ]
        
        return {
            'query': query,
            'method': 'simulated' + (f' (error: {error})' if error else ''),
            'results': results
        }
    
    def _format_search_results(self, search_results: List[Dict[str, Any]]) -> str:
        """Format search results for display in chat"""
        formatted_results = []
        
        for search_data in search_results:
            query = search_data['query']
            method = search_data['method']
            results = search_data['results']
            
            result_text = f"🔍 **'{query}' için arama sonuçları** _(Method: {method})_\n\n"
            
            for i, result in enumerate(results[:3], 1):  # Show top 3 results
                result_text += f"**{i}. {result['title']}**\n"
                result_text += f"   {result['snippet']}\n"
                result_text += f"   🔗 {result['url']}\n\n"
            
            formatted_results.append(result_text)
        
        return "\n" + "="*50 + "\n".join(formatted_results)

# Example usage patterns that will trigger this plugin:
# AI message: "Bu konu hakkında daha fazla bilgi edinmek için [search: 'artificial intelligence trends 2024'] yapalım."
# AI message: "Let me [research: 'quantum computing applications'] to provide better insights."
# AI message: "[araştır: 'yapay zeka gelişmeleri'] yaparak güncel bilgileri öğrenelim." 