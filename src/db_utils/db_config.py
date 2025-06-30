"""Database configuration and connection utilities for PostgreSQL."""

import os
import psycopg2
from typing import Dict
from contextlib import contextmanager


class DatabaseConfig:
    """Database configuration management."""
    
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = os.getenv('DB_PORT', '5432')
        self.database = os.getenv('DB_NAME', 'postgres')
        self.user = os.getenv('DB_USER', 'user')
        self.password = os.getenv('DB_PASSWORD', 'password')
    
    def get_connection_params(self) -> Dict[str, str]:
        """Get database connection parameters as dictionary."""
        return {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.user,
            'password': self.password
        }


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    config = DatabaseConfig()
    conn = None
    try:
        conn = psycopg2.connect(**config.get_connection_params())
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()