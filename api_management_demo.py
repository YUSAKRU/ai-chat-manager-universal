#!/usr/bin/env python3
"""
🔑 API Yönetimi Demo - Kullanıcı Kendi API'larını Nasıl Atar?
"""

import os
import sys
sys.path.append('src')

from ai_adapters.secure_config import SecureConfigManager
from ai_adapters.universal_adapter import UniversalAIAdapter

def demo_api_management():
    print("🔑 API YÖNETIMI DEMO")
    print("="*50)
    
    # 1. Güvenli Config Manager
    config_manager = SecureConfigManager("config/my_apis.enc")
    
    print("\n📝 1. KULLANICI API ANAHTARLARINI EKLİYOR:")
    print("-"*30)
    
    # Kullanıcı kendi API'larını ekler
    apis_to_add = {
        "gemini": "AIzaSyDdI0hCZtE6vhOKzHqL...",  # Kullanıcının gerçek Gemini API'sı
        "openai": "sk-proj-abc123xyz456...",       # Kullanıcının gerçek OpenAI API'sı 
        "claude": "sk-ant-api03-abc123...",        # Kullanıcının Claude API'sı (gelecekte)
        "custom_ai": "custom-api-key-123..."       # Özel AI servisi
    }
    
    for provider, api_key in apis_to_add.items():
        success = config_manager.save_api_key(provider, api_key)
        print(f"   {provider:12} → {'✅ Eklendi' if success else '❌ Hata'}")
    
    print("\n🤖 2. UNIVERSAL ADAPTER ÇOK FAZLA MODEL DESTEKLİYOR:")
    print("-"*40)
    
    ai_adapter = UniversalAIAdapter(config_manager)
    
    # Kullanıcı farklı modeller ekleyebilir
    models_to_add = [
        {"type": "gemini", "model": "gemini-1.5-pro", "id": "gemini-pro"},
        {"type": "gemini", "model": "gemini-1.5-flash", "id": "gemini-flash"},
        {"type": "openai", "model": "gpt-4o", "id": "gpt4o"},
        {"type": "openai", "model": "gpt-4o-mini", "id": "gpt4o-mini"},
        {"type": "openai", "model": "gpt-3.5-turbo", "id": "gpt35"},
    ]
    
    for model_config in models_to_add:
        try:
            adapter_id = ai_adapter.add_adapter(
                adapter_type=model_config["type"],
                adapter_id=model_config["id"],
                api_key=config_manager.get_api_key(model_config["type"]),
                model=model_config["model"]
            )
            print(f"   ✅ {model_config['id']:12} → {model_config['model']}")
        except Exception as e:
            print(f"   ❌ {model_config['id']:12} → Hata: {str(e)[:30]}...")
    
    print("\n🎭 3. ROLLERE ATAMA (Kullanıcı kendi atamasını yapar):")
    print("-"*40)
    
    # Kullanıcı istediği modeli istediği role atar
    role_assignments = {
        "project_manager": "gemini-pro",      # PM → Gemini 1.5 Pro
        "lead_developer": "gpt4o",            # LD → GPT-4o  
        "boss": "gpt4o-mini",                 # Boss → GPT-4o Mini
        "researcher": "gemini-flash",         # Araştırmacı → Gemini Flash
        "code_reviewer": "gpt35"              # Code Review → GPT-3.5
    }
    
    for role, adapter_id in role_assignments.items():
        try:
            ai_adapter.assign_role(role, adapter_id)
            print(f"   ✅ {role:15} → {adapter_id}")
        except Exception as e:
            print(f"   ❌ {role:15} → Hata: {str(e)[:30]}...")
    
    print("\n📊 4. API YÖNETİMİ ÖZELLİKLERİ:")
    print("-"*30)
    
    features = [
        "✅ Şifrelenmiş API anahtarı saklama",
        "✅ Çoklu provider desteği (Gemini, OpenAI, Claude...)",
        "✅ Çoklu model desteği (aynı provider'dan farklı modeller)",
        "✅ Dinamik adapter ekleme/çıkarma",
        "✅ Rol-tabanlı model atama",
        "✅ API anahtarı güvenliği (PBKDF2 + Fernet şifreleme)",
        "✅ Rate limiting ve error handling",
        "✅ Real-time maliyet takibi",
        "✅ Adapter durumu izleme",
        "✅ Hot-swapping (çalışırken model değiştirme)"
    ]
    
    for feature in features:
        print(f"   {feature}")
    
    print("\n🚀 5. KULLANIM ÖRNEKLERİ:")
    print("-"*20)
    
    examples = [
        "# Yeni API ekleme",
        "config_manager.save_api_key('mistral', 'your-mistral-key')",
        "",
        "# Yeni model ekleme", 
        "adapter_id = ai_adapter.add_adapter('openai', model='gpt-4-turbo')",
        "",
        "# Role atama",
        "ai_adapter.assign_role('data_analyst', adapter_id)",
        "",
        "# Mesaj gönderme",
        "response = await ai_adapter.send_message('data_analyst', 'Analyze this data')",
        "",
        "# Direkt adapter kullanımı",
        "response = await ai_adapter.send_message_to_adapter(adapter_id, 'Hello')"
    ]
    
    for example in examples:
        print(f"   {example}")
    
    print("\n" + "="*50)
    print("🎯 SONUÇ: Kullanıcı tamamen kendi API'larını yönetebilir!")

if __name__ == "__main__":
    demo_api_management() 