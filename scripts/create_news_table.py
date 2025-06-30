import sys
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from db_utils import DatabaseSchema


def create_news_tables():
    """Create tables to store NewsAPI responses and articles"""
    db_schema = DatabaseSchema()
    
    # Initialize all database tables
    if db_schema.initialize_database():
        print("All tables created successfully!")
    else:
        print("Failed to create database tables.")


if __name__ == "__main__":
    create_news_tables()