#!/usr/bin/env python3
"""
Initialize PostgreSQL database with sample data
"""

import os
import sys
import logging
import pandas as pd
import random
from datetime import datetime, timedelta
from python.src.gdelt.database.postgres_adapter import get_postgres_adapter
from python.src.gdelt.config.database_config import get_database_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_sample_articles(num_articles=100):
    """Generate sample articles"""
    articles = []

    # Define some sample data
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

    # Generate articles
    for i in range(num_articles):
        # Generate random date within the last 30 days
        days_ago = random.randint(0, 30)
        article_date = datetime.now() - timedelta(days=days_ago)

        # Select random theme
        theme = random.choice(themes)

        # Generate article
        article = {
            'url': f'https://{random.choice(domains)}/article_{i}',
            'title': f'Sample Article {i}: {theme[1]} News',
            'seendate': article_date.strftime('%Y-%m-%d %H:%M:%S'),
            'language': 'en',
            'domain': random.choice(domains),
            'sourcecountry': random.choice(countries),
            'theme_id': theme[0],
            'theme_description': theme[1],
            'fetch_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'trust_score': random.uniform(0.3, 0.9),
            'sentiment_polarity': random.uniform(-0.8, 0.8),
            'content_hash': f'hash_{i}'
        }

        articles.append(article)

    return articles

def generate_sample_entities(articles, num_entities=50):
    """Generate sample entities"""
    entities = []
    entity_mentions = []

    # Define some sample entities
    person_entities = ['Joe Biden', 'Vladimir Putin', 'Xi Jinping', 'Emmanuel Macron', 'Olaf Scholz']
    org_entities = ['United Nations', 'World Health Organization', 'Google', 'Apple', 'Microsoft']
    loc_entities = ['United States', 'Russia', 'China', 'France', 'Germany']

    all_entities = []
    for entity in person_entities:
        all_entities.append((entity, 'PERSON'))
    for entity in org_entities:
        all_entities.append((entity, 'ORGANIZATION'))
    for entity in loc_entities:
        all_entities.append((entity, 'LOCATION'))

    # Generate additional random entities
    for i in range(num_entities - len(all_entities)):
        entity_type = random.choice(['PERSON', 'ORGANIZATION', 'LOCATION'])
        entity_name = f'Entity {i} ({entity_type})'
        all_entities.append((entity_name, entity_type))

    # Generate entity mentions
    for article in articles:
        # Each article mentions 1-5 random entities
        num_mentions = random.randint(1, 5)
        for _ in range(num_mentions):
            entity_text, entity_type = random.choice(all_entities)

            # Add entity to list if not already present
            entity_exists = False
            for entity in entities:
                if entity['text'] == entity_text and entity['type'] == entity_type:
                    entity_exists = True
                    break

            if not entity_exists:
                entity = {
                    'text': entity_text,
                    'type': entity_type,
                    'count': 1,
                    'num_sources': 1,
                    'source_diversity': random.uniform(0.1, 0.9),
                    'trust_score': random.uniform(0.3, 0.9)
                }
                entities.append(entity)

            # Add entity mention
            mention = {
                'article_url': article['url'],
                'text': entity_text,
                'type': entity_type,
                'context': f'Context for {entity_text} in article {article["url"]}'
            }
            entity_mentions.append(mention)

    return entities, entity_mentions

