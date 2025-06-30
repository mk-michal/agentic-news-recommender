#!/usr/bin/env python3
"""
News Pipeline Orchestrator

This script runs the complete news processing pipeline:
1. Extract articles from NewsAPI
2. Process responses to articles  
3. Create vector database
4. Create mock users and reading history
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import argparse

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import the modified script functions
from scripts.etl.newsapi_extractor import main as extract_news
from scripts.etl.process_response_to_articles import main as process_responses
from scripts.etl.create_vector_db import main as create_vector_db
from scripts.etl.create_mock_users import main as create_users


def main():
    """Main pipeline orchestrator function."""
    parser = argparse.ArgumentParser(description='Run the complete news processing pipeline')
    parser.add_argument('--keywords', '-k', type=str, 
                       default='Technology,Finance,Health',
                       help='Comma-separated keywords to search for')
    parser.add_argument('--count', '-c', type=int, default=50,
                       help='Number of articles to retrieve per keyword/date combination')
    parser.add_argument('--start-date', '-s', type=str,
                       default='2025-06-20',
                       help='Start date for article extraction in YYYY-MM-DD format')
    parser.add_argument('--end-date', '-e', type=str,
                       default='2025-06-21', 
                       help='End date for article extraction in YYYY-MM-DD format')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("STARTING NEWS PROCESSING PIPELINE")
    print("=" * 60)
    
    # Step 1: Extract news articles
    print("\n🔄 Step 1: Extracting news articles from NewsAPI...")
    response_ids = extract_news(
        keywords=args.keywords,
        count=args.count,
        dates=f"{args.start_date},{args.end_date}"
    )
    
    if not response_ids:
        print("❌ No articles extracted. Pipeline terminated.")
        return
    
    print(f"✅ Step 1 complete. Extracted {len(response_ids)} response batches.")
    
    # Step 2: Process responses to articles
    print("\n🔄 Step 2: Processing responses to individual articles...")
    processed_count = 0
    for response_id in response_ids:
        result = process_responses(response_id=response_id)
        if result:
            processed_count += 1
    
    print(f"✅ Step 2 complete. Processed {processed_count} response batches.")
    
    # Step 3: Create vector database
    print("\n🔄 Step 3: Creating vector database...")
    vector_result = create_vector_db(date_str=args.start_date)
    
    if vector_result:
        print("✅ Step 3 complete. Vector database created.")
    else:
        print("⚠️  Step 3 completed with warnings. Check vector database.")
    
    # Step 4: Create mock users
    print("\n🔄 Step 4: Creating mock users and reading history...")
    user_result = create_users()
    
    if user_result:
        print("✅ Step 4 complete. Mock users and reading history created.")
    else:
        print("⚠️  Step 4 completed with warnings. Check user creation.")
    
    print("\n" + "=" * 60)
    print("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\nYou can now run the analysis crew with:")
    print("python scripts/run_crew.py")


if __name__ == "__main__":
    main()