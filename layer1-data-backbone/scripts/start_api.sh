#!/bin/bash
# Start Healthcare API server

cd "$(dirname "$0")/../api"

echo "🏥 Starting Healthcare API..."
echo "========================================"

# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -q -r requirements.txt
    echo "✅ Dependencies installed"
fi

echo ""
echo "🚀 Launching API server..."
echo "📡 API: http://localhost:8000"
echo "📚 Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo "========================================"
echo ""

python app/main.py

