"""Database operations for news data management."""

import json
from typing import Dict, Any, Optional
from .db_config import get_db_connection, DatabaseConfig


class DatabaseOperations:
    """Database operations manager."""
    
    def __init__(self):
        self.config = DatabaseConfig()
    
    def save_news_data(self, raw_request: Dict[str, Any], raw_response: Dict[str, Any]) -> Optional[int]:
        """Save raw request and response to database."""
        insert_sql = """
        INSERT INTO news_api_responses (raw_request, raw_response)
        VALUES (%s, %s)
        RETURNING id;
        """
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(insert_sql, (json.dumps(raw_request), json.dumps(raw_response)))
            record_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            return record_id
    
    def get_response_by_id(self, response_id: int) -> Optional[Dict[str, Any]]:
        """Get a response record by ID."""
        select_sql = """
        SELECT id, raw_request, raw_response, created_at
        FROM news_api_responses
        WHERE id = %s;
        """
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(select_sql, (response_id,))
            row = cursor.fetchone()
            cursor.close()
            
            if row:
                return {
                    'id': row[0],
                    'raw_request': row[1],
                    'raw_response': row[2],
                    'created_at': row[3]
                }
            return None
    
    def process_response_to_articles(self, response_id: int) -> bool:
        """Process a raw response and extract articles to the articles table."""
        # Get the response data
        response_data = self.get_response_by_id(response_id)
        if not response_data:
            print(f"No response found with ID: {response_id}")
            return False
        
        raw_response = response_data['raw_response']
        articles_data = raw_response.get('articles', {}).get('results', [])
        
        if not articles_data:
            print(f"No articles found in response ID: {response_id}")
            return False
        
        insert_sql = """
        INSERT INTO articles (request_id, url, lang, date, datatype, title, body, sentiment, source_uri)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            articles_inserted = 0
            for article in articles_data:
                cursor.execute(insert_sql, (
                    response_id,
                    article.get('url'),
                    article.get('lang'),
                    article.get('date'),
                    article.get('dataType'),
                    article.get('title'),
                    article.get('body'),
                    article.get('sentiment'),
                    article.get('source', {}).get('uri')
                ))
                articles_inserted += 1
            
            conn.commit()
            cursor.close()
            print(f"Successfully processed {articles_inserted} articles from response ID: {response_id}")
            return True
        
    def get_database_schema(self) -> str:
        """Get complete database schema information."""
        schema_sql = """
        SELECT 
            t.table_name,
            c.column_name,
            c.data_type,
            c.character_maximum_length,
            c.is_nullable,
            c.column_default,
            tc.constraint_type,
            kcu.constraint_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.tables t
        LEFT JOIN information_schema.columns c ON t.table_name = c.table_name
        LEFT JOIN information_schema.key_column_usage kcu ON c.table_name = kcu.table_name 
            AND c.column_name = kcu.column_name
        LEFT JOIN information_schema.table_constraints tc ON kcu.constraint_name = tc.constraint_name
        LEFT JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name
        WHERE t.table_schema = 'public' 
            AND t.table_type = 'BASE TABLE'
            AND t.table_name IN ('users', 'articles', 'user_articles', 'news_api_responses')
        ORDER BY t.table_name, c.ordinal_position;
        """
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(schema_sql)
            rows = cursor.fetchall()
            cursor.close()
            
            # Format schema information
            schema_info = {}
            for row in rows:
                table_name = row[0]
                if table_name not in schema_info:
                    schema_info[table_name] = []
                
                column_info = {
                    'column_name': row[1],
                    'data_type': row[2],
                    'max_length': row[3],
                    'nullable': row[4],
                    'default': row[5],
                    'constraint_type': row[6],
                    'foreign_table': row[8],
                    'foreign_column': row[9]
                }
                schema_info[table_name].append(column_info)
            
            # Build readable schema description
            schema_description = "DATABASE SCHEMA INFORMATION:\n\n"
            for table_name, columns in schema_info.items():
                schema_description += f"{table_name} table:\n"
                for col in columns:
                    data_type = col['data_type']
                    if col['max_length']:
                        data_type += f"({col['max_length']})"
                    
                    constraints = []
                    if col['constraint_type'] == 'PRIMARY KEY':
                        constraints.append('PRIMARY KEY')
                    elif col['constraint_type'] == 'FOREIGN KEY':
                        constraints.append(f"REFERENCES {col['foreign_table']}({col['foreign_column']})")
                    elif col['constraint_type'] == 'UNIQUE':
                        constraints.append('UNIQUE')
                    
                    if col['nullable'] == 'NO':
                        constraints.append('NOT NULL')
                    
                    constraint_str = f" ({', '.join(constraints)})" if constraints else ""
                    schema_description += f"   - {col['column_name']} {data_type}{constraint_str}\n"
                
                schema_description += "\n"
            
            return schema_description