# indici MCP Chatbot

A professional MCP (Model Context Protocol) server with LLM chatbot integration for the indici Reports API.

## Features

- **MCP Server**: Connects to indiciAPI endpoints for indici Reports
- **LLM Chatbot**: Powered by Groq API for intelligent report generation
- **Web Interface**: Professional indici-themed UI with sidebar sample queries
- **Real-time Communication**: WebSocket-based chat interface

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
│   ├── chat_handler.py     # Chat logic and MCP integration
│   └── prompts.py          # System prompts and templates
├── web/                    # Web interface
│   ├── static/             # CSS, JS, images
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   ├── templates/          # HTML templates
│   │   ├── index.html
│   │   └── chat.html
│   └── app.py              # Flask web application
├── requirements.txt        # Python dependencies
├── config.json            # Application configuration
└── README.md              # This file
```

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure your API keys in `.env` file (see ENV_SETUP.md)
4. Start the MCP server:
   ```bash
   python mcp_server/server.py
   ```
5. Start the web interface:
   ```bash
   python web/app.py
   ```

## API Endpoints

The MCP server provides access to the following indiciAPI endpoints:

- **Generate indici Reports (GET)**: Query-based report generation
- **Generate indici Reports (POST)**: JSON body-based report generation
- **Health Check**: Service health verification

## Usage

1. Open the web interface at `http://localhost:5000`
2. Use the sidebar sample queries or type custom requests
3. The chatbot will interact with the indiciAPI through the MCP server
4. View formatted report results in the chat interface

## Configuration

### Environment Variables
Configure API keys and sensitive settings in `.env` file:
- Groq API key
- OpenRouter API key
- See `ENV_SETUP.md` for complete setup guide

### Application Settings
Edit `config.json` to configure:
- indiciAPI base URL
- MCP server settings
- Web interface settings
- Model parameters (with environment variable override)
