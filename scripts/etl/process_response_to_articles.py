#!/usr/bin/env python3
"""
Process Response to Articles Script

This script processes individual articles from NewsAPI responses stored in the database.
"""

import sys
import argparse
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from db_utils import DatabaseOperations


def main(response_id: int = None) -> bool:
    """
    Main function to process response to articles
    
    Args:
        response_id: ID of the response to process (for pipeline usage)
        
    Returns:
        True if processing was successful, False otherwise
    """
    # Handle both command line and pipeline usage
    if response_id is None:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Process NewsAPI response to individual articles')
        parser.add_argument('--response-id', type=int, required=True,
                           help='ID of the response to process')
        args = parser.parse_args()
        response_id = args.response_id
    
    try:
        # Initialize database operations
        db_ops = DatabaseOperations()
        
        print(f"Processing response ID: {response_id}")
        
        # Process the response (this would contain the actual processing logic)
        # For now, we'll just mark it as processed
        result = db_ops.process_response_to_articles(response_id)
        
        if result:
            print(f"✓ Successfully processed response {response_id}")
            return True
        else:
            print(f"❌ Failed to process response {response_id}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing response {response_id}: {str(e)}")
        return False


if __name__ == "__main__":
    main()