"""
OpenRouter Client for QWEN Model Integration.
Provides QWEN model access through OpenRouter API with tool calling capabilities.
"""

import json
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from mcp_server.config import config

logger = logging.getLogger(__name__)

class OpenRouterChatbot:
    """OpenRouter chatbot client for QWEN model with enhanced tool calling."""
    
    def __init__(self):
        """Initialize the OpenRouter chatbot client."""
        self.api_key = config.openrouter_api_key
        self.model = config.openrouter_model
        self.max_tokens = config.openrouter_max_tokens
        self.temperature = config.openrouter_temperature
        self.base_url = config.openrouter_base_url
        self.conversation_history = []
        
        # Headers for OpenRouter API
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://indici-mcp-chatbot.local",
            "X-Title": "Indici MCP Chatbot"
        }

    async def _call_openrouter_api(self, prompt: str, max_tokens: int = None, temperature: float = None) -> str:
        """Make API call to OpenRouter."""
        try:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature or self.temperature
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["choices"][0]["message"]["content"]
                    else:
                        error_text = await response.text()
                        logger.error(f"OpenRouter API error {response.status}: {error_text}")
                        raise Exception(f"OpenRouter API error: {response.status}")
                        
        except Exception as e:
            logger.error(f"OpenRouter API call failed: {e}")
            raise

    async def _call_openrouter_api_with_temp(self, prompt: str, max_tokens: int = None, temperature: float = None) -> str:
        """Make API call to OpenRouter with custom temperature."""
        return await self._call_openrouter_api(prompt, max_tokens, temperature)

    def _preprocess_message(self, message: str) -> str:
        """Preprocess message for common typos and variations."""
        # Common typos and variations
        replacements = {
            "capiation": "capitation",
            "capitaion": "capitation", 
            "providor": "provider",
            "providr": "provider",
            "reprot": "report",
            "reort": "report",
            "mont": "month",
            "yer": "year",
            "shw": "show",
            "lst": "list"
        }
        
        processed = message.lower()
        for typo, correct in replacements.items():
            processed = processed.replace(typo, correct)
        
        return processed

    def _get_current_month_dates(self) -> Dict[str, str]:
        """Get current month date range."""
        now = datetime.now()
        first_day = now.replace(day=1)
        if now.month == 12:
            last_day = now.replace(year=now.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            last_day = now.replace(month=now.month + 1, day=1) - timedelta(days=1)
        
        return {
            "date_from": first_day.strftime("%Y-%m-%d"),
            "date_to": last_day.strftime("%Y-%m-%d")
        }

    def _get_current_year_dates(self) -> Dict[str, str]:
        """Get current year date range."""
        now = datetime.now()
        return {
            "date_from": f"{now.year}-01-01",
            "date_to": f"{now.year}-12-31"
        }

    async def _handle_message_with_llm(self, message: str, mcp_client=None) -> str:
        """Enhanced LLM handling with intelligent intent recognition and tool calling."""
        
        # Preprocess message for common typos and variations
        processed_message = self._preprocess_message(message)
        
        # Get available tools dynamically
        available_tools = await self._get_tool_schemas(mcp_client)
        
        # Get current month and year dates for reports
        current_month_dates = self._get_current_month_dates()
        current_year_dates = self._get_current_year_dates()
        current_month_from = current_month_dates["date_from"]
        current_month_to = current_month_dates["date_to"]
        current_year_from = current_year_dates["date_from"]
        current_year_to = current_year_dates["date_to"]

        conversation_prompt = f"""You are an intelligent assistant for the Indici Reports system. Your primary role is to help users generate Provider Capitation Reports and manage income provider data.

IMPORTANT INSTRUCTIONS:
1. If the user wants to call a tool, respond with: TOOL_CALL: tool_name|{{parameters}}
2. Use the exact tool names and parameter formats shown below
3. For conversational responses, respond naturally without the TOOL_CALL prefix
4. Always use practice_id: 1 as the default unless specified otherwise (0 is invalid)
5. Current month dates: {current_month_from} to {current_month_to}
6. Current year dates: {current_year_from} to {current_year_to}

CRITICAL DATE RULES:
- If user doesn't specify dates, DO NOT include date_from or date_to parameters (let API use defaults)
- Only include dates if user explicitly mentions time periods like "current month", "this year", or specific dates
- Never use future dates - all dates must be current or past

CRITICAL PRINT RULES:
- If user mentions ANY form of "print" (print, printing, printable, etc.), ALWAYS include "print_report": true
- Look for print keywords in the entire message, not just at the beginning

PROVIDER NAME EXTRACTION:
- If user mentions a specific provider name, include it as "provider_name" parameter
- Extract exact provider names like "Av VOC PROVIDER", "Dr. Smith", etc.

AVAILABLE TOOLS:
{available_tools}

EXAMPLES:
- "Generate current month report" → TOOL_CALL: get_provider_capitation_report|{{"practice_id": 1, "date_from": "{current_month_from}", "date_to": "{current_month_to}"}}
- "Show yearly report" → TOOL_CALL: get_provider_capitation_report|{{"practice_id": 1, "date_from": "{current_year_from}", "date_to": "{current_year_to}"}}
- "Show provider capitation report" → TOOL_CALL: get_provider_capitation_report|{{"practice_id": 1}}
- "Print provider capitation report for Dr. Smith" → TOOL_CALL: get_provider_capitation_report|{{"practice_id": 1, "provider_name": "Dr. Smith", "print_report": true}}
- "Only print provider capitation report for this provider Av VOC PROVIDER" → TOOL_CALL: get_provider_capitation_report|{{"practice_id": 1, "provider_name": "Av VOC PROVIDER", "print_report": true}}
- "Show report for Av VOC PROVIDER" → TOOL_CALL: get_provider_capitation_report|{{"practice_id": 1, "provider_name": "Av VOC PROVIDER"}}
- "Print report" → TOOL_CALL: get_provider_capitation_report|{{"practice_id": 1, "print_report": true}}
- "List income providers" → TOOL_CALL: get_all_income_providers|{{"practice_id": 1, "practice_location_id": 0}}

User Message: {processed_message}

Response:
"""

        try:
            # Use lower temperature for more consistent tool calling
            response = await self._call_openrouter_api_with_temp(conversation_prompt, max_tokens=1500, temperature=0.3)

            # Log the raw LLM response for debugging
            logger.info(f"QWEN Raw Response: {response[:200]}...")

            # Check if LLM wants to call a tool
            if response.startswith("TOOL_CALL:"):
                logger.info(f"Tool call detected: {response}")
                return await self._handle_llm_tool_call(response, mcp_client)
            else:
                # Direct conversational response
                logger.info(f"Conversational response: {response[:100]}...")
                return response

        except Exception as e:
            logger.error(f"Enhanced LLM message handling failed: {e}")
            return "I'm here to help you with indici reports. What would you like to know or do today?"

    async def _get_tool_schemas(self, mcp_client) -> str:
        """Get formatted tool schemas for the LLM prompt."""
        
        try:
            tools = await mcp_client.list_tools()
            tool_descriptions = []
            
            for tool in tools:
                name = tool.get('name', 'Unknown')
                description = tool.get('description', 'No description')
                schema = tool.get('inputSchema', {})
                properties = schema.get('properties', {})
                
                tool_desc = f"**{name}**: {description}\n"
                if properties:
                    tool_desc += "   Parameters:\n"
                    for param, details in properties.items():
                        param_type = details.get('type', 'unknown')
                        param_desc = details.get('description', 'No description')
                        tool_desc += f"   - {param} ({param_type}): {param_desc}\n"
                
                tool_descriptions.append(tool_desc)
            
            return "\n".join(tool_descriptions)
            
        except Exception as e:
            logger.error(f"Error getting tool schemas: {e}")
            return "Error retrieving tool information"

    async def _handle_llm_tool_call(self, llm_response: str, mcp_client) -> str:
        """Parse LLM tool call response and execute the tool with enhanced error handling."""
        try:
            # Parse: "TOOL_CALL: tool_name|{parameters}"
            if "|" not in llm_response:
                return "I understand you want to use a tool, but I need more specific information."
            
            tool_part = llm_response.replace("TOOL_CALL:", "").strip()
            tool_name, params_str = tool_part.split("|", 1)
            tool_name = tool_name.strip()
            
            # Parse parameters with better error handling
            if params_str.strip() == "{}":
                parameters = {}
            else:
                try:
                    parameters = json.loads(params_str)
                    # Remove None values to avoid API errors
                    parameters = {k: v for k, v in parameters.items() if v is not None}
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON decode error for parameters: {params_str}, error: {e}")
                    parameters = {}
            
            # Call the tool
            if mcp_client:
                result = await mcp_client.call_tool(tool_name, parameters)
                if hasattr(result, 'content') and result.content:
                    return result.content[0].text
                else:
                    return str(result)
            else:
                return "❌ Tool functionality is not available right now."
                
        except Exception as e:
            logger.error(f"Enhanced tool call handling failed: {e}")
            return f"❌ Error executing tool: {str(e)}"

    def add_to_history(self, role: str, content: str):
        """Add message to conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 20 messages
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history."""
        return self.conversation_history.copy()

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history.clear()
