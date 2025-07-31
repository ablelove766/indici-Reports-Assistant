# Environment Variables Setup Guide

This project now uses environment variables to securely manage API keys and configuration settings.

## Quick Setup

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file with your actual API keys:**
   ```bash
   # Replace with your actual API keys
   GROQ_API_KEY=your_actual_groq_api_key_here
   OPENROUTER_API_KEY=your_actual_openrouter_api_key_here
   ```

3. **The `.env` file is automatically ignored by git** to keep your secrets safe.

## Environment Variables

### Required API Keys
- `GROQ_API_KEY` - Your Groq API key
- `OPENROUTER_API_KEY` - Your OpenRouter API key

### Optional Configuration
All other settings have defaults from `config.json`, but can be overridden:

- `GROQ_MODEL` - Groq model name (default: llama3-8b-8192)
- `GROQ_MAX_TOKENS` - Max tokens for Groq (default: 1024)
- `GROQ_TEMPERATURE` - Temperature for Groq (default: 0.7)
- `OPENROUTER_MODEL` - OpenRouter model (default: qwen/qwen3-32b)
- `OPENROUTER_MAX_TOKENS` - Max tokens for OpenRouter (default: 1024)
- `OPENROUTER_TEMPERATURE` - Temperature for OpenRouter (default: 0.7)
- `OPENROUTER_BASE_URL` - OpenRouter base URL
- `INDICI_API_BASE_URL` - Indici API base URL
- `INDICI_API_TIMEOUT` - API timeout in seconds
- `MCP_SERVER_HOST` - MCP server host
- `MCP_SERVER_PORT` - MCP server port
- `WEB_INTERFACE_HOST` - Web interface host
- `WEB_INTERFACE_PORT` - Web interface port
- `WEB_INTERFACE_DEBUG` - Debug mode (true/false)
- `LOG_LEVEL` - Logging level (INFO, DEBUG, etc.)
- `ENABLE_LLM_INTENT_DETECTION` - Enable LLM intent detection (true/false)
- `ENABLE_LLM_RESPONSE_ENHANCEMENT` - Enable LLM response enhancement (true/false)

## How It Works

The configuration system now:
1. **First checks environment variables** for each setting
2. **Falls back to config.json** if environment variable is not set
3. **Automatically loads** the `.env` file when the application starts

## Security Benefits

- ✅ API keys are no longer stored in code
- ✅ `.env` file is ignored by git
- ✅ Easy to use different keys for different environments
- ✅ Fallback to config.json for non-sensitive settings

## Migration

Your existing `config.json` still works! The API key fields have been cleared for security, but all other settings remain as defaults.
