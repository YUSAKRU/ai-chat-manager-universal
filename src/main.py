import os
import time
import threading
import signal
import sys
from typing import Dict, Any, Optional
from flask import Flask, render_template, request, jsonify, redirect, url_for
import webbrowser
from ai_adapters.universal_adapter import UniversalAIAdapter
from ai_adapters.secure_config import SecureConfigManager
from config import Config
from logger import logger
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpecialistRole:
    """Specialist role definition"""
    def __init__(self, name: str, key: str, description: str, expertise: list, prompt_template: str):
        self.name = name
        self.key = key
        self.description = description
        self.expertise = expertise
        self.prompt_template = prompt_template

class OrchestratorResponse:
    """Orchestrator response structure"""
    def __init__(self, primary_response: str, specialist_responses: dict, active_specialists: list, suggested_next_actions: list):
        self.primary_response = primary_response
        self.specialist_responses = specialist_responses
        self.active_specialists = active_specialists
        self.suggested_next_actions = suggested_next_actions

class AIOrchestrator:
    """MCP-style AI Orchestration System"""
    
    def __init__(self, adapters: Dict[str, UniversalAIAdapter]):
        self.adapters = adapters
        self.conversation_history = []
        
        # Define specialist roles
        self.specialists = {
            "project_manager": SpecialistRole(
                name="Proje Yöneticisi",
                key="project_manager", 
                description="Proje planlaması, zaman çizelgesi, kaynak yönetimi uzmanı",
                expertise=["proje planı", "zaman yönetimi", "milestone", "kaynak planlaması", "risk yönetimi"],
                prompt_template="""Sen bir deneyimli Proje Yöneticisisin. Kullanıcının isteğini proje yönetimi perspektifinden değerlendir:

Kullanıcı Mesajı: {message}

Proje yönetimi açısından:
- Hangi adımlar gerekli?
- Zaman çizelgesi nasıl olmalı?
- Hangi kaynaklar gerekli?
- Potansiyel riskler neler?

Pratik ve uygulanabilir öneriler sun."""
            ),
            
            "lead_developer": SpecialistRole(
                name="Kıdemli Geliştirici",
                key="lead_developer",
                description="Kod yazma, teknik kararlar, mimari tasarım uzmanı", 
                expertise=["kodlama", "mimari", "framework", "teknoloji seçimi", "performans"],
                prompt_template="""Sen bir deneyimli Kıdemli Geliştiricisin. Kullanıcının isteğini teknik perspektiften değerlendir:

Kullanıcı Mesajı: {message}

Teknik açıdan:
- Hangi teknolojiler uygun?
- Mimari nasıl olmalı?
- Geliştirme yaklaşımı nedir?
- Teknik riskler neler?

Kod örnekleri ve pratik çözümler öner."""
            ),
            
            "business_analyst": SpecialistRole(
                name="İş Analisti",
                key="business_analyst",
                description="İş gereksinimleri, süreç analizi, pazar araştırması uzmanı",
                expertise=["iş analizi", "gereksinimler", "süreç", "stakeholder", "pazar araştırması"],
                prompt_template="""Sen bir deneyimli İş Analistisin. Kullanıcının isteğini iş perspektifinden değerlendir:

Kullanıcı Mesajı: {message}

İş analizi açısından:
- Temel gereksinimler neler?
- Hangi süreçler etkilenir?
- Stakeholder'lar kimler?
- İş değeri nedir?

Detaylı analiz ve öneriler sun."""
            ),
            
            "ui_ux_designer": SpecialistRole(
                name="UI/UX Tasarımcı",
                key="ui_ux_designer", 
                description="Kullanıcı deneyimi, arayüz tasarımı, kullanılabilirlik uzmanı",
                expertise=["UI tasarım", "UX", "kullanıcı deneyimi", "arayüz", "prototip", "mobil tasarım"],
                prompt_template="""Sen bir deneyimli UI/UX Tasarımcısın. Kullanıcının isteğini tasarım perspektifinden değerlendir:

Kullanıcı Mesajı: {message}

Tasarım açısından:
- Kullanıcı deneyimi nasıl olmalı?
- Arayüz tasarım prensipleri neler?
- Hangi tasarım kalıpları uygun?
- Kullanılabilirlik öncelikleri neler?

Görsel ve deneyim önerileri sun."""
            ),
            
            "marketing_specialist": SpecialistRole(
                name="Pazarlama Uzmanı", 
                key="marketing_specialist",
                description="Pazarlama stratejisi, kullanıcı analizi, pazar konumlandırma uzmanı",
                expertise=["pazarlama", "kullanıcı analizi", "hedef kitle", "rekabet analizi", "strateji"],
                prompt_template="""Sen bir deneyimli Pazarlama Uzmanısın. Kullanıcının isteğini pazarlama perspektifinden değerlendir:

Kullanıcı Mesajı: {message}

Pazarlama açısından:
- Hedef kitle kimler?
- Pazar konumlandırması nasıl olmalı?
- Rekabet durumu nedir?
- Pazarlama stratejisi nedir?

Pazar odaklı öneriler ve analiz sun."""
            ),
            
            "qa_engineer": SpecialistRole(
                name="QA Mühendisi",
                key="qa_engineer",
                description="Test stratejileri, kalite güvence, hata yönetimi uzmanı", 
                expertise=["test", "kalite", "QA", "hata", "test otomasyonu"],
                prompt_template="""Sen bir deneyimli QA Mühendisisin. Kullanıcının isteğini kalite perspektifinden değerlendir:

Kullanıcı Mesajı: {message}

Kalite açısından:
- Test stratejisi nasıl olmalı?
- Hangi test türleri gerekli?
- Kalite kriterleri neler?
- Risk alanları neler?

Test planı ve kalite önerileri sun."""
            ),
            
            "devops_engineer": SpecialistRole(
                name="DevOps Mühendisi",
                key="devops_engineer", 
                description="Deployment, altyapı, CI/CD, operasyon uzmanı",
                expertise=["deployment", "altyapı", "CI/CD", "docker", "monitoring", "ölçeklendirme"],
                prompt_template="""Sen bir deneyimli DevOps Mühendisisin. Kullanıcının isteğini operasyon perspektifinden değerlendir:

Kullanıcı Mesajı: {message}

DevOps açısından:
- Deployment stratejisi nedir?
- Altyapı gereksinimleri neler?
- CI/CD süreci nasıl olmalı?
- Monitoring ve alerting nedir?

Operasyonel çözümler ve öneriler sun."""
            )
        }
        
    def analyze_message_intent(self, message: str) -> Dict[str, float]:
        """Analyze message to determine which specialists are needed"""
        
        intent_scores = {}
        message_lower = message.lower()
        
        # Keyword-based scoring for each specialist
        for specialist_key, specialist in self.specialists.items():
            score = 0
            
            # Check for expertise keywords
            for expertise in specialist.expertise:
                if expertise in message_lower:
                    score += 1
                    
            # Additional context analysis
            if specialist_key == "project_manager":
                pm_keywords = ["proje", "plan", "başla", "organize", "zaman", "milestone", "hedef"]
                score += sum(1 for kw in pm_keywords if kw in message_lower)
                
            elif specialist_key == "lead_developer":
                dev_keywords = ["kod", "yazılım", "geliştir", "teknik", "framework", "dil", "programlama", "mobil", "uygulama"]
                score += sum(1 for kw in dev_keywords if kw in message_lower)
                
            elif specialist_key == "ui_ux_designer":
                design_keywords = ["tasarım", "arayüz", "kullanıcı", "mobil", "web", "deneyim", "UI", "UX"]
                score += sum(1 for kw in design_keywords if kw in message_lower)
                
            elif specialist_key == "marketing_specialist":
                marketing_keywords = ["pazarlama", "kullanıcı", "hedef", "müşteri", "pazar", "rekabet"]
                score += sum(1 for kw in marketing_keywords if kw in message_lower)
                
            elif specialist_key == "business_analyst":
                ba_keywords = ["iş", "analiz", "gereksinim", "süreç", "analizi", "değer"]
                score += sum(1 for kw in ba_keywords if kw in message_lower)
                
            elif specialist_key == "qa_engineer":
                qa_keywords = ["test", "kalite", "hata", "doğrula", "kontrol"]
                score += sum(1 for kw in qa_keywords if kw in message_lower)
                
            elif specialist_key == "devops_engineer":
                devops_keywords = ["deploy", "yayınla", "sunucu", "altyapı", "docker", "cloud"]
                score += sum(1 for kw in devops_keywords if kw in message_lower)
                
            intent_scores[specialist_key] = score
            
        # Normalize scores
        max_score = max(intent_scores.values()) if intent_scores.values() else 1
        for key in intent_scores:
            intent_scores[key] = intent_scores[key] / max_score if max_score > 0 else 0
            
        return intent_scores
        
    def select_specialists(self, intent_scores: Dict[str, float], threshold: float = 0.3) -> list:
        """Select specialists based on intent scores"""
        
        selected = []
        
        # Always include specialists with high scores
        for specialist_key, score in intent_scores.items():
            if score >= threshold:
                selected.append(specialist_key)
                
        # Ensure at least one specialist is selected
        if not selected:
            # Select the highest scoring specialist
            best_specialist = max(intent_scores.items(), key=lambda x: x[1])
            selected.append(best_specialist[0])
            
        # For new projects, include project manager by default
        if any(keyword in intent_scores for keyword in ["başla", "yeni", "proje"]):
            if "project_manager" not in selected:
                selected.append("project_manager")
                
        return selected
        
    def get_specialist_response(self, specialist_key: str, message: str) -> Optional[str]:
        """Get response from a specific specialist"""
        
        if specialist_key not in self.specialists:
            return None
            
        specialist = self.specialists[specialist_key]
        
        # Find an available adapter
        adapter = None
        for adapter_name, adapter_instance in self.adapters.items():
            if adapter_instance and hasattr(adapter_instance, 'generate_response'):
                adapter = adapter_instance
                break
                
        if not adapter:
            logger.error("No available adapter for specialist response")
            return None
            
        try:
            prompt = specialist.prompt_template.format(message=message)
            response = adapter.generate_response(prompt)
            return response
            
        except Exception as e:
            logger.error(f"Error getting specialist response for {specialist_key}: {e}")
            return None
            
    def orchestrate_response(self, message: str) -> OrchestratorResponse:
        """Orchestrate multi-specialist response to user message"""
        
        logger.info(f"Orchestrating response for message: {message[:100]}...")
        
        # Add to conversation history
        self.conversation_history.append({"role": "user", "message": message})
        
        # Analyze intent
        intent_scores = self.analyze_message_intent(message)
        logger.info(f"Intent scores: {intent_scores}")
        
        # Select specialists
        selected_specialists = self.select_specialists(intent_scores)
        logger.info(f"Selected specialists: {selected_specialists}")
        
        # Get responses from specialists
        specialist_responses = {}
        for specialist_key in selected_specialists:
            response = self.get_specialist_response(specialist_key, message)
            if response:
                specialist_responses[specialist_key] = response
                logger.info(f"Got response from {specialist_key}")
                
        # Generate primary orchestrated response
        primary_response = self.generate_orchestrated_response(message, specialist_responses)
        
        # Suggest next actions
        suggested_actions = self.suggest_next_actions(message, selected_specialists)
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "assistant", 
            "message": primary_response,
            "specialists": selected_specialists,
            "specialist_responses": specialist_responses
        })
        
        return OrchestratorResponse(
            primary_response=primary_response,
            specialist_responses=specialist_responses,
            active_specialists=selected_specialists,
            suggested_next_actions=suggested_actions
        )
        
    def generate_orchestrated_response(self, message: str, specialist_responses: Dict[str, str]) -> str:
        """Generate coordinated response from specialist inputs"""
        
        if not specialist_responses:
            return "Üzgünüm, şu anda uzmanlardan yanıt alamadım. Lütfen tekrar deneyin."
            
        # Find an adapter for orchestration
        adapter = None
        for adapter_name, adapter_instance in self.adapters.items():
            if adapter_instance and hasattr(adapter_instance, 'generate_response'):
                adapter = adapter_instance
                break
                
        if not adapter:
            # Fallback: simple concatenation
            response_parts = []
            for specialist_key, response in specialist_responses.items():
                specialist_name = self.specialists[specialist_key].name
                response_parts.append(f"## {specialist_name} Görüşü:\n{response}\n")
            return "\n".join(response_parts)
            
        try:
            # Create orchestration prompt
            specialist_inputs = ""
            for specialist_key, response in specialist_responses.items():
                specialist_name = self.specialists[specialist_key].name
                specialist_inputs += f"\n### {specialist_name}:\n{response}\n"
                
            orchestration_prompt = f"""Sen bir uzman koordinatörüsün. Kullanıcının sorusuna farklı uzmanlardan gelen yanıtları koordine ederek tek bir tutarlı yanıt hazırla.

Kullanıcı Sorusu: {message}

Uzman Yanıtları:{specialist_inputs}

Görevin:
1. Uzman yanıtlarını analiz et
2. Çelişkileri çöz 
3. En önemli noktaları öne çıkar
4. Tutarlı, kapsamlı ve uygulanabilir bir yanıt hazırla
5. Türkçe ve anlaşılır bir dille yanıtla

Koordine edilmiş yanıt:"""

            orchestrated_response = adapter.generate_response(orchestration_prompt)
            return orchestrated_response
            
        except Exception as e:
            logger.error(f"Error in orchestration: {e}")
            # Fallback response
            response_parts = []
            for specialist_key, response in specialist_responses.items():
                specialist_name = self.specialists[specialist_key].name
                response_parts.append(f"## {specialist_name} Görüşü:\n{response}\n")
            return "\n".join(response_parts)
            
    def suggest_next_actions(self, message: str, active_specialists: list) -> list:
        """Suggest next actions based on current context"""
        
        suggestions = []
        
        # Based on active specialists, suggest relevant next steps
        if "project_manager" in active_specialists:
            suggestions.append("Proje detaylarını ve gereksinimlerini belirle")
            suggestions.append("Zaman çizelgesi ve milestone'ları planla")
            
        if "lead_developer" in active_specialists:
            suggestions.append("Teknik mimariyi detaylandır")
            suggestions.append("Geliştirme ortamını kur")
            
        if "ui_ux_designer" in active_specialists:
            suggestions.append("Kullanıcı persona'larını tanımla")
            suggestions.append("Wireframe ve mockup hazırla")
            
        if "marketing_specialist" in active_specialists:
            suggestions.append("Hedef kitle analizini derinleştir")
            suggestions.append("Rekabet analizi yap")
            
        if "business_analyst" in active_specialists:
            suggestions.append("İş gereksinimlerini dokümante et")
            suggestions.append("Süreç haritalarını çıkar")
            
        if "qa_engineer" in active_specialists:
            suggestions.append("Test stratejisini belirle")
            suggestions.append("Kalite kriterlerini tanımla")
            
        if "devops_engineer" in active_specialists:
            suggestions.append("CI/CD pipeline'ını kur")
            suggestions.append("Altyapı planını hazırla")
            
        return suggestions[:5]  # Limit to 5 suggestions
        
    def get_specialist_info(self) -> Dict[str, Dict]:
        """Get information about all specialists"""
        
        specialist_info = {}
        for key, specialist in self.specialists.items():
            specialist_info[key] = {
                "name": specialist.name,
                "description": specialist.description,
                "expertise": specialist.expertise
            }
        return specialist_info

