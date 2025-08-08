"""Configuration management for the MCP server."""

import json
import os
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration manager for the MCP server."""
    
    def __init__(self, config_path: str = None):
        """Initialize configuration from JSON file."""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.json"
        
        self.config_path = config_path
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
    
    @property
    def groq_api_key(self) -> str:
        """Get Groq API key from environment or config."""
        return os.getenv("GROQ_API_KEY") or self._config["groq"]["api_key"]

    @property
    def openrouter_api_key(self) -> str:
        """Get OpenRouter API key from environment or config."""
        return os.getenv("OPENROUTER_API_KEY") or self._config["openrouter"]["api_key"]

    @property
    def openrouter_model(self) -> str:
        """Get OpenRouter model from environment or config."""
        return os.getenv("OPENROUTER_MODEL") or self._config["openrouter"]["model"]

    @property
    def openrouter_max_tokens(self) -> int:
        """Get OpenRouter max tokens from environment or config."""
        env_val = os.getenv("OPENROUTER_MAX_TOKENS")
        return int(env_val) if env_val else self._config["openrouter"]["max_tokens"]

    @property
    def openrouter_temperature(self) -> float:
        """Get OpenRouter temperature from environment or config."""
        env_val = os.getenv("OPENROUTER_TEMPERATURE")
        return float(env_val) if env_val else self._config["openrouter"]["temperature"]

    @property
    def openrouter_base_url(self) -> str:
        """Get OpenRouter base URL from environment or config."""
        return os.getenv("OPENROUTER_BASE_URL") or self._config["openrouter"]["base_url"]
    
    @property
    def groq_model(self) -> str:
        """Get Groq model name from environment or config."""
        return os.getenv("GROQ_MODEL") or self._config["groq"]["model"]

    @property
    def groq_max_tokens(self) -> int:
        """Get Groq max tokens from environment or config."""
        env_val = os.getenv("GROQ_MAX_TOKENS")
        return int(env_val) if env_val else self._config["groq"]["max_tokens"]

    @property
    def groq_temperature(self) -> float:
        """Get Groq temperature from environment or config."""
        env_val = os.getenv("GROQ_TEMPERATURE")
        return float(env_val) if env_val else self._config["groq"]["temperature"]
    
    @property
    def indici_api_base_url(self) -> str:
        """Get IndiciAPI base URL from environment or config."""
        return os.getenv("INDICI_API_BASE_URL") or self._config["indici_api"]["base_url"]

    @property
    def indici_api_endpoints(self) -> Dict[str, str]:
        """Get IndiciAPI endpoints."""
        return self._config["indici_api"]["endpoints"]

    @property
    def indici_api_timeout(self) -> int:
        """Get IndiciAPI timeout from environment or config."""
        env_val = os.getenv("INDICI_API_TIMEOUT")
        return int(env_val) if env_val else self._config["indici_api"]["timeout"]
    
    @property
    def mcp_server_host(self) -> str:
        """Get MCP server host from environment or config."""
        return os.getenv("MCP_SERVER_HOST") or self._config["mcp_server"]["host"]

    @property
    def mcp_server_port(self) -> int:
        """Get MCP server port from environment or config."""
        env_val = os.getenv("MCP_SERVER_PORT")
        return int(env_val) if env_val else self._config["mcp_server"]["port"]

    @property
    def mcp_server_name(self) -> str:
        """Get MCP server name from environment or config."""
        return os.getenv("MCP_SERVER_NAME") or self._config["mcp_server"]["name"]

    @property
    def mcp_server_version(self) -> str:
        """Get MCP server version from environment or config."""
        return os.getenv("MCP_SERVER_VERSION") or self._config["mcp_server"]["version"]
    
    @property
    def web_interface_host(self) -> str:
        """Get web interface host from environment or config."""
        return os.getenv("WEB_INTERFACE_HOST") or self._config["web_interface"]["host"]

    @property
    def web_interface_port(self) -> int:
        """Get web interface port from environment or config."""
        env_val = os.getenv("WEB_INTERFACE_PORT")
        return int(env_val) if env_val else self._config["web_interface"]["port"]

    @property
    def web_interface_debug(self) -> bool:
        """Get web interface debug mode from environment or config."""
        env_val = os.getenv("WEB_INTERFACE_DEBUG")
        if env_val:
            return env_val.lower() in ('true', '1', 'yes', 'on')
        return self._config["web_interface"]["debug"]
    
    @property
    def logging_level(self) -> str:
        """Get logging level from environment or config."""
        return os.getenv("LOG_LEVEL") or self._config["logging"]["level"]

    @property
    def logging_format(self) -> str:
        """Get logging format from environment or config."""
        return os.getenv("LOG_FORMAT") or self._config["logging"]["format"]

    @property
    def enable_llm_intent_detection(self) -> bool:
        """Get LLM intent detection setting from environment or config."""
        env_val = os.getenv("ENABLE_LLM_INTENT_DETECTION")
        if env_val:
            return env_val.lower() in ('true', '1', 'yes', 'on')
        return self._config.get("llm_features", {}).get("enable_llm_intent_detection", True)

    @property
    def enable_llm_response_enhancement(self) -> bool:
        """Get LLM response enhancement setting from environment or config."""
        env_val = os.getenv("ENABLE_LLM_RESPONSE_ENHANCEMENT")
        if env_val:
            return env_val.lower() in ('true', '1', 'yes', 'on')
        return self._config.get("llm_features", {}).get("enable_llm_response_enhancement", True)

    @property
    def fallback_to_rules(self) -> bool:
        """Get fallback to rules setting from environment or config."""
        env_val = os.getenv("FALLBACK_TO_RULES")
        if env_val:
            return env_val.lower() in ('true', '1', 'yes', 'on')
        return self._config.get("llm_features", {}).get("fallback_to_rules", True)

    @property
    def intent_detection_temperature(self) -> float:
        """Get intent detection temperature from environment or config."""
        env_val = os.getenv("INTENT_DETECTION_TEMPERATURE")
        return float(env_val) if env_val else self._config.get("llm_features", {}).get("intent_detection_temperature", 0.1)

    @property
    def response_enhancement_temperature(self) -> float:
        """Get response enhancement temperature from environment or config."""
        env_val = os.getenv("RESPONSE_ENHANCEMENT_TEMPERATURE")
        return float(env_val) if env_val else self._config.get("llm_features", {}).get("response_enhancement_temperature", 0.3)

    # Azure AD / Teams SSO Configuration
    @property
    def azure_client_id(self) -> str:
        """Get Azure AD client ID from environment or config."""
        return os.getenv("AZURE_CLIENT_ID") or self._config.get("azure_ad", {}).get("client_id", "")

    @property
    def azure_client_secret(self) -> str:
        """Get Azure AD client secret from environment or config."""
        return os.getenv("AZURE_CLIENT_SECRET") or self._config.get("azure_ad", {}).get("client_secret", "")

    @property
    def azure_tenant_id(self) -> str:
        """Get Azure AD tenant ID from environment or config."""
        return os.getenv("AZURE_TENANT_ID") or self._config.get("azure_ad", {}).get("tenant_id", "")

    @property
    def azure_authority(self) -> str:
        """Get Azure AD authority URL from environment or config."""
        return os.getenv("AZURE_AUTHORITY") or self._config.get("azure_ad", {}).get("authority", f"https://login.microsoftonline.com/{self.azure_tenant_id}")

    @property
    def azure_scope(self) -> str:
        """Get Azure AD scope from environment or config."""
        return os.getenv("AZURE_SCOPE") or self._config.get("azure_ad", {}).get("scope", "https://graph.microsoft.com/.default")

    @property
    def teams_app_id(self) -> str:
        """Get Teams app ID from environment or config."""
        return os.getenv("TEAMS_APP_ID") or self._config.get("teams", {}).get("app_id", self.azure_client_id)


    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def update(self, key: str, value: Any) -> None:
        """Update configuration value."""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self) -> None:
        """Save configuration to file."""
        with open(self.config_path, 'w') as f:
            json.dump(self._config, f, indent=2)

# Global configuration instance
config = Config()
