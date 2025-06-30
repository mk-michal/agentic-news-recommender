#!/usr/bin/env python3
"""
Database Analysis Execution Script

This script orchestrates the execution of database analysis using CrewAI agents.
"""

import json
import sys
from pathlib import Path
from typing import Tuple, Any, Dict

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from crewai import Crew
from src.llm.agent.models import ClusterAnalysisOutput, RecommendationOutput
from src.llm.agent.agents import DatabaseAgent, RecommenderAgent
from src.llm.agent.tasks import QueryTaskBuilder
from src.llm.agent.tools import DatabaseTools, RecommenderTools
from src.llm.agent.mcp_config import MCPServerConfig


class DatabaseAnalysisExecutor:
    """Main class for executing database analysis through CrewAI agents."""
    
    def __init__(self):
        self.mcp_config = MCPServerConfig()
        self.db_tools = DatabaseTools(self.mcp_config)
        self.recommender_tools = RecommenderTools(self.mcp_config)
        self.task_builder = QueryTaskBuilder()
    
    def execute_full_analysis(self, user_email: str) -> Dict[str, Any]:
        """Execute the complete analysis pipeline with one crew and two agents."""
        
        # Get tools for both agents
        pg_tools = self.db_tools.get_tools_with_context().tools
        rec_pg_tools, vector_tool = self.recommender_tools.get_tools_with_context()
        recommender_tools = rec_pg_tools.tools + [vector_tool] 
        
        # Create agents
        db_agent = DatabaseAgent.create_agent(list(pg_tools))
        recommender_agent = RecommenderAgent.create_agent(recommender_tools)
        
        # Create tasks
        analysis_task = self.task_builder.create_analysis_task(user_email, db_agent)
        
        # Create recommendation task that will receive input from analysis task
        recommendation_task = self.task_builder.create_recommendation_task_with_context(recommender_agent)
        
        # Set up task dependencies - recommendation task depends on analysis task
        recommendation_task.context = [analysis_task]
        
        # Execute the crew with both agents and tasks
        result = self._run_single_crew(db_agent, recommender_agent, analysis_task, recommendation_task, user_email)
        return result
    
    def _run_single_crew(self, db_agent, recommender_agent, analysis_task, recommendation_task, user_email) -> Dict[str, Any]:
        """Run a single crew with both agents and tasks."""
        
        print("=== Starting Complete Analysis Pipeline ===")
        
        # Create single crew with both agents and tasks
        crew = Crew(
            agents=[db_agent, recommender_agent],
            tasks=[analysis_task, recommendation_task],
            verbose=True,
            memory=True
        )
        cluster_result = crew.kickoff()
        
        # Process cluster analysis result
        if isinstance(cluster_result, ClusterAnalysisOutput):
            cluster_analysis = cluster_result
        else:
            cluster_analysis = ClusterAnalysisOutput.parse_obj(json.loads(cluster_result.raw))
        
        print("✓ Generated 3 user interest clusters")
        
        # Now create and run the recommendation task
        print("\n=== Step 2: Finding Article Recommendations ===")
        recommendation_task = self.task_builder.create_recommendation_task(cluster_analysis, recommender_agent)
        
        recommendation_crew = Crew(
            agents=[recommender_agent],
            tasks=[recommendation_task],
            verbose=True,
            memory=True
        )
        recommendation_result = recommendation_crew.kickoff()
        
        print("✓ Generated article recommendations")
                # Process cluster analysis result
        if isinstance(cluster_result, RecommendationOutput):
            recommendation_result = cluster_result
        else:
            recommendation_result = RecommendationOutput.parse_obj(json.loads(recommendation_result.raw))
        
        return {
            "user_email": user_email,
            "cluster_analysis": cluster_analysis,
            "recommendations": recommendation_result.dict() if hasattr(recommendation_result, 'dict') else recommendation_result
        }


def main():
    """Main execution function."""
    user_email = "michalkucirka@gmail.com"
    
    executor = DatabaseAnalysisExecutor()
    
    # Execute full pipeline
    full_result = executor.execute_full_analysis(user_email)
    
    print("\n" + "="*60)
    print("=== COMPLETE ANALYSIS AND RECOMMENDATIONS ===")
    print("="*60)
    
    # Display cluster analysis
    print("\n--- USER READING CLUSTERS ---")
    cluster_analysis = full_result["cluster_analysis"]
    
    if isinstance(cluster_analysis, dict):
        print(f"Cluster 1: {cluster_analysis.get('cluster_1', 'N/A')}")
        print(f"\nCluster 2: {cluster_analysis.get('cluster_2', 'N/A')}")
        print(f"\nCluster 3: {cluster_analysis.get('cluster_3', 'N/A')}")
    else:
        print(f"Cluster Analysis: {cluster_analysis}")
    
    # Display final recommendations
    print("\n--- FINAL RECOMMENDATIONS ---")
    recommendations = full_result["recommendations"]
    
    if isinstance(recommendations, dict):
        for i, cluster_key in enumerate(["cluster_1_recommendations", "cluster_2_recommendations", "cluster_3_recommendations"], 1):
            if cluster_key in recommendations:
                cluster_recs = recommendations[cluster_key]
                print(f"\n=== Cluster {i} ===")
                print(f"Theme: {cluster_recs.get('cluster_description', 'N/A')}")
                
                articles = cluster_recs.get('articles', [])
                for j, article in enumerate(articles, 1):
                    print(f"\nArticle {j}:")
                    print(f"  ID: {article.get('article_id', 'N/A')}")
                    print(f"  Title: {article.get('title', 'N/A')}")
                    print(f"  Source: {article.get('source', 'N/A')}")
                    print(f"  URL: {article.get('url', 'N/A')}")
                    body = article.get('body', '')
                    if body:
                        print(f"  Body Preview: {body[:200]}...")
    else:
        print(f"Recommendations: {recommendations}")


if __name__ == "__main__":
    main()