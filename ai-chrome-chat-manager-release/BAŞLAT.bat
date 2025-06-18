@echo off
chcp 65001 >nul
title AI Chrome Chat Manager - Universal Edition

echo.
echo ================================================================================
echo 🎯 AI CHROME CHAT MANAGER - UNIVERSAL EDITION
echo    Akıllı AI-to-AI Köprü Sistemi ^& Plugin Ecosystem
echo ================================================================================
echo.

echo 📋 Sistem kontrol ediliyor...

:: Python kontrolü
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python bulunamadı! Lütfen Python 3.8+ yükleyin.
    echo 📥 İndirme: https://python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo ✅ Python bulundu!

:: Bağımlılık kontrolü
echo 📦 Bağımlılıklar kontrol ediliyor...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo 🔧 Bağımlılıklar yükleniyor...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Bağımlılık yükleme hatası!
        pause
        exit /b 1
    )
)

echo ✅ Bağımlılıklar hazır!
echo.

:: Uygulama başlatma
echo 🚀 AI Chrome Chat Manager başlatılıyor...
echo.
python quickstart.py

echo.
echo Uygulama kapatıldı.
pause 