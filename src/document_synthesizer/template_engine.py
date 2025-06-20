"""
📄 TemplateEngine - Professional Document Templates
=================================================

Yapılandırılmış belgeler için profesyonel şablonlar:
- Meeting Summary templates
- Decision Log templates  
- Action Items templates
- Project Brief templates
"""

from typing import Dict, Any, List
from datetime import datetime
from .conversation_analyzer import ConversationInsights, ConversationParticipant, DecisionItem, ActionItem


class TemplateEngine:
    """Professional Document Template Generator"""
    
    def __init__(self):
        self.template_dir = "templates/documents"
        
    def generate_meeting_summary_markdown(self, insights: ConversationInsights) -> str:
        """Meeting Summary için Markdown template"""
        
        template = f"""# 📋 {insights.title}

**Oluşturulma Tarihi:** {self._format_date(insights.created_at)}  
**Session ID:** `{insights.session_id}`  
**Toplam Tur:** {insights.total_turns}  
**Süre:** {insights.duration_summary}

---

## 🎯 Toplantı Amacı

{insights.purpose}

---

## 👥 Katılımcılar

{self._format_participants(insights.participants)}

---

## 🔑 Ana Tartışma Noktaları

{self._format_key_points(insights.key_points)}

---

## ✅ Alınan Kararlar

{self._format_decisions(insights.decisions)}

---

## 📋 Eylem Maddeleri

{self._format_action_items(insights.action_items)}

---

## 📊 Özet

- **Toplam Katılımcı:** {len(insights.participants)}
- **Ana Konu Sayısı:** {len(insights.key_points)}
- **Alınan Karar:** {len(insights.decisions)}
- **Eylem Maddesi:** {len(insights.action_items)}

---

*Bu belge AI Document Synthesizer tarafından otomatik olarak oluşturulmuştur.*  
*Oluşturulma Zamanı: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}*
"""
        
        return template.strip()
    
    def generate_meeting_summary_html(self, insights: ConversationInsights) -> str:
        """Meeting Summary için HTML template"""
        
        html_template = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{insights.title} - Toplantı Özeti</title>
    <style>
        {self._get_html_styles()}
    </style>
</head>
<body>
    <div class="container">
        <header class="document-header">
            <h1>📋 {insights.title}</h1>
            <div class="document-meta">
                <span class="meta-item">📅 {self._format_date(insights.created_at)}</span>
                <span class="meta-item">🆔 {insights.session_id[:8]}</span>
                <span class="meta-item">⏱️ {insights.duration_summary}</span>
                <span class="meta-item">🔄 {insights.total_turns} Tur</span>
            </div>
        </header>

        <section class="purpose-section">
            <h2>🎯 Toplantı Amacı</h2>
            <p class="purpose-text">{insights.purpose}</p>
        </section>

        <section class="participants-section">
            <h2>👥 Katılımcılar</h2>
            {self._format_participants_html(insights.participants)}
        </section>

        <section class="key-points-section">
            <h2>🔑 Ana Tartışma Noktaları</h2>
            {self._format_key_points_html(insights.key_points)}
        </section>

        <section class="decisions-section">
            <h2>✅ Alınan Kararlar</h2>
            {self._format_decisions_html(insights.decisions)}
        </section>

        <section class="actions-section">
            <h2>📋 Eylem Maddeleri</h2>
            {self._format_action_items_html(insights.action_items)}
        </section>

        <section class="summary-section">
            <h2>📊 Özet</h2>
            <div class="summary-grid">
                <div class="summary-item">
                    <span class="summary-number">{len(insights.participants)}</span>
                    <span class="summary-label">Katılımcı</span>
                </div>
                <div class="summary-item">
                    <span class="summary-number">{len(insights.key_points)}</span>
                    <span class="summary-label">Ana Konu</span>
                </div>
                <div class="summary-item">
                    <span class="summary-number">{len(insights.decisions)}</span>
                    <span class="summary-label">Karar</span>
                </div>
                <div class="summary-item">
                    <span class="summary-number">{len(insights.action_items)}</span>
                    <span class="summary-label">Eylem</span>
                </div>
            </div>
        </section>

        <footer class="document-footer">
            <p>Bu belge <strong>AI Document Synthesizer</strong> tarafından otomatik olarak oluşturulmuştur.</p>
            <p>Oluşturulma Zamanı: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
        </footer>
    </div>
</body>
</html>"""
        
        return html_template
    
    def generate_action_items_markdown(self, insights: ConversationInsights) -> str:
        """Action Items için specialized Markdown template"""
        
        template = f"""# 📋 Eylem Planı - {insights.title}

**Oluşturulma Tarihi:** {self._format_date(insights.created_at)}  
**Kaynak Toplantı:** {insights.session_id}

