import time
from datetime import datetime

class ProjectManager:
    def __init__(self, message_broker, browser_handler=None, name="Proje Yöneticisi"):
        self.name = name
        self.message_broker = message_broker
        self.browser_handler = browser_handler
        self.role = "project_manager"
        self.active_tasks = []
        self.team_members = []
        
        # Message broker'a abone ol
        self.message_broker.subscribe("ld_to_pm", self.receive_message)
        self.message_broker.subscribe("boss_to_pm", self.receive_message)
        
        print(f"👔 {self.name} sisteme bağlandı")

    def receive_message(self, message_obj):
        """Gelen mesajları işle"""
        sender = message_obj.get("sender", "Bilinmeyen")
        content = message_obj.get("content", "")
        
        print(f"📨 {self.name} mesaj aldı [{sender}]: {content[:100]}...")
        
        # Mesaja göre otomatik yanıt ver
        if "görev tamamlandı" in content.lower() or "task completed" in content.lower():
            self.provide_feedback("Harika iş! Görev başarıyla tamamlanmış. Bir sonraki aşamaya geçebiliriz.")
        elif "sorun" in content.lower() or "problem" in content.lower():
            self.provide_feedback("Anlıyorum. Bu sorunu birlikte çözelim. Detayları paylaşabilir misin?")
        elif "yardım" in content.lower() or "help" in content.lower():
            self.provide_feedback("Tabii ki yardım edebilirim. Hangi konuda desteğe ihtiyacın var?")

    def assign_task(self, task_description, target_member="Lead Developer"):
        """Görev ata"""
        task = {
            "id": f"task_{int(time.time())}",
            "description": task_description,
            "assigned_to": target_member,
            "assigned_by": self.name,
            "created_at": datetime.now().isoformat(),
            "status": "assigned"
        }
        
        self.active_tasks.append(task)
        
        # Mesaj oluştur ve gönder
        message = f"🎯 Yeni Görev Ataması:\n\n" \
                 f"Görev: {task_description}\n" \
                 f"Atanan: {target_member}\n" \
                 f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n" \
                 f"Lütfen bu görevi incele ve geri bildirimde bulun."
        
        self.message_broker.publish("pm_to_ld", message, sender=self.name)
        
        # Browser'a da gönder (eğer varsa)
        if self.browser_handler:
            self.browser_handler.send_message(self.role, message)
        
        print(f"📋 Görev atandı: {task_description}")
        return task

    def provide_feedback(self, feedback):
        """Geri bildirim ver"""
        message = f"💬 Proje Yöneticisi Geri Bildirimi:\n\n{feedback}\n\n" \
                 f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        self.message_broker.publish("pm_to_ld", message, sender=self.name)
        
        # Browser'a da gönder (eğer varsa)
        if self.browser_handler:
            self.browser_handler.send_message(self.role, message)
        
        print(f"💬 Geri bildirim verildi: {feedback[:50]}...")

    def request_status_update(self):
        """Durum güncellemesi iste"""
        message = f"📊 Merhaba! Aktif görevlerin durumu hakkında güncelleme alabilir miyim?\n\n" \
                 f"Lütfen aşağıdaki konularda bilgi ver:\n" \
                 f"• Tamamlanan işler\n" \
                 f"• Devam eden çalışmalar\n" \
                 f"• Karşılaşılan sorunlar\n" \
                 f"• İhtiyaç duyulan destek"
        
        self.message_broker.publish("pm_to_ld", message, sender=self.name)
        
        if self.browser_handler:
            self.browser_handler.send_message(self.role, message)

    def create_project_plan(self, project_name, requirements):
        """Proje planı oluştur"""
        plan_message = f"📋 PROJE PLANI: {project_name}\n\n" \
                      f"Gereksinimler:\n{requirements}\n\n" \
                      f"Lütfen bu projeyi değerlendir ve implementasyon önerilerini paylaş.\n" \
                      f"Hangi teknolojileri kullanmayı planlıyorsun?"
        
        self.message_broker.publish("pm_to_ld", plan_message, sender=self.name)
        
        if self.browser_handler:
            self.browser_handler.send_message(self.role, plan_message)

    def get_active_tasks(self):
        """Aktif görevleri getir"""
        return self.active_tasks

    def set_browser_handler(self, browser_handler):
        """Browser handler'ı ayarla"""
        self.browser_handler = browser_handler