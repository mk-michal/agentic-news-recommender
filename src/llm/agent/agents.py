from crewai import Agent
from typing import List, Any


class DatabaseAgent:
    """Factory class for creating database analysis agents."""
    
    AGENT_ROLE = "Database Analyst"
    AGENT_GOAL = ("Query and analyze data from PostgreSQL database to provide insights "
                  "about user reading habits and news recommendations")
    AGENT_BACKSTORY = """I am a skilled database analyst with expertise in PostgreSQL operations. 
    I can query user reading history, analyze article preferences, and provide data-driven insights 
    for news recommendations. I understand database schemas and can write efficient SQL queries."""
    
    @staticmethod
    def create_agent(tools: List[Any]) -> Agent:
        """Create a database analyst agent with given tools."""
        return Agent(
            role=DatabaseAgent.AGENT_ROLE,
            goal=DatabaseAgent.AGENT_GOAL,
            backstory=DatabaseAgent.AGENT_BACKSTORY,
            tools=tools,
            verbose=True,
            allow_delegation=False
        )