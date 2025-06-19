#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Orchestrator EXE Builder - PRODUCTION READY
Optimized build for stable, fast, and compact executable
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def main():
    print("🏗️ AI Orchestrator EXE Builder - PRODUCTION")
    print("=" * 60)
    
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
    
    # PyInstaller command - OPTIMIZED
    pyinstaller_cmd = [
        "pyinstaller",
        "--onefile",                           # Tek dosya
        "--windowed",                          # GUI mod (console gizli)
        "--name=AI_Orchestrator_Production",   # Yeni isim
        "--distpath=dist",                     # Output klasörü
        "--workpath=build",                    # Temp klasörü
        "--clean",                             # Temiz build
        
        # Optimize etmek için
        "--strip",                             # Debug sembollerini çıkar
        "--noupx",                             # UPX sıkıştırma kullanma
        
        # Template ve static dosyaları dahil et
        f"--add-data={templates_dir}{os.pathsep}templates",
        f"--add-data={static_dir}{os.pathsep}static",
        
        # Sadece gerekli modülleri dahil et
        f"--add-data={src_dir}/ai_adapters{os.pathsep}ai_adapters",
        f"--add-data={src_dir}/config.py{os.pathsep}.",
        f"--add-data={src_dir}/logger.py{os.pathsep}.",
        
        # Gereksiz modülleri hariç tut
        "--exclude-module=torch",              # PyTorch çok büyük
        "--exclude-module=tensorflow", 
        "--exclude-module=matplotlib",
        "--exclude-module=scipy", 
        "--exclude-module=pandas",
        "--exclude-module=numpy",
        "--exclude-module=sympy",
        "--exclude-module=pytest",
        
        # Ana dosya
        str(src_dir / "main.py")
    ]
    
    print("🔨 Optimize edilmiş EXE build başlatılıyor...")
    print(f"📁 Kaynak: {src_dir / 'main.py'}")
    print(f"📦 Hedef: dist/AI_Orchestrator_Production.exe")
    print("⚡ Optimizasyonlar aktif: Strip debug, Exclude heavy modules")
    
    try:
        # Run PyInstaller
        print("⏳ Build süreci başladı (birkaç dakika sürebilir)...")
        result = subprocess.run(pyinstaller_cmd, check=True, capture_output=True, text=True)
        
        print("✅ EXE başarıyla oluşturuldu!")
        
        # Check output
        exe_path = dist_dir / "AI_Orchestrator_Production.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"📊 Dosya boyutu: {size_mb:.1f} MB")
            print(f"📍 Konum: {exe_path.absolute()}")
            
            # Create usage info
            print("\n" + "="*60)
            print("�� PRODUCTION EXE HAZIR!")
            print("="*60)
            print("📋 Kullanım Talimatları:")
            print("1. 🚀 AI_Orchestrator_Production.exe dosyasını çift tıklayın")
            print("2. 🌐 Web tarayıcı otomatik açılacak (http://localhost:5000)")
            print("3. 🔑 API Yönetimi'nden API anahtarlarınızı girin")
            print("4. 🤖 AI uzmanları ile çalışmaya başlayın!")
            print("\n🔧 Özellikler:")
            print("  ✅ Hızlı başlatma (optimize edilmiş)")
            print("  ✅ Kompakt boyut (gereksiz modüller çıkarıldı)")
            print("  ✅ GUI modlu (terminal gizli)")
            print("  ✅ Production-ready")
            
        else:
            print("❌ EXE dosyası oluşturulamadı!")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Build hatası: {e}")
        if e.stdout:
            print(f"Output: {e.stdout[-500:]}")  # Son 500 karakter
        if e.stderr:
            print(f"Error: {e.stderr[-500:]}")   # Son 500 karakter
        return False
        
    except FileNotFoundError:
        print("❌ PyInstaller bulunamadı!")
        print("📦 Yüklemek için: pip install pyinstaller")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎉 PRODUCTION BUILD TAMAMLANDI!")
        print("🚀 Artık projeniz pazara sunulmaya hazır!")
    else:
        print("\n💥 Build başarısız!")
        print("🔧 Lütfen hataları kontrol edin ve tekrar deneyin.")
        sys.exit(1) 