from crewai import Task, Agent
from src.llm.agent.models import ClusterAnalysisOutput
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.db_utils.db_operations import DatabaseOperations


class QueryTaskBuilder:
    """Builder class for creating database query tasks."""
    
    def __init__(self, schema_info: str = None):
        self.schema_info = schema_info or self._get_schema_info()
    
    def _get_schema_info(self) -> str:
        """Get database schema information."""
        db_ops = DatabaseOperations()
        return db_ops.get_database_schema()
    
    def create_analysis_task(self, user_email: str, agent: Agent) -> Task:
        """Create a user analysis task with clustering."""
        description = self._build_task_description(user_email)
        
        return Task(
            description=description,
            agent=agent,
            expected_output="A structured analysis with 3 cluster descriptions",
            output_pydantic=ClusterAnalysisOutput
        )
    
    def _build_task_description(self, user_email: str) -> str:
        """Build comprehensive task description."""
        return f"""
        Analyze reading history for user with email '{user_email}'. Include article titles, 
        read dates, user info and any patterns in reading behaviour.
        
        {self.schema_info}
        
        Please use the available PostgreSQL tools to:
        1. Write and execute appropriate SQL queries for the user using the schema above
        2. Analyze the results and provide insights
        3. Format the response in a clear, readable manner
        4. Cluster related user articles into 3 different clusters and output one paragraph for each cluster
        5. Output the results as structured data with 3 cluster descriptions
        
        Note: The user_articles table tracks which articles users have read/interacted with, 
        articles table contains article details, and users table contains user profiles.
        """