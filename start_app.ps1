# PowerShell script to start Indici MCP Chatbot with Teams SSO
Write-Host "🚀 Starting Indici MCP Chatbot with Teams SSO..." -ForegroundColor Green
Write-Host ""

# Check if new virtual environment exists
if (-not (Test-Path "venv_new\Scripts\python.exe")) {
    Write-Host "❌ Virtual environment not found. Please run setup_venv.ps1 first." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "❌ .env file not found. Please copy .env.example to .env and configure your API keys." -ForegroundColor Red
    Write-Host "⚠️  SECURITY WARNING: Never commit your .env file to version control!" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✅ Using virtual environment: venv_new" -ForegroundColor Green
Write-Host "✅ Environment variables loaded from .env" -ForegroundColor Green
Write-Host "✅ Teams SSO authentication enabled" -ForegroundColor Green
Write-Host "✅ Microsoft Graph integration ready" -ForegroundColor Green
Write-Host ""

# Start the Flask application
Write-Host "🌐 Starting server on http://localhost:10000" -ForegroundColor Cyan
Write-Host "📱 Teams tab URL: http://localhost:10000/teams" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

& ".\venv_new\Scripts\python.exe" web/app.py
