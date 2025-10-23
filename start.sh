#!/bin/bash

# Fantasy League Assistant Startup Script
# Starts both the API server and web UI

echo "=============================================="
echo "🏈 Starting Fantasy League Assistant"
echo "=============================================="
echo ""

# Check if we're in the right directory
if [ ! -f "config.py" ]; then
    echo "❌ Error: config.py not found. Please run this script from the project root."
    exit 1
fi

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "=============================================="
    echo "🛑 Shutting down services..."
    echo "=============================================="
    kill $API_PID 2>/dev/null
    kill $WEB_PID 2>/dev/null
    exit 0
}

trap cleanup INT TERM

# Start API server in background
echo "🚀 Starting API server on http://localhost:5001..."
python3 api_server.py > api_server.log 2>&1 &
API_PID=$!
sleep 2

# Check if API server started successfully
if ! ps -p $API_PID > /dev/null; then
    echo "❌ Failed to start API server. Check api_server.log for details."
    exit 1
fi
echo "✅ API server started (PID: $API_PID)"
echo ""

# Start web UI in background
echo "🚀 Starting web UI on http://localhost:3000..."
cd web-ui
npm run dev > ../web_ui.log 2>&1 &
WEB_PID=$!
cd ..
sleep 3

# Check if web UI started successfully
if ! ps -p $WEB_PID > /dev/null; then
    echo "❌ Failed to start web UI. Check web_ui.log for details."
    kill $API_PID
    exit 1
fi
echo "✅ Web UI started (PID: $WEB_PID)"
echo ""

echo "=============================================="
echo "✅ All services running!"
echo "=============================================="
echo ""
echo "🌐 Open your browser to: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"
echo "=============================================="
echo ""

# Wait for user to press Ctrl+C
wait