class OrchestratorWebApp:
    """Web application for AI Orchestrator"""
    
    def __init__(self):
        # Handle paths for both development and PyInstaller EXE
        if hasattr(sys, '_MEIPASS'):
            # Running as PyInstaller EXE
            template_dir = os.path.join(sys._MEIPASS, 'templates')
            static_dir = os.path.join(sys._MEIPASS, 'static')
        else:
            # Running from source
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            template_dir = os.path.join(base_dir, 'templates')
            static_dir = os.path.join(base_dir, 'static')
        
        self.app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
        self.adapters = {}
        self.orchestrator = None
        self.setup_routes()
        
    def load_adapters(self) -> bool:
        """Load available AI adapters"""
        try:
            secure_config = SecureConfigManager()
            
            # Try to load adapters
            adapters_loaded = 0
            
            # Load Gemini adapters
            gemini_key = secure_config.get_api_key('gemini')
            if gemini_key:
                from ai_adapters.gemini_adapter import GeminiAdapter
                
                # Create multiple Gemini instances for different specialists
                self.adapters['gemini-main'] = GeminiAdapter(api_key=gemini_key)
                self.adapters['gemini-specialist'] = GeminiAdapter(api_key=gemini_key)
                adapters_loaded += 2
                
            # Load OpenAI adapters if available
            openai_key = secure_config.get_api_key('openai')
            if openai_key:
                from ai_adapters.openai_adapter import OpenAIAdapter
                self.adapters['openai-main'] = OpenAIAdapter(api_key=openai_key)
                adapters_loaded += 1
                
            logger.info(f"Loaded {adapters_loaded} AI adapters")
            
            if adapters_loaded > 0:
                self.orchestrator = AIOrchestrator(self.adapters)
                return True
            else:
                logger.warning("No AI adapters loaded")
                return False
                
        except Exception as e:
            logger.error(f"Error loading adapters: {e}")
            return False
            
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            return render_template('orchestrator.html')
            
        @self.app.route('/orchestrate', methods=['POST'])
        def orchestrate():
            try:
                data = request.get_json()
                message = data.get('message', '')
                
                if not message:
                    return jsonify({'success': False, 'error': 'Mesaj boş olamaz'})
                
                if not self.orchestrator:
                    return jsonify({'success': False, 'error': 'Orchestrator hazır değil'})
                
                # Get orchestrated response
                response = self.orchestrator.orchestrate_response(message)
                
                return jsonify({
                    'success': True,
                    'data': {
                        'primary_response': response.primary_response,
                        'specialist_responses': response.specialist_responses,
                        'active_specialists': response.active_specialists,
                        'suggested_next_actions': response.suggested_next_actions
                    }
                })
                
            except Exception as e:
                logger.error(f"Error in orchestrate endpoint: {e}")
                return jsonify({'success': False, 'error': str(e)})
                
        @self.app.route('/specialist_info')
        def specialist_info():
            try:
                if not self.orchestrator:
                    return jsonify({'success': False, 'error': 'Orchestrator hazır değil'})
                    
                specialists = self.orchestrator.get_specialist_info()
                return jsonify({'success': True, 'specialists': specialists})
                
            except Exception as e:
                logger.error(f"Error in specialist_info endpoint: {e}")
                return jsonify({'success': False, 'error': str(e)})
                
        @self.app.route('/system_status')
        def system_status():
            try:
                adapters_available = len([a for a in self.adapters.values() if a is not None])
                specialists_available = len(self.orchestrator.specialists) if self.orchestrator else 0
                
                return jsonify({
                    'success': True,
                    'status': {
                        'adapters_available': adapters_available,
                        'specialists_available': specialists_available,
                        'orchestrator_ready': self.orchestrator is not None
                    }
                })
                
            except Exception as e:
                logger.error(f"Error in system_status endpoint: {e}")
                return jsonify({'success': False, 'error': str(e)})
                
        @self.app.route('/api_management')
        def api_management():
            return render_template('api_management.html')
            
    def run(self, host='localhost', port=5000, debug=False):
        """Run the web application"""
        self.app.run(host=host, port=port, debug=debug)

