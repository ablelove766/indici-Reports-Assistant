# Indici MCP Chatbot - Setup Guide

## Overview

This guide will help you set up and run the complete Indici MCP Chatbot system, which includes:

1. **IndiciAPI** - The .NET Core API for Provider Capitation Reports
2. **MCP Server** - Python MCP server that connects to IndiciAPI
3. **Groq Chatbot** - LLM-powered chatbot using Groq API
4. **Web Interface** - Professional Indici-themed web UI

## Prerequisites

### Software Requirements
- **Python 3.8+** (for MCP server and chatbot)
- **.NET 5.0+** (for IndiciAPI)
- **SQL Server** (for database)
- **Modern web browser** (Chrome, Firefox, Safari, Edge)

### API Keys
- **Groq API Key**: Configure in `.env` file (see ENV_SETUP.md)
- **OpenRouter API Key**: Configure in `.env` file (see ENV_SETUP.md)

## Installation Steps

### 1. Set Up IndiciAPI (if not already running)

```bash
# Navigate to IndiciAPI directory
cd "d:\MCP Projects\IndiciAPI"

# Build the project
dotnet build

# Run the API
dotnet run
```

The API will be available at:
- HTTP: `http://localhost:5010`
- HTTPS: `https://localhost:5011`
- Swagger: `https://localhost:5011/swagger`

### 2. Set Up Python Environment

```bash
# Navigate to the chatbot directory
cd "d:\MCP Projects\IndiciMCP-Chatbot"

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Settings

The configuration is already set up in `config.json`:

```json
{
  "groq": {
    "api_key": "",
    "model": "llama3-8b-8192"
  },
  "indici_api": {
    "base_url": "http://localhost:5010"
  },
  "web_interface": {
    "host": "localhost",
    "port": 5000
  }
}
```

**Note**: API keys are now loaded from environment variables. See `ENV_SETUP.md` for configuration details.
```

### 4. Start the Web Interface

```bash
# Make sure you're in the IndiciMCP-Chatbot directory
cd "d:\MCP Projects\IndiciMCP-Chatbot"

# Start the web application
python web/app.py
```

The web interface will be available at: `http://localhost:5000`

## Testing the System

### 1. Verify IndiciAPI is Running

Open your browser and go to:
- `http://localhost:5010/api/Reports/ProviderCapitationReport/health`

You should see a health check response.

### 2. Test the Web Interface

1. Open `http://localhost:5000` in your browser
2. You should see the Indici-themed chatbot interface
3. Check that the status indicator shows "Connected"
4. Sample queries should load in the sidebar

### 3. Test Sample Queries

Try these sample queries in the chatbot:

#### Basic Health Check
```
Check if the service is healthy
```

#### Generate Monthly Report
```
Generate a Provider Capitation Report for practice ID 128 for the current month
```

#### Generate Yearly Report
```
Show me the Provider Capitation Report for practice 128 for the entire year 2024
```

#### Custom Date Range
```
Generate report for practice 128 from January 1, 2024 to June 30, 2024
```

### 4. Expected Responses

The chatbot should:
- Respond with formatted report summaries
- Show practice ID, date ranges, and total amounts
- Display top results from the reports
- Provide helpful insights and suggestions

## Troubleshooting

### Common Issues

#### 1. IndiciAPI Not Responding
- **Problem**: Chatbot shows API connection errors
- **Solution**: 
  - Ensure IndiciAPI is running on `http://localhost:5010`
  - Check if the database connection is working
  - Verify the API endpoints are accessible

#### 2. Groq API Errors
- **Problem**: Chatbot responses are generic or show API errors
- **Solution**:
  - Verify the Groq API key is correct
  - Check internet connection
  - Monitor Groq API rate limits

#### 3. Web Interface Not Loading
- **Problem**: Browser shows connection refused
- **Solution**:
  - Ensure Python dependencies are installed
  - Check if port 5000 is available
  - Verify Flask app is running without errors

#### 4. Sample Queries Not Loading
- **Problem**: Sidebar shows "Failed to load samples"
- **Solution**:
  - Check MCP client connection
  - Verify IndiciAPI health endpoint
  - Check browser console for JavaScript errors

### Debug Mode

To enable debug mode, set `debug: true` in `config.json` under `web_interface`.

### Logs

Check the console output for detailed logs:
- **Web App**: Shows Flask and SocketIO logs
- **MCP Client**: Shows API call logs
- **Groq Client**: Shows LLM interaction logs

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │    │   Flask Web     │    │   Groq LLM      │
│   (User UI)     │◄──►│   Application   │◄──►│   (Chatbot)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   MCP Client    │◄──►│   IndiciAPI     │
                       │   (Tool Calls)  │    │   (.NET Core)   │
                       └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │   SQL Server    │
                                              │   (Database)    │
                                              └─────────────────┘
```

## Features

### Chatbot Capabilities
- ✅ Natural language processing for report requests
- ✅ Intelligent date parsing (current month, year, custom ranges)
- ✅ Practice ID extraction and defaults
- ✅ Provider and location filtering
- ✅ Health check monitoring
- ✅ Sample query suggestions

### Web Interface Features
- ✅ Professional Indici-themed design
- ✅ Real-time chat with typing indicators
- ✅ Sidebar with sample queries
- ✅ Connection status monitoring
- ✅ Responsive design for mobile/desktop
- ✅ Character count and input validation

### API Integration
- ✅ GET endpoint for flexible queries
- ✅ POST endpoint for structured requests
- ✅ Health check endpoint
- ✅ Error handling and timeout management
- ✅ Formatted response summaries

## Next Steps

1. **Database Setup**: Ensure your SQL Server has the required stored procedures
2. **Production Deployment**: Configure for production environment
3. **Security**: Add authentication and authorization
4. **Monitoring**: Set up logging and monitoring
5. **Scaling**: Consider load balancing for high traffic

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the console logs for error details
3. Verify all services are running correctly
4. Test individual components separately
