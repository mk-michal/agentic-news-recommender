#!/usr/bin/env python3
"""
Create Vector Database Script

This script creates a vector database from articles for semantic search.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, date

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.llm.vector_store import VectorStore


def main(date_str: str = None) -> bool:
    """
    Main function to create vector database
    
    Args:
        date_str: Date string in YYYY-MM-DD format (for pipeline usage)
        
    Returns:
        True if vector database creation was successful, False otherwise
    """
    # Handle both command line and pipeline usage
    if date_str is None:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Create vector database for articles')
        parser.add_argument('--date', type=str, required=True,
                           help='Date in YYYY-MM-DD format')
        parser.add_argument('--full-rebuild', action='store_true',
                           help='Force full rebuild instead of incremental update')
        args = parser.parse_args()
        date_str = args.date

    
    # Parse the date
    target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    print(f"Creating vector database for date: {target_date}")
    
    # Create vector store
    vector_store = VectorStore(use_existing_version=True)
    
    # Build the vector database
    vector_store.create_index(incremental=False)
    
    print(f"✓ Successfully created vector database for {target_date}")
    return True


if __name__ == "__main__":
    main()