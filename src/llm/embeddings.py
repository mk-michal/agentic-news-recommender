from openai import OpenAI
from typing import List
import os
import numpy as np


class EmbeddingsGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.embedding_dimension = 1536  # text-embedding-3-small dimension
    
    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for a given text using OpenAI API."""
        try:
            response = self.client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return np.zeros(self.embedding_dimension).tolist()