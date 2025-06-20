"""
Live Document Canvas API Test Script
"""

import requests
import json

def test_canvas_apis():
    """Canvas API'lerini test et"""
    base_url = "http://localhost:5000"
    
    print("🎨 Live Document Canvas API Test")
    print("=" * 50)
    
    # 1. Canvas Statistics Test
    print("\n1️⃣ Canvas Statistics Test:")
    try:
        response = requests.get(f"{base_url}/api/canvas/statistics")
        if response.status_code == 200:
            stats = response.json()
            print("✅ Statistics API çalışıyor")
            print(f"   📊 Aktif belgeler: {stats['statistics']['documents']['total_documents']}")
            print(f"   🪟 Aktif pencereler: {stats['statistics']['canvas']['active_windows']}")
        else:
            print(f"❌ Statistics API hatası: {response.status_code}")
    except Exception as e:
        print(f"❌ Statistics API bağlantı hatası: {e}")
    
    # 2. Yeni Belge Oluşturma Test
    print("\n2️⃣ Yeni Belge Oluşturma Test:")
    try:
        document_data = {
            "title": "Test Belgesi - API Testi",
            "content": "# Test Başlığı\n\nBu belge API testi için oluşturulmuştur.\n\n## Alt Başlık\n\nİçerik test metni.",
            "type": "markdown"
        }
        
        response = requests.post(
            f"{base_url}/api/canvas/documents",
            headers={"Content-Type": "application/json"},
            json=document_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Belge oluşturma başarılı")
            print(f"   📄 Document ID: {result['document_id']}")
            print(f"   🪟 Window ID: {result['window_id']}")
            print(f"   📝 Başlık: {result['title']}")
            
            # Test için belge ID'sini sakla
            document_id = result['document_id']
            
            # 3. Belge Bilgilerini Getirme Test
            print("\n3️⃣ Belge Bilgileri Getirme Test:")
            doc_response = requests.get(f"{base_url}/api/canvas/documents/{document_id}")
            
            if doc_response.status_code == 200:
                doc_info = doc_response.json()
                print("✅ Belge bilgileri alındı")
                print(f"   📄 Başlık: {doc_info['document']['title']}")
                print(f"   📊 Sürüm: v{doc_info['document']['version']}")
                print(f"   👥 Aktif kullanıcılar: {len(doc_info['document']['active_users'])}")
                print(f"   📝 İçerik uzunluğu: {len(doc_info['document']['content'])} karakter")
            else:
                print(f"❌ Belge bilgileri alma hatası: {doc_response.status_code}")
                
        else:
            print(f"❌ Belge oluşturma hatası: {response.status_code}")
            print(f"   Hata detayı: {response.text}")
            
    except Exception as e:
        print(f"❌ Belge oluşturma bağlantı hatası: {e}")
    
    # 4. Canvas Windows List Test  
    print("\n4️⃣ Canvas Windows Listesi Test:")
    try:
        response = requests.get(f"{base_url}/api/canvas/windows")
        if response.status_code == 200:
            windows = response.json()
            print("✅ Windows listesi alındı")
            print(f"   🪟 Toplam pencere: {windows['total_windows']}")
            if windows['windows']:
                for window in windows['windows']:
                    print(f"   - {window['title']} ({window['window_id'][:8]}...)")
        else:
            print(f"❌ Windows listesi hatası: {response.status_code}")
    except Exception as e:
        print(f"❌ Windows listesi bağlantı hatası: {e}")
    
    # 5. Final Statistics
    print("\n5️⃣ Final Statistics:")
    try:
        response = requests.get(f"{base_url}/api/canvas/statistics")
        if response.status_code == 200:
            stats = response.json()
            print("✅ Final Statistics")
            print(f"   📊 Toplam belgeler: {stats['statistics']['documents']['total_documents']}")
            print(f"   📊 Aktif belgeler: {stats['statistics']['documents']['active_documents']}")
            print(f"   🪟 Aktif pencereler: {stats['statistics']['canvas']['active_windows']}")
            print(f"   👥 Toplam kullanıcılar: {stats['statistics']['documents']['total_active_users']}")
    except Exception as e:
        print(f"❌ Final statistics hatası: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Test tamamlandı!")

if __name__ == "__main__":
    test_canvas_apis() 