#!/usr/bin/env python3
"""
Sample Notes Creator
====================

Çeşitli örnek notlar oluşturmak için script
"""
import requests
import json

BASE_URL = "http://localhost:5000/api/notes"

def create_sample_notes():
    """Örnek notları oluştur"""
    
    # Workspace ID'yi al
    response = requests.get(f"{BASE_URL}/workspaces?user_id=default_user")
    if not response.json().get('success'):
        print("❌ Workspace bulunamadı")
        return
    
    workspace_id = response.json()['workspaces'][0]['id']
    print(f"📁 Workspace: {workspace_id}")
    
    sample_notes = [
        {
            "title": "📚 Python Öğreniyorum",
            "content": """<h1>🐍 Python Öğrenme Notları</h1>

<h2>🎯 Hedeflerim</h2>
<ul>
    <li>Flask ile web uygulaması geliştirmek</li>
    <li>SQLAlchemy ile veritabanı işlemleri</li>
    <li>AI entegrasyonu yapmak</li>
    <li>RESTful API tasarımı</li>
</ul>

<h2>📖 Öğrendiklerim</h2>
<p><strong>Flask Routing:</strong></p>
<pre><code>@app.route('/api/notes', methods=['GET', 'POST'])
def handle_notes():
    return jsonify({'status': 'success'})</code></pre>

<p><strong>SQLAlchemy Models:</strong></p>
<pre><code>class Note(Base):
    __tablename__ = 'notes'
    id = Column(String, primary_key=True)</code></pre>

<h2>🚀 Sonraki Adımlar</h2>
<ol>
    <li>WebSocket entegrasyonu</li>
    <li>Real-time collaboration</li>
    <li>AI-powered features</li>
</ol>""",
            "workspace_id": workspace_id,
            "created_by": "default_user"
        },
        {
            "title": "🤖 AI Integration Notları",
            "content": """<h1>🧠 AI Entegrasyon Rehberi</h1>

<h2>🎯 Gemini API Kullanımı</h2>
<p>Gemini API ile not analizi ve içerik iyileştirme özellikleri geliştiriyorum.</p>

<h3>🔧 Temel Özellikler</h3>
<ul>
    <li><strong>📝 Not Analizi:</strong> İçerik kategorize etme</li>
    <li><strong>🏷️ Otomatik Etiketleme:</strong> Smart tag suggestions</li>
    <li><strong>📋 Özet Oluşturma:</strong> Long content summarization</li>
    <li><strong>🔗 İlgili Notlar:</strong> Content-based recommendations</li>
    <li><strong>✍️ Yazım İyileştirme:</strong> Grammar and style improvements</li>
</ul>

<blockquote>
💡 <strong>Pro Tip:</strong> AI özelliklerini kullanırken context'i korumak önemli!
</blockquote>""",
            "workspace_id": workspace_id,
            "created_by": "default_user"
        },
        {
            "title": "🚀 Proje Roadmap",
            "content": """<h1>🗺️ AI Notes App Roadmap</h1>

<h2>✅ Tamamlanan Özellikler (v1.0)</h2>
<ul>
    <li>✅ Temel not alma sistemi</li>
    <li>✅ Workspace yönetimi</li>
    <li>✅ SQLite database entegrasyonu</li>
    <li>✅ RESTful API</li>
    <li>✅ Responsive web arayüzü</li>
    <li>✅ Otomatik kaydetme</li>
    <li>✅ Arama fonksiyonu</li>
</ul>

<h2>🔄 Geliştirilecek Özellikler (v1.1)</h2>
<ul>
    <li>🔄 AI analiz sistemi</li>
    <li>🔄 Otomatik etiketleme</li>
    <li>🔄 İçerik özetleme</li>
    <li>🔄 İlgili not önerileri</li>
    <li>🔄 Yazım denetimi</li>
</ul>

<h2>⏳ Gelecek Sürümler</h2>
<h3>📅 v2.0 - Collaboration Features</h3>
<ul>
    <li>Real-time collaboration</li>
    <li>Comment sistemi</li>
    <li>Version control</li>
    <li>Team workspaces</li>
</ul>""",
            "workspace_id": workspace_id,
            "created_by": "default_user"
        }
    ]
    
    created_count = 0
    for note_data in sample_notes:
        try:
            response = requests.post(f"{BASE_URL}/", json=note_data)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"✅ Not oluşturuldu: {note_data['title']}")
                    created_count += 1
                else:
                    print(f"❌ Not oluşturulamadı: {note_data['title']} - {result}")
            else:
                print(f"❌ HTTP Error ({response.status_code}): {note_data['title']}")
        except Exception as e:
            print(f"❌ Error creating note {note_data['title']}: {e}")
    
    print(f"\n🎉 {created_count}/{len(sample_notes)} örnek not oluşturuldu!")
    print(f"🌐 Web arayüzünü kontrol edin: http://localhost:5000/notes")

if __name__ == "__main__":
    print("📝 Örnek notlar oluşturuluyor...\n")
    create_sample_notes()
 