#!/usr/bin/env python3
"""
🧪 Maliyet Hesaplama Test Scripti
Gerçek API çağrıları yapmadan maliyet hesaplamalarını test eder
"""

# Örnek token kullanımları
test_scenarios = [
    {
        "name": "Basit soru-cevap",
        "input_tokens": 50,
        "output_tokens": 100,
        "models": ["gpt-3.5-turbo", "gpt-4", "gemini-1.5-pro"]
    },
    {
        "name": "Uzun kod analizi",
        "input_tokens": 2000,
        "output_tokens": 1500,
        "models": ["gpt-4", "gemini-1.5-pro"]
    },
    {
        "name": "Dokümantasyon yazma",
        "input_tokens": 800,
        "output_tokens": 3000,
        "models": ["gpt-4o", "gpt-3.5-turbo"]
    }
]

# OpenAI fiyatlandırması (per 1M token)
openai_costs = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4": {"input": 30.00, "output": 60.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50}
}

# Gemini fiyatlandırması (per 1M token)
gemini_costs = {
    "gemini-1.5-pro": {"input": 1.25, "output": 3.75},
    "gemini-pro": {"input": 0.0, "output": 0.0}  # Free tier
}

def calculate_openai_cost(model, input_tokens, output_tokens):
    if model not in openai_costs:
        return 0.0
    
    costs = openai_costs[model]
    input_cost = (input_tokens / 1_000_000) * costs["input"]
    output_cost = (output_tokens / 1_000_000) * costs["output"]
    return input_cost + output_cost

def calculate_gemini_cost(model, input_tokens, output_tokens):
    if model not in gemini_costs:
        return 0.0
    
    costs = gemini_costs[model]
    input_cost = (input_tokens / 1_000_000) * costs["input"]
    output_cost = (output_tokens / 1_000_000) * costs["output"]
    return input_cost + output_cost

def main():
    print("🧪 MALİYET HESAPLAMA TEST SİSTEMİ")
    print("="*50)
    
    total_cost = 0.0
    
    for scenario in test_scenarios:
        print(f"\n📝 {scenario['name']}")
        print(f"   Input: {scenario['input_tokens']} tokens")
        print(f"   Output: {scenario['output_tokens']} tokens")
        print("   " + "-"*40)
        
        scenario_total = 0.0
        
        for model in scenario['models']:
            if model.startswith('gpt'):
                cost = calculate_openai_cost(model, scenario['input_tokens'], scenario['output_tokens'])
            else:
                cost = calculate_gemini_cost(model, scenario['input_tokens'], scenario['output_tokens'])
            
            scenario_total += cost
            total_cost += cost
            
            print(f"   {model:20} → ${cost:.6f}")
        
        print(f"   {'TOPLAM:':<20} → ${scenario_total:.6f}")
    
    print("\n" + "="*50)
    print(f"🎯 GENEL TOPLAM MALİYET: ${total_cost:.6f}")
    print(f"💰 Yaklaşık: ${total_cost:.4f}")
    print("="*50)
    
    # Günlük kullanım senaryosu
    print("\n📅 GÜNLÜK KULLANIM SENARYOSu (100 istek):")
    daily_cost = total_cost * 100
    print(f"   Günlük maliyet: ${daily_cost:.2f}")
    print(f"   Aylık maliyet: ${daily_cost * 30:.2f}")

if __name__ == "__main__":
    main() 