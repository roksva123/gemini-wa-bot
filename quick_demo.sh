#!/usr/bin/env bash
# ==================================================================================
# QUICK DEMO SCRIPT - Customize dan Jalankan Tests dalam 2 Menit
# ==================================================================================
# Cara pakai:
#   bash quick_demo.sh
#
# Script ini akan:
#   1. Copy template yang paling sesuai
#   2. Edit dengan data bisnis Anda (guided)
#   3. Jalankan tests
#   4. Buka report di browser

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     🚀 WhatsApp Bot - Quick Demo Setup (2 Menit)          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python &> /dev/null; then
    echo "❌ Python tidak ditemukan. Install Python 3.8+ terlebih dahulu."
    exit 1
fi

# Check if bot is running
echo "📌 Checking if bot is running..."
if ! timeout 2 python -c "import httpx; httpx.get('http://localhost:8000/health', timeout=2)" 2>/dev/null; then
    echo "⚠️  Bot tidak running di http://localhost:8000"
    echo "   Jalankan terlebih dahulu: python main.py"
    exit 1
fi
echo "✅ Bot is running!"
echo ""

# Ask which template to use
echo "📋 Pilih jenis bisnis Anda:"
echo "  1) Toko Reparasi HP (Phone Repair)"
echo "  2) Toko Online / E-Commerce"
echo "  3) Custom (manual edit)"
echo ""
read -p "Pilih (1/2/3): " choice

case $choice in
    1)
        TEMPLATE="test_templates/test_cases.phone_repair.yaml"
        BUSINESS="Phone Repair"
        ;;
    2)
        TEMPLATE="test_templates/test_cases.ecommerce.yaml"
        BUSINESS="E-Commerce"
        ;;
    3)
        TEMPLATE="test_cases.yaml"
        BUSINESS="Custom"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

# Copy template
if [ "$TEMPLATE" != "test_cases.yaml" ]; then
    echo ""
    echo "📋 Copying template untuk $BUSINESS..."
    cp "$TEMPLATE" test_cases.yaml
    echo "✅ Template copied to test_cases.yaml"
fi

# Ask to edit
echo ""
echo "📝 Edit test_cases.yaml dengan data bisnis Anda:"
echo "   - Ganti jam_kerja, alamat, nomor_admin, dll"
echo "   - Sesuaikan pertanyaan dengan bahasa customer Anda"
echo ""
read -p "Buka editor sekarang? (y/n): " edit_choice

if [ "$edit_choice" = "y" ]; then
    if [ -n "$EDITOR" ]; then
        $EDITOR test_cases.yaml
    elif command -v nano &> /dev/null; then
        nano test_cases.yaml
    elif command -v code &> /dev/null; then
        code test_cases.yaml
    else
        echo "⚠️  Tidak bisa membuka editor. Edit manual: test_cases.yaml"
    fi
fi

# Install dependencies
echo ""
echo "📌 Installing dependencies..."
pip install -q pyyaml httpx 2>/dev/null || pip install pyyaml httpx

# Run tests
echo ""
echo "🚀 Menjalankan tests..."
echo "════════════════════════════════════════════════════════════"
python demo_test_runner.py

# Try to open report
echo ""
echo "📊 Buka report di browser:"
if command -v xdg-open &> /dev/null; then
    xdg-open test_report.html
elif command -v open &> /dev/null; then
    open test_report.html
elif command -v start &> /dev/null; then
    start test_report.html
else
    echo "   file://$(pwd)/test_report.html"
fi

echo ""
echo "✅ Done! Report tersimpan di:"
echo "   • test_report.html  (visual report - share ini ke client)"
echo "   • test_report.json  (raw data for automation)"
