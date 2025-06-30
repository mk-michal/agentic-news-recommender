#!/usr/bin/env python3
"""
NewsAPI Connector Example Script with Database Storage

This script demonstrates how to use the NewsAPIConnector to search for articles
and save the results to PostgreSQL database.
"""

import sys
import os
import argparse
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from etl.api_connector import NewsAPIConnector
from db_utils import DatabaseOperations


def main():
    """Main function to demonstrate NewsAPI usage"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Search for news articles using NewsAPI')
    parser.add_argument('--keyword', '-k', type=str, help='Keyword to search for (default: Tesla Inc)')
    parser.add_argument('--count', '-c', type=int, default=100,
                       help='Number of articles to retrieve (default: 100)')
    args = parser.parse_args()
    
    # Initialize database operations
    db_ops = DatabaseOperations()
    
    # Initialize connector (replace with your actual API key)
    api_key = os.getenv("NEWSAPI_KEY", "your-newsapi-key-here")
        
    with NewsAPIConnector(api_key) as connector:
        # Search for articles with user-provided keyword
        print(f"Searching for {args.keyword} articles...")
        
        # Prepare request data for database
        search_request = {
            "keyword": args.keyword,
            "articles_count": args.count,
            "articles_sort_by": "date",
            "ignore_source_group_uri": "paywall/paywalled_sources"
        }
        
        results = connector.search_articles(**search_request)
        
        # Save to database using the new utility
        record_id = db_ops.save_news_data(search_request, results)
        if record_id:
            print(f"Data saved to database with ID: {record_id}")
        
        articles = results.get('articles', {}).get('results', [])
        print(f"Found {len(articles)} articles")


if __name__ == "__main__":
    main()