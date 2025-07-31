"""MCP Client for connecting to the Indici MCP Server."""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
import aiohttp
from datetime import datetime

logger = logging.getLogger(__name__)

class MCPClient:
    """Client for communicating with the MCP server."""
    
    def __init__(self, server_url: str = None):
        """Initialize the MCP client."""
        self.server_url = server_url or "http://localhost:8000"
        self.session = None
        self.tools = []
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def connect(self) -> bool:
        """Connect to the MCP server and initialize."""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # For this implementation, we'll simulate MCP calls by directly calling the tools
            # In a real MCP setup, this would connect to the actual MCP server
            logger.info("MCP Client initialized (direct tool integration)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {str(e)}")
            return False
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the MCP server."""
        # Simulate the tools that would be available from the MCP server
        return [
            {
                "name": "get_provider_capitation_report",
                "description": "Get Provider Capitation Report using query parameters",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "practice_id": {"type": "integer", "description": "Practice ID (required)"},
                        "date_from": {"type": "string", "description": "Start date (optional)"},
                        "date_to": {"type": "string", "description": "End date (optional)"},
                        "provider_name": {"type": "string", "description": "Provider Name(s) (optional)"},
                        "location_id": {"type": "string", "description": "Location ID(s) (optional)"},
                        "practice_location_id": {"type": "integer", "description": "Practice Location ID (optional)"},
                        "sort_by": {"type": "string", "description": "Sort by field (optional)"}
                    },
                    "required": ["practice_id"]
                }
            },
            {
                "name": "generate_provider_capitation_report",
                "description": "Generate Provider Capitation Report using JSON request body",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "practice_id": {"type": "integer", "description": "Practice ID (required)"},
                        "date_from": {"type": "string", "description": "Start date in ISO format (required)"},
                        "date_to": {"type": "string", "description": "End date in ISO format (required)"},
                        "requested_by": {"type": "integer", "description": "User ID (required)"},
                        "provider_name": {"type": "string", "description": "Provider Name(s) (optional)"},
                        "location_id": {"type": "string", "description": "Location ID(s) (optional)"},
                        "practice_location_id": {"type": "integer", "description": "Practice Location ID (optional)"},
                        "sort_by": {"type": "string", "description": "Sort by field (optional)"}
                    },
                    "required": ["practice_id", "date_from", "date_to", "requested_by"]
                }
            },
            {
                "name": "health_check",
                "description": "Check the health of the Provider Capitation Report service",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_all_income_providers",
                "description": "Get all income providers for Provider Capitation Report. Returns simple table with only Provider Full Name.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "practice_id": {"type": "integer", "description": "Practice ID (defaults to 0)"},
                        "practice_location_id": {"type": "integer", "description": "Practice Location ID (defaults to 0)"}
                    },
                    "required": []
                }
            },
            {
                "name": "get_sample_queries",
                "description": "Get sample queries for the chatbot interface",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> 'MCPToolResult':
        """Call a tool on the MCP server."""
        try:
            # Import here to avoid circular imports
            from mcp_server.tools import indici_tools
            
            logger.info(f"Calling tool: {name} with arguments: {arguments}")
            
            if name == "get_provider_capitation_report":
                # Extract print flag and remove it from arguments before API call
                print_report = arguments.pop('print_report', False)

                result = await indici_tools.get_provider_capitation_report(**arguments)

                if print_report:
                    # Format for display in chat
                    formatted_result = indici_tools.format_report_summary(result)
                    # Generate print content for popup and auto-trigger
                    print_content = indici_tools.format_print_report(result)
                    # Add automatic popup trigger to the display result
                    popup_result = indici_tools.add_auto_print_popup(formatted_result, print_content)
                    return MCPToolResult(content=[MCPTextContent(text=popup_result)])
                else:
                    # Format for display only
                    formatted_result = indici_tools.format_report_summary(result)
                    return MCPToolResult(content=[MCPTextContent(text=formatted_result)])
            
            elif name == "generate_provider_capitation_report":
                result = await indici_tools.generate_provider_capitation_report(**arguments)
                formatted_result = indici_tools.format_report_summary(result)
                return MCPToolResult(content=[MCPTextContent(text=formatted_result)])

            elif name == "get_all_income_providers":
                result = await indici_tools.get_all_income_providers(**arguments)
                formatted_result = indici_tools.format_income_providers_simple_table(result.get("data", {}))
                return MCPToolResult(content=[MCPTextContent(text=formatted_result)])

            elif name == "health_check":
                result = await indici_tools.health_check()
                
                if result.get("success", True):
                    health_text = "✅ Provider Capitation Report service is healthy!"
                    if "data" in result:
                        health_text += f"\n\nService Details:\n{result['data']}"
                else:
                    health_text = f"❌ Service health check failed: {result.get('error', 'Unknown error')}"
                
                return MCPToolResult(content=[MCPTextContent(text=health_text)])
            
            elif name == "get_sample_queries":
                sample_queries = indici_tools.get_sample_queries()
                
                queries_text = "📝 **Sample Queries You Can Try:**\n\n"
                for i, query in enumerate(sample_queries, 1):
                    queries_text += f"**{i}. {query['title']}**\n"
                    queries_text += f"   *{query['description']}*\n"
                    queries_text += f"   \"{query['query']}\"\n\n"
                
                return MCPToolResult(content=[MCPTextContent(text=queries_text)])
            
            else:
                error_text = f"❌ Unknown tool: {name}"
                return MCPToolResult(content=[MCPTextContent(text=error_text)])
                
        except Exception as e:
            logger.error(f"Error calling tool {name}: {str(e)}")
            error_text = f"❌ Error executing {name}: {str(e)}"
            return MCPToolResult(content=[MCPTextContent(text=error_text)])
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.session:
            await self.session.close()
            self.session = None
        logger.info("MCP Client disconnected")

class MCPTextContent:
    """Represents text content from MCP response."""
    
    def __init__(self, text: str):
        self.type = "text"
        self.text = text

class MCPToolResult:
    """Represents a tool result from MCP."""
    
    def __init__(self, content: List[MCPTextContent]):
        self.content = content

# Global MCP client instance
mcp_client = MCPClient()
