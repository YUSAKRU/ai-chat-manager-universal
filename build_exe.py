#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Orchestrator EXE Builder
Builds single executable for the MCP-style orchestrator system
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def main():
    print("🏗️ AI Orchestrator EXE Builder")
    print("=" * 50)
    
    # Get project root
    project_root = Path(__file__).parent
    src_dir = project_root / "src"
    templates_dir = project_root / "templates"
    static_dir = project_root / "static"
    build_dir = project_root / "build"
    dist_dir = project_root / "dist"
    
    # Clean previous builds
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    print("🧹 Önceki build dosyaları temizlendi")
    
    # PyInstaller command for orchestrator
    pyinstaller_cmd = [
        "pyinstaller",
        "--onefile",                    # Tek dosya olarak paketleme
        "--windowed",                   # Console penceresiz
        "--name=AI_Orchestrator",       # EXE ismi
        "--distpath=dist",              # Output klasörü
        "--workpath=build",             # Temp klasörü
        
        # Add data files
        f"--add-data={templates_dir};templates",
        f"--add-data={static_dir};static",
        
        # Add source modules
        f"--add-data={src_dir}/ai_adapters;ai_adapters",
        f"--add-data={src_dir}/config.py;.",
        f"--add-data={src_dir}/logger.py;.",
        
        # Main entry point
        str(src_dir / "main.py")
    ]
    
    print("🔨 EXE build başlatılıyor...")
    print(f"📁 Kaynak: {src_dir / 'main.py'}")
    print(f"📦 Hedef: dist/AI_Orchestrator.exe")
    
    try:
        # Run PyInstaller
        result = subprocess.run(pyinstaller_cmd, check=True, capture_output=True, text=True)
        
        print("✅ EXE başarıyla oluşturuldu!")
        
        # Check output
        exe_path = dist_dir / "AI_Orchestrator.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"📊 Dosya boyutu: {size_mb:.1f} MB")
            print(f"📍 Konum: {exe_path.absolute()}")
            
            # Create shortcut info
            print("\n📋 Kullanım:")
            print("1. AI_Orchestrator.exe dosyasını çift tıklayın")
            print("2. Web tarayıcı otomatik açılacak (http://localhost:5000)")
            print("3. API anahtarlarınızı web arayüzünden girin")
            print("4. AI uzmanlar ile sohbet etmeye başlayın!")
            
        else:
            print("❌ EXE dosyası oluşturulamadı!")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Build hatası: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False
        
    except FileNotFoundError:
        print("❌ PyInstaller bulunamadı!")
        print("Yüklemek için: pip install pyinstaller")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎉 Build tamamlandı!")
    else:
        print("\n💥 Build başarısız!")
        sys.exit(1) 