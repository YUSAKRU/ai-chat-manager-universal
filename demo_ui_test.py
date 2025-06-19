#!/usr/bin/env python3
"""
🎨 AI Orchestrator UI Demo Server
Modern UI/UX test için basit Flask sunucu
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
import os
import time
import random

app = Flask(__name__)

# Demo data
DEMO_SPECIALISTS = {
    'project_manager': {
        'name': 'AI Proje Yöneticisi',
        'description': 'Proje koordinasyonu, zaman yönetimi ve ekip organizasyonu konularında uzmandır.',
        'expertise': ['Agile Metodoloji', 'Risk Yönetimi', 'Ekip Koordinasyonu', 'Kalite Kontrolü']
    },
    'lead_developer': {
        'name': 'AI Kıdemli Geliştirici', 
        'description': 'Yazılım mimarisi, kod geliştirme ve teknik çözümler konularında uzmandır.',
        'expertise': ['Python', 'JavaScript', 'Sistem Mimarisi', 'API Tasarımı', 'Veritabanı']
    },
    'ui_ux_designer': {
        'name': 'AI UI/UX Tasarımcı',
        'description': 'Kullanıcı deneyimi, arayüz tasarımı ve kullanılabilirlik konularında uzmandır.',
        'expertise': ['UI/UX Design', 'Figma', 'User Research', 'Prototyping', 'Design Systems']
    },
    'business_analyst': {
        'name': 'AI İş Analisti',
        'description': 'İş süreçleri, gereksinim analizi ve sistem optimizasyonu konularında uzmandır.',
        'expertise': ['İş Süreç Analizi', 'Gereksinim Toplama', 'Veri Analizi', 'Raporlama']
    }
}

DEMO_RESPONSES = [
    "Bu harika bir proje fikri! Hemen başlayalım.",
    "Teknik mimariye odaklanarak başlayabiliriz.",
    "Kullanıcı deneyimi açısından bazı önerilerim var.",
    "İş süreçlerini detaylandırmamız gerekecek.",
    "Bu konuda kapsamlı bir analiz yapmalıyız.",
    "Implementasyon aşamasında dikkat etmemiz gereken noktalar var."
]

@app.route('/')
def index():
    """Ana sayfa - Universal template"""
    return render_template('index_universal.html')

@app.route('/orchestrator')
def orchestrator():
    """Orchestrator sayfası"""
    return render_template('orchestrator.html')

@app.route('/api-management')
def api_management():
    """API management sayfası"""
    return render_template('api_management.html')

# Demo API endpoints
@app.route('/orchestrate', methods=['POST'])
def orchestrate():
    """Demo orchestration endpoint"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        # Simulate processing delay
        time.sleep(random.uniform(1, 3))
        
        # Determine specialists based on keywords
        active_specialists = []
        if any(word in message.lower() for word in ['proje', 'plan', 'organize']):
            active_specialists.append('project_manager')
        if any(word in message.lower() for word in ['kod', 'geliştir', 'program', 'api']):
            active_specialists.append('lead_developer')
        if any(word in message.lower() for word in ['tasarım', 'ui', 'ux', 'kullanıcı']):
            active_specialists.append('ui_ux_designer')
        if any(word in message.lower() for word in ['analiz', 'süreç', 'iş', 'gereksinim']):
            active_specialists.append('business_analyst')
            
        # Default to project manager if no specific specialist detected
        if not active_specialists:
            active_specialists = ['project_manager']
        
        # Generate response
        primary_response = f"Mesajınızı analiz ettim: '{message[:50]}{'...' if len(message) > 50 else ''}'"
        
        # Generate specialist responses
        specialist_responses = {}
        for specialist in active_specialists:
            specialist_responses[specialist] = random.choice(DEMO_RESPONSES)
        
        # Generate suggested actions
        suggested_actions = [
            "Teknik detayları inceleyelim",
            "Proje planını oluşturalım", 
            "Kullanıcı ihtiyaçlarını analiz edelim",
            "MVP özelliklerini belirleyelim"
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'primary_response': primary_response,
                'active_specialists': active_specialists,
                'specialist_responses': specialist_responses,
                'suggested_next_actions': random.sample(suggested_actions, 2)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/specialist_info')
def specialist_info():
    """Demo specialist info endpoint"""
    return jsonify({
        'success': True,
        'specialists': DEMO_SPECIALISTS
    })

@app.route('/system_status')
def system_status():
    """Demo system status endpoint"""
    return jsonify({
        'success': True,
        'status': {
            'adapters_available': 3,
            'specialists_available': len(DEMO_SPECIALISTS),
            'uptime': '99.9%',
            'last_check': time.time()
        }
    })

# Static files
@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return render_template('404.html'), 404 if os.path.exists('templates/404.html') else ('Page not found', 404)

@app.errorhandler(500)
def server_error(error):
    """500 error handler"""
    return jsonify({'error': 'Internal server error', 'success': False}), 500

if __name__ == '__main__':
    print("🎨 AI Orchestrator UI Demo Server Starting...")
    print("📡 Server will be available at:")
    print("   • http://localhost:5000          - Universal Dashboard")
    print("   • http://localhost:5000/orchestrator - Specialist Coordination")
    print("   • http://localhost:5000/api-management - API Management")
    print("\n✨ Modern UI Features:")
    print("   • Dark/Light Mode Toggle")
    print("   • Advanced Animations")
    print("   • Mobile Responsive Design")
    print("   • Real-time Specialist Coordination")
    print("   • Professional Analytics Dashboard")
    print("\n🚀 Starting development server...")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    ) 