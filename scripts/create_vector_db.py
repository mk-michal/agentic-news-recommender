from src.llm.vector_store import VectorStore
from datetime import datetime
import argparse

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Build vector database for articles on a specific date')
    parser.add_argument('--date', type=str, required=True, 
                      help='Target date in YYYY-MM-DD format')
    
    args = parser.parse_args()
    
    try:
        # Parse the date
        target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        
        # Create and save vector database
        vector_store = VectorStore(target_date)
        vector_store.create_index()
        
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD format")
    except Exception as e:
        print(f"Error creating vector database: {e}")

if __name__ == "__main__":
    main()