def insert_sample_data(db, articles, entities, entity_mentions):
    """Insert sample data into database"""
    # Insert articles
    for article in articles:
        db.execute_query(
            '''
            INSERT INTO articles
            (url, title, seendate, language, domain, sourcecountry, theme_id, theme_description,
             fetch_date, trust_score, sentiment_polarity, content_hash)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO UPDATE
            SET title = EXCLUDED.title,
                seendate = EXCLUDED.seendate,
                language = EXCLUDED.language,
                domain = EXCLUDED.domain,
                sourcecountry = EXCLUDED.sourcecountry,
                theme_id = EXCLUDED.theme_id,
                theme_description = EXCLUDED.theme_description,
                fetch_date = EXCLUDED.fetch_date,
                trust_score = EXCLUDED.trust_score,
                sentiment_polarity = EXCLUDED.sentiment_polarity,
                content_hash = EXCLUDED.content_hash
            RETURNING id
            ''',
            (
                article['url'],
                article['title'],
                article['seendate'],
                article['language'],
                article['domain'],
                article['sourcecountry'],
                article['theme_id'],
                article['theme_description'],
                article['fetch_date'],
                article['trust_score'],
                article['sentiment_polarity'],
                article['content_hash']
            )
        )

    # Get article IDs
    article_ids = {}
    for article in articles:
        result = db.execute_query(
            'SELECT id FROM articles WHERE url = %s',
            (article['url'],)
        )
        if result:
            article_ids[article['url']] = result[0]['id']

    # Insert entities
    for entity in entities:
        result = db.execute_query(
            '''
            INSERT INTO entities
            (text, type, count, num_sources, source_diversity, trust_score)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (text, type) DO UPDATE
            SET count = EXCLUDED.count,
                num_sources = EXCLUDED.num_sources,
                source_diversity = EXCLUDED.source_diversity,
                trust_score = EXCLUDED.trust_score
            RETURNING id
            ''',
            (
                entity['text'],
                entity['type'],
                entity['count'],
                entity['num_sources'],
                entity['source_diversity'],
                entity['trust_score']
            )
        )

    # Get entity IDs
    entity_ids = {}
    for entity in entities:
        result = db.execute_query(
            'SELECT id FROM entities WHERE text = %s AND type = %s',
            (entity['text'], entity['type'])
        )
        if result:
            entity_ids[(entity['text'], entity['type'])] = result[0]['id']

    # Insert article-entity relationships
    for mention in entity_mentions:
        article_id = article_ids.get(mention['article_url'])
        entity_id = entity_ids.get((mention['text'], mention['type']))

        if article_id and entity_id:
            db.execute_query(
                '''
                INSERT INTO article_entities
                (article_id, entity_id, context)
                VALUES (%s, %s, %s)
                ON CONFLICT (article_id, entity_id) DO UPDATE
                SET context = EXCLUDED.context
                ''',
                (
                    article_id,
                    entity_id,
                    mention['context']
                ),
                fetch=False
            )

    # Update source statistics
    for domain, group in pd.DataFrame(articles).groupby('domain'):
        if not domain or pd.isna(domain):
            continue

        try:
            # Try with country column
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
                    group.iloc[0]['sourcecountry'],
                    len(group),
                    group['trust_score'].mean()
                ),
                fetch=False
            )
        except Exception as e:
            # Fall back to version without country column
            logger.warning(f"Error inserting source with country: {e}")
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
                    len(group),
                    group['trust_score'].mean()
                ),
                fetch=False
            )

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Initialize PostgreSQL database with sample data')
    parser.add_argument('--config-path', type=str, default='config/database.json',
                        help='Path to database configuration file')
    parser.add_argument('--num-articles', type=int, default=100,
                        help='Number of sample articles to generate')
    parser.add_argument('--num-entities', type=int, default=50,
                        help='Number of sample entities to generate')
    parser.add_argument('--reset', action='store_true',
                        help='Reset database before inserting sample data')
    args = parser.parse_args()

    # Get database configuration
    db_config = get_database_config(args.config_path)

    # Get PostgreSQL adapter
    db = get_postgres_adapter(**db_config['postgres'])

    # Reset database if requested
    if args.reset:
        logger.info("Resetting database...")
        db.reset_database()

    # Make sure the sources table has the country column
    try:
        logger.info("Ensuring sources table has country column...")
        db.execute_query('ALTER TABLE sources ADD COLUMN IF NOT EXISTS country TEXT;', fetch=False)
    except Exception as e:
        logger.warning(f"Error adding country column: {e}")

    # Generate sample data
    logger.info(f"Generating {args.num_articles} sample articles...")
    articles = generate_sample_articles(args.num_articles)

    logger.info(f"Generating {args.num_entities} sample entities...")
    entities, entity_mentions = generate_sample_entities(articles, args.num_entities)

    # Insert sample data
    logger.info("Inserting sample data into database...")
    insert_sample_data(db, articles, entities, entity_mentions)

    # Print summary
    article_count = db.execute_query('SELECT COUNT(*) as count FROM articles')[0]['count']
    entity_count = db.execute_query('SELECT COUNT(*) as count FROM entities')[0]['count']
    mention_count = db.execute_query('SELECT COUNT(*) as count FROM article_entities')[0]['count']
    source_count = db.execute_query('SELECT COUNT(*) as count FROM sources')[0]['count']

    logger.info(f"Sample data inserted successfully:")
    logger.info(f"- {article_count} articles")
    logger.info(f"- {entity_count} entities")
    logger.info(f"- {mention_count} entity mentions")
    logger.info(f"- {source_count} sources")

if __name__ == '__main__':
    main()
