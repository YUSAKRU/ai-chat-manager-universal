#!/usr/bin/env python3
"""
PHASE 5.1 PROFESSIONAL VALIDATION - CLEAN VERSION
Enterprise-grade Rich Text Editor Testing
"""

import requests
import time
import json
import sys
from datetime import datetime

class Phase51ComprehensiveTest:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.test_results = {}
        self.start_time = datetime.now()
        
    def log_test(self, test_name, status, details=""):
        """Test sonucunu logla"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        symbol = "✅" if status else "❌"
        print(f"{symbol} [{timestamp}] {test_name}")
        if details:
            print(f"   📋 {details}")
        
        self.test_results[test_name] = {
            "status": status,
            "details": details,
            "timestamp": timestamp
        }
    
    def test_system_core(self):
        """Test: System Core Functionality"""
        print("\n🎯 SYSTEM CORE VALIDATION")
        print("=" * 50)
        
        try:
            # Homepage test
            response = requests.get(f"{self.base_url}/", timeout=5)
            self.log_test("Homepage Access", 
                         response.status_code == 200, 
                         f"Status: {response.status_code}")
            
            # Critical API endpoints
            endpoints = [
                ("/api/canvas/statistics", "Canvas Statistics"),
                ("/api/documents/statistics", "Document Statistics"),
                ("/api/analytics", "Analytics API")
            ]
            
            for endpoint, name in endpoints:
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                    self.log_test(f"{name}", 
                                 response.status_code == 200,
                                 f"Status: {response.status_code}")
                except Exception as e:
                    self.log_test(f"{name}", False, f"Error: {str(e)}")
                    
        except Exception as e:
            self.log_test("System Core Failed", False, str(e))
    
    def test_rich_text_infrastructure(self):
        """Test: Rich Text Editor Infrastructure"""
        print("\n📝 RICH TEXT EDITOR INFRASTRUCTURE")
        print("=" * 50)
        
        try:
            # Get homepage HTML
            response = requests.get(f"{self.base_url}/")
            html_content = response.text
            
            # Check Tiptap references
            tiptap_found = "@tiptap/core" in html_content
            self.log_test("Tiptap CDN Reference", 
                         tiptap_found,
                         "Found in HTML template")
            
            # Check static resources
            resources = [
                ("/static/css/canvas.css", "Canvas CSS"),
                ("/static/js/canvas/LiveEditor.js", "LiveEditor JS")
            ]
            
            for resource, name in resources:
                try:
                    response = requests.get(f"{self.base_url}{resource}", timeout=5)
                    self.log_test(f"{name} Loading", 
                                 response.status_code == 200,
                                 f"Size: {len(response.content)} bytes")
                except Exception as e:
                    self.log_test(f"{name} Loading", False, str(e))
                    
        except Exception as e:
            self.log_test("Rich Text Infrastructure Failed", False, str(e))
    
    def test_document_system(self):
        """Test: Document Creation and Retrieval System"""
        print("\n📄 DOCUMENT SYSTEM VALIDATION")
        print("=" * 50)
        
        try:
            # Test document creation
            doc_data = {
                "title": f"Test Document - {datetime.now().strftime('%H:%M:%S')}",
                "content": "<h1>Test Heading</h1><p>This is a <strong>test</strong> document.</p>"
            }
            
            response = requests.post(f"{self.base_url}/api/canvas/documents", 
                                   json=doc_data, timeout=10)
            
            if response.status_code == 200:
                doc_response = response.json()
                doc_id = doc_response.get('document_id')
                self.log_test("Document Creation", True, 
                             f"Doc ID: {doc_id}")
                
                # Test document retrieval
                if doc_id:
                    get_response = requests.get(f"{self.base_url}/api/canvas/documents/{doc_id}")
                    self.log_test("Document Retrieval", 
                                 get_response.status_code == 200,
                                 f"Status: {get_response.status_code}")
                    
                    # Check response content
                    if get_response.status_code == 200:
                        content = get_response.json()
                        self.log_test("Document Content Valid", 
                                     'document' in content or 'error' not in content,
                                     f"Response: {list(content.keys())}")
                else:
                    self.log_test("Document Retrieval", False, "No document ID returned")
            else:
                self.log_test("Document Creation", False, 
                             f"Status: {response.status_code}")
                             
        except Exception as e:
            self.log_test("Document System Failed", False, str(e))
    
    def test_ai_document_synthesis(self):
        """Test: AI Document Synthesis"""
        print("\n🧠 AI DOCUMENT SYNTHESIS VALIDATION")
        print("=" * 50)
        
        try:
            # Test AI document generation
            conversation_data = {
                "conversation": [
                    {"role": "user", "content": "Test meeting started."},
                    {"role": "assistant", "content": "Hello! Ready to help."},
                    {"role": "user", "content": "Phase 5.1 status?"},
                    {"role": "assistant", "content": "Phase 5.1 rich text editor completed."}
                ],
                "document_type": "meeting_summary"
            }
            
            response = requests.post(f"{self.base_url}/api/documents/generate", 
                                   json=conversation_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                files_created = result.get('files_created', [])
                self.log_test("AI Document Generation", True,
                             f"Status: {response.status_code}")
                self.log_test("Document Files Created", 
                             len(files_created) > 0,
                             f"Files: {files_created}")
            else:
                # Detailed error reporting
                try:
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get('error', 'Unknown error')
                    self.log_test("AI Document Generation", False,
                                 f"Status: {response.status_code}, Error: {error_msg}")
                except:
                    self.log_test("AI Document Generation", False,
                                 f"Status: {response.status_code}, Raw: {response.text[:100]}")
                             
        except Exception as e:
            self.log_test("AI Document Synthesis Failed", False, str(e))
    
    def run_comprehensive_test(self):
        """Run all comprehensive tests"""
        print("🏁 PHASE 5.1 COMPREHENSIVE VALIDATION SUITE")
        print("=" * 60)
        print(f"🕐 Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Target: {self.base_url}")
        print()
        
        # Run test groups
        self.test_system_core()
        self.test_rich_text_infrastructure()
        self.test_document_system()
        self.test_ai_document_synthesis()
        
        # Print comprehensive summary
        self.print_comprehensive_summary()
    
    def print_comprehensive_summary(self):
        """Print detailed test summary"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results.values() if result['status'])
        failed = len(self.test_results) - passed
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📝 Total: {len(self.test_results)}")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"🎯 Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        
        # Show failed tests with details
        if failed > 0:
            print("\n❌ FAILED TESTS ANALYSIS:")
            for test_name, result in self.test_results.items():
                if not result['status']:
                    print(f"   🔴 {test_name}")
                    print(f"      └── {result['details']}")
        
        # Strategic assessment
        success_rate = (passed/len(self.test_results)*100)
        if success_rate >= 95:
            print("\n🎉 PHASE 5.1 VALIDATION: EXCELLENT!")
            print("   System exceeds enterprise standards.")
        elif success_rate >= 85:
            print("\n✅ PHASE 5.1 VALIDATION: SUCCESSFUL!")
            print("   System meets enterprise standards with minor issues.")
        elif success_rate >= 70:
            print("\n⚠️  PHASE 5.1 VALIDATION: PARTIALLY SUCCESSFUL")
            print("   Core functionality works, improvements needed.")
        else:
            print("\n🚨 PHASE 5.1 VALIDATION: CRITICAL ISSUES")
            print("   Major problems detected, immediate attention required.")

if __name__ == "__main__":
    test_suite = Phase51ComprehensiveTest()
    test_suite.run_comprehensive_test() 