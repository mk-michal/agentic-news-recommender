from crewai import Crew, Agent, Task
from crewai_tools import MCPServerAdapter
from typing import List, Any
from src.llm.agent.mcp_config import MCPServerConfig


class DatabaseTools:
    """Factory class for creating database tools through MCP server."""
    
    def __init__(self, mcp_config: MCPServerConfig = None):
        self.mcp_config = mcp_config or MCPServerConfig()
    
    def get_tools(self) -> List[Any]:
        """Get database tools from MCP server."""
        try:
            with MCPServerAdapter(self.mcp_config.server_params) as pg_tools:
                self._print_available_tools(pg_tools)
                return list(pg_tools)
        except Exception as e:
            MCPServerConfig.handle_mcp_error(e)
            raise
    
    def get_tools_with_context(self):
        """Get tools with MCP server context manager."""
        try:
            return MCPServerAdapter(self.mcp_config.server_params)
        except Exception as e:
            MCPServerConfig.handle_mcp_error(e)
            raise
    
    def _print_available_tools(self, tools) -> None:
        """Print available PostgreSQL tools for debugging."""
        tool_names = [tool.name for tool in tools]
        print(f"Available PostgreSQL tools: {tool_names}")