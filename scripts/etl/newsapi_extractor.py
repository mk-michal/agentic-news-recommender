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
from datetime import datetime
from typing import List

# Add the src directory to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from etl.api_connector import NewsAPIConnector
from db_utils import DatabaseOperations


def main(keywords: str = None, count: int = None, dates: str = None) -> List[int]:
    """
    Main function to demonstrate NewsAPI usage
    
    Args:
        keywords: Comma-separated keywords (for pipeline usage)
        count: Number of articles per search (for pipeline usage)  
        dates: Comma-separated dates (for pipeline usage)
        
    Returns:
        List of response IDs created in the database
    """
    # Handle both command line and pipeline usage
    if keywords is None or count is None or dates is None:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Search for news articles using NewsAPI')
        parser.add_argument('--keywords', '-k', type=str, 
                           default='Sport,Finance,Politics',
                           help='Comma-separated keywords to search for (default: Sport,Finance,Politics)')
        parser.add_argument('--count', '-c', type=int, default=50,
                           help='Number of articles to retrieve per keyword/date combination (default: 50)')
        parser.add_argument('--dates', '-d', type=str,
                           default='2025-06-20,2025-06-21',
                           help='Comma-separated dates to search in YYYY-MM-DD format (default: 2025-06-20,2025-06-21)')
        args = parser.parse_args()
        
        keywords = args.keywords
        count = args.count
        dates = args.dates
    
    # Parse keywords into a list
    keywords_list = [keyword.strip() for keyword in keywords.split(',')]
    
    # Parse dates into a list
    target_dates = [date.strip() for date in dates.split(',')]
    
    # Initialize database operations
    db_ops = DatabaseOperations()
    
    # Initialize connector (replace with your actual API key)
    api_key = os.getenv("NEWSAPI_KEY", "your-newsapi-key-here")
    
    response_ids = []
        
    with NewsAPIConnector(api_key) as connector:
        total_articles = 0
        successful_searches = 0
        total_searches = len(keywords_list) * len(target_dates)
        
        print(f"Starting search for {len(keywords_list)} keywords across {len(target_dates)} dates...")
        print(f"Keywords: {', '.join(keywords_list)}")
        print(f"Dates: {', '.join(target_dates)}")
        print(f"Total searches to perform: {total_searches}")
        print("=" * 50)
        
        # Loop through each date and keyword combination
        for date_str in target_dates:
            for keyword in keywords_list:
                print(f"\nSearching for '{keyword}' articles on {date_str}...")
                
                # Prepare request data for database
                search_request = {
                    "keyword": keyword,
                    "articles_count": count,
                    "articles_sort_by": "date",
                    "ignore_source_group_uri": "paywall/paywalled_sources",
                    "dateStart": date_str,
                    "dateEnd": date_str,
                }
                
                results = connector.search_articles(**search_request)
                
                # Save to database using the new utility
                record_id = db_ops.save_news_data(search_request, results)
                if record_id:
                    print(f"✓ Data saved to database with ID: {record_id}")
                    response_ids.append(record_id)
                
                articles = results.get('articles', {}).get('results', [])
                article_count = len(articles)
                total_articles += article_count
                successful_searches += 1
                print(f"✓ Found {article_count} articles for '{keyword}' on {date_str}")

        
        print("\n" + "=" * 50)
        print(f"=== SEARCH SUMMARY ===")
        print(f"Total keywords searched: {len(keywords_list)}")
        print(f"Total dates searched: {len(target_dates)}")
        print(f"Successful searches: {successful_searches}/{total_searches}")
        print(f"Total articles found: {total_articles}")
        print(f"Average articles per search: {total_articles/successful_searches:.1f}" if successful_searches > 0 else "Average articles per search: 0")
        print(f"Keywords: {', '.join(keywords_list)}")
        print(f"Dates: {', '.join(target_dates)}")
        print(f"Response IDs created: {response_ids}")
    
    return response_ids


if __name__ == "__main__":
    main()