"""
Enhanced LLM-based chatbot client using Groq API for indici Reports.
Provides intelligent natural language understanding and tool calling.
"""

import json
import logging
from typing import Dict, Any, List
from groq import Groq
from datetime import datetime

from mcp_server.config import config
from .prompts import ERROR_MESSAGES

logger = logging.getLogger(__name__)

class GroqChatbot:
    def __init__(self):
        """Initialize the enhanced Groq chatbot client."""
        self.client = Groq(api_key=config.groq_api_key)
        self.model = config.groq_model
        self.max_tokens = config.groq_max_tokens
        self.temperature = config.groq_temperature
        self.conversation_history = []

    async def _call_groq_api(self, prompt: str, max_tokens: int = None) -> str:
        """Make API call to Groq."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens or self.max_tokens,
                temperature=self.temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            raise

    async def _call_groq_api_with_temp(self, prompt: str, max_tokens: int = None, temperature: float = None) -> str:
        """Make API call to Groq with custom temperature."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature or self.temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            raise

    async def process_message(self, message: str, mcp_client=None) -> str:
        """Process user message with enhanced natural language understanding."""
        try:
            # Add to conversation history
            self.add_to_history("user", message)
            
            # Handle with enhanced LLM
            response = await self._handle_message_with_llm(message, mcp_client)
            
            # Add response to history
            self.add_to_history("assistant", response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return ERROR_MESSAGES['general_error']

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

        # Enhanced but concise LLM prompt for intelligent intent recognition
        conversation_prompt = f"""
ANALYZE USER MESSAGE: "{processed_message}"
ORIGINAL MESSAGE: "{message}"

CURRENT DATES:
- Month: {current_month_from} to {current_month_to}
- Year: {current_year_from} to {current_year_to}

TOOLS AVAILABLE:
{available_tools}

RESPONSE RULES:
1. Provider capitation/financial reports → TOOL_CALL: get_provider_capitation_report|{{params}}
2. Provider lists → TOOL_CALL: get_all_income_providers|{{}}
3. Health/status check → TOOL_CALL: health_check|{{}}
4. Greetings/casual → Direct friendly response

PARAMETER EXTRACTION:
- practice_id: ALWAYS include and set to 1 (0 is invalid)
- provider_name: Extract names like "Dr. Smith", "Ahmad", etc. (ONLY if mentioned)
- date_from/date_to: Extract date ranges or auto-add for monthly/yearly (ONLY if needed)
- print_report: ALWAYS set to true if ANY form of "print" is mentioned (print, printing, printable, etc.)
- Monthly requests → Add current month dates
- Yearly/annual requests → Add current year dates
- IMPORTANT: Only include parameters that are actually needed. Do NOT include null/None values.
- CRITICAL: If user says "print" anywhere, ALWAYS include "print_report": true

EXAMPLES:
"Show me capitation data for Dr. Smith" → TOOL_CALL: get_provider_capitation_report|{{"provider_name": "Dr. Smith", "practice_id": 1}}
"show me provider capitation report" → TOOL_CALL: get_provider_capitation_report|{{"practice_id": 1}}
"print provider capitation report" → TOOL_CALL: get_provider_capitation_report|{{"practice_id": 1, "print_report": true}}
"print capitation report" → TOOL_CALL: get_provider_capitation_report|{{"practice_id": 1, "print_report": true}}
"printable provider report" → TOOL_CALL: get_provider_capitation_report|{{"practice_id": 1, "print_report": true}}
"monthly financial report" → TOOL_CALL: get_provider_capitation_report|{{"practice_id": 1, "date_from": "{current_month_from}", "date_to": "{current_month_to}"}}
"print yearly summary" → TOOL_CALL: get_provider_capitation_report|{{"practice_id": 1, "date_from": "{current_year_from}", "date_to": "{current_year_to}", "print_report": true}}
"what providers do we have" → TOOL_CALL: get_all_income_providers|{{"practice_id": 1}}
"is system working" → TOOL_CALL: health_check|{{}}
"hello" → Hi! I'm your indici Reports assistant. How can I help you today?

CRITICAL: Respond with EXACT format shown above. NO explanations.

Response:
"""

        try:
            # Use lower temperature for more consistent tool calling
            response = await self._call_groq_api_with_temp(conversation_prompt, max_tokens=1500, temperature=0.3)

            # Log the raw LLM response for debugging
            logger.info(f"LLM Raw Response: {response[:200]}...")

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
        """Get available tool schemas dynamically."""
        if not mcp_client:
            return "No tools available (MCP client not connected)"
        
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
        return self.conversation_history

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []

    def _get_current_month_dates(self) -> Dict[str, str]:
        """Get current month date range."""
        from datetime import date
        
        today = date.today()
        first_day = today.replace(day=1)
        
        return {
            "date_from": first_day.strftime("%Y-%m-%d"),
            "date_to": today.strftime("%Y-%m-%d")
        }

    def _get_current_year_dates(self) -> Dict[str, str]:
        """Get current year date range."""
        from datetime import date
        
        today = date.today()
        first_day = today.replace(month=1, day=1)
        
        return {
            "date_from": first_day.strftime("%Y-%m-%d"),
            "date_to": today.strftime("%Y-%m-%d")
        }

    def _preprocess_message(self, message: str) -> str:
        """Preprocess message to handle common typos and variations."""
        # Common typo corrections for medical/financial terms
        typo_corrections = {
            'captiation': 'capitation',
            'captation': 'capitation',
            'capiation': 'capitation',
            'providor': 'provider',
            'providr': 'provider',
            'provder': 'provider',
            'repot': 'report',
            'reort': 'report',
            'finacial': 'financial',
            'financal': 'financial',
            'montly': 'monthly',
            'monthyl': 'monthly',
            'yealy': 'yearly',
            'anual': 'annual',
            'sumary': 'summary',
            'summry': 'summary',
            'healt': 'health',
            'chek': 'check',
            'staus': 'status',
            'systm': 'system'
        }

        processed = message.lower()
        for typo, correction in typo_corrections.items():
            processed = processed.replace(typo, correction)

        return processed
