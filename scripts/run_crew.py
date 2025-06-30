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

query_output = ClusterAnalysisOutput(
    cluster_1="Technology & Innovation: The user exhibits a strong interest in technology and innovation, particularly in the automotive sector, as reflected in articles such as 'Crypto's Audacious Bid to Rebuild Stock Market on the Blockchain' and 'Tesla shakes up executive ranks as sales falter'. Their focus on advancements in electric vehicles and automated systems highlights a keen interest in how technology is reshaping industries and driving market dynamics. The consistent engagement with these themes suggests that they are eager to stay informed about the latest innovations and challenges faced by technology companies.", 
    cluster_2="Finance & Market Trends: This cluster encapsulates the user's notable interest in financial markets, as evidenced by articles such as 'How To Trade SPY, Top Tech Stocks As Core Inflation Edges Up Above Expectations' and 'Cathie Wood's Ark Invest Continues To Offload Coinbase, Bets Big On SoFi Technologies'. The analysis of market behaviors and investment strategies indicates a proactive approach to understanding economic trends, reinforcing their desire to keep abreast of financial shifts and potential opportunities within the markets. This consistent interaction with financial topics demonstrates an ongoing commitment to navigating complex market landscapes.", 
    cluster_3="Public Health & Policy: The user shows awareness of significant public health issues and governance, with articles like 'Bill Gates Warns Of 'Perilous' Times After Trump Administration Pulls Funding From Gavi' highlighting their concern for healthcare funding and its implications. This interest suggests that the user is engaged with broader societal issues, emphasizing a balance between their technology and finance interests, and an understanding of how public policy affects health outcomes. Their engagement with these topics reflects a desire to be informed about the socio-political landscape and its impact on public health."
    )

class DatabaseAnalysisExecutor:
    """Main class for executing database analysis through CrewAI agents."""
    
    def __init__(self):
        self.mcp_config = MCPServerConfig()
        self.db_tools = DatabaseTools(self.mcp_config)
        self.recommender_tools = RecommenderTools(self.mcp_config)
        self.task_builder = QueryTaskBuilder()
    
    def execute_full_analysis(self, user_email: str) -> Dict[str, Any]:
        """Execute the complete analysis pipeline with one crew and two agents."""            # Get tools for both agents
        pg_tools =  self.db_tools.get_tools_with_context().tools
        rec_pg_tools, vector_tool = self.recommender_tools.get_tools_with_context()
        # Create agents
        recommender_tools = rec_pg_tools.tools + [vector_tool] 
        db_agent = DatabaseAgent.create_agent(list(pg_tools))
        recommender_agent = RecommenderAgent.create_agent(recommender_tools)
        
        # Create tasks
        analysis_task = self.task_builder.create_analysis_task(user_email, db_agent)
        
        # The recommendation task needs the cluster analysis result
        # We'll need to structure this differently since tasks are created upfront
        # Let's create a placeholder and update it during execution
        
        # Execute the crew
        result = self._run_complete_crew(db_agent, recommender_agent, analysis_task, user_email)
        return result
                

    
    def _run_complete_crew(self, db_agent, recommender_agent, analysis_task, user_email) -> Dict[str, Any]:
        """Run the complete crew with both agents and tasks."""
        
        # First, run just the analysis task to get cluster results
        print("=== Step 1: Analyzing User Reading Patterns ===")
        analysis_crew = Crew(
            agents=[db_agent],
            tasks=[analysis_task],
            verbose=True,
            memory=True
        )
        cluster_result = analysis_crew.kickoff()
        
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
        
        return {
            "user_email": user_email,
            "cluster_analysis": cluster_analysis.dict() if hasattr(cluster_analysis, 'dict') else cluster_analysis,
            "recommendations": recommendation_result.dict() if hasattr(recommendation_result, 'dict') else recommendation_result
        }

    # Keep the old method for backward compatibility
    def execute_user_analysis(self, user_email: str) -> Tuple[str, str, str] | Any:
        """Execute user analysis query and return results."""
        try:
            with self.db_tools.get_tools_with_context() as pg_tools:
                # Create agent and task
                agent = DatabaseAgent.create_agent(list(pg_tools))
                task = self.task_builder.create_analysis_task(user_email, agent)
                
                # Execute the analysis
                result = self._run_crew_analysis(agent, task)
                
                return result
                
        except Exception as e:
            print(f"Error during analysis execution: {e}")
            raise
    
    def _run_crew_analysis(self, agent, task) -> Any:
        """Run the CrewAI analysis."""
        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=True,
            memory=True
        )
        return crew.kickoff()


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