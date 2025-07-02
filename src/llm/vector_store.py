import os
import json
import pickle
import numpy as np
from pathlib import Path
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple
import faiss
from openai import OpenAI
from dataclasses import dataclass

from src.db_utils.db_config import get_db_connection

@dataclass
class VectorMetadata:
    """Metadata for vector index versioning"""
    version: str
    created_at: str
    model_name: str
    model_version: str
    embedding_dimension: int
    total_articles: int
    date_range: Dict[str, str]
    sources: List[str]

class VectorStore:
    """Enhanced vector store with versioning, batching, and filtering capabilities"""
    
    def __init__(self, batch_size: int = 50, use_existing_version: bool = True):
        self.batch_size = batch_size
        self.client = OpenAI()
        self.embedding_model = "text-embedding-3-small"
        self.embedding_dimension = 1536
        
        # Setup paths with versioning
        self.base_path = Path("data/vector_store")
        
        if use_existing_version:
            self.current_version = self._get_latest_version()
        else:
            self.current_version = self._get_next_version()
            
        self.version_path = self.base_path / f"v{self.current_version}"
        self.version_path.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.index_path = self.version_path / "faiss_index.bin"
        self.metadata_path = self.version_path / "metadata.json"
        self.articles_path = self.version_path / "articles.pkl"
        self.version_info_path = self.base_path / "versions.json"
    
    def _get_latest_version(self) -> str:
        """Get the latest existing version or create first version"""
        versions_file = self.base_path / "versions.json"
        if not versions_file.exists():
            return "1.0.0"
        
        with open(versions_file, 'r') as f:
            versions_data = json.load(f)
        
        if not versions_data.get('versions') or not versions_data.get('latest'):
            return "1.0.0"
        
        return versions_data['latest']
    
    def _get_next_version(self) -> str:
        """Get next version number for the index"""
        versions_file = self.base_path / "versions.json"
        if not versions_file.exists():
            return "1.0.0"
        
        with open(versions_file, 'r') as f:
            versions_data = json.load(f)
        
        if not versions_data.get('versions'):
            return "1.0.0"
        
        latest_version = max(versions_data['versions'].keys())
        major, minor, patch = map(int, latest_version.split('.'))
        return f"{major}.{minor}.{patch + 1}"
    
    def _save_version_info(self, metadata: VectorMetadata):
        """Save version information to versions.json"""
        versions_file = self.base_path / "versions.json"
        
        if versions_file.exists():
            with open(versions_file, 'r') as f:
                versions_data = json.load(f)
        else:
            versions_data = {"versions": {}, "latest": None}
        
        versions_data["versions"][self.current_version] = {
            "created_at": metadata.created_at,
            "model_name": metadata.model_name,
            "total_articles": metadata.total_articles,
            "date_range": metadata.date_range,
            "path": str(self.version_path)
        }
        versions_data["latest"] = self.current_version
        
        with open(versions_file, 'w') as f:
            json.dump(versions_data, f, indent=2)
    
    def get_articles_for_date(self, date_filter: Optional[date] = None, 
                            sources_filter: Optional[List[str]] = None) -> List[Dict]:
        """Get articles with optional filtering by date and sources"""
        query = """
            SELECT id, title, body, url, source_uri, date
            FROM articles 
        """
        params = []
        conditions = []
        
        if date_filter:
            conditions.append("DATE(date) = %s")
            params.append(date_filter)
        
        if sources_filter:
            placeholders = ','.join(['%s'] * len(sources_filter))
            conditions.append(f"source_uri IN ({placeholders})")
            params.extend(sources_filter)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY date DESC"
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def _get_existing_article_ids(self) -> set:
        """Get article IDs that already have embeddings"""
        if not self.articles_path.exists():
            return set()
        
        with open(self.articles_path, 'rb') as f:
            existing_articles = pickle.load(f)
        
        return set(article['id'] for article in existing_articles)
    
    def create_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for a batch of texts"""
        response = self.client.embeddings.create(
            input=texts,
            model=self.embedding_model
        )
        return [embedding.embedding for embedding in response.data]

    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for better embeddings"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Limit length to avoid token limits
        max_length = 8000  # Conservative limit for text-embedding-3-small
        if len(text) > max_length:
            text = text[:max_length]
        
        return text
    
    def create_index(self, incremental: bool = False, force_new_version: bool = False, target_date: Optional[date] = None) -> bool:
        """Create or update vector index with batching"""
        print(f"Creating vector index (incremental: {incremental})")
        if target_date:
            print(f"Filtering by target date: {target_date}")
        
        # Only create new version if explicitly forced
        if force_new_version:
            print("Creating new version...")
            self.current_version = self._get_next_version()
            self.version_path = self.base_path / f"v{self.current_version}"
            self.version_path.mkdir(parents=True, exist_ok=True)
            self.index_path = self.version_path / "faiss_index.bin"
            self.metadata_path = self.version_path / "metadata.json"
            self.articles_path = self.version_path / "articles.pkl"
            incremental = False  # Treat as full rebuild for new version

        # Get articles - apply target_date filter if provided
        if target_date:
            articles = self.get_articles_for_date(date_filter=target_date)
        else:
            articles = self.get_articles_for_date()
        
        if not articles:
            print(f"No articles found for the specified criteria")
            return False
        
        # Handle incremental updates
        if incremental:
            existing_ids = self._get_existing_article_ids()
            articles = [a for a in articles if a['id'] not in existing_ids]
            if target_date:
                print(f"Found {len(articles)} new articles for {target_date} for incremental update")
            else:
                print(f"Found {len(articles)} new articles for incremental update")
        
        if not articles:
            print("No new articles to process")
            return True
        
        # Initialize or load existing index
        if incremental and self.index_path.exists():
            print(f"Loading existing index version {self.current_version}")
            index = faiss.read_index(str(self.index_path))
            with open(self.articles_path, 'rb') as f:
                existing_articles = pickle.load(f)
        else:
            print(f"Creating new index version {self.current_version}")
            # Create simple flat index
            index = faiss.IndexFlatIP(self.embedding_dimension)
            existing_articles = []
        
        # Process articles in batches
        all_embeddings = []
        processed_articles = existing_articles.copy()
        
        print(f"Processing {len(articles)} articles in batches of {self.batch_size}")
        
        for i in range(0, len(articles), self.batch_size):
            batch = articles[i:i + self.batch_size]
            print(f"Processing batch {i // self.batch_size + 1}/{(len(articles) - 1) // self.batch_size + 1}")
            
            # Prepare texts for embedding
            texts = []
            for article in batch:
                # Use 'body' field from database
                content = self._preprocess_text(article.get('body', ''))
                title = self._preprocess_text(article.get('title', ''))
                combined_text = f"{title}\n\n{content}"
                texts.append(combined_text)
            
            # Create embeddings for batch
            batch_embeddings = self.create_embeddings_batch(texts)
            all_embeddings.extend(batch_embeddings)
            processed_articles.extend(batch)
        
        # Convert embeddings to numpy array and add to index
        if all_embeddings:
            embeddings_array = np.array(all_embeddings, dtype=np.float32)
            index.add(embeddings_array)
        
        # Save index and metadata
        faiss.write_index(index, str(self.index_path))
        
        with open(self.articles_path, 'wb') as f:
            pickle.dump(processed_articles, f)
        
        # Create and save metadata
        sources = list(set(article.get('source_uri', 'unknown') for article in processed_articles))
        dates = [article.get('date') for article in processed_articles if article.get('date')]
        date_range = {
            'start': str(min(dates).date() if hasattr(min(dates), 'date') else min(dates)) if dates else 'unknown',
            'end': str(max(dates).date() if hasattr(max(dates), 'date') else max(dates)) if dates else 'unknown'
        }
        
        metadata = VectorMetadata(
            version=self.current_version,
            created_at=datetime.now().isoformat(),
            model_name=self.embedding_model,
            model_version="3-small",
            embedding_dimension=self.embedding_dimension,
            total_articles=len(processed_articles),
            date_range=date_range,
            sources=sources
        )
        
        with open(self.metadata_path, 'w') as f:
            json.dump(metadata.__dict__, f, indent=2)
        
        # Only save version info for new versions or full rebuilds
        if force_new_version or not incremental:
            self._save_version_info(metadata)
        
        update_type = "incremental update" if incremental else "full rebuild"
        print(f"✓ Successfully completed {update_type} for index version {self.current_version}")
        print(f"✓ Total articles: {len(processed_articles)}")
        print(f"✓ Date range: {date_range['start']} to {date_range['end']}")
        print(f"✓ Sources: {', '.join(sources)}")
        
        return True
    
    def search_similar(self, query: str, k: int = 5, 
                      date_range: Optional[Tuple[date, date]] = None) -> List[Dict]:
        """Search for similar articles with optional date filtering"""
        # Load index and articles
        if not self.index_path.exists():
            print("Vector index not found")
            return []
        
        index = faiss.read_index(str(self.index_path))
        with open(self.articles_path, 'rb') as f:
            articles = pickle.load(f)
        
        # Filter articles by date if specified
        if date_range:
            filtered_articles = []
            filtered_indices = []
            
            for idx, article in enumerate(articles):
                article_date = article.get('date')
                if article_date:
                    if isinstance(article_date, str):
                        article_date = datetime.fromisoformat(article_date.replace('Z', '+00:00')).date()
                    elif hasattr(article_date, 'date'):
                        article_date = article_date.date()
                    
                    if date_range[0] <= article_date <= date_range[1]:
                        filtered_articles.append(article)
                        filtered_indices.append(idx)
            
            if not filtered_articles:
                return []
            
            # Create filtered index
            filtered_embeddings = [index.reconstruct(idx) for idx in filtered_indices]
            filtered_index = faiss.IndexFlatIP(self.embedding_dimension)
            filtered_index.add(np.array(filtered_embeddings, dtype=np.float32))
            
            search_index = filtered_index
            search_articles = filtered_articles
        else:
            search_index = index
            search_articles = articles
    
        # Create query embedding and search
        query_embedding = self.create_embeddings_batch([self._preprocess_text(query)])[0]
        query_vector = np.array([query_embedding], dtype=np.float32)
    
        scores, indices = search_index.search(query_vector, min(k, len(search_articles)))
    
        # Build results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(search_articles):
                results.append({
                    **search_articles[idx],
                    'similarity_score': float(score)
                })
    
        return results
            
    
    def get_available_versions(self) -> Dict:
        """Get information about available index versions"""
        versions_file = self.base_path / "versions.json"
        if not versions_file.exists():
            return {"versions": {}, "latest": None}
        
        with open(versions_file, 'r') as f:
            return json.load(f)
    
    def cleanup_old_versions(self, keep_latest_n: int = 3):
        """Clean up old versions, keeping only the latest N"""
        versions_info = self.get_available_versions()
        versions = list(versions_info.get("versions", {}).keys())
        
        if len(versions) <= keep_latest_n:
            return
        
        # Sort versions and remove old ones
        versions.sort(key=lambda x: tuple(map(int, x.split('.'))))
        to_remove = versions[:-keep_latest_n]
        
        for version in to_remove:
            version_path = Path(versions_info["versions"][version]["path"])
            if version_path.exists():
                import shutil
                shutil.rmtree(version_path)
                print(f"Removed old version: {version}")
            
            del versions_info["versions"][version]
        
        # Update versions file
        with open(self.base_path / "versions.json", 'w') as f:
            json.dump(versions_info, f, indent=2)