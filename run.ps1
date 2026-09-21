# Quick start script untuk Windows PowerShell

Write-Host "🚀 Gemini WhatsApp Bot - Quick Start" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host ""

# Check Python version
Write-Host "✓ Checking Python version..." -ForegroundColor Cyan
$pythonVersion = python --version 2>&1
Write-Host "  $pythonVersion"

# Create virtual environment
if (-not (Test-Path "venv")) {
    Write-Host "✓ Creating virtual environment..." -ForegroundColor Cyan
    python -m venv venv
} else {
    Write-Host "✓ Virtual environment already exists" -ForegroundColor Cyan
}

# Activate virtual environment
Write-Host "✓ Activating virtual environment..." -ForegroundColor Cyan
& ".\venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host "✓ Installing dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠ .env file not found. Creating from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "   Please edit .env with your credentials and run this script again" -ForegroundColor Yellow
    exit 1
}

# Check PostgreSQL connection
Write-Host "✓ Checking PostgreSQL connection..." -ForegroundColor Cyan
try {
    python -c "from database import engine; engine.connect(); print('   ✓ Database connection successful')" 2>$null
} catch {
    Write-Host "   ⚠ Could not connect to database" -ForegroundColor Yellow
    Write-Host "   Make sure PostgreSQL is running and DATABASE_URL is correct in .env" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To start the bot, run:" -ForegroundColor White
Write-Host "  python main.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "Or use uvicorn directly:" -ForegroundColor White
Write-Host "  uvicorn main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Yellow
