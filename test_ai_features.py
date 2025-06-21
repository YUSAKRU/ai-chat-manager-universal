#!/usr/bin/env python3
"""
AI Features Test Script
=======================

Not sistemi AI özelliklerini test eder.
"""
import requests
import json
import time

BASE_URL = "http://localhost:5000/api/notes"

def test_ai_features():
    """AI özelliklerini test et"""
    print("🤖 AI Özellik Testleri Başlıyor...\n")
    
    # 1. Workspace ve not listesi al
    print("📋 Notlar listeleniyor...")
    response = requests.get(f"{BASE_URL}/workspaces?user_id=default_user")
    
    if not response.json().get('success'):
        print("❌ Workspace bulunamadı")
        return
    
    workspace_id = response.json()['workspaces'][0]['id']
    
    # Notları al
    notes_response = requests.get(f"{BASE_URL}/?workspace_id={workspace_id}")
    
    if not notes_response.json().get('success'):
        print("❌ Notlar bulunamadı")
        return
    
    notes = notes_response.json()['notes']
    if not notes:
        print("❌ Test edilecek not bulunamadı")
        return
    
    test_note = notes[0]  # İlk notu test et
    note_id = test_note['id']
    
    print(f"✅ Test edilecek not: {test_note['title']}")
    print(f"📝 Not ID: {note_id}\n")
    
    # 2. AI Analiz Testi
    print("🔍 AI Analiz testi...")
    try:
        response = requests.post(f"{BASE_URL}/{note_id}/ai/analyze")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                analysis = data['analysis']
                print(f"✅ Analiz başarılı!")
                print(f"   📂 Kategori: {analysis.get('category', 'N/A')}")
                print(f"   😊 Duygu: {analysis.get('sentiment', 'N/A')}")
                print(f"   🏷️ Anahtar kelimeler: {', '.join(analysis.get('keywords', []))}")
                print(f"   📊 Güven oranı: %{round(analysis.get('confidence', 0) * 100)}")
            else:
                print(f"❌ Analiz başarısız: {data.get('error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Analiz testi hatası: {e}")
    
    print()
    
    # 3. Etiket Önerisi Testi
    print("🏷️ Etiket önerisi testi...")
    try:
        response = requests.post(f"{BASE_URL}/{note_id}/ai/suggest-tags")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                suggested = data['suggested_tags']
                current = data['current_tags']
                print(f"✅ Etiket önerisi başarılı!")
                print(f"   💡 Önerilen: {', '.join(suggested)}")
                print(f"   📌 Mevcut: {', '.join(current)}")
            else:
                print(f"❌ Etiket önerisi başarısız: {data.get('error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Etiket önerisi testi hatası: {e}")
    
    print()
    
    # 4. Özet Oluşturma Testi
    print("📄 Özet oluşturma testi...")
    try:
        response = requests.post(f"{BASE_URL}/{note_id}/ai/summarize", 
                               json={"length": "short"})
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                summary = data['summary']
                print(f"✅ Özet oluşturma başarılı!")
                print(f"   📝 Özet: {summary}")
            else:
                print(f"❌ Özet oluşturma başarısız: {data.get('error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Özet oluşturma testi hatası: {e}")
    
    print()
    
    # 5. İlgili Notlar Testi
    print("🔗 İlgili notlar testi...")
    try:
        response = requests.get(f"{BASE_URL}/{note_id}/ai/related")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                related = data['related_notes']
                print(f"✅ İlgili notlar bulma başarılı!")
                print(f"   🔍 Bulunan ilgili not sayısı: {len(related)}")
                for item in related[:3]:  # İlk 3'ünü göster
                    note_info = item['note']
                    score = item['similarity_score']
                    print(f"   📄 {note_info['title']} (Benzerlik: %{round(score * 100)})")
            else:
                print(f"❌ İlgili notlar bulma başarısız: {data.get('error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"❌ İlgili notlar testi hatası: {e}")
    
    print()
    
    # 6. Yazım İyileştirme Testi
    print("✍️ Yazım iyileştirme testi...")
    try:
        response = requests.post(f"{BASE_URL}/{note_id}/ai/improve-writing")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                improvements = data['improvements']
                print(f"✅ Yazım iyileştirme başarılı!")
                print(f"   📝 Değişiklik sayısı: {len(improvements.get('changes', []))}")
                print(f"   💡 Öneri sayısı: {len(improvements.get('suggestions', []))}")
                
                if improvements.get('suggestions'):
                    print(f"   📋 İlk öneri: {improvements['suggestions'][0]}")
            else:
                print(f"❌ Yazım iyileştirme başarısız: {data.get('error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Yazım iyileştirme testi hatası: {e}")
    
    print("\n🎉 AI Özellik Testleri Tamamlandı!")
    print(f"🌐 Web arayüzünde test edin: http://localhost:5000/notes")
    print("💡 Not seçip sağ paneldeki AI butonlarını deneyin!")

def test_server_status():
    """Sunucu durumunu kontrol et"""
    try:
        response = requests.get("http://localhost:5000/api/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('ai_adapter_ready'):
                print("✅ Sunucu hazır (AI entegrasyonu aktif)")
                return True
            else:
                print("⚠️ Sunucu hazır ama AI entegrasyonu pasif")
                return False
        else:
            print(f"❌ Sunucu yanıt vermiyor: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Sunucu bağlantı hatası: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Sunucu durumu kontrol ediliyor...")
    if test_server_status():
        print()
        test_ai_features()
    else:
        print("🚀 Lütfen önce sunucuyu başlatın: python run_production.py")
