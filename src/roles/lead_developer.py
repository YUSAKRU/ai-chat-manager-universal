import time
from datetime import datetime

class LeadDeveloper:
    def __init__(self, message_broker, browser_handler=None, name="Uzman Geliştirici"):
        self.name = name
        self.message_broker = message_broker
        self.browser_handler = browser_handler
        self.role = "lead_developer"
        self.current_tasks = []
        self.completed_tasks = []
        self.skills = ["Python", "JavaScript", "React", "Node.js", "AI/ML"]
        
        # Message broker'a abone ol
        self.message_broker.subscribe("pm_to_ld", self.receive_message)
        self.message_broker.subscribe("boss_to_ld", self.receive_message)
        
        print(f"👨‍💻 {self.name} sisteme bağlandı")

    def receive_message(self, message_obj):
        """Gelen mesajları işle"""
        sender = message_obj.get("sender", "Bilinmeyen")
        content = message_obj.get("content", "")
        
        print(f"📨 {self.name} mesaj aldı [{sender}]: {content[:100]}...")
        
        # Mesaja göre otomatik yanıt ver
        if "görev ataması" in content.lower() or "task" in content.lower():
            self.acknowledge_task(content)
        elif "durum güncellemesi" in content.lower() or "status update" in content.lower():
            self.report_progress()
        elif "proje planı" in content.lower() or "project plan" in content.lower():
            self.analyze_project_requirements(content)

    def acknowledge_task(self, task_content):
        """Görev alındığını onaylا"""
        response = f"✅ Görev Alındı!\n\n" \
                  f"Görev detaylarını inceledim. Aşağıdaki yaklaşımı öneriyorum:\n\n" \
                  f"🔍 Analiz Aşaması:\n" \
                  f"• Gereksinimleri detaylı olarak analiz edeceğim\n" \
                  f"• Teknik spesifikasyonları belirleyeceğim\n" \
                  f"• Risk analizini yapacağım\n\n" \
                  f"⚡ İmplementasyon:\n" \
                  f"• Modüler yapı kullanacağım\n" \
                  f"• Best practices'leri uygulayacağım\n" \
                  f"• Test odaklı geliştirme yapacağım\n\n" \
                  f"📅 Tahmini süre hakkında kısa sürede bilgi vereceğim."
        
        self.message_broker.publish("ld_to_pm", response, sender=self.name)
        
        if self.browser_handler:
            self.browser_handler.send_message(self.role, response)

    def report_progress(self, custom_message=None):
        """İlerleme raporla"""
        if custom_message:
            message = custom_message
        else:
            message = f"📊 DURUM RAPORU - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n" \
                     f"🔥 Aktif Görevler: {len(self.current_tasks)}\n" \
                     f"✅ Tamamlanan: {len(self.completed_tasks)}\n\n" \
                     f"💪 Mevcut Çalışmalarım:\n" \
                     f"• Kod review ve optimizasyon\n" \
                     f"• API entegrasyonları\n" \
                     f"• Test senaryoları\n\n" \
                     f"🚀 Öncelikli Konular:\n" \
                     f"• Performance iyileştirmeler\n" \
                     f"• Security best practices\n" \
                     f"• Kullanıcı deneyimi optimizasyonu\n\n" \
                     f"❓ İhtiyaç Duyduğum Destek:\n" \
                     f"• Tasarım spesifikasyonları\n" \
                     f"• API dokümantasyonu"
        
        self.message_broker.publish("ld_to_pm", message, sender=self.name)
        
        if self.browser_handler:
            self.browser_handler.send_message(self.role, message)
        
        print(f"📊 İlerleme raporu gönderildi")

    def implement_feature(self, feature_description):
        """Özellik implementasyonu"""
        implementation_plan = f"🛠️ FEATURE İMPLEMENTASYONU\n\n" \
                             f"Özellik: {feature_description}\n\n" \
                             f"📋 İmplementasyon Planı:\n" \
                             f"1. Gereksinim analizi ✅\n" \
                             f"2. Teknik tasarım 🔄\n" \
                             f"3. Kod geliştirme ⏳\n" \
                             f"4. Unit testler ⏳\n" \
                             f"5. Integration testler ⏳\n" \
                             f"6. Code review ⏳\n" \
                             f"7. Deployment ⏳\n\n" \
                             f"🔧 Kullanılacak Teknolojiler:\n" \
                             f"• Backend: Python/FastAPI\n" \
                             f"• Frontend: React/TypeScript\n" \
                             f"• Database: PostgreSQL\n" \
                             f"• Testing: Pytest, Jest\n\n" \
                             f"⏱️ Tahmini süre: 3-5 gün"
        
        self.message_broker.publish("ld_to_pm", implementation_plan, sender=self.name)
        
        if self.browser_handler:
            self.browser_handler.send_message(self.role, implementation_plan)

    def analyze_project_requirements(self, project_content):
        """Proje gereksinimlerini analiz et"""
        analysis = f"🔍 PROJE ANALİZİ\n\n" \
                  f"Proje detaylarını inceledim. İşte teknik değerlendirmem:\n\n" \
                  f"💡 Önerilen Teknoloji Stack:\n" \
                  f"• Frontend: React + TypeScript\n" \
                  f"• Backend: Python FastAPI\n" \
                  f"• Database: PostgreSQL\n" \
                  f"• Real-time: WebSocket/Socket.IO\n" \
                  f"• Hosting: Docker + AWS/Azure\n\n" \
                  f"⚠️ Dikkat Edilmesi Gerekenler:\n" \
                  f"• Scalability planlaması\n" \
                  f"• Security best practices\n" \
                  f"• API rate limiting\n" \
                  f"• Error handling\n\n" \
                  f"📋 Geliştirme Süreci:\n" \
                  f"• Agile/Scrum metodolojisi\n" \
                  f"• Git flow kullanımı\n" \
                  f"• CI/CD pipeline kurulumu\n" \
                  f"• Automated testing\n\n" \
                  f"🕐 Tahmini proje süresi: 2-3 hafta"
        
        self.message_broker.publish("ld_to_pm", analysis, sender=self.name)
        
        if self.browser_handler:
            self.browser_handler.send_message(self.role, analysis)

    def ask_question(self, question):
        """Soru sor"""
        message = f"❓ SORU/AÇIKLAMA TALEBİ\n\n" \
                 f"{question}\n\n" \
                 f"Lütfen bu konuda rehberlik edebilir misin?"
        
        self.message_broker.publish("ld_to_pm", message, sender=self.name)
        
        if self.browser_handler:
            self.browser_handler.send_message(self.role, message)

    def suggest_improvement(self, area, suggestion):
        """İyileştirme öner"""
        message = f"💡 İYİLEŞTİRME ÖNERİSİ\n\n" \
                 f"Alan: {area}\n" \
                 f"Öneri: {suggestion}\n\n" \
                 f"Bu iyileştirme performans ve kullanıcı deneyimini artıracaktır."
        
        self.message_broker.publish("ld_to_pm", message, sender=self.name)
        
        if self.browser_handler:
            self.browser_handler.send_message(self.role, message)

    def set_browser_handler(self, browser_handler):
        """Browser handler'ı ayarla"""
        self.browser_handler = browser_handler