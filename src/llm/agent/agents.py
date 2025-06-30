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


class ReportWriterAgent:
    """Factory class for creating markdown report writer agents."""
    
    AGENT_ROLE = "Content Report Writer"
    AGENT_GOAL = ("Create engaging, personalized markdown reports summarizing article recommendations "
                  "based on user analysis and preferences")
    AGENT_BACKSTORY = """I am a skilled content writer and report generator with expertise in creating 
    engaging, personalized content. I specialize in transforming technical analysis and article recommendations 
    into readable, well-structured markdown reports that highlight the most relevant and interesting content 
    for each user. I excel at summarizing complex information and presenting it in an accessible, 
    engaging format that captures the user's attention and provides clear value."""
    
    @staticmethod
    def create_agent() -> Agent:
        """Create a report writer agent (no tools needed - uses LLM capabilities)."""
        return Agent(
            role=ReportWriterAgent.AGENT_ROLE,
            goal=ReportWriterAgent.AGENT_GOAL,
            backstory=ReportWriterAgent.AGENT_BACKSTORY,
            tools=[],  # No tools needed - pure LLM content generation
            verbose=True,
            allow_delegation=False
        )