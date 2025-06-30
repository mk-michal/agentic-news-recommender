"""Database schema management and table creation utilities."""

from .db_config import get_db_connection


class DatabaseSchema:
    """Database schema operations manager."""
    
    def create_news_table(self) -> bool:
        """Create the news_api_responses table if it doesn't exist."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS news_api_responses (
            id SERIAL PRIMARY KEY,
            raw_request JSONB NOT NULL,
            raw_response JSONB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(create_table_sql)
            conn.commit()
            cursor.close()
        return True
    
    def create_articles_table(self) -> bool:
        """Create the articles table if it doesn't exist."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS articles (
            id SERIAL PRIMARY KEY,
            request_id INTEGER REFERENCES news_api_responses(id) ON DELETE CASCADE,
            url TEXT,
            lang VARCHAR(10),
            date DATE,
            datatype VARCHAR(50),
            title TEXT,
            body TEXT,
            sentiment DECIMAL(10, 8),
            source_uri VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_articles_request_id ON articles(request_id);
        CREATE INDEX IF NOT EXISTS idx_articles_date ON articles(date);
        CREATE INDEX IF NOT EXISTS idx_articles_lang ON articles(lang);
        """
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(create_table_sql)
            conn.commit()
            cursor.close()
        return True
    
    def create_users_table(self) -> bool:
        """Create the users table if it doesn't exist."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            user_email VARCHAR(255) UNIQUE NOT NULL,
            user_preferences TEXT,
            age INTEGER,
            gender VARCHAR(6) CHECK (gender IN ('male', 'female')),
            location VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(user_email);
        """
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(create_table_sql)
            conn.commit()
            cursor.close()
        return True
    
    def create_user_article_relation_table(self) -> bool:
        """Create the many-to-many relationship table between users and articles."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS user_articles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_user_article UNIQUE (user_id, article_id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_user_articles_user_id ON user_articles(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_articles_article_id ON user_articles(article_id);
        """
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(create_table_sql)
            conn.commit()
            cursor.close()
        return True
    
    def initialize_database(self) -> bool:
        """Initialize all database tables."""
        self.create_news_table()
        self.create_articles_table()
        self.create_users_table()
        self.create_user_article_relation_table()
        print("Database initialized successfully")
