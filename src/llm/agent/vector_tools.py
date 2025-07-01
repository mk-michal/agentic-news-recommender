from crewai.tools import BaseTool 
from typing import List, Tuple
from datetime import date
import json
from src.llm.vector_store import VectorStore


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
