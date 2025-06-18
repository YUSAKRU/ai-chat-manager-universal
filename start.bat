@echo off
echo ================================================================================
echo                AI CHROME CHAT MANAGER - UNIVERSAL EDITION
echo                        Akilli AI-to-AI Kopru Sistemi
echo ================================================================================
echo.

REM Python kontrolu
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python bulunamadi! Lutfen Python yukleyin: https://python.org
    pause
    exit /b 1
)

echo ✅ Python bulundu!
echo.

REM Secenekleri goster
echo 🎮 CALISTIRMA SECENEKLERI:
echo.
echo [1] DEMO MODE      - API anahtari gerektirmez
echo [2] PRODUCTION     - Gercek API anahtarlari gerekir
echo [3] QUICK START    - Interaktif menu
echo [4] SETUP          - Kurulum yardimcisi
echo.

set /p choice="🎯 Seciminizi yapin (1-4): "

if "%choice%"=="1" (
    echo.
    echo 🎮 DEMO MODE baslatiliyor...
    echo 🌐 Tarayiciniz otomatik acilacak: http://localhost:5000
    echo ❌ Cikmak icin: Ctrl+C
    python run_demo.py
) else if "%choice%"=="2" (
    echo.
    echo 🚀 PRODUCTION MODE baslatiliyor...
    python run_production.py
) else if "%choice%"=="3" (
    echo.
    echo 🎯 QUICK START menu aciliyor...
    python quickstart.py
) else if "%choice%"=="4" (
    echo.
    echo 🔧 SETUP baslatiliyor...
    pip install -r requirements.txt
    echo ✅ Kurulum tamamlandi!
) else (
    echo ❌ Gecersiz secim!
)

echo.
pause 