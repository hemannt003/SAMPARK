#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
#  Sampark AI — Local development startup script
#  Starts both FastAPI backend and Streamlit frontend
# ═══════════════════════════════════════════════════════════════
set -e

echo "═══════════════════════════════════════"
echo "  Sampark AI — Starting dev servers"
echo "═══════════════════════════════════════"

# Check .env
if [ ! -f .env ]; then
    echo "⚠  No .env file found. Copying from .env.example ..."
    cp .env.example .env
    echo "   Please edit .env with your API keys."
fi

# Install deps if needed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Create data dir
mkdir -p data/faiss_index

# Start FastAPI in background
echo "🚀 Starting FastAPI on :8000 ..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend
sleep 3

# Start Streamlit
echo "🎨 Starting Streamlit on :8501 ..."
streamlit run app.py --server.port 8501 --server.address 0.0.0.0 &
FRONTEND_PID=$!

echo ""
echo "═══════════════════════════════════════"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:8501"
echo "  API Docs: http://localhost:8000/docs"
echo "═══════════════════════════════════════"
echo "  Press Ctrl+C to stop both servers"
echo ""

# Trap Ctrl+C to kill both
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM
wait
