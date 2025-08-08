@echo off
echo 🔧 Setting up Virtual Environment for Indici MCP Chatbot...
echo.

REM Create new virtual environment
echo 📦 Creating virtual environment...
python -m venv venv_new

REM Install all required packages
echo 📥 Installing dependencies...
venv_new\Scripts\pip.exe install PyJWT msal requests cryptography Flask-Session Flask Flask-SocketIO python-dotenv groq pydantic aiohttp pillow eventlet

echo.
echo ✅ Virtual environment setup complete!
echo ✅ All Teams SSO dependencies installed
echo.
echo 🚀 You can now run: start_app.bat
echo.

pause
