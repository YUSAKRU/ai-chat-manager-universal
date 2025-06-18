#!/usr/bin/env python3
"""
Plugin System Test Script
"""
import asyncio
import sys
import os

# Add src directory to path
sys.path.append('src')

from plugin_manager import plugin_manager

async def test_plugins():
    """Test the plugin system with various triggers"""
    
    print("🔌 Plugin System Test Starting...")
    print("="*50)
    
    # Load plugins
    plugin_manager.load_plugins()
    print(f"\n✅ Loaded plugins: {list(plugin_manager.plugins.keys())}")
    
    # Test messages
    test_messages = [
        'Bu sistemde [demo: "test message"] komutu ile plugin test ediyorum.',
        'Let me [search: "AI developments 2024"] to get latest information.',
        'Please [analyze: "data.csv"] to understand the dataset.',
        'System plugin test çalıştırarak durumu kontrol edelim.',
        '[hello] plugin sistemi!'
    ]
    
    print("\n🧪 Testing Plugin Triggers...")
    print("="*50)
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n📝 Test {i}: {message}")
        
        try:
            results = await plugin_manager.process_message(message)
            
            if results:
                print(f"   ✅ {len(results)} plugin(s) triggered:")
                for result in results:
                    plugin_name = result.get('plugin_name', 'Unknown')
                    role = result.get('role', 'Unknown Role')
                    result_type = result.get('type', 'unknown')
                    print(f"      🔌 {plugin_name} ({role}) - Type: {result_type}")
                    
                    # Show content preview
                    content = result.get('content', '')
                    if content:
                        preview = content[:100] + "..." if len(content) > 100 else content
                        print(f"         Content: {preview}")
            else:
                print("   ❌ No plugins triggered")
                
        except Exception as e:
            print(f"   🚨 Error: {str(e)}")
    
    print("\n" + "="*50)
    print("🎯 Plugin System Test Completed!")

if __name__ == "__main__":
    asyncio.run(test_plugins()) 