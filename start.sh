#!/bin/bash
# ═══════════════════════════════════════════════
#  WANDATA ATS Checker — Quick Start Script
# ═══════════════════════════════════════════════

echo ""
echo "  ██╗    ██╗ █████╗ ███╗   ██╗██████╗  █████╗ ████████╗ █████╗ "
echo "  ██║    ██║██╔══██╗████╗  ██║██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗"
echo "  ██║ █╗ ██║███████║██╔██╗ ██║██║  ██║███████║   ██║   ███████║"
echo "  ██║███╗██║██╔══██║██║╚██╗██║██║  ██║██╔══██║   ██║   ██╔══██║"
echo "  ╚███╔███╔╝██║  ██║██║ ╚████║██████╔╝██║  ██║   ██║   ██║  ██║"
echo "   ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝"
echo ""
echo "  AI-Powered ATS Resume Intelligence"
echo "════════════════════════════════════════════"

# Check Python
if ! command -v python3 &>/dev/null; then
  echo "❌ Python 3 not found. Please install Python 3.8+"
  exit 1
fi

echo "✅ Python $(python3 --version | cut -d' ' -f2) detected"

# Install deps
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt -q --break-system-packages 2>/dev/null || \
pip3 install -r requirements.txt -q

echo "✅ Dependencies ready"
echo ""
echo "🚀 Starting WANDATA ATS Server..."
echo "   Open: http://localhost:5000"
echo "════════════════════════════════════════════"
echo ""

# Run server
python3 app.py
