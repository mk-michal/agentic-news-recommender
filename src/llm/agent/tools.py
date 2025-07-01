from crewai import Crew, Agent, Task
from crewai_tools import MCPServerAdapter
from typing import List, Any
from datetime import date
from typing import List, Optional, Tuple
import json

from src.llm.agent.mcp_config import MCPServerConfig


class DatabaseTools:
    """Factory class for creating database tools through MCP server."""
    
    def __init__(self, mcp_config: MCPServerConfig = None):
        self.mcp_config = mcp_config or MCPServerConfig()
    
    def get_tools(self):
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


class RecommenderTools:
    """Factory class for creating recommendation tools (PostgreSQL + Vector DB)."""
    
    def __init__(self, mcp_config: MCPServerConfig = None, target_date: date = None):
        self.mcp_config = mcp_config or MCPServerConfig()
        self.target_date = target_date or date(2025, 6, 20)
        # Pass target_date to vector tool
        from .vector_tools import VectorDatabaseTool as VectorTool
        self.vector_tool = VectorTool(self.target_date)
    
    def get_tools(self) -> List[Any]:
        """Get both PostgreSQL and vector database tools."""
        try:
            with MCPServerAdapter(self.mcp_config.server_params) as pg_tools:
                all_tools = list(pg_tools) + [self.vector_tool]
                self._print_available_tools(all_tools)
                return all_tools
        except Exception as e:
            MCPServerConfig.handle_mcp_error(e)
            raise
    
    def get_tools_with_context(self):
        """Get tools with MCP server context manager."""
        try:
            return MCPServerAdapter(self.mcp_config.server_params), self.vector_tool
        except Exception as e:
            MCPServerConfig.handle_mcp_error(e)
            raise
    
    def _print_available_tools(self, tools) -> None:
        """Print available tools for debugging."""
        tool_names = [tool.name for tool in tools]
        print(f"Available tools: {tool_names}")


class VectorDatabaseTool:
    """Enhanced vector database tool with filtering capabilities"""
    
    def __init__(self, target_date: date):
        self.target_date = target_date
        from src.llm.vector_store import VectorStore
        self.vector_store = VectorStore(target_date)
    
    def search_similar_articles(self, query: str, k: int = 5, 
                              date_range: Optional[str] = None,
                              sources: Optional[str] = None) -> str:
        """
        Search for articles similar to the query with optional filtering.
        
        Args:
            query: Search query text
            k: Number of results to return
            date_range: Date range filter in format "YYYY-MM-DD,YYYY-MM-DD" 
            sources: Comma-separated list of sources to filter by
            
        Returns:
            JSON string with similar articles
        """
        from datetime import datetime
        
        # Parse date range - if not provided, use target_date as upper bound
        date_range_tuple = None
        if date_range:
            start_str, end_str = date_range.split(',')
            start_date = datetime.strptime(start_str.strip(), '%Y-%m-%d').date()
            end_date = datetime.strptime(end_str.strip(), '%Y-%m-%d').date()
            date_range_tuple = (start_date, end_date)
        else:
            # Default: search only articles before target_date
            from datetime import date as date_type
            start_date = date_type(2000, 1, 1)  # Very early date
            date_range_tuple = (start_date, self.target_date)
        
        # Parse sources
        sources_list = None
        if sources:
            sources_list = [s.strip() for s in sources.split(',')]
        
        # Search
        results = self.vector_store.search_similar(
            query=query,
            k=k,
            date_range=date_range_tuple,
            sources_filter=sources_list
        )
        
        # Format results
        formatted_results = []
        for article in results:
            formatted_results.append({
                'id': article.get('id'),
                'title': article.get('title'),
                'content': article.get('content', '')[:500] + '...',  # Truncate for agent
                'url': article.get('url'),
                'source': article.get('source'),
                'published_at': str(article.get('published_at')),
                'similarity_score': article.get('similarity_score', 0)
            })
        
        return json.dumps(formatted_results, indent=2)