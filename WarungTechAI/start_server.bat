@echo off
echo 🚀 Starting WarungTech AI Assistant...
echo =====================================

cd /d "%~dp0"

echo 🔧 Checking configuration...
python test_config.py
if errorlevel 1 (
    echo ❌ Configuration test failed!
    pause
    exit /b 1
)

echo.
echo 🤖 Starting AI server...
echo 📡 Server will be available at: http://localhost:5000
echo 🔍 Health check: http://localhost:5000/health
echo 💬 Chat endpoint: http://localhost:5000/chat
echo.
echo ⏹️ Press Ctrl+C to stop the server
echo =====================================

python start_ai_server.py

pause