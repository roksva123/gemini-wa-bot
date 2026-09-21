#!/bin/bash
# Quick start script untuk Linux/Mac

echo "🚀 Gemini WhatsApp Bot - Quick Start"
echo "===================================="

# Check Python version
echo "✓ Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "  Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "✓ Creating virtual environment..."
    python3 -m venv venv
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "✓ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "✓ Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠ .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "   Please edit .env with your credentials and run this script again"
    exit 1
fi

# Check PostgreSQL connection
echo "✓ Checking PostgreSQL connection..."
python3 -c "from database import engine; engine.connect(); print('   ✓ Database connection successful')" 2>/dev/null || {
    echo "   ⚠ Could not connect to database"
    echo "   Make sure PostgreSQL is running and DATABASE_URL is correct in .env"
}

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the bot, run:"
echo "  python main.py"
echo ""
echo "Or use uvicorn directly:"
echo "  uvicorn main:app --reload --host 0.0.0.0 --port 8000"
