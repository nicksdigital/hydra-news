#!/usr/bin/env python3
"""
Simple script to populate PostgreSQL database with sample data
"""

import os
import sys
import logging
import random
from datetime import datetime, timedelta
from python.src.gdelt.database.postgres_adapter import get_postgres_adapter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database connection parameters
DB_PARAMS = {
    'host': 'localhost',
    'port': 5432,
    'dbname': 'gdelt_news',
    'user': 'postgres',
    'password': 'adv62062',
    'min_conn': 1,
    'max_conn': 10
}

def reset_database():
    """Reset the database"""
    db = get_postgres_adapter(**DB_PARAMS)
    db.reset_database()
    logger.info("Database reset successfully")
    return db

def populate_database():
    """Populate the database with sample data"""
    db = reset_database()
    
    # Add country column to sources table if it doesn't exist
    try:
        db.execute_query('ALTER TABLE sources ADD COLUMN IF NOT EXISTS country TEXT;', fetch=False)
        logger.info("Added country column to sources table")
    except Exception as e:
        logger.warning(f"Error adding country column: {e}")
    
    # Sample data
    domains = ['cnn.com', 'bbc.com', 'reuters.com', 'nytimes.com', 'washingtonpost.com']
    countries = ['US', 'GB', 'FR', 'DE', 'JP']
    themes = [
        ('ECON', 'Economy'),
        ('POL', 'Politics'),
        ('ENV', 'Environment'),
        ('TECH', 'Technology'),
        ('HEALTH', 'Health')
    ]
    
    # Insert articles
    logger.info("Inserting articles...")
    for i in range(50):
        days_ago = random.randint(0, 30)
        article_date = datetime.now() - timedelta(days=days_ago)
        theme = random.choice(themes)
        domain = random.choice(domains)
        country = random.choice(countries)
        
        db.execute_query(
            '''
            INSERT INTO articles
            (url, title, seendate, language, domain, sourcecountry, theme_id, theme_description,
             fetch_date, trust_score, sentiment_polarity, content_hash)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''',
            (
                f'https://{domain}/article_{i}',
                f'Sample Article {i}: {theme[1]} News',
                article_date.strftime('%Y-%m-%d %H:%M:%S'),
                'en',
                domain,
                country,
                theme[0],
                theme[1],
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                random.uniform(0.3, 0.9),
                random.uniform(-0.8, 0.8),
                f'hash_{i}'
            ),
            fetch=False
        )
    
    # Insert entities
    logger.info("Inserting entities...")
    entities = [
        ('Joe Biden', 'PERSON'),
        ('Vladimir Putin', 'PERSON'),
        ('Xi Jinping', 'PERSON'),
        ('United Nations', 'ORGANIZATION'),
        ('World Health Organization', 'ORGANIZATION'),
        ('Google', 'ORGANIZATION'),
        ('United States', 'LOCATION'),
        ('Russia', 'LOCATION'),
        ('China', 'LOCATION')
    ]
    
    for entity, entity_type in entities:
        db.execute_query(
            '''
            INSERT INTO entities
            (text, type, count, num_sources, source_diversity, trust_score)
            VALUES (%s, %s, %s, %s, %s, %s)
            ''',
            (
                entity,
                entity_type,
                random.randint(5, 50),
                random.randint(1, 5),
                random.uniform(0.1, 0.9),
                random.uniform(0.3, 0.9)
            ),
            fetch=False
        )
    
    # Get article IDs
    article_ids = db.execute_query('SELECT id FROM articles')
    article_ids = [row['id'] for row in article_ids]
    
    # Get entity IDs
    entity_ids = db.execute_query('SELECT id, text FROM entities')
    entity_id_map = {row['text']: row['id'] for row in entity_ids}
    
    # Insert article-entity relationships
    logger.info("Inserting article-entity relationships...")
    for article_id in article_ids:
        # Each article mentions 1-3 random entities
        num_mentions = random.randint(1, 3)
        selected_entities = random.sample(entities, min(num_mentions, len(entities)))
        
        for entity, _ in selected_entities:
            entity_id = entity_id_map.get(entity)
            if entity_id:
                db.execute_query(
                    '''
                    INSERT INTO article_entities
                    (article_id, entity_id, context)
                    VALUES (%s, %s, %s)
                    ''',
                    (
                        article_id,
                        entity_id,
                        f'Context for {entity} in article {article_id}'
                    ),
                    fetch=False
                )
    
    # Insert sources
    logger.info("Inserting sources...")
    for domain in domains:
        try:
            db.execute_query(
                '''
                INSERT INTO sources
                (domain, country, article_count, trust_score)
                VALUES (%s, %s, %s, %s)
                ''',
                (
                    domain,
                    random.choice(countries),
                    random.randint(10, 100),
                    random.uniform(0.3, 0.9)
                ),
                fetch=False
            )
        except Exception as e:
            logger.warning(f"Error inserting source with country: {e}")
            db.execute_query(
                '''
                INSERT INTO sources
                (domain, article_count, trust_score)
                VALUES (%s, %s, %s)
                ''',
                (
                    domain,
                    random.randint(10, 100),
                    random.uniform(0.3, 0.9)
                ),
                fetch=False
            )
    
    # Print summary
    article_count = db.execute_query('SELECT COUNT(*) as count FROM articles')[0]['count']
    entity_count = db.execute_query('SELECT COUNT(*) as count FROM entities')[0]['count']
    mention_count = db.execute_query('SELECT COUNT(*) as count FROM article_entities')[0]['count']
    source_count = db.execute_query('SELECT COUNT(*) as count FROM sources')[0]['count']
    
    logger.info(f"Database populated successfully:")
    logger.info(f"- {article_count} articles")
    logger.info(f"- {entity_count} entities")
    logger.info(f"- {mention_count} entity mentions")
    logger.info(f"- {source_count} sources")

if __name__ == '__main__':
    populate_database()