def main():
    """Main function"""
    print("🧠 AI Orchestrator - MCP Style System")
    print("=" * 50)
    
    # Initialize web app
    app = OrchestratorWebApp()
    
    # Load adapters
    print("🔧 AI adapterleri yükleniyor...")
    if not app.load_adapters():
        print("❌ API anahtarları bulunamadı!")
        print("\n📝 Lütfen API anahtarlarınızı ayarlayın:")
        print("1. Web arayüzünden API Yönetimi > API anahtarlarını girin")
        print("2. Sistem otomatik olarak adapterleri yükleyecek")
        print("\n🌐 Web arayüzü başlatılıyor...")
    else:
        print("✅ AI adapterleri başarıyla yüklendi")
        print(f"🤖 {len(app.adapters)} adapter aktif")
        print(f"👥 {len(app.orchestrator.specialists)} uzman hazır")
    
    # Start web server
    print("\n🌐 Web sunucusu başlatılıyor...")
    print("🚀 http://localhost:5000 adresinde açılacak")
    
    try:
        # Open browser automatically
        threading.Timer(2.0, lambda: webbrowser.open('http://localhost:5000')).start()
        
        # Run Flask app
        app.run(host='localhost', port=5000, debug=False)
        
    except KeyboardInterrupt:
        print("\n⚠️ Sistem kapatılıyor...")
    except Exception as e:
        print(f"❌ Hata oluştu: {e}")

if __name__ == "__main__":
    main()