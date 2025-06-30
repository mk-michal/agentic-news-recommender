import faiss
import numpy as np
import pandas as pd
from typing import List, Tuple
from datetime import date
from pathlib import Path
from src.llm.embeddings import EmbeddingsGenerator
from src.db_utils.db_config import get_db_connection

class VectorStore:
    def __init__(self, target_date: date):
        self.embedding_generator = EmbeddingsGenerator()
        self.base_path = Path("data/vector_store")
        self.target_date = target_date
        self.index_path = self.base_path / f"articles_index_{target_date.isoformat()}.faiss"
        self.article_ids_path = self.base_path / f"article_ids_{target_date.isoformat()}.npy"
    
    def _fetch_articles(self) -> pd.DataFrame:
        """Fetch articles from PostgreSQL database for specific date."""
        query = """
        SELECT id, body 
        FROM articles 
        WHERE body IS NOT NULL 
        AND LENGTH(body) > 0
        AND date = %s
        """
        with get_db_connection() as conn:
            return pd.read_sql(query, conn, params=(self.target_date,))
    
    def create_index(self) -> None:
        """Create and save FAISS index from article embeddings."""
        # Create directory if it doesn't exist
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Fetch articles
        df = self._fetch_articles()
        if df.empty:
            print(f"No articles found for date {self.target_date}")
            return
            
        print(f"Fetched {len(df)} articles from database for {self.target_date}")
        
        # Generate embeddings
        embeddings = []
        for i, text in enumerate(df['body'].values):
            embedding = self.embedding_generator.get_embedding(str(text))
            embeddings.append(embedding)
            if i % 100 == 0:
                print(f"Processed {i}/{len(df)} articles")
        
        # Create and save index
        embeddings_array = np.array(embeddings).astype('float32')
        dimension = len(embeddings[0])
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings_array)
        
        # Save index and article IDs
        faiss.write_index(index, str(self.index_path))
        np.save(str(self.article_ids_path), df['id'].values)
        print(f"Vector database created successfully for {self.target_date}!")
    
    def search(self, query: str, k: int = 5) -> List[Tuple[int, float]]:
        """Search for similar articles using the vector database."""
        if not self.index_path.exists():
            raise FileNotFoundError(f"No vector database found for date {self.target_date}")
            
        # Load index and article IDs
        index = faiss.read_index(str(self.index_path))
        article_ids = np.load(str(self.article_ids_path))
        
        # Generate query embedding and search
        query_embedding = self.embedding_generator.get_embedding(query)
        query_embedding = np.array([query_embedding]).astype('float32')
        distances, indices = index.search(query_embedding, k)
        
        # Return article IDs with their distances
        return list(zip(article_ids[indices[0]], distances[0]))