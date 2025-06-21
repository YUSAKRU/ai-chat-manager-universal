#!/usr/bin/env python3
"""
Notes Web API Test Script
"""
import requests
import json

BASE_URL = "http://localhost:5000/api/notes"

def test_workspace_creation():
    """Test workspace creation"""
    print("🔧 Workspace oluşturuluyor...")
    
    data = {
        "name": "Benim Notlarım",
        "description": "Ana çalışma alanı",
        "user_id": "default_user"
    }
    
    response = requests.post(f"{BASE_URL}/workspaces", json=data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print(f"✅ Workspace oluşturuldu: {result['workspace']['name']}")
            return result['workspace']['id']
        else:
            print(f"❌ Workspace oluşturulamadı: {result}")
    else:
        print(f"❌ HTTP Error: {response.status_code}")
    
    return None

def test_note_creation(workspace_id):
    """Test note creation"""
    print("📝 Not oluşturuluyor...")
    
    data = {
        "title": "İlk Notum",
        "content": "<p>Bu benim ilk notum! 🎉</p><p>AI destekli not alma sistemi harika!</p>",
        "workspace_id": workspace_id,
        "created_by": "default_user"
    }
    
    response = requests.post(f"{BASE_URL}/", json=data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print(f"✅ Not oluşturuldu: {result['note']['title']}")
            return result['note']['id']
        else:
            print(f"❌ Not oluşturulamadı: {result}")
    else:
        print(f"❌ HTTP Error: {response.status_code}")
    
    return None

def test_multiple_notes(workspace_id):
    """Create multiple test notes"""
    print("📚 Çoklu not oluşturuluyor...")
    
    notes_data = [
        {
            "title": "Python Öğreniyorum",
            "content": "<h2>Python Notları</h2><p>Flask web framework kullanarak API geliştiriyorum.</p><ul><li>Routes</li><li>Blueprints</li><li>Database</li></ul>",
            "workspace_id": workspace_id,
            "created_by": "default_user"
        },
        {
            "title": "AI Integration",
            "content": "<h2>AI Entegrasyonu</h2><p>Gemini API kullanarak not analizi yapıyorum.</p><p>Özellikler:</p><ul><li>Otomatik kategorizasyon</li><li>Etiket önerisi</li><li>İçerik özetleme</li></ul>",
            "workspace_id": workspace_id,
            "created_by": "default_user"
        },
        {
            "title": "Proje Planlama",
            "content": "<h2>Not Alma Uygulaması</h2><p>Frontend: HTML, CSS, JavaScript</p><p>Backend: Python Flask</p><p>Database: SQLite</p><p>AI: Gemini API</p>",
            "workspace_id": workspace_id,
            "created_by": "default_user"
        }
    ]
    
    created_notes = []
    for note_data in notes_data:
        response = requests.post(f"{BASE_URL}/", json=note_data)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Not oluşturuldu: {result['note']['title']}")
                created_notes.append(result['note']['id'])
    
    return created_notes

def test_list_workspaces():
    """Test listing workspaces"""
    print("📋 Workspace'ler listeleniyor...")
    
    response = requests.get(f"{BASE_URL}/workspaces?user_id=default_user")
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            workspaces = result['workspaces']
            print(f"✅ {len(workspaces)} workspace bulundu")
            for ws in workspaces:
                print(f"   - {ws['name']} (ID: {ws['id']})")
            return workspaces
        else:
            print(f"❌ Workspace listelenemedi: {result}")
    else:
        print(f"❌ HTTP Error: {response.status_code}")
    
    return []

def test_list_notes(workspace_id):
    """Test listing notes"""
    print("📄 Notlar listeleniyor...")
    
    response = requests.get(f"{BASE_URL}/?workspace_id={workspace_id}")
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            notes = result['notes']
            print(f"✅ {len(notes)} not bulundu")
            for note in notes:
                print(f"   - {note['title']} (ID: {note['id']})")
            return notes
        else:
            print(f"❌ Notlar listelenemedi: {result}")
    else:
        print(f"❌ HTTP Error: {response.status_code}")
    
    return []

def main():
    print("🚀 Notes Web API Test başlıyor...\n")
    
    # 1. Workspace'leri listele
    workspaces = test_list_workspaces()
    
    workspace_id = None
    if workspaces:
        workspace_id = workspaces[0]['id']
        print(f"📁 Mevcut workspace kullanılıyor: {workspace_id}")
    else:
        # 2. Workspace oluştur
        workspace_id = test_workspace_creation()
    
    if not workspace_id:
        print("❌ Workspace bulunamadı, test sonlandırılıyor.")
        return
    
    print()
    
    # 3. Notları listele
    existing_notes = test_list_notes(workspace_id)
    
    if not existing_notes:
        # 4. Test notları oluştur
        print()
        test_note_creation(workspace_id)
        test_multiple_notes(workspace_id)
        
        print()
        # 5. Notları tekrar listele
        test_list_notes(workspace_id)
    
    print("\n🎉 Test tamamlandı!")
    print(f"🌐 Web arayüzü: http://localhost:5000/notes")

if __name__ == "__main__":
    main() 