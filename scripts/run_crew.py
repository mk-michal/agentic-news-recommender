#!/usr/bin/env python3
"""
Database Analysis Execution Script

This script orchestrates the execution of database analysis using CrewAI agents.
"""

import sys
from pathlib import Path
from typing import Tuple, Any

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from crewai import Crew
from src.llm.agent.models import ClusterAnalysisOutput
from src.llm.agent.agents import DatabaseAgent
from src.llm.agent.tasks import QueryTaskBuilder
from src.llm.agent.tools import DatabaseTools
from src.llm.agent.mcp_config import MCPServerConfig


class DatabaseAnalysisExecutor:
    """Main class for executing database analysis through CrewAI agents."""
    
    def __init__(self):
        self.mcp_config = MCPServerConfig()
        self.tools = DatabaseTools(self.mcp_config)
        self.task_builder = QueryTaskBuilder()
    
    def execute_user_analysis(self, user_email: str) -> Tuple[str, str, str] | Any:
        """Execute user analysis query and return results."""
        try:
            with self.tools.get_tools_with_context() as pg_tools:
                # Create agent and task
                agent = DatabaseAgent.create_agent(list(pg_tools))
                task = self.task_builder.create_analysis_task(user_email, agent)
                
                # Execute the analysis
                result = self._run_crew_analysis(agent, task)
                
                return self._process_result(result)
                
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
    
    def _process_result(self, result: Any) -> Tuple[str, str, str] | Any:
        """Process and return the analysis result."""
        if isinstance(result, ClusterAnalysisOutput):
            return result.to_tuple()
        return result


def main():
    """Main execution function."""
    user_email = "michalkucirka@gmail.com"
    
    executor = DatabaseAnalysisExecutor()
    result = executor.execute_user_analysis(user_email)
    
    if result:
        print("\n=== Database Analysis Result ===")
        if isinstance(result, tuple):
            print(f"Cluster 1: {result[0]}")
            print(f"Cluster 2: {result[1]}")
            print(f"Cluster 3: {result[2]}")
        else:
            print(result)
    else:
        print("No results returned from analysis.")
        



if __name__ == "__main__":
    main()