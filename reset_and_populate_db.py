#!/usr/bin/env python3
"""
Reset and populate PostgreSQL database with sample data
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

def create_sample_data(db, num_articles=100):
    """Create sample data"""
    # Sample data
    domains = ['cnn.com', 'bbc.com', 'reuters.com', 'nytimes.com', 'washingtonpost.com']
    countries = ['US', 'GB', 'FR', 'DE', 'JP', 'CN', 'RU', 'IN', 'BR', 'ZA']
    themes = [
        ('ECON', 'Economy'),
        ('POL', 'Politics'),
        ('ENV', 'Environment'),
        ('TECH', 'Technology'),
        ('HEALTH', 'Health'),
        ('WAR', 'War and Conflict')
    ]
    person_entities = ['Joe Biden', 'Vladimir Putin', 'Xi Jinping', 'Emmanuel Macron', 'Olaf Scholz']
    org_entities = ['United Nations', 'World Health Organization', 'Google', 'Apple', 'Microsoft']
    loc_entities = ['United States', 'Russia', 'China', 'France', 'Germany']

    # Create articles
    logger.info(f"Creating {num_articles} sample articles...")
    article_ids = []
    for i in range(num_articles):
        # Generate random date within the last 30 days
        days_ago = random.randint(0, 30)
        article_date = datetime.now() - timedelta(days=days_ago)

        # Select random theme
        theme = random.choice(themes)

        # Insert article
        try:
            result = db.execute_query(
                '''
                INSERT INTO articles
                (url, title, seendate, language, domain, sourcecountry, theme_id, theme_description,
                 fetch_date, trust_score, sentiment_polarity, content_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                ''',
                (
                    f'https://{random.choice(domains)}/article_{i}',
                    f'Sample Article {i}: {theme[1]} News',
                    article_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'en',
                    random.choice(domains),
                    random.choice(countries),
                    theme[0],
                    theme[1],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    random.uniform(0.3, 0.9),
                    random.uniform(-0.8, 0.8),
                    f'hash_{i}'
                )
            )

            if result:
                article_ids.append(result[0]['id'])
        except Exception as e:
            logger.warning(f"Error inserting article {i}: {e}")

    # Create entities
    logger.info("Creating sample entities...")
    entity_ids = {}

    # Add person entities
    for entity in person_entities:
        result = db.execute_query(
            '''
            INSERT INTO entities
            (text, type, count, num_sources, source_diversity, trust_score)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            ''',
            (
                entity,
                'PERSON',
                random.randint(5, 50),
                random.randint(1, 5),
                random.uniform(0.1, 0.9),
                random.uniform(0.3, 0.9)
            )
        )
        if result:
            entity_ids[entity] = result[0]['id']

    # Add organization entities
    for entity in org_entities:
        result = db.execute_query(
            '''
            INSERT INTO entities
            (text, type, count, num_sources, source_diversity, trust_score)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            ''',
            (
                entity,
                'ORGANIZATION',
                random.randint(5, 50),
                random.randint(1, 5),
                random.uniform(0.1, 0.9),
                random.uniform(0.3, 0.9)
            )
        )
        if result:
            entity_ids[entity] = result[0]['id']

    # Add location entities
    for entity in loc_entities:
        result = db.execute_query(
            '''
            INSERT INTO entities
            (text, type, count, num_sources, source_diversity, trust_score)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            ''',
            (
                entity,
                'LOCATION',
                random.randint(5, 50),
                random.randint(1, 5),
                random.uniform(0.1, 0.9),
                random.uniform(0.3, 0.9)
            )
        )
        if result:
            entity_ids[entity] = result[0]['id']

    # Create article-entity relationships
    logger.info("Creating article-entity relationships...")
    for article_id in article_ids:
        # Each article mentions 1-5 random entities
        num_mentions = random.randint(1, 5)
        entities = random.sample(list(entity_ids.keys()), min(num_mentions, len(entity_ids)))

        for entity in entities:
            try:
                db.execute_query(
                    '''
                    INSERT INTO article_entities
                    (article_id, entity_id, context)
                    VALUES (%s, %s, %s)
                    ''',
                    (
                        article_id,
                        entity_ids[entity],
                        f'Context for {entity} in article {article_id}'
                    ),
                    fetch=False
                )
            except Exception as e:
                logger.warning(f"Error creating relationship between article {article_id} and entity {entity}: {e}")

    # Create sources
    logger.info("Creating sample sources...")
    for domain in domains:
        try:
            # Try to add the country column if it doesn't exist
            db.execute_query('ALTER TABLE sources ADD COLUMN IF NOT EXISTS country TEXT;', fetch=False)

            # Insert with country
            db.execute_query(
                '''
                INSERT INTO sources
                (domain, country, article_count, trust_score)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (domain) DO UPDATE
                SET country = EXCLUDED.country,
                    article_count = EXCLUDED.article_count,
                    trust_score = EXCLUDED.trust_score
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
            logger.warning(f"Error adding country column or inserting with country: {e}")

            # Insert without country
            db.execute_query(
                '''
                INSERT INTO sources
                (domain, article_count, trust_score)
                VALUES (%s, %s, %s)
                ON CONFLICT (domain) DO UPDATE
                SET article_count = EXCLUDED.article_count,
                    trust_score = EXCLUDED.trust_score
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

    logger.info(f"Sample data created successfully:")
    logger.info(f"- {article_count} articles")
    logger.info(f"- {entity_count} entities")
    logger.info(f"- {mention_count} entity mentions")
    logger.info(f"- {source_count} sources")

def main():
    """Main function"""
    # Reset database
    db = reset_database()

    # Create sample data
    create_sample_data(db, num_articles=200)

    logger.info("Database reset and populated successfully")

if __name__ == '__main__':
    main()
