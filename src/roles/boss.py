import time
from datetime import datetime

class Boss:
    def __init__(self, message_broker, browser_handler=None, name="Patron"):
        self.name = name
        self.message_broker = message_broker
        self.browser_handler = browser_handler
        self.role = "boss"
        self.is_monitoring = False
        
        print(f"👑 {self.name} sisteme bağlandı")

    def join_conversation(self, announcement=True):
        """Konuşmaya katıl"""
        self.is_monitoring = True
        
        # Tüm kanallara abone ol
        self.message_broker.subscribe("pm_to_ld", self.monitor_conversation)
        self.message_broker.subscribe("ld_to_pm", self.monitor_conversation)
        
        if announcement:
            message = f"👑 PATRON KONUŞMAYA KATILDI\n\n" \
                     f"Merhaba ekip! Ben {self.name}.\n" \
                     f"Konuşmanızı takip ediyorum ve gerektiğinde müdahale edeceğim.\n\n" \
                     f"🎯 Beklentilerim:\n" \
                     f"• Kaliteli ve hızlı çözümler\n" \
                     f"• Açık iletişim\n" \
                     f"• Proaktif yaklaşım\n" \
                     f"• Problem çözme odaklılık\n\n" \
                     f"Başarılar!"
            
            # Her iki kanala da mesaj gönder
            self.message_broker.publish("boss_to_pm", message, sender=self.name)
            self.message_broker.publish("boss_to_ld", message, sender=self.name)

    def monitor_conversation(self, message_obj):
        """Konuşmayı takip et"""
        if self.is_monitoring:
            sender = message_obj.get("sender", "")
            content = message_obj.get("content", "")
            
            # Kritik durumlarda otomatik müdahale
            if any(keyword in content.lower() for keyword in ["sorun", "problem", "hata", "gecikme", "blocked"]):
                self.intervene_automatically(content, sender)

    def intervene_automatically(self, problematic_content, sender):
        """Otomatik müdahale"""
        intervention = f"👑 PATRON MÜDAHALESİ\n\n" \
                      f"Bir sorun tespit ettim. Hemen çözüm odaklı hareket edelim!\n\n" \
                      f"🔍 Sorun: {problematic_content[:100]}...\n\n" \
                      f"💡 Önerilerim:\n" \
                      f"• Sorunu detaylandıralım\n" \
                      f"• Alternatif çözümler düşünelim\n" \
                      f"• Gerekirse external yardım alalım\n" \
                      f"• Timeline'ı gözden geçirelim\n\n" \
                      f"Bu konuyu öncelik haline getirelim!"
        
        self.message_broker.publish("boss_to_pm", intervention, sender=self.name)
        self.message_broker.publish("boss_to_ld", intervention, sender=self.name)

    def send_directive(self, message, target="both"):
        """Direktif gönder"""
        formatted_message = f"👑 PATRON DİREKTİFİ\n\n{message}\n\n" \
                           f"Bu talimatın yerine getirilmesini bekliyorum.\n" \
                           f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        if target in ["both", "pm"]:
            self.message_broker.publish("boss_to_pm", formatted_message, sender=self.name)
        if target in ["both", "ld"]:
            self.message_broker.publish("boss_to_ld", formatted_message, sender=self.name)
        
        print(f"📢 Direktif gönderildi: {message[:50]}...")

    def request_status_report(self):
        """Durum raporu iste"""
        message = f"📊 DURUM RAPORU TALEBİ\n\n" \
                 f"Ekip, detaylı bir durum raporu istiyorum:\n\n" \
                 f"📋 Proje Yöneticisi için:\n" \
                 f"• Aktif görevler ve durumları\n" \
                 f"• Timeline ve milestone'lar\n" \
                 f"• Risk faktörleri\n" \
                 f"• Kaynak ihtiyaçları\n\n" \
                 f"💻 Lead Developer için:\n" \
                 f"• Teknik progress\n" \
                 f"• Code quality metrics\n" \
                 f"• Karşılaşılan teknik zorluklar\n" \
                 f"• İhtiyaç duyulan teknik destek\n\n" \
                 f"Bu raporu 1 saat içinde bekliyorum."
        
        self.message_broker.publish("boss_to_pm", message, sender=self.name)
        self.message_broker.publish("boss_to_ld", message, sender=self.name)

    def approve_decision(self, decision):
        """Karar onayla"""
        message = f"✅ ONAY\n\n" \
                 f"Karar: {decision}\n\n" \
                 f"Bu kararı onaylıyorum. Hayata geçirin!"
        
        self.message_broker.publish("boss_to_pm", message, sender=self.name)
        self.message_broker.publish("boss_to_ld", message, sender=self.name)

    def reject_proposal(self, proposal, reason):
        """Öneriyi reddet"""
        message = f"❌ RED\n\n" \
                 f"Reddedilen öneri: {proposal}\n" \
                 f"Sebep: {reason}\n\n" \
                 f"Lütfen alternatif çözümler getirin."
        
        self.message_broker.publish("boss_to_pm", message, sender=self.name)
        self.message_broker.publish("boss_to_ld", message, sender=self.name)

    def set_priority(self, task, priority_level="HIGH"):
        """Öncelik belirle"""
        message = f"🔥 ÖNCELİK ATAMASI\n\n" \
                 f"Görev: {task}\n" \
                 f"Öncelik Seviyesi: {priority_level}\n\n" \
                 f"Bu görev diğer her şeyden önce tamamlanmalı!"
        
        self.message_broker.publish("boss_to_pm", message, sender=self.name)
        self.message_broker.publish("boss_to_ld", message, sender=self.name)

    def motivate_team(self):
        """Takımı motive et"""
        motivational_message = f"🚀 TAKIM MOTİVASYONU\n\n" \
                              f"Harika iş çıkarıyorsunuz ekip! 👏\n\n" \
                              f"🌟 Güçlü yanlarınız:\n" \
                              f"• İletişim kalitesi\n" \
                              f"• Problem çözme becerisi\n" \
                              f"• Proaktif yaklaşım\n" \
                              f"• Teknik uzmanlık\n\n" \
                              f"Böyle devam edin, hedefe yaklaştık! 🎯"
        
        self.message_broker.publish("boss_to_pm", motivational_message, sender=self.name)
        self.message_broker.publish("boss_to_ld", motivational_message, sender=self.name)

    def stop_monitoring(self):
        """İzlemeyi durdur"""
        self.is_monitoring = False
        print(f"👑 {self.name} izlemeyi durdurdu")

    def set_browser_handler(self, browser_handler):
        """Browser handler'ı ayarla"""
        self.browser_handler = browser_handler