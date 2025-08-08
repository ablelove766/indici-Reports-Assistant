@echo off
echo 🚀 Starting Indici MCP Chatbot with Teams SSO...
echo.

REM Check if new virtual environment exists
if not exist "venv_new\Scripts\python.exe" (
    echo ❌ Virtual environment not found. Please run setup_venv.bat first.
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo ❌ .env file not found. Please copy .env.example to .env and configure your API keys.
    echo ⚠️  SECURITY WARNING: Never commit your .env file to version control!
    pause
    exit /b 1
)

echo ✅ Using virtual environment: venv_new
echo ✅ Environment variables loaded from .env
echo ✅ Teams SSO authentication enabled
echo ✅ Microsoft Graph integration ready
echo.

REM Start the Flask application
echo 🌐 Starting server on http://localhost:10000
echo 📱 Teams tab URL: http://localhost:10000/teams
echo ⚠️  Press Ctrl+C to stop the server
echo.

venv_new\Scripts\python.exe web/app.py

pause
