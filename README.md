# indici MCP Chatbot

A professional MCP (Model Context Protocol) server with LLM chatbot integration for the indici Reports API.

## Features

- **MCP Server**: Connects to indiciAPI endpoints for indici Reports
- **LLM Chatbot**: Powered by Groq API for intelligent report generation
- **Web Interface**: Professional indici-themed UI with sidebar sample queries
- **Real-time Communication**: WebSocket-based chat interface
- **Microsoft Teams Integration**: SSO authentication and Teams tab support
- **Secure Authentication**: Azure AD integration with token exchange
- **Mobile Responsive**: Optimized for Teams mobile and desktop

## Project Structure

```
indiciMCP-Chatbot/
├── mcp_server/              # MCP Server implementation
│   ├── __init__.py
│   ├── server.py           # Main MCP server
│   ├── tools.py            # API tools and endpoints
│   └── config.py           # Configuration settings
├── chatbot/                # Chatbot implementation
│   ├── __init__.py
│   ├── groq_client.py      # Groq API integration
│   ├── openrouter_client.py # OpenRouter API integration
│   ├── chat_handler.py     # Chat logic and MCP integration
│   ├── mcp_client.py       # MCP client integration
│   └── prompts.py          # System prompts and templates
├── web/                    # Web interface
│   ├── static/             # CSS, JS, images
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   ├── templates/          # HTML templates
│   │   ├── index.html
│   │   ├── teams_*.html    # Teams-specific templates
│   │   └── chat.html
│   ├── app.py              # Flask web application
│   └── auth.py             # Teams SSO authentication
├── teams/                  # Microsoft Teams integration
│   ├── manifest.json       # Teams app manifest
│   ├── README.md           # Teams setup guide
│   └── icons/              # Teams app icons
├── venv_new/               # Virtual environment (not in git)
├── requirements_clean.txt  # Python dependencies
├── config.json            # Application configuration
├── .env.example           # Environment variables template
├── .env                   # Environment variables (not in git)
├── setup_venv.bat         # Virtual environment setup
├── start_app.bat          # Application startup script
└── README.md              # This file
```

## Installation

1. Clone the repository
2. Set up virtual environment:
   ```bash
   # Run the setup script
   setup_venv.bat
   ```
   Or manually:
   ```bash
   python -m venv venv_new
   venv_new\Scripts\pip install -r requirements_clean.txt
   ```
3. Configure your API keys:
   - Copy `.env.example` to `.env`
   - Add your actual API keys (NEVER commit the .env file!)
4. Start the application:
   ```bash
   # Use the start script
   start_app.bat
   ```
   Or manually:
   ```bash
   venv_new\Scripts\python web/app.py
   ```

## API Endpoints

The MCP server provides access to the following indiciAPI endpoints:

- **Generate indici Reports (GET)**: Query-based report generation
- **Generate indici Reports (POST)**: JSON body-based report generation
- **Health Check**: Service health verification

## Usage

1. Open the web interface at `http://localhost:10000`
2. For Teams integration, use `http://localhost:10000/teams`
3. Use the sidebar sample queries or type custom requests
4. The chatbot will interact with the indiciAPI through the MCP server
5. View formatted report results in the chat interface

## Configuration

### Environment Variables
Configure API keys and sensitive settings in `.env` file:
- **GROQ_API_KEY**: Your Groq API key for LLM functionality
- **OPENROUTER_API_KEY**: Your OpenRouter API key for alternative LLM
- **AZURE_CLIENT_ID**: Azure AD application ID for Teams SSO
- **AZURE_CLIENT_SECRET**: Azure AD client secret for Teams SSO
- **AZURE_TENANT_ID**: Your Azure AD tenant ID

⚠️ **Security Warning**: Never commit your `.env` file or expose API keys in code!

## Microsoft Teams Integration

### Features
- **Single Sign-On (SSO)**: Automatic authentication using Teams identity
- **Silent Authentication**: No additional login required for Teams users
- **Token Exchange**: Secure On-Behalf-Of flow for Microsoft Graph access
- **Responsive Design**: Optimized for Teams desktop and mobile
- **Iframe Embedding**: Secure embedding as Teams tab

### Setup
1. Configure Azure AD app registration with your credentials in `.env`
2. Update `teams/manifest.json` with your app details
3. Deploy to your hosting platform (e.g., render.com)
4. Install the Teams app using the manifest

### Teams URLs
- **Configuration**: `https://your-domain.com/teams/config`
- **Tab Interface**: `https://your-domain.com/teams`
- **Local Testing**: `http://localhost:10000/teams`

### Application Settings
Edit `config.json` to configure:
- indiciAPI base URL
- MCP server settings
- Web interface settings
- Model parameters (with environment variable override)
