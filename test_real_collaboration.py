#!/usr/bin/env python3
"""
🏁 PHASE 6.1 REAL COLLABORATION TEST
F1 Pit Crew Standards: Test actual cursor movement between two browser windows
"""

import subprocess
import time
import webbrowser
import requests
import json
from datetime import datetime

def check_server_status():
    """Server çalışıyor mu kontrol et"""
    try:
        response = requests.get('http://localhost:5000/api/status', timeout=5)
        if response.status_code == 200:
            print("✅ Server running and responsive")
            return True
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server not reachable: {e}")
        return False

def create_test_document():
    """Test için bir canvas document oluştur"""
    try:
        document_data = {
            'title': 'Phase 6.1 Collaboration Test Document',
            'content': 'This is a test document for real-time collaboration.\n\nMove your cursor around and see it in the other window!',
            'metadata': {
                'test_mode': True,
                'created_for': 'phase_6_1_collaboration',
                'timestamp': datetime.now().isoformat()
            }
        }
        
        response = requests.post(
            'http://localhost:5000/api/canvas/documents',
            json=document_data,
            timeout=10
        )
        
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            document_id = result.get('document_id')
            print(f"✅ Test document created: {document_id}")
            return document_id
        else:
            print(f"❌ Failed to create test document: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating test document: {e}")
        return None

def open_collaboration_windows(document_id):
    """İki browser window açar - collaboration test için"""
    base_url = f"http://localhost:5000/?test_collaboration=true&document_id={document_id}"
    
    try:
        print("\n🎯 Opening browser windows for collaboration test...")
        
        # Chrome'da iki farklı window aç
        # Profil 1 - Sol taraf
        subprocess.Popen([
            "chrome", 
            "--new-window",
            "--window-position=100,100",
            "--window-size=800,600",
            f"--user-data-dir=C:/temp/chrome_profile_1",
            base_url + "&user=User1"
        ])
        
        time.sleep(2)
        
        # Profil 2 - Sağ taraf
        subprocess.Popen([
            "chrome",
            "--new-window", 
            "--window-position=920,100",
            "--window-size=800,600",
            f"--user-data-dir=C:/temp/chrome_profile_2",
            base_url + "&user=User2"
        ])
        
        print("✅ Two browser windows opened")
        print("📍 Left window: User1 (position 100,100)")
        print("📍 Right window: User2 (position 920,100)")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to open browser windows: {e}")
        print("💡 Fallback: Using default browser...")
        
        # Fallback: default browser kullan
        try:
            webbrowser.open(base_url + "&user=User1")
            time.sleep(3)
            webbrowser.open(base_url + "&user=User2")
            return True
        except Exception as fallback_error:
            print(f"❌ Fallback also failed: {fallback_error}")
            return False

def run_manual_test_instructions():
    """Manual test talimatları"""
    print("\n" + "="*60)
    print("🏁 PHASE 6.1 COLLABORATION TEST - MANUAL INSTRUCTIONS")
    print("="*60)
    print()
    print("SUCCESS CRITERIA:")
    print("✅ You should see TWO different colored cursors")
    print("✅ When you move mouse in one window, cursor appears in the other")
    print("✅ Each user should have different colored cursor (red, blue, green, etc.)")
    print("✅ User names should appear next to cursors")
    print()
    print("TEST STEPS:")
    print("1. 🖱️  Move your mouse in the LEFT window")
    print("2. 👀 Look at the RIGHT window - do you see a colored cursor?")
    print("3. 🖱️  Move your mouse in the RIGHT window") 
    print("4. 👀 Look at the LEFT window - do you see a different colored cursor?")
    print("5. ✍️  Try clicking and typing in both windows")
    print()
    print("WHAT TO EXPECT:")
    print("• Different colored cursor for each user")
    print("• Smooth cursor movement tracking")
    print("• User presence indicators")
    print("• Real-time updates (no lag > 100ms)")
    print()
    print("❌ IF YOU DON'T SEE CURSORS:")
    print("• Check browser console for errors (F12)")
    print("• Verify WebSocket connection")
    print("• Check server logs")
    print()
    
    input("👆 Press ENTER when you have completed the test...")
    
    print("\n" + "="*40)
    print("TEST EVALUATION")
    print("="*40)
    
    while True:
        result = input("\n🏁 Did you see REAL-TIME CURSOR MOVEMENT between windows? (y/n): ").lower().strip()
        
        if result == 'y':
            print("\n🎉 SUCCESS! Phase 6.1 CORE FEATURE WORKING!")
            print("✅ Multi-user cursor tracking confirmed")
            print("✅ Real-time collaboration system functional")
            break
        elif result == 'n':
            print("\n❌ FAILURE! Phase 6.1 needs debugging")
            print("🔍 Collaboration features not working as expected")
            debug_info()
            break
        else:
            print("Please answer 'y' for yes or 'n' for no")

def debug_info():
    """Debug bilgileri topla"""
    print("\n🔍 DEBUG INFORMATION:")
    print("-" * 30)
    
    # WebSocket bağlantı test
    try:
        import socketio
        sio = socketio.SimpleClient()
        sio.connect('http://localhost:5000')
        print("✅ WebSocket connection successful")
        sio.disconnect()
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
    
    # Server logs check
    print("\n📋 Check server console for:")
    print("• '👥 User {name} joined document {id}' messages")
    print("• WebSocket connection/disconnection logs")
    print("• Any error messages about cursor_moved events")
    
    print("\n🛠️  Next steps:")
    print("1. Check browser console (F12) for JavaScript errors")
    print("2. Verify LiveEditor.js is loading correctly")
    print("3. Check if users are actually joining document rooms")
    print("4. Test WebSocket events manually")

def main():
    """Main test runner"""
    print("🏁 PHASE 6.1 REAL-TIME COLLABORATION TEST")
    print("=" * 50)
    
    # 1. Server kontrol
    if not check_server_status():
        print("\n❌ Cannot proceed - server not running")
        print("💡 Run: python run_production.py")
        return
    
    # 2. Test document oluştur
    document_id = create_test_document()
    if not document_id:
        print("\n❌ Cannot proceed - failed to create test document")
        return
    
    # 3. Browser windows aç
    if not open_collaboration_windows(document_id):
        print("\n❌ Cannot proceed - failed to open browser windows")
        return
    
    # 4. Manual test yap
    run_manual_test_instructions()
    
    print("\n🏁 Test completed!")
    print(f"📄 Test document ID: {document_id}")

if __name__ == "__main__":
    main() 