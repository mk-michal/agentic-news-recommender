from crewai import Crew, Agent, Task
from crewai_tools import MCPServerAdapter
from typing import List, Any
from datetime import date
from psycopg2.extras import RealDictCursor
from crewai.tools import BaseTool
from src.llm.vector_store import VectorStore
import psycopg2


from typing import List, Optional, Tuple
import json

from src.llm.agent.mcp_config import MCPServerConfig


class DatabaseTool(BaseTool):
    name: str = "database_query"
    description: str = """
    Execute SQL queries against the PostgreSQL database.
    Use this tool to query product information, categories, prices, etc.
    Input should be a valid SQL SELECT statement.
    """
    # Declare as Pydantic fields
    database_url: str = None
    
    def __init__(self, database_url: str):
        super().__init__()
        self.database_url = database_url
    
    def _run(self, sql_query: str) -> str:
        """Execute SQL query and return results."""
        try:
            # Validate that it's a SELECT query for safety
            query_upper = sql_query.strip().upper()
            if not query_upper.startswith('SELECT'):
                return "Error: Only SELECT queries are allowed for security reasons."
            
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(sql_query)
                    results = cursor.fetchall()
                    
                    if not results:
                        return "No results found."
                    
                    # Convert to list of dictionaries for better readability
                    results_list = [dict(row) for row in results]
                    
                    # Format results nicely
                    if len(results_list) == 1:
                        return f"Query result: {results_list[0]}"
                    else:
                        return f"Query results ({len(results_list)} rows): {results_list}"
                        
        except psycopg2.Error as e:
            logger.error(f"Database error: {e}")
            return f"Database error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return f"Error executing query: {str(e)}"


class VectorDatabaseTool(BaseTool):
    """Tool for searching similar articles in vector database."""
    
    name: str = "vector_similarity_search"
    description: str = """
    Search for similar articles in the vector database using semantic similarity.
    Input should be a search query (string) and it will return article IDs with similarity scores.
    Use this tool to find articles that are semantically similar to a given topic or cluster description.
    This tool automatically filters to only show articles published BEFORE the target date.
    Returns a list of article IDs with their similarity scores.
    """
    # Declare as Pydantic fields
    target_date: date = None
    vector_store: VectorStore = None
    
    def __init__(self, target_date: date = None):
        super().__init__()
        self.target_date = target_date or date(2025, 6, 20)  # Default to available date
        self.vector_store = VectorStore(self.target_date)
    
    def _run(self, query: str) -> str:
        """Execute vector similarity search and return article IDs with scores."""
        from datetime import date as date_type
        
        # Set date range to filter articles before target_date
        start_date = date_type(2000, 1, 1)  # Very early date
        date_range = (start_date, self.target_date)
        
        # Search for similar articles with date filtering
        similar_articles = self.vector_store.search_similar(
            query=query, 
            k=2,
            date_range=date_range
        )
        
        if not similar_articles:
            return f"No similar articles found for query: {query} before {self.target_date}"
        
        # Format results as simple ID list for the agent
        article_ids = [article['id'] for article in similar_articles]
        
        return str(article_ids)
    

class RecommenderTools:
    """Factory class for creating recommendation tools (PostgreSQL + Vector DB)."""
    
    def __init__(self, database_url: str, vector_db_path: str):
        """Initialize tools with database and vector database connections."""
        self.database_url = database_url
        self.vector_db_path = vector_db_path
        
        # Initialize tools
        self.database_tool = DatabaseTool(database_url)
        self.vector_tool = VectorTool(vector_db_path)
    
    def get_tools(self) -> List[Any]:
        """Get all available tools."""
        try:
            tools = [self.database_tool, self.vector_tool]
            logger.info(f"Successfully initialized {len(tools)} tools")
            return tools
        except Exception as e:
            logger.error(f"Error initializing tools: {e}")
            raise
    
    def _print_available_tools(self, tools) -> None:
        """Print available tools for debugging."""
        tool_names = [tool.name for tool in tools]
        print(f"Available tools: {tool_names}")