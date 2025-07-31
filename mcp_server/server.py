"""MCP Server for Indici Reports API."""

import asyncio
import logging
import sys
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

# MCP imports
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
)

from .config import config
from .tools import indici_tools

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.logging_level),
    format=config.logging_format
)
logger = logging.getLogger(__name__)

class IndiciMCPServer:
    """MCP Server for Indici Reports API."""
    
    def __init__(self):
        """Initialize the MCP server."""
        self.server = Server(config.mcp_server_name)
        self.setup_tools()
    
    def setup_tools(self):
        """Set up the MCP tools."""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="get_provider_capitation_report",
                    description="Get Provider Capitation Report using query parameters. Practice ID defaults to 0. Date validation: if date_to provided, date_from is required; date_from must be <= current date; date_to must be > date_from. Null dates are sent to API if not provided.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "practice_id": {
                                "type": "integer",
                                "description": "Practice ID (defaults to 0 if not provided)"
                            },
                            "date_from": {
                                "type": "string",
                                "description": "Start date (optional, will be null if not provided). Supports formats: YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY. Must be <= current date."
                            },
                            "date_to": {
                                "type": "string",
                                "description": "End date (optional, will be null if not provided). Supports formats: YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY. Must be > date_from if both provided."
                            },
                            "provider_name": {
                                "type": "string",
                                "description": "Provider Name(s) - comma separated (optional)"
                            },
                            "location_id": {
                                "type": "string",
                                "description": "Location ID(s) - comma separated (optional)"
                            },
                            "practice_location_id": {
                                "type": "integer",
                                "description": "Practice Location ID (optional)"
                            },
                            "sort_by": {
                                "type": "string",
                                "description": "Sort by field (optional)"
                            }
                        },
                        "required": []
                    }
                ),

                Tool(
                    name="health_check",
                    description="Check the health of the Provider Capitation Report service.",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="get_all_income_providers",
                    description="Get all income providers for Provider Capitation Report. Returns a simple table with only Provider Full Name. Practice ID and Location ID default to 0.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "practice_id": {
                                "type": "integer",
                                "description": "Practice ID (defaults to 0 if not provided)"
                            },
                            "practice_location_id": {
                                "type": "integer",
                                "description": "Practice Location ID (defaults to 0 if not provided)"
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="get_sample_queries",
                    description="Get sample queries that users can try with the chatbot.",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool calls."""
            try:
                logger.info(f"Tool called: {name} with arguments: {arguments}")
                
                if name == "get_provider_capitation_report":
                    result = await indici_tools.get_provider_capitation_report(**arguments)
                    formatted_result = indici_tools.format_report_summary(result)

                    return CallToolResult(
                        content=[
                            TextContent(
                                type="text",
                                text=formatted_result
                            )
                        ]
                    )

                elif name == "get_all_income_providers":
                    result = await indici_tools.get_all_income_providers(**arguments)
                    formatted_result = indici_tools.format_income_providers_simple_table(result.get("data", {}))

                    return CallToolResult(
                        content=[
                            TextContent(
                                type="text",
                                text=formatted_result
                            )
                        ]
                    )

                elif name == "health_check":
                    result = await indici_tools.health_check()
                    
                    if result.get("success", True):
                        health_text = "✅ Provider Capitation Report service is healthy!"
                        if "data" in result:
                            health_text += f"\n\nService Details:\n{result['data']}"
                    else:
                        health_text = f"❌ Service health check failed: {result.get('error', 'Unknown error')}"
                    
                    return CallToolResult(
                        content=[
                            TextContent(
                                type="text",
                                text=health_text
                            )
                        ]
                    )
                
                elif name == "get_sample_queries":
                    sample_queries = indici_tools.get_sample_queries()
                    
                    queries_text = "📝 **Sample Queries You Can Try:**\n\n"
                    for i, query in enumerate(sample_queries, 1):
                        queries_text += f"**{i}. {query['title']}**\n"
                        queries_text += f"   *{query['description']}*\n"
                        queries_text += f"   \"{query['query']}\"\n\n"
                    
                    return CallToolResult(
                        content=[
                            TextContent(
                                type="text",
                                text=queries_text
                            )
                        ]
                    )
                
                else:
                    return CallToolResult(
                        content=[
                            TextContent(
                                type="text",
                                text=f"❌ Unknown tool: {name}"
                            )
                        ]
                    )
                    
            except Exception as e:
                logger.error(f"Error in tool call {name}: {str(e)}")
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"❌ Error executing {name}: {str(e)}"
                        )
                    ]
                )
    
    async def run(self):
        """Run the MCP server."""
        logger.info(f"Starting Indici MCP Server v{config.mcp_server_version}")
        logger.info(f"Connecting to IndiciAPI at: {config.indici_api_base_url}")
        
        # Run the server
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name=config.mcp_server_name,
                    server_version=config.mcp_server_version
                )
            )

def main():
    """Main entry point."""
    server = IndiciMCPServer()
    asyncio.run(server.run())

if __name__ == "__main__":
    main()
