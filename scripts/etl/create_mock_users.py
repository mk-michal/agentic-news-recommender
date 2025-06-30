#!/usr/bin/env python3
"""
Script to create mock user data and insert them into the users table.
Also creates mock history of read articles for the primary user.
"""

import sys
import os
import random
from datetime import datetime

# Add the project root to the path so we can import project modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from src.db_utils.db_config import get_db_connection


def create_mock_users():
    """Create and insert mock users into the database."""
    
    # List of mock users with realistic data
    mock_users = [
        {
            "email": "michalkucirka@gmail.com",
            "preferences": "I'm interested in technology news, especially AI and machine learning advancements. "
                          "I enjoy reading about financial markets and investment strategies. "
                          "Health and fitness articles are also interesting to me, particularly nutrition science. "
                          "I prefer concise articles with data visualizations when available.",
            "age": 32,
            "gender": "male", 
            "location": "Prague"
        },
        {
            "email": "jan.novak@example.com",
            "preferences": "I follow political news both domestic and international with great interest. "
                          "Environmental sustainability topics are important to me. "
                          "I enjoy in-depth analyses rather than brief news. "
                          "Scientific breakthroughs in renewable energy catch my attention regularly.",
            "age": 45,
            "gender": "male",
            "location": "Brno"
        },
        {
            "email": "anna.svobodova@example.com",
            "preferences": "I'm passionate about culinary arts and food culture articles. "
                          "Travel destinations and experiences are my favorite reads. "
                          "I also enjoy fashion news and sustainable clothing topics. "
                          "Local Czech cultural events and arts coverage is something I look for daily.",
            "age": 28,
            "gender": "female",
            "location": "Ostrava"
        },
        {
            "email": "martin.dvorak@example.com",
            "preferences": "Sports news is my primary interest, particularly football and hockey. "
                          "I follow automotive industry developments and new car reviews. "
                          "Weekend leisure activity suggestions are useful for my family outings. "
                          "I appreciate articles with practical DIY advice for home improvement.",
            "age": 37,
            "gender": "male",
            "location": "Plzeň"
        },
        {
            "email": "petra.novotna@example.com",
            "preferences": "Education trends and learning methodologies interest me professionally. "
                          "Parenting advice and child development research are topics I follow closely. "
                          "Mental health awareness and psychology studies help with my work. "
                          "Book reviews and literary discussions are my weekend reading pleasure.",
            "age": 41,
            "gender": "female",
            "location": "Liberec"
        }
    ]
    
    # Connect to the database and insert mock users
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if users already exist to avoid duplicates
        cursor.execute("SELECT user_email FROM users")
        existing_emails = [row[0] for row in cursor.fetchall()]
        
        # Insert users that don't already exist
        inserted_count = 0
        for user in mock_users:
            if user["email"] not in existing_emails:
                cursor.execute(
                    """
                    INSERT INTO users (user_email, user_preferences, age, gender, location)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (user["email"], user["preferences"], user["age"], user["gender"], user["location"])
                )
                inserted_count += 1
                print(f"Inserted user: {user['email']}")
            else:
                print(f"User {user['email']} already exists, skipping.")
        
        conn.commit()
        
        print(f"\nSuccessfully inserted {inserted_count} new mock users into the database.")
        
        # Verify users in the database
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        print(f"Total users in database: {total_users}")
        
        return inserted_count > 0


def create_article_history_for_primary_user():
    """
    Create mock article reading history for the user with email michalkucirka@gmail.com.
    Selects 10 random articles from the articles table and creates records in user_articles table.
    """
    primary_email = "michalkucirka@gmail.com"
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if the primary user exists
        cursor.execute("SELECT id FROM users WHERE user_email = %s", (primary_email,))
        user_result = cursor.fetchone()
        if not user_result:
            print(f"Error: User {primary_email} not found in the database.")
            return False
        
        user_id = user_result[0]
        
        # Check if there are any articles in the database
        cursor.execute("SELECT COUNT(*) FROM articles")
        article_count = cursor.fetchone()[0]
        if article_count == 0:
            print("Error: No articles found in the database.")
            return False
        
        # Check if the user already has article history
        cursor.execute("SELECT COUNT(*) FROM user_articles WHERE user_id = %s", (user_id,))
        existing_history_count = cursor.fetchone()[0]
        if existing_history_count > 0:
            print(f"User {primary_email} already has {existing_history_count} article history records.")
            # For pipeline usage, don't prompt for input - just continue
            print("Adding more records to existing history...")
        
        # Get 10 random articles
        cursor.execute("""
            SELECT id FROM articles 
            ORDER BY RANDOM() 
            LIMIT 10
        """)
        random_articles = cursor.fetchall()
        
        if len(random_articles) < 10:
            print(f"Warning: Only found {len(random_articles)} articles in the database.")
        
        # Insert user-article relations
        inserted_count = 0
        for article_row in random_articles:
            article_id = article_row[0]
            
            # Check if relation already exists
            cursor.execute(
                "SELECT id FROM user_articles WHERE user_id = %s AND article_id = %s", 
                (user_id, article_id)
            )
            if cursor.fetchone():
                print(f"Article {article_id} is already in user's history, skipping.")
                continue
            
            # Insert the relationship
            cursor.execute(
                "INSERT INTO user_articles (user_id, article_id) VALUES (%s, %s)",
                (user_id, article_id)
            )
            inserted_count += 1
        
        conn.commit()
        
        print(f"\nSuccessfully added {inserted_count} articles to {primary_email}'s reading history.")
        
        # Verify the total history for the user
        cursor.execute("SELECT COUNT(*) FROM user_articles WHERE user_id = %s", (user_id,))
        total_history = cursor.fetchone()[0]
        print(f"Total articles in user's history: {total_history}")
        
        # Display some details about the articles added
        cursor.execute("""
            SELECT a.id, a.title, a.source_uri, a.date 
            FROM articles a
            JOIN user_articles ua ON a.id = ua.article_id
            WHERE ua.user_id = %s
            ORDER BY ua.created_at DESC
            LIMIT 10
        """, (user_id,))
        
        print("\nRecent articles in user's history:")
        articles = cursor.fetchall()
        for i, (id, title, source, date) in enumerate(articles, 1):
            print(f"{i}. [{id}] {title} (from {source}, {date})")
        
        return True


def main() -> bool:
    """
    Main function for pipeline usage
    
    Returns:
        True if user creation was successful, False otherwise
    """
    print("Creating mock users...")
    user_result = create_mock_users()
    
    print("\nCreating article history for primary user...")
    history_result = create_article_history_for_primary_user()
    
    print("\nDone!")
    return user_result and history_result
    


if __name__ == "__main__":
    main()