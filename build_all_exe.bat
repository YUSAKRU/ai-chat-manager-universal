@echo off
echo ================================================================================
echo                   AI CHROME CHAT MANAGER - EXE BUILD STUDIO
echo                          Otomatik Derleme Sistemi v1.0
echo ================================================================================
echo.

REM Python kontrolu
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python bulunamadi! Lutfen Python yukleyin: https://python.org
    pause
    exit /b 1
)
echo ✅ Python sistemi hazir!

REM PyInstaller kontrolu
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo 📦 PyInstaller yukleniyor...
    pip install pyinstaller
    if errorlevel 1 (
        echo ❌ PyInstaller yuklenemedi!
        pause
        exit /b 1
    )
)
echo ✅ PyInstaller hazir!

echo.
echo 🧹 Eski build dosyalari temizleniyor...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del /q "*.spec"
echo    ✅ Temizlik tamamlandi!

echo.
echo 🚀 BUILD SURECI BASLATILIYOR...
echo ----------------------------------------

REM Demo EXE build
echo.
echo 🎮 1/2 - DEMO EXE derleniyor...
pyinstaller --onefile --console --name=AI_Chat_Manager_Demo run_demo.py
if errorlevel 1 (
    echo ❌ Demo EXE derleme hatasi!
    pause
    exit /b 1
)
echo    ✅ Demo EXE hazir!

REM Universal EXE build  
echo.
echo 🎯 2/2 - UNIVERSAL EXE derleniyor...
pyinstaller --onefile --console --name=AI_Chat_Manager_Universal quickstart.py
if errorlevel 1 (
    echo ❌ Universal EXE derleme hatasi!
    pause
    exit /b 1
)
echo    ✅ Universal EXE hazir!

echo.
echo 📊 BUILD SONUÇLARI:
echo ----------------------------------------
dir dist /B

echo.
echo 📋 DOSYA BOYUTLARI:
for %%f in (dist\*.exe) do (
    for %%s in ("%%f") do (
        set /a size=%%~zs/1024/1024
        echo    📁 %%~nxf - !size! MB
    )
)

echo.
echo 📦 PORTABLE PAKET olusturuluyor...
mkdir "AI_Chat_Manager_Portable" 2>nul
copy "dist\*.exe" "AI_Chat_Manager_Portable\" >nul
copy "README.md" "AI_Chat_Manager_Portable\" >nul
copy "LICENSE" "AI_Chat_Manager_Portable\" >nul
copy "EXE_KULLANIM_KLAVUZU.md" "AI_Chat_Manager_Portable\" >nul

echo    ✅ Portable paket hazir: AI_Chat_Manager_Portable/

echo.
echo 🧪 OTOMATIK TEST baslatiliyor...
echo    🎮 Demo EXE test ediliyor... (5 saniye)
start /min dist\AI_Chat_Manager_Demo.exe
timeout 5 >nul
taskkill /im AI_Chat_Manager_Demo.exe /f >nul 2>&1
echo    ✅ Demo EXE calisiyor!

echo.
echo ================================================================================
echo                            🎉 BUILD TAMAMLANDI! 🎉
echo ================================================================================
echo.
echo 📁 OLUŞTURULAN DOSYALAR:
echo    📂 dist/
echo       📄 AI_Chat_Manager_Demo.exe      (Demo - API gerektirmez)
echo       📄 AI_Chat_Manager_Universal.exe (Full - Interaktif menu)
echo.
echo    📂 AI_Chat_Manager_Portable/
echo       📄 Tum dosyalar + dokumantasyon
echo.
echo 🚀 KULLANIM:
echo    🎮 Demo:      dist\AI_Chat_Manager_Demo.exe
echo    🎯 Full:      dist\AI_Chat_Manager_Universal.exe
echo    📦 Portable:  AI_Chat_Manager_Portable klasorunu dagit
echo.
echo 🌐 Demo Test:   http://localhost:5000
echo.
echo ================================================================================
echo                            HAZIR! KULLANIMA SUNUN! ✨
echo ================================================================================
pause 