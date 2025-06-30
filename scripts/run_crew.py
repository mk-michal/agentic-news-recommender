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
from src.llm.agent.agents import DatabaseAgent, RecommenderAgent, ReportWriterAgent
from src.llm.agent.models import ClusterAnalysisOutput, RecommendationOutput, PersonalizedReportOutput
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
        """Execute the complete analysis pipeline with three agents."""
        
        # Get tools for both agents
        pg_tools = self.db_tools.get_tools_with_context().tools
        rec_pg_tools, vector_tool = self.recommender_tools.get_tools_with_context()
        recommender_tools = rec_pg_tools.tools + [vector_tool] 
        
        # Create agents
        db_agent = DatabaseAgent.create_agent(list(pg_tools))
        recommender_agent = RecommenderAgent.create_agent(recommender_tools)
        report_agent = ReportWriterAgent.create_agent()
        
        # Create tasks
        analysis_task = self.task_builder.create_analysis_task(user_email, db_agent)
        recommendation_task = self.task_builder.create_recommendation_task_with_context(recommender_agent)
        report_task = self.task_builder.create_report_generation_task(user_email, report_agent)
        
        # Set up task dependencies
        recommendation_task.context = [analysis_task]
        report_task.context = [analysis_task, recommendation_task]
        
        # Execute the crew with all three agents and tasks
        result = self._run_single_crew(
            [db_agent, recommender_agent, report_agent], 
            [analysis_task, recommendation_task, report_task], 
            user_email
        )
        return result
    
    def _run_single_crew(self, agents, tasks, user_email) -> Dict[str, Any]:
        """Run a single crew with all agents and tasks."""
        
        print("=== Starting Complete Analysis Pipeline ===")
        
        # Create single crew with all agents and tasks
        crew = Crew(
            agents=agents,
            tasks=tasks,
            verbose=True,
            memory=True
        )
        result = crew.kickoff()
        result = PersonalizedReportOutput.parse_obj(json.loads(result.raw)['markdown_report'])
        
        # Save the markdown report to file if it's a PersonalizedReportOutput
        if hasattr(result, 'markdown_report'):
            # Create reports directory if it doesn't exist
            from pathlib import Path
            reports_dir = Path(__file__).parent.parent / "reports"
            reports_dir.mkdir(exist_ok=True)
            
            # Generate filename with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"news_recommendations_{user_email.replace('@', '_at_')}_{timestamp}.md"
            file_path = reports_dir / filename
            
            result.save_to_file(str(file_path))
            print(f"Report saved to: {file_path}")
        
        return result


def main():
    """Main execution function."""
    user_email = "michalkucirka@gmail.com"
    
    executor = DatabaseAnalysisExecutor()
    
    # Execute full pipeline
    full_result = executor.execute_full_analysis(user_email)
    print("\n=== Analysis Complete ===")
    if hasattr(full_result, 'report_title'):
        print(f"Generated report: {full_result.report_title}")
    
if __name__ == "__main__":
    main()