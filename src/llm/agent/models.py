from pydantic import BaseModel
from typing import Tuple, List, Dict, Any


class ClusterAnalysisOutput(BaseModel):
    """Structured output model for cluster analysis results."""
    cluster_1: str
    cluster_2: str
    cluster_3: str

class ArticleDetails(BaseModel):
    """Model for detailed article information."""
    article_id: int
    title: str
    url: str
    source: str
    body: str


class ClusterRecommendations(BaseModel):
    """Model for recommendations for a single cluster."""
    cluster_description: str
    articles: List[ArticleDetails]


class RecommendationOutput(BaseModel):
    """Structured output model for final article recommendations."""
    cluster_1_recommendations: ClusterRecommendations
    cluster_2_recommendations: ClusterRecommendations
    cluster_3_recommendations: ClusterRecommendations
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "cluster_1_recommendations": self.cluster_1_recommendations.dict(),
            "cluster_2_recommendations": self.cluster_2_recommendations.dict(),
            "cluster_3_recommendations": self.cluster_3_recommendations.dict()
        }

class PersonalizedReportOutput(BaseModel):
    """Structured output model for personalized markdown report."""
    markdown_report: str
    report_title: str
    user_email: str
    
    def save_to_file(self, file_path: str) -> None:
        """Save the markdown report to a file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.markdown_report)