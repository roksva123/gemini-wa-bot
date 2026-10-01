@echo off
REM ==================================================================================
REM QUICK DEMO SCRIPT - Customize dan Jalankan Tests dalam 2 Menit (Windows)
REM ==================================================================================
REM Cara pakai:
REM   quick_demo.bat
REM
REM Script ini akan:
REM   1. Copy template yang paling sesuai
REM   2. Edit dengan data bisnis Anda (guided)
REM   3. Jalankan tests
REM   4. Buka report di browser

setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║     🚀 WhatsApp Bot - Quick Demo Setup ^(2 Menit^)          ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python tidak ditemukan. Install Python 3.8+ terlebih dahulu.
    pause
    exit /b 1
)

REM Check if bot is running
echo 📌 Checking if bot is running...
timeout /t 1 /nobreak >nul
python -c "import httpx; httpx.get('http://localhost:8000/health', timeout=2)" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Bot tidak running di http://localhost:8000
    echo    Jalankan terlebih dahulu: python main.py
    echo.
    pause
    exit /b 1
)
echo ✅ Bot is running!
echo.

REM Ask which template to use
echo 📋 Pilih jenis bisnis Anda:
echo    1) Toko Reparasi HP ^(Phone Repair^)
echo    2) Toko Online / E-Commerce
echo    3) Custom ^(manual edit^)
echo.
set /p choice="Pilih (1/2/3): "

if "%choice%"=="1" (
    set TEMPLATE=test_templates\test_cases.phone_repair.yaml
    set BUSINESS=Phone Repair
) else if "%choice%"=="2" (
    set TEMPLATE=test_templates\test_cases.ecommerce.yaml
    set BUSINESS=E-Commerce
) else if "%choice%"=="3" (
    set TEMPLATE=test_cases.yaml
    set BUSINESS=Custom
) else (
    echo Invalid choice
    pause
    exit /b 1
)

REM Copy template
if not "%TEMPLATE%"=="test_cases.yaml" (
    echo.
    echo 📋 Copying template untuk %BUSINESS%...
    copy "%TEMPLATE%" test_cases.yaml >nul
    echo ✅ Template copied to test_cases.yaml
)

REM Ask to edit
echo.
echo 📝 Edit test_cases.yaml dengan data bisnis Anda:
echo    - Ganti jam_kerja, alamat, nomor_admin, dll
echo    - Sesuaikan pertanyaan dengan bahasa customer Anda
echo.
set /p edit_choice="Buka editor sekarang? (y/n): "

if /i "%edit_choice%"=="y" (
    if exist "%WINDIR%\notepad.exe" (
        start notepad.exe test_cases.yaml
        echo ✓ Notepad dibuka. Simpan file dan tutup untuk lanjut.
        pause
    ) else (
        echo ⚠️  Tidak bisa membuka editor. Edit manual: test_cases.yaml
        pause
    )
)

REM Install dependencies
echo.
echo 📌 Installing dependencies...
pip install -q pyyaml httpx >nul 2>&1

REM Run tests
echo.
echo 🚀 Menjalankan tests...
echo ════════════════════════════════════════════════════════════
python demo_test_runner.py

REM Try to open report
echo.
echo 📊 Buka report di browser:
start test_report.html

echo.
echo ✅ Done! Report tersimpan di:
echo    • test_report.html  ^(visual report - share ini ke client^)
echo    • test_report.json  ^(raw data for automation^)
echo.
pause
