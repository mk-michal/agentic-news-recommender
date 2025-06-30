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
            # Search for similar articles
        similar_articles = self.vector_store.search(query, k=2)
        
        if not similar_articles:
            return f"No similar articles found for query: {query}"
        
        # Format results as simple ID and score pairs
        results = []
        for article_id, similarity_score in similar_articles:
            results.append({
                "article_id": article_id,
                "similarity_score": float(similarity_score)
            })
        
        return [el['article_id'] for el in results]
        