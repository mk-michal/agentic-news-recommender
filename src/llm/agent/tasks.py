from crewai import Task, Agent
from src.llm.agent.models import ClusterAnalysisOutput, RecommendationOutput, PersonalizedReportOutput
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
        description = f"""
        Analyze the reading history and preferences for user with email '{user_email}'.

        DATABASE SCHEMA:
        {self.schema_info}
        
        Your task is to:
        1. Query the database to find all articles this user has read or interacted with
        2. Analyze the user's reading patterns, topics of interest, and preferences
        3. Group the user's interests into 3 distinct clusters based on topics, themes, or content types
        4. For each cluster, write a detailed paragraph describing the user's interests in that area
        
        Use natural language to describe what you want to find, and let the PostgreSQL tool 
        figure out the appropriate queries. For example:
        - "Find all articles read by user with email {user_email}"
        - "Get article titles and content for articles read by this user"
        - "Show me user profile information and reading statistics"
        
        The database contains tables for users, articles, and user_articles (reading history).
        
        Output 3 cluster descriptions as structured data.
        """
        
        return Task(
            description=description,
            agent=agent,
            expected_output="A structured analysis with 3 cluster descriptions based on user reading patterns",
            output_pydantic=ClusterAnalysisOutput
        )

    
    def create_recommendation_task_with_context(self, agent: Agent) -> Task:
        """Create a recommendation task that uses context from the analysis task."""
        description = f"""
        Based on the cluster analysis results from the previous task, recommend relevant articles by combining 
        vector similarity search with database retrieval.

        IMPORTANT: Only recommend articles published BEFORE the target date. The vector search tool 
        automatically filters articles by date, ensuring recommendations are from prior periods only.

        POSTGRESQL DATABASE SCHEMA:
        {self.schema_info}

        Your task is to:
        1. Extract the 3 cluster descriptions from the previous task's output
        2. Use the vector_similarity_search tool to find 2 most similar articles for each cluster description
           (This tool automatically filters to articles published before the target date)
        3. Extract the article IDs from the vector search results
        4. Use the PostgreSQL tools to retrieve complete article information (title, url, source_uri, body) for these article IDs
        5. Organize the recommendations by cluster with full article details
        
        Process for each cluster:
        - Search for articles similar to the cluster description using vector search
        - The vector search will only return articles published before the target date
        - Get the article IDs from the search results
        - Query the articles table to get complete information for these IDs
        - Structure the final output with cluster descriptions and article details
        
        Use natural language queries for PostgreSQL like:
        - "Get article details for article IDs: [list of IDs]"
        - "Find title, url, source_uri, and body for articles with these IDs"
        
        Expected output format:
        - cluster_1_recommendations: cluster description + 2 articles with full details
        - cluster_2_recommendations: cluster description + 2 articles with full details  
        - cluster_3_recommendations: cluster description + 2 articles with full details
        
        Each article should include: article_id, title, url, source, body
        """
        
        return Task(
            description=description,
            agent=agent,
            expected_output="Complete article recommendations organized by cluster with full metadata, filtered to articles published before the target date",
            output_pydantic=RecommendationOutput
        )
    
    def create_report_generation_task(self, user_email: str, agent: Agent) -> Task:
        """Create a markdown report generation task."""
        description = f"""
        Create a personalized, engaging markdown report for user '{user_email}' based on the cluster analysis 
        and article recommendations from the previous tasks.

        IMPORTANT CONSTRAINTS:
        - YOU MUST include EXACTLY 6 articles in the report (2 from each cluster)
        - Each timeline entry MUST be on a separate line
        - If fewer than 6 articles are available, search for additional related articles to reach exactly 6

        Your task is to:
        1. Extract the analysis results and article recommendations from the previous tasks
        2. Verify you have exactly 6 articles total (2 per cluster) - if not, supplement with related articles
        3. Create an engaging introduction that explains why these articles were selected
        4. Organize the content into a well-structured markdown report
        5. For each recommended article, provide:
           - Article title (as clickable link using the URL)
           - Source publication and published date
           - A compelling 2-3 sentence summary based on the article body
           - Why this article fits the user's interests (reference the cluster it belongs to)
        6. Enhance each article by searching the web for similar/related stories:
           - Use web search to find 2-3 related articles on the same topic
           - Scrape the related articles to get their publication dates
           - Create a chronological timeline showing the story development
           - Format timeline entries with title links, source, and date

        The report should:
        - Start with a personalized greeting and brief explanation of the recommendation system
        - List articles one by one with enhanced timelines
        - Use proper markdown formatting (headers, links, bullet points, etc.)
        - Have an engaging, conversational tone
        - Include a conclusion encouraging the user to explore these articles

        MANDATORY FORMAT - Structure the report EXACTLY as follows:
        # Personalized News Recommendations for [User]
        
        ## Introduction
        [Engaging intro about the recommendation system and user's interests]
        
        ## Recommended Articles
        
        ### [Article 1 Title](article_url)
        article_url | source | published_date
        Article summary, main points (one paragraph)

        <small>**Timeline:** (Related stories in chronological order)</small>
        <small>1. [Connected article 1 Title](link) | Source | Date</small>
        <small>2. [Connected article 2 Title](link) | Source | Date</small>
        <small>3. [Current article title](original_url) | Source | Date</small>
        
        ### [Article 2 Title](article_url)
        article_url | source | published_date
        Article summary, main points (one paragraph)

        <small>**Timeline:** (Related stories in chronological order)</small>
        <small>1. [Connected article 1 Title](link) | Source | Date</small>
        <small>2. [Connected article 2 Title](link) | Source | Date</small>
        <small>3. [Current article title](original_url) | Source | Date</small>

        ### [Article 3 Title](article_url)
        article_url | source | published_date
        Article summary, main points (one paragraph)

        <small>**Timeline:** (Related stories in chronological order)</small>
        <small>1. [Connected article 1 Title](link) | Source | Date</small>
        <small>2. [Connected article 2 Title](link) | Source | Date</small>
        <small>3. [Current article title](original_url) | Source | Date</small>

        ### [Article 4 Title](article_url)
        article_url | source | published_date
        Article summary, main points (one paragraph)

        <small>**Timeline:** (Related stories in chronological order)</small>
        <small>1. [Connected article 1 Title](link) | Source | Date</small>
        <small>2. [Connected article 2 Title](link) | Source | Date</small>
        <small>3. [Current article title](original_url) | Source | Date</small>

        ### [Article 5 Title](article_url)
        article_url | source | published_date
        Article summary, main points (one paragraph)

        <small>**Timeline:** (Related stories in chronological order)</small>
        <small>1. [Connected article 1 Title](link) | Source | Date</small>
        <small>2. [Connected article 2 Title](link) | Source | Date</small>
        <small>3. [Current article title](original_url) | Source | Date</small>

        ### [Article 6 Title](article_url)
        article_url | source | published_date
        Article summary, main points (one paragraph)

        <small>**Timeline:** (Related stories in chronological order)</small>
        <small>1. [Connected article 1 Title](link) | Source | Date</small>
        <small>2. [Connected article 2 Title](link) | Source | Date</small>
        <small>3. [Current article title](original_url) | Source | Date</small>
        
        ## Conclusion
        [Encouraging closing remarks]
        
        TIMELINE FORMATTING RULES:
        - Each timeline entry MUST be on its own separate line
        - Each line starts with <small> and ends with </small>
        - Use numbered list format (1., 2., 3.)
        - Order timeline entries chronologically (oldest to newest)
        - Include the original recommended article as the final timeline entry
        - Extract publication dates from scraped content accurately
        
        ARTICLE COUNT VALIDATION:
        - Count all articles before generating the report
        - If you have fewer than 6 articles, search for additional relevant articles using web search
        - Ensure the final report contains exactly 6 article sections
        - Each article must have a complete timeline with 2-3 related stories
        
        Make it personal, engaging, and valuable for the user with comprehensive context through timelines.
        """
        
        return Task(
            description=description,
            agent=agent,
            expected_output="A complete markdown report with exactly 6 personalized article recommendations, each with chronological timelines where every timeline entry is on a separate line",
            output_pydantic=PersonalizedReportOutput
        )