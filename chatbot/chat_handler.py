"""
Professional Chat Handler with Integrated Chatbot Logic.
Combines web integration and core chatbot functionality in one file.
Uses either Intent approach or LLM approach based on config.json settings.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from .intent_classifier import ProfessionalIntentClassifier, IntentType
from .groq_client import GroqChatbot
from .openrouter_client import OpenRouterChatbot
from .chatbot_config import SimpleConfigManager
from .prompts import ERROR_MESSAGES
from .mcp_client import mcp_client

logger = logging.getLogger(__name__)

class MCPChatHandler:
    """
    Professional chat handler with integrated chatbot logic.
    Uses either Intent approach or LLM approach based on configuration settings.
    """

    def __init__(self, mcp_client_instance=None):
        """Initialize the professional chat handler with integrated chatbot."""
        # Configuration and core components
        self.config_manager = SimpleConfigManager()
        self.intent_classifier = ProfessionalIntentClassifier()
        self.groq_chatbot = GroqChatbot()
        self.qwen_chatbot = OpenRouterChatbot()

        # MCP client and session management
        self.mcp_client = mcp_client_instance or mcp_client
        self.session_data = {}

        # Conversation history and metrics
        self.conversation_history = []
        self.performance_metrics = {
            "total_requests": 0,
            "intent_processed": 0,
            "groq_processed": 0,
            "qwen_processed": 0,
            "errors": 0,
            "average_response_time": 0.0
        }

    def set_mcp_client(self, mcp_client_instance):
        """Set the MCP client for tool calls."""
        self.mcp_client = mcp_client_instance
    
    async def handle_message(self, message: str, session_id: str = "default") -> Dict[str, Any]:
        """
        Handle incoming chat message using professional hybrid system.

        Args:
            message: User message
            session_id: Session identifier for conversation tracking

        Returns:
            Dict containing response and metadata
        """
        try:
            # Initialize session if needed
            if session_id not in self.session_data:
                self.session_data[session_id] = {
                    "created_at": datetime.now(),
                    "message_count": 0,
                    "last_activity": datetime.now()
                }

            session = self.session_data[session_id]
            session["message_count"] += 1
            session["last_activity"] = datetime.now()

            # Handle clear command
            if message.lower().strip() == "clear":
                self.clear_history()
                return {
                    "response": "✅ Chat history cleared successfully!",
                    "type": "system",
                    "timestamp": datetime.now().isoformat(),
                    "session_id": session_id,
                    "message_count": session["message_count"],
                    "success": True
                }

            # Process message using integrated chatbot logic
            response = await self.process_message_internal(message)
            response_type = "chat"

            # Add to conversation history
            self.add_to_history("user", message)
            self.add_to_history("assistant", response)

            return {
                "response": response,
                "type": response_type,
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "message_count": session["message_count"],
                "success": True
            }

        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            return {
                "response": ERROR_MESSAGES["general_error"],
                "type": "error",
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "error": str(e),
                "success": False
            }



    async def get_sample_queries(self) -> Dict[str, Any]:
        """Get sample queries for the UI."""
        try:
            if self.mcp_client:
                result = await self.mcp_client.call_tool("get_sample_queries", {})
                
                if hasattr(result, 'content') and result.content:
                    sample_text = result.content[0].text
                    return {
                        "samples": sample_text,
                        "success": True
                    }
            
            # Fallback samples if MCP is not available
            fallback_samples = [
                {
                    "title": "Generate Monthly Report",
                    "query": "Generate a Provider Capitation Report for practice ID 128 for the current month",
                    "description": "Get current month's capitation report"
                },
                {
                    "title": "Yearly Summary", 
                    "query": "Show me the Provider Capitation Report for practice 128 for the entire year 2024",
                    "description": "Annual capitation summary"
                },
                {
                    "title": "Health Check",
                    "query": "Check if the Provider Capitation Report service is healthy",
                    "description": "Verify service status"
                }
            ]
            
            return {
                "samples": fallback_samples,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error getting sample queries: {str(e)}")
            return {
                "samples": [],
                "success": False,
                "error": str(e)
            }
    
    def get_session_info(self, session_id: str = "default") -> Dict[str, Any]:
        """Get session information."""
        if session_id in self.session_data:
            session = self.session_data[session_id]
            return {
                "session_id": session_id,
                "created_at": session["created_at"].isoformat(),
                "message_count": session["message_count"],
                "last_activity": session["last_activity"].isoformat(),
                "conversation_history": self.chatbot.get_conversation_history()
            }
        else:
            return {
                "session_id": session_id,
                "exists": False
            }
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old sessions."""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        sessions_to_remove = []
        for session_id, session_data in self.session_data.items():
            if session_data["last_activity"] < cutoff_time:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.session_data[session_id]
            logger.info(f"Cleaned up old session: {session_id}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on chat system."""
        try:
            # Test Groq connection
            groq_healthy = False
            if self.config_manager.use_groq():
                try:
                    test_response = await self.groq_chatbot._call_groq_api("Hello")
                    groq_healthy = bool(test_response and not test_response.startswith("❌"))
                except:
                    groq_healthy = False

            # Test QWEN connection
            qwen_healthy = False
            if self.config_manager.use_qwen():
                try:
                    test_response = await self.qwen_chatbot._call_openrouter_api("Hello")
                    qwen_healthy = bool(test_response and not test_response.startswith("❌"))
                except:
                    qwen_healthy = False

            # Test MCP connection if available
            mcp_healthy = False
            if self.mcp_client:
                try:
                    result = await self.mcp_client.call_tool("health_check", {})
                    mcp_healthy = bool(result)
                except:
                    mcp_healthy = False

            return {
                "groq_healthy": groq_healthy,
                "qwen_healthy": qwen_healthy,
                "mcp_healthy": mcp_healthy,
                "active_sessions": len(self.session_data),
                "timestamp": datetime.now().isoformat(),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "chatbot_healthy": False,
                "mcp_healthy": False,
                "error": str(e),
                "success": False
            }

    # ============================================================================
    # INTEGRATED CHATBOT CORE METHODS
    # ============================================================================

    async def process_message_internal(self, message: str) -> str:
        """
        Process user message using configured approach.

        Args:
            message: User input message

        Returns:
            Response string for the user
        """
        try:
            # Update metrics
            self.performance_metrics["total_requests"] += 1

            # Determine processing approach from config
            use_intent = self.config_manager.use_intent_approach()
            use_groq = self.config_manager.use_groq()
            use_qwen = self.config_manager.use_qwen()
            fallback_order = self.config_manager.get_fallback_order()

            logger.info(f"Processing message: '{message[:50]}...' (Intent: {use_intent}, Groq: {use_groq}, QWEN: {use_qwen})")

            # Process based on configuration with fallback support
            response = None
            last_error = None

            for model_type in fallback_order:
                try:
                    if model_type == "intent" and use_intent:
                        response = await self._process_with_intent(message)
                        self.performance_metrics["intent_processed"] += 1
                        break
                    elif model_type == "groq" and use_groq:
                        response = await self._process_with_groq(message)
                        self.performance_metrics["groq_processed"] += 1
                        break
                    elif model_type == "qwen" and use_qwen:
                        response = await self._process_with_qwen(message)
                        self.performance_metrics["qwen_processed"] += 1
                        break
                except Exception as e:
                    logger.warning(f"Error with {model_type} model: {e}")
                    last_error = e
                    continue

            if response is None:
                if not any([use_intent, use_groq, use_qwen]):
                    response = "❌ No processing approach is enabled in configuration. Please check config files."
                else:
                    response = f"❌ All enabled models failed. Last error: {str(last_error) if last_error else 'Unknown error'}"

            return response

        except Exception as e:
            self.performance_metrics["errors"] += 1
            logger.error(f"Error processing message: {e}")
            return ERROR_MESSAGES.get('general_error', 'I encountered an error. Please try again.')

    async def _process_with_intent(self, message: str) -> str:
        """Process using intent classification approach."""
        try:
            # Classify intent
            intent_result = self.intent_classifier.classify_intent(message)

            # Convert to parameters for tool calling
            parameters = intent_result.parameters

            # Determine which tool to call based on intent
            if intent_result.intent == IntentType.INCOME_PROVIDERS_LIST:
                return await self._call_income_providers_tool(parameters)
            elif intent_result.intent == IntentType.HEALTH_CHECK:
                return await self._call_health_check_tool()
            elif intent_result.intent == IntentType.GREETING:
                return "👋 Hello! I'm your indici Reports Assistant. How can I help you with Provider Capitation reports today?"
            elif intent_result.intent == IntentType.HELP:
                return self._get_help_message()
            else:
                # Default to provider capitation report
                return await self._call_capitation_report_tool(parameters)

        except Exception as e:
            logger.error(f"Intent processing error: {e}")
            return f"❌ Error processing your request: {str(e)}"

    async def _process_with_groq(self, message: str) -> str:
        """Process using Groq LLM approach."""
        try:
            return await self.groq_chatbot._handle_message_with_llm(message, self.mcp_client)
        except Exception as e:
            logger.error(f"Groq processing error: {e}")
            return "I'm having trouble understanding your request with Groq. Could you please rephrase it?"

    async def _process_with_qwen(self, message: str) -> str:
        """Process using QWEN LLM approach."""
        try:
            return await self.qwen_chatbot._handle_message_with_llm(message, self.mcp_client)
        except Exception as e:
            logger.error(f"QWEN processing error: {e}")
            return "I'm having trouble understanding your request with QWEN. Could you please rephrase it?"

    # Legacy method for backward compatibility
    async def _process_with_llm(self, message: str) -> str:
        """Process using LLM approach (legacy - defaults to Groq)."""
        return await self._process_with_groq(message)

    async def _call_capitation_report_tool(self, parameters: Dict[str, Any]) -> str:
        """Call provider capitation report tool."""
        try:
            clean_params = {k: v for k, v in parameters.items() if v is not None}
            logger.info(f"Calling provider capitation report with parameters: {clean_params}")
            result = await self.mcp_client.call_tool("get_provider_capitation_report", clean_params)

            response_text = ""
            if hasattr(result, 'content') and result.content:
                response_text = result.content[0].text
            else:
                response_text = str(result)

            # Check if print was requested
            if parameters.get("print_report", False):
                # Add print instruction to the response
                response_text += "\n\n🖨️ **Print Instructions:** The report above has been formatted for printing. You can print this page or copy the data to your preferred document format."
                logger.info("Print functionality triggered for capitation report")

            return response_text
        except Exception as e:
            logger.error(f"Error calling capitation report tool: {e}")
            return f"❌ Error generating provider capitation report: {str(e)}"

    async def _call_income_providers_tool(self, parameters: Dict[str, Any]) -> str:
        """Call income providers tool."""
        try:
            clean_params = {k: v for k, v in parameters.items() if v is not None}
            logger.info(f"Calling income providers with parameters: {clean_params}")
            result = await self.mcp_client.call_tool("get_all_income_providers", clean_params)

            if hasattr(result, 'content') and result.content:
                return result.content[0].text
            else:
                return str(result)
        except Exception as e:
            logger.error(f"Error calling income providers tool: {e}")
            return f"❌ Error retrieving provider list: {str(e)}"

    async def _call_health_check_tool(self) -> str:
        """Call health check tool."""
        try:
            result = await self.mcp_client.call_tool("health_check", {})

            if hasattr(result, 'content') and result.content:
                return result.content[0].text
            else:
                return str(result)
        except Exception as e:
            logger.error(f"Error calling health check tool: {e}")
            return f"❌ Health check failed: {str(e)}"

    def _get_help_message(self) -> str:
        """Get help message."""
        return """🔧 **I can help you with Provider Capitation Reports:**

📊 **Provider Capitation Reports**
- "Show me provider capitation report"
- "Provider report for Dr. Smith"
- "Print monthly capitation summary"
- "Yearly financial report"

👥 **Provider Lists**
- "What providers do we have?"
- "Show me all income providers"

🔍 **System Health**
- "Health check"
- "Is the system working?"

💬 **Natural Language**
- I understand typos and variations
- Just ask naturally: "I need financial data for Ahmad"

What would you like to explore?"""

    def add_to_history(self, role: str, content: str):
        """Add message to conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

        # Keep only last 50 messages for performance
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history."""
        return self.conversation_history

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        total = self.performance_metrics["total_requests"]
        if total == 0:
            return self.performance_metrics

        return {
            **self.performance_metrics,
            "intent_processing_rate": (self.performance_metrics["intent_processed"] / total) * 100,
            "llm_processing_rate": (self.performance_metrics["llm_processed"] / total) * 100,
            "error_rate": (self.performance_metrics["errors"] / total) * 100,
            "success_rate": ((total - self.performance_metrics["errors"]) / total) * 100
        }

    def _update_response_time(self, response_time: float):
        """Update average response time."""
        current_avg = self.performance_metrics["average_response_time"]
        total_requests = self.performance_metrics["total_requests"]

        # Calculate running average
        new_avg = ((current_avg * (total_requests - 1)) + response_time) / total_requests
        self.performance_metrics["average_response_time"] = new_avg

    def reset_metrics(self) -> Dict[str, Any]:
        """Reset performance metrics."""
        self.performance_metrics = {
            "total_requests": 0,
            "intent_processed": 0,
            "llm_processed": 0,
            "errors": 0,
            "average_response_time": 0.0
        }
        return {"success": True, "message": "Metrics reset successfully"}

    def get_sidebar_configuration(self) -> Dict[str, Any]:
        """Get sidebar configuration for frontend."""
        return self.config_manager.get_sidebar_configuration()

    def get_system_status(self) -> Dict[str, Any]:
        """Get system status."""
        config_summary = self.config_manager.get_config_summary()

        return {
            "status": "operational",
            "configuration": config_summary,
            "performance": self.get_performance_metrics(),
            "components": {
                "intent_classifier": "active" if config_summary["use_intent_approach"] else "disabled",
                "groq_processor": "active" if config_summary["use_groq"] else "disabled",
                "qwen_processor": "active" if config_summary["use_qwen"] else "disabled",
                "conversation_history": f"{len(self.conversation_history)} messages"
            },
            "last_updated": datetime.now().isoformat()
        }

# Global chat handler instance
chat_handler = MCPChatHandler()
