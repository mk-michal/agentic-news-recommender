# News Daily Digest AI Recommender

A sophisticated news recommendation system using CrewAI agents, PostgreSQL, vector databases, and semantic search to provide personalized article recommendations based on user reading history. The system aggregates news from multiple sources to deliver comprehensive daily digests.

## Installation and Setup

### 1. Environment Setup

Install dependencies using `uv`:

```bash
# Create virtual environment and install dependencies
uv sync
```

### 2. Database Setup

Ensure your local PostgreSQL database is running and accessible. The system requires a PostgreSQL instance for storing articles, user data, and reading history.

### 3. Environment Variables

Set up the required API keys:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export NEWSAPI_KEY="your-newsapi-key"
export SERPER_API_KEY="your-serper-api-key"
```

## Getting Started

### 1. Initialize Database

First, create the necessary database tables:

```bash
python scripts/create_news_table.py
```

This creates all required tables for storing news responses, articles, users, and reading history.

## Data Pipeline

### News Data Source

The system uses [NewsAPI.ai](https://newsapi.ai/documentation?tab=introduction) to fetch news articles from multiple sources. You'll need an API key from NewsAPI.ai (2,500 requests are free for testing).

### 2. Run Complete Pipeline

Execute the full data processing pipeline:

```bash
NEWSAPI_KEY=<news-api-key> OPENAI_API_KEY='<openai-api-key>' PYTHONPATH=src python3 scripts/pipeline_runner.py
```

This orchestrates the following steps:

#### Individual Pipeline Scripts:

1. **`newsapi_extractor.py`** - Extracts articles from NewsAPI
   - Searches for articles using specified keywords across multiple news sources
   - Supports multiple keywords and date ranges
   - Stores raw API responses in PostgreSQL
   - Default: searches for Technology, Finance, Health articles

2. **`process_response_to_articles.py`** - Processes API responses
   - Converts raw API responses into individual article records
   - Extracts article metadata (title, URL, content, etc.)
   - Stores processed articles in the database

3. **`create_vector_db.py`** - Creates vector embeddings
   - Generates semantic embeddings for articles using OpenAI
   - Stores embeddings in ChromaDB for similarity search
   - Enables semantic article recommendations

4. **`create_mock_users.py`** - Sets up test users
   - Creates mock user accounts
   - Generates reading history for the primary user
   - Establishes user-article relationships

## Agent System

### Prerequisites for Agent Execution

- **MCP Server**: Local Model Context Protocol server for PostgreSQL database access
- **Node.js**: Required to run the MCP server via npx
- **Serper API Key**: Required for web search functionality (get from [serper.dev](https://serper.dev/))

### MCP Server Setup

The system uses the Model Context Protocol (MCP) server for database access. Start the MCP server for PostgreSQL:

```bash
# Install npx if not already available
npm install -g npx

# Start MCP server (replace with your PostgreSQL connection string)
npx @modelcontextprotocol/server-postgres postgresql://username:password@localhost:5432/database_name
```

### 3. Run Recommendation Agent

Execute the AI agent system:

```bash
SERPER_API_KEY=<serper-api-key> OPENAI_API_KEY=<openai-api-key> PYTHONPATH=src python3 scripts/run_crew.py
```

## Agent Architecture

The system uses CrewAI with three specialized agents:

### Agents (`src/llm/agent/agents.py`)

1. **DatabaseAgent** - Database Analyst
   - Queries PostgreSQL to analyze user reading habits
   - Performs cluster analysis on user's article history
   - Identifies reading patterns and preferences

2. **RecommenderAgent** - Article Recommender
   - Uses vector similarity search to find relevant articles
   - Combines semantic search with database queries
   - Selects articles matching user's interest clusters

3. **ReportWriterAgent** - Content Report Writer
   - Creates personalized markdown reports
   - Searches for related articles and timelines
   - Generates engaging, contextual content

### Tasks (`src/llm/agent/tasks.py`)

1. **Analysis Task** - User reading pattern analysis
2. **Recommendation Task** - Article recommendation with context
3. **Report Generation Task** - Personalized markdown report creation

### Tools (`src/llm/agent/tools.py`)

1. **DatabaseTools** - PostgreSQL access via MCP server
2. **VectorDatabaseTool** - Semantic similarity search
3. **Web Search Tools** - SerperDev for related article discovery
4. **Web Scraping Tools** - Content extraction for timelines

## Project Structure

```
### File Structure Overview

```
.
├── README.md
├── pyproject.toml           # Project dependencies and configuration
├── data/
│   ├── reports/            # Generated recommendation reports
│   └── vector_store/       # FAISS vector database files
├── scripts/
│   ├── create_news_table.py     # Database initialization
│   ├── pipeline_runner.py       # Complete data pipeline
│   └── run_crew.py              # Agent execution
├── src/
    ├── db_utils/               # Database utilities
    ├── etl/                    # Data extraction and processing
    └── llm/                    # AI agent system
       └── agent/              # CrewAI agent implementation

```

## Output

The system generates personalized news recommendation reports in the `reports/` directory, featuring:

- Tailored article selections based on reading history from multiple news sources
- Chronological timelines for each recommended article
- Related article discovery and context
- Engaging, personalized content presentation

## Features

- **Multi-source News Aggregation**: Fetches articles from various news sources via NewsAPI.ai
- **Semantic Search**: Uses OpenAI embeddings and FAISS for similarity-based recommendations
- **Personalized Recommendations**: Analyzes user reading history to suggest relevant articles
- **Timeline Generation**: Creates chronological context for recommended articles
- **Automated Reporting**: Generates comprehensive markdown reports with personalized insights
- **MCP Integration**: Uses Model Context Protocol for secure database access

## Technical Stack

- **Backend**: Python 3.12+, PostgreSQL, FAISS
- **AI Framework**: CrewAI, OpenAI GPT models
- **Data Processing**: Custom ETL pipeline with vector embeddings
- **Database**: PostgreSQL for structured data, FAISS for vector similarity
- **APIs**: NewsAPI.ai, Serper.dev, OpenAI