---

## 🎯 Toplantı Özeti

{insights.purpose}

---

## ⚡ Yüksek Öncelikli Görevler

{self._format_action_items_by_priority(insights.action_items, 'high')}

---

## 📊 Orta Öncelikli Görevler

{self._format_action_items_by_priority(insights.action_items, 'medium')}

---

## 📝 Düşük Öncelikli Görevler

{self._format_action_items_by_priority(insights.action_items, 'low')}

---

## 👥 Sorumlular Bazında

{self._format_action_items_by_assignee(insights.action_items)}

---

## 📈 İlerleme Takibi

- [ ] Yüksek öncelikli görevler tamamlandı
- [ ] Orta öncelikli görevler %50 tamamlandı  
- [ ] Tüm görevler assign edildi
- [ ] İlk checkpoint toplantısı planlandı

---

*Bu eylem planı {datetime.now().strftime('%d.%m.%Y')} tarihinde oluşturulmuştur.*
"""
        
        return template.strip()
    
    def generate_decisions_log_markdown(self, insights: ConversationInsights) -> str:
        """Decision Log için specialized Markdown template"""
        
        template = f"""# ✅ Karar Defteri - {insights.title}

**Toplantı Tarihi:** {self._format_date(insights.created_at)}  
**Katılımcılar:** {', '.join([p.display_name for p in insights.participants])}

---

## 📋 Toplantı Bağlamı

{insights.purpose}

---

## 🎯 Alınan Kararlar

{self._format_decisions_detailed(insights.decisions)}

---

## 📊 Karar Özeti

- **Toplam Karar Sayısı:** {len(insights.decisions)}
- **Yüksek Güvenirlik (>0.8):** {len([d for d in insights.decisions if d.confidence_level > 0.8])}
- **Orta Güvenirlik (0.5-0.8):** {len([d for d in insights.decisions if 0.5 <= d.confidence_level <= 0.8])}
- **Düşük Güvenirlik (<0.5):** {len([d for d in insights.decisions if d.confidence_level < 0.5])}

---

## 🔄 Takip Gereken Kararlar

{self._format_follow_up_decisions(insights.decisions)}

---

