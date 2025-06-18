#!/usr/bin/env python3
"""
🏗️ EXE Build Script - AI Chrome Chat Manager
PyInstaller ile Windows exe dosyası oluşturur
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def create_exe_build():
    print("🏗️ AI CHROME CHAT MANAGER EXE BUILD")
    print("="*50)
    
    # Build directory'yi temizle
    print("🧹 Build klasörü temizleniyor...")
    for folder in ['build', 'dist', '__pycache__']:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"   ✅ {folder} silindi")
    
    # PyInstaller spec dosyası oluştur
    print("\n📝 PyInstaller spec dosyası oluşturuluyor...")
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Ana script dosyaları
a = Analysis(
    ['quickstart.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('plugins', 'plugins'),
        ('memory-bank', 'memory-bank'),
        ('env.example', '.'),
        ('README.md', '.'),
        ('requirements.txt', '.')
    ],
    hiddenimports=[
        'flask',
        'flask_socketio',
        'google.generativeai',
        'openai',
        'cryptography',
        'sqlite3',
        'webbrowser',
        'threading',
        'asyncio',
        'json',
        'uuid',
        'time',
        'datetime',
        'pathlib',
        'src.ai_adapters.base_adapter',
        'src.ai_adapters.gemini_adapter', 
        'src.ai_adapters.openai_adapter',
        'src.ai_adapters.universal_adapter',
        'src.ai_adapters.secure_config',
        'src.web_ui_universal',
        'src.plugin_manager',
        'src.project_memory',
        'src.memory_bank_integration'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AI_Chrome_Chat_Manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico'  # İkon varsa
)
'''
    
    with open('ai_chat_manager.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    print("   ✅ ai_chat_manager.spec oluşturuldu")
    
    # Demo için basit EXE build
    print("\n🚀 DEMO EXE oluşturuluyor...")
    demo_cmd = [
        'pyinstaller',
        '--onefile',                    # Tek exe dosyası
        '--windowed',                   # Console gizli (demo için)
        '--name=AI_Chat_Manager_Demo',  # EXE adı
        '--distpath=exe_output',        # Çıktı klasörü
        '--add-data=templates;templates',
        '--add-data=static;static',
        '--hidden-import=flask',
        '--hidden-import=flask_socketio',
        'run_demo.py'
    ]
    
    try:
        result = subprocess.run(demo_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ Demo EXE başarıyla oluşturuldu!")
        else:
            print(f"   ❌ Demo EXE hatası: {result.stderr}")
    except Exception as e:
        print(f"   ❌ Demo EXE build hatası: {e}")
    
    # Production için advanced EXE build
    print("\n🏭 PRODUCTION EXE oluşturuluyor...")
    production_cmd = [
        'pyinstaller',
        '--onefile',
        '--console',                       # Console görünür (debug için)
        '--name=AI_Chat_Manager_Full',
        '--distpath=exe_output',
        '--add-data=templates;templates',
        '--add-data=static;static',
        '--add-data=plugins;plugins',
        '--add-data=src;src',
        '--hidden-import=flask',
        '--hidden-import=flask_socketio', 
        '--hidden-import=google.generativeai',
        '--hidden-import=openai',
        '--hidden-import=cryptography',
        'quickstart.py'
    ]
    
    try:
        result = subprocess.run(production_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ Production EXE başarıyla oluşturuldu!")
        else:
            print(f"   ❌ Production EXE hatası: {result.stderr}")
    except Exception as e:
        print(f"   ❌ Production EXE build hatası: {e}")
    
    # Portable versiyon için bundle oluştur
    print("\n📦 PORTABLE BUNDLE oluşturuluyor...")
    bundle_cmd = [
        'pyinstaller',
        '--onedir',                        # Klasör formatı
        '--console',
        '--name=AI_Chat_Manager_Portable',
        '--distpath=exe_output',
        '--add-data=templates;templates',
        '--add-data=static;static',
        '--add-data=plugins;plugins',
        '--add-data=memory-bank;memory-bank',
        '--add-data=README.md;.',
        'quickstart.py'
    ]
    
    try:
        result = subprocess.run(bundle_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ Portable Bundle başarıyla oluşturuldu!")
        else:
            print(f"   ❌ Bundle hatası: {result.stderr}")
    except Exception as e:
        print(f"   ❌ Bundle build hatası: {e}")
    
    # Build sonuçlarını göster
    print("\n📊 BUILD SONUÇLARI:")
    print("-"*30)
    
    exe_output = Path('exe_output')
    if exe_output.exists():
        for file in exe_output.iterdir():
            if file.is_file():
                size_mb = file.stat().st_size / (1024 * 1024)
                print(f"   📁 {file.name}")
                print(f"      💾 Boyut: {size_mb:.1f} MB")
                print(f"      📍 Konum: {file.absolute()}")
                print()
            elif file.is_dir():
                print(f"   📂 {file.name}/ (Klasör)")
                print(f"      📍 Konum: {file.absolute()}")
                print()
    
    # Kullanım talimatları
    print("🎯 EXE KULLANIM TALİMATLARI:")
    print("-"*30)
    instructions = [
        "1. 🎮 Demo EXE:",
        "   - AI_Chat_Manager_Demo.exe çift tıkla",
        "   - Otomatik tarayıcı açılır",
        "   - API anahtarı gerektirmez",
        "",
        "2. 🏭 Production EXE:",
        "   - AI_Chat_Manager_Full.exe çalıştır",
        "   - İnteraktif menüden API kurulumu yap",
        "   - Tam özellikli sistem",
        "",
        "3. 📦 Portable Bundle:",
        "   - AI_Chat_Manager_Portable klasörünü kopyala",
        "   - quickstart.exe çalıştır",
        "   - Tüm dosyalar dahil"
    ]
    
    for instruction in instructions:
        print(f"   {instruction}")
    
    print("\n" + "="*50)
    print("🎉 EXE BUILD TAMAMLANDI!")
    print("📁 Dosyalar: exe_output/ klasöründe")

if __name__ == "__main__":
    create_exe_build() 