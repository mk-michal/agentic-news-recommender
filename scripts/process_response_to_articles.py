#!/usr/bin/env python3
"""
Process Raw NewsAPI Response to Articles Table

This script takes a response_id as input and processes the raw response
to extract individual articles into the articles table.
"""

import sys
import argparse
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from db_utils import DatabaseSchema, DatabaseOperations

def main():
    """Main function to process response to articles"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process raw NewsAPI response to articles table')
    parser.add_argument('--response-id', '-r', type=int, required=True,
                       help='Response ID to process from news_api_responses table')
    args = parser.parse_args()
    
    # Initialize database components
    db_ops = DatabaseOperations()
    
    # Process the response
    print(f"Processing response ID: {args.response_id}")
    db_ops.process_response_to_articles(args.response_id)
    print("Processing completed successfully!")


if __name__ == "__main__":
    main()