*Bu karar defteri resmi kayıt niteliğindedir.*  
*Oluşturulma: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}*
"""
        
        return template.strip()
    
    # Formatting Helper Methods
    
    def _format_date(self, iso_date: str) -> str:
        """ISO date'i Türkçe formata çevir"""
        try:
            dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
            return dt.strftime('%d.%m.%Y %H:%M')
        except:
            return iso_date
    
    def _format_participants(self, participants: List[ConversationParticipant]) -> str:
        """Katılımcıları Markdown formatında listele"""
        if not participants:
            return "*Katılımcı bilgisi bulunamadı.*"
        
        lines = []
        for p in participants:
            lines.append(f"- **{p.display_name}** ({p.role})")
            lines.append(f"  - Mesaj Sayısı: {p.message_count}")
            if p.key_contributions:
                lines.append("  - Ana Katkıları:")
                for contrib in p.key_contributions:
                    lines.append(f"    - {contrib}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_participants_html(self, participants: List[ConversationParticipant]) -> str:
        """Katılımcıları HTML formatında listele"""
        if not participants:
            return "<p><em>Katılımcı bilgisi bulunamadı.</em></p>"
        
        html = "<div class='participants-grid'>"
        for p in participants:
            html += f"""
            <div class='participant-card'>
                <h3>{p.display_name}</h3>
                <p class='participant-role'>{p.role}</p>
                <p class='participant-stats'>{p.message_count} mesaj</p>
                <div class='participant-contributions'>
                    <h4>Ana Katkıları:</h4>
                    <ul>
            """
            for contrib in p.key_contributions:
                html += f"<li>{contrib}</li>"
            html += "</ul></div></div>"
        
        html += "</div>"
        return html
    
    def _format_key_points(self, key_points: List[str]) -> str:
        """Ana noktaları Markdown formatında listele"""
        if not key_points:
            return "*Ana tartışma noktası tespit edilemedi.*"
        
        lines = []
        for i, point in enumerate(key_points, 1):
            lines.append(f"{i}. {point}")
        
        return "\n".join(lines)
    
    def _format_key_points_html(self, key_points: List[str]) -> str:
        """Ana noktaları HTML formatında listele"""
        if not key_points:
            return "<p><em>Ana tartışma noktası tespit edilemedi.</em></p>"
        
        html = "<ol class='key-points-list'>"
        for point in key_points:
            html += f"<li class='key-point-item'>{point}</li>"
        html += "</ol>"
        
        return html
    
    def _format_decisions(self, decisions: List[DecisionItem]) -> str:
        """Kararları Markdown formatında listele"""
        if not decisions:
            return "*Bu toplantıda net karar alınmamıştır.*"
        
        lines = []
        for i, decision in enumerate(decisions, 1):
            confidence_icon = "🟢" if decision.confidence_level > 0.8 else "🟡" if decision.confidence_level > 0.5 else "🔴"
            lines.append(f"### {i}. {decision.decision} {confidence_icon}")
            lines.append(f"**Bağlam:** {decision.context}")
            lines.append(f"**Katılımcılar:** {', '.join(decision.participants_involved)}")
            lines.append(f"**Güvenirlik:** {decision.confidence_level:.1%}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_decisions_html(self, decisions: List[DecisionItem]) -> str:
        """Kararları HTML formatında listele"""
        if not decisions:
            return "<p><em>Bu toplantıda net karar alınmamıştır.</em></p>"
        
        html = "<div class='decisions-list'>"
        for i, decision in enumerate(decisions, 1):
            confidence_class = "high" if decision.confidence_level > 0.8 else "medium" if decision.confidence_level > 0.5 else "low"
            html += f"""
            <div class='decision-item confidence-{confidence_class}'>
                <h3>Karar {i}: {decision.decision}</h3>
                <p class='decision-context'><strong>Bağlam:</strong> {decision.context}</p>
                <p class='decision-participants'><strong>Katılımcılar:</strong> {', '.join(decision.participants_involved)}</p>
                <div class='confidence-meter'>
                    <span class='confidence-label'>Güvenirlik: {decision.confidence_level:.1%}</span>
                    <div class='confidence-bar'>
                        <div class='confidence-fill' style='width: {decision.confidence_level * 100}%'></div>
                    </div>
                </div>
            </div>
            """
        html += "</div>"
        
        return html
    
    def _format_action_items(self, action_items: List[ActionItem]) -> str:
        """Eylem maddelerini Markdown formatında listele"""
        if not action_items:
            return "*Bu toplantıdan eylem maddesi çıkmamıştır.*"
        
        lines = []
        for i, item in enumerate(action_items, 1):
            priority_icon = "🔴" if item.priority == "high" else "🟡" if item.priority == "medium" else "🟢"
            lines.append(f"### {i}. {item.action} {priority_icon}")
            lines.append(f"**Sorumlu:** {item.assignee}")
            lines.append(f"**Öncelik:** {item.priority.upper()}")
            if item.deadline:
                lines.append(f"**Teslim Tarihi:** {item.deadline}")
            lines.append(f"**Bağlam:** {item.context}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_action_items_html(self, action_items: List[ActionItem]) -> str:
        """Eylem maddelerini HTML formatında listele"""
        if not action_items:
            return "<p><em>Bu toplantıdan eylem maddesi çıkmamıştır.</em></p>"
        
        html = "<div class='action-items-list'>"
        for i, item in enumerate(action_items, 1):
            html += f"""
            <div class='action-item priority-{item.priority}'>
                <h3>Eylem {i}: {item.action}</h3>
                <div class='action-meta'>
                    <span class='assignee'>👤 {item.assignee}</span>
                    <span class='priority'>⚡ {item.priority.upper()}</span>
                    {f'<span class="deadline">📅 {item.deadline}</span>' if item.deadline else ''}
                </div>
                <p class='action-context'>{item.context}</p>
            </div>
            """
        html += "</div>"
        
        return html
    
    def _format_action_items_by_priority(self, action_items: List[ActionItem], priority: str) -> str:
        """Belirli önceliğe göre eylem maddelerini listele"""
        filtered_items = [item for item in action_items if item.priority == priority]
        
        if not filtered_items:
            return f"*{priority.upper()} öncelikli görev bulunmamaktadır.*"
        
        lines = []
        for i, item in enumerate(filtered_items, 1):
            lines.append(f"- [ ] **{item.action}**")
            lines.append(f"  - Sorumlu: {item.assignee}")
            if item.deadline:
                lines.append(f"  - Deadline: {item.deadline}")
            lines.append(f"  - Açıklama: {item.context}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_action_items_by_assignee(self, action_items: List[ActionItem]) -> str:
        """Sorumlulara göre eylem maddelerini grupla"""
        if not action_items:
            return "*Eylem maddesi bulunmamaktadır.*"
        
        assignee_groups = {}
        for item in action_items:
            if item.assignee not in assignee_groups:
                assignee_groups[item.assignee] = []
            assignee_groups[item.assignee].append(item)
        
        lines = []
        for assignee, items in assignee_groups.items():
            lines.append(f"### 👤 {assignee}")
            for item in items:
                priority_icon = "🔴" if item.priority == "high" else "🟡" if item.priority == "medium" else "🟢"
                lines.append(f"- [ ] {item.action} {priority_icon}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_decisions_detailed(self, decisions: List[DecisionItem]) -> str:
        """Detaylı karar formatı"""
        if not decisions:
            return "*Bu toplantıda net karar alınmamıştır.*"
        
        lines = []
        for i, decision in enumerate(decisions, 1):
            lines.append(f"## Karar {i}")
            lines.append(f"**Karar:** {decision.decision}")
            lines.append(f"**Gerekçe:** {decision.context}")
            lines.append(f"**Karar Verenler:** {', '.join(decision.participants_involved)}")
            lines.append(f"**Güvenirlik Skoru:** {decision.confidence_level:.1%}")
            lines.append(f"**Durum:** {'✅ Kesin' if decision.confidence_level > 0.8 else '⚠️ Gözden Geçirilmeli' if decision.confidence_level > 0.5 else '❓ Belirsiz'}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_follow_up_decisions(self, decisions: List[DecisionItem]) -> str:
        """Takip gereken kararları listele"""
        follow_up_decisions = [d for d in decisions if d.confidence_level < 0.8]
        
        if not follow_up_decisions:
            return "*Tüm kararlar yeterli güvenirlik seviyesindedir.*"
        
        lines = []
        for decision in follow_up_decisions:
            lines.append(f"- **{decision.decision}** (Güvenirlik: {decision.confidence_level:.1%})")
            lines.append(f"  - Açıklama gereken nokta: {decision.context}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _get_html_styles(self) -> str:
        """HTML template için CSS stilleri"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f8f9fa;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .document-header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e9ecef;
        }
        
        .document-header h1 {
            color: #2c3e50;
            margin-bottom: 15px;
        }
        
        .document-meta {
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
        }
        
        .meta-item {
            background: #e9ecef;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.9em;
        }
        
        section {
            margin-bottom: 30px;
        }
        
        h2 {
            color: #34495e;
            border-left: 4px solid #3498db;
            padding-left: 15px;
            margin-bottom: 15px;
        }
        
        .purpose-text {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }
        
        .participants-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }
        
        .participant-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #e9ecef;
        }
        
        .participant-card h3 {
            color: #2c3e50;
            margin-bottom: 5px;
        }
        
        .participant-role {
            color: #7f8c8d;
            font-style: italic;
        }
        
        .key-points-list {
            list-style: none;
            counter-reset: point-counter;
        }
        
        .key-point-item {
            counter-increment: point-counter;
            margin-bottom: 10px;
            padding: 10px;
            background: #f8f9fa;
            border-left: 4px solid #27ae60;
            border-radius: 5px;
        }
        
        .key-point-item::before {
            content: counter(point-counter);
            background: #27ae60;
            color: white;
            padding: 2px 8px;
            border-radius: 50%;
            margin-right: 10px;
            font-weight: bold;
        }
        
        .decisions-list .decision-item {
            margin-bottom: 20px;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #e9ecef;
        }
        
        .decision-item.confidence-high {
            border-left: 4px solid #27ae60;
            background: #f8fff8;
        }
        
        .decision-item.confidence-medium {
            border-left: 4px solid #f39c12;
            background: #fffef8;
        }
        
        .decision-item.confidence-low {
            border-left: 4px solid #e74c3c;
            background: #fff8f8;
        }
        
        .confidence-meter {
            margin-top: 10px;
        }
        
        .confidence-bar {
            background: #e9ecef;
            height: 6px;
            border-radius: 3px;
            overflow: hidden;
        }
        
        .confidence-fill {
            height: 100%;
            background: linear-gradient(90deg, #e74c3c, #f39c12, #27ae60);
            transition: width 0.3s ease;
        }
        
        .action-items-list .action-item {
            margin-bottom: 15px;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #e9ecef;
        }
        
        .action-item.priority-high {
            border-left: 4px solid #e74c3c;
            background: #fff8f8;
        }
        
        .action-item.priority-medium {
            border-left: 4px solid #f39c12;
            background: #fffef8;
        }
        
        .action-item.priority-low {
            border-left: 4px solid #27ae60;
            background: #f8fff8;
        }
        
        .action-meta {
            display: flex;
            gap: 15px;
            margin: 10px 0;
            flex-wrap: wrap;
        }
        
        .action-meta span {
            background: #e9ecef;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.85em;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }
        
        .summary-item {
            text-align: center;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
        }
        
        .summary-number {
            display: block;
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .summary-label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        
        .document-footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e9ecef;
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
        }
        
        @media (max-width: 600px) {
            .container {
                margin: 10px;
                padding: 15px;
            }
            
            .document-meta {
                flex-direction: column;
                align-items: center;
            }
            
            .participants-grid {
                grid-template-columns: 1fr;
            }
            
            .summary-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        """ 