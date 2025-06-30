from pydantic import BaseModel
from typing import Tuple


class ClusterAnalysisOutput(BaseModel):
    """Structured output model for cluster analysis results."""
    cluster_1: str
    cluster_2: str
    cluster_3: str
    
    def to_tuple(self) -> Tuple[str, str, str]:
        """Convert to tuple format."""
        return (self.cluster_1, self.cluster_2, self.cluster_3)