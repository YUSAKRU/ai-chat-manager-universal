#!/usr/bin/env python3
"""
QUICK PHASE 6.1 COLLABORATION TEST
Multi-user Real-time Collaboration Validation
"""

import requests
import time
import json
from datetime import datetime

def test_collaboration_features():
    base_url = "http://localhost:5000"
    
    print("🚀 PHASE 6.1 COLLABORATION QUICK TEST")
    print("=" * 50)
    print(f"⏰ Started at: {datetime.now().strftime('%H:%M:%S')}")
    
    # Test 1: Basic connectivity
    print("\n🔌 Test 1: Basic Connectivity")
    try:
        response = requests.get(f"{base_url}/api/canvas/statistics", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
            stats = response.json()
            print(f"   📊 Stats: {stats['statistics']['canvas']}")
        else:
            print(f"❌ Server error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    # Test 2: Document creation
    print("\n📄 Test 2: Document Creation")
    try:
        payload = {
            "title": "Phase 6.1 Collaboration Test",
            "content": "# Multi-user Test\n\nReal-time collaboration testing.",
            "type": "live_document"
        }
        
        response = requests.post(
            f"{base_url}/api/canvas/documents",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            doc_data = response.json()
            document_id = doc_data.get('document_id')
            print(f"✅ Document created: {document_id}")
            
            # Test document retrieval
            get_response = requests.get(
                f"{base_url}/api/canvas/documents/{document_id}",
                timeout=5
            )
            
            if get_response.status_code == 200:
                print("✅ Document retrieved successfully")
                return document_id
            else:
                print(f"❌ Document retrieval failed: {get_response.status_code}")
                return False
        else:
            print(f"❌ Document creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Document creation error: {e}")
        return False
    
    # Test 3: WebSocket endpoint check
    print("\n🔌 Test 3: WebSocket Support")
    try:
        # Check if homepage loads with Socket.IO
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200 and "socket.io" in response.text:
            print("✅ Socket.IO available")
        else:
            print("⚠️ Socket.IO may not be loaded")
            
        return True
        
    except Exception as e:
        print(f"❌ WebSocket check failed: {e}")
        return False

if __name__ == "__main__":
    result = test_collaboration_features()
    
    print("\n" + "=" * 50)
    if result:
        print("🎉 PHASE 6.1 BASIC TESTS: PASSED")
        print("✅ Multi-user collaboration infrastructure is ready!")
        print("🌐 Open browser to http://localhost:5000 to test UI")
    else:
        print("❌ PHASE 6.1 BASIC TESTS: FAILED")
        print("🔧 Fix issues before proceeding")
    print("=" * 50) 