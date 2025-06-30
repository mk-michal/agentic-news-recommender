from crewai import Agent
from typing import List, Any


class DatabaseAgent:
    """Factory class for creating database analysis agents."""
    
    AGENT_ROLE = "Database Analyst"
    AGENT_GOAL = ("Query and analyze data from PostgreSQL database to provide insights "
                  "about user reading habits and news recommendations")
    AGENT_BACKSTORY = """I am a skilled database analyst with expertise in PostgreSQL operations. 
    I can query user reading history, analyze article preferences, and provide data-driven insights 
    for news recommendations. I communicate with databases using natural language descriptions 
    of what I want to find, and let the database tools figure out the appropriate SQL queries."""
    
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


class RecommenderAgent:
    """Factory class for creating article recommendation agents."""
    
    AGENT_ROLE = "Article Recommender Specialist"
    AGENT_GOAL = ("Recommend relevant articles based on user history and preferences using "
                  "both vector similarity search and database retrieval")
    AGENT_BACKSTORY = """I am an expert in content recommendation systems with deep knowledge 
    of both semantic similarity search and database operations. I can analyze user interest clusters, 
    find the most relevant articles using vector embeddings and similarity algorithms, then retrieve 
    complete article information from databases. I combine vector search capabilities with database 
    operations to provide comprehensive article recommendations with full metadata including titles, 
    URLs, sources, and content previews."""
    
    @staticmethod
    def create_agent(tools: List[Any]) -> Agent:
        """Create a recommender agent with given tools."""
        return Agent(
            role=RecommenderAgent.AGENT_ROLE,
            goal=RecommenderAgent.AGENT_GOAL,
            backstory=RecommenderAgent.AGENT_BACKSTORY,
            tools=tools,
            verbose=True,
            allow_delegation=False
        )