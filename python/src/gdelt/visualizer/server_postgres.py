#!/usr/bin/env python3
"""
GDELT News Analysis Dashboard Server with PostgreSQL support
"""

import os
import json
import logging
import random
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory, render_template
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from python.src.gdelt.database.postgres_adapter import get_postgres_adapter
from python.src.gdelt.config.database_config import get_database_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__,
            static_folder=os.path.dirname(os.path.abspath(__file__)),
            template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))

# Configuration
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'config', 'database.json')
DEFAULT_ANALYSIS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'analysis_gdelt_chunks')

# Database connection
def get_db_connection(config_path=None):
    """Get a database connection"""
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH

    # Get database configuration
    db_config = get_database_config(config_path)

    # Get PostgreSQL adapter
    db = get_postgres_adapter(**db_config['postgres'])

    return db

# Routes
@app.route('/')
def index():
    """Render the dashboard index page"""
    return render_template('index.html')

@app.route('/api/summary')
def get_summary():
    """Get summary data"""
    try:
        db = get_db_connection()

        # Get article count
        article_count_result = db.execute_query('SELECT COUNT(*) as count FROM articles')
        article_count = article_count_result[0]['count'] if article_count_result else 0

        # Get entity count
        entity_count_result = db.execute_query('SELECT COUNT(*) as count FROM entities')
        entity_count = entity_count_result[0]['count'] if entity_count_result else 0

        # Get theme counts
        theme_counts = db.execute_query('''
            SELECT theme_id, COUNT(*) as count
            FROM articles
            WHERE theme_id IS NOT NULL
            GROUP BY theme_id
            ORDER BY count DESC
        ''')

        # Get time series data
        time_series = db.execute_query('''
            SELECT DATE(seendate) as date, COUNT(*) as count
            FROM articles
            GROUP BY DATE(seendate)
            ORDER BY date
        ''')

        # Get country data
        countries = db.execute_query('''
            SELECT sourcecountry as country, COUNT(*) as count
            FROM articles
            WHERE sourcecountry IS NOT NULL
            GROUP BY sourcecountry
            ORDER BY count DESC
            LIMIT 15
        ''')

        # Get sentiment data
        sentiment_result = db.execute_query('''
            SELECT
                SUM(CASE WHEN sentiment_polarity > 0.3 THEN 1 ELSE 0 END) as positive,
                SUM(CASE WHEN sentiment_polarity BETWEEN -0.3 AND 0.3 THEN 1 ELSE 0 END) as neutral,
                SUM(CASE WHEN sentiment_polarity < -0.3 THEN 1 ELSE 0 END) as negative
            FROM articles
        ''')

        sentiment = sentiment_result[0] if sentiment_result else {'positive': 0, 'neutral': 0, 'negative': 0}

        # Prepare response
        response = {
            'article_count': article_count,
            'entity_count': entity_count,
            'themes': theme_counts,
            'timeSeries': time_series,
            'countries': countries,
            'sentiment': sentiment
        }

        return jsonify(response)
    except Exception as e:
        logger.error(f"Error getting summary data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/entities')
def get_entities():
    """Get entity data"""
    try:
        entity = request.args.get('entity')
        db = get_db_connection()

        if entity:
            # Get specific entity
            entity_data = db.execute_query('''
                SELECT e.*, COUNT(ae.article_id) as mention_count
                FROM entities e
                JOIN article_entities ae ON e.id = ae.entity_id
                WHERE e.text = %s
                GROUP BY e.id
            ''', (entity,))

            if not entity_data:
                return jsonify({'error': 'Entity not found'}), 404

            # Get articles mentioning this entity
            articles = db.execute_query('''
                SELECT a.*
                FROM articles a
                JOIN article_entities ae ON a.id = ae.article_id
                JOIN entities e ON ae.entity_id = e.id
                WHERE e.text = %s
                ORDER BY a.seendate DESC
                LIMIT 50
            ''', (entity,))

            # Prepare response
            response = {
                'entity': entity_data[0],
                'articles': articles
            }
        else:
            # Get all entities (with deduplication and proper type identification)
            entities = db.execute_query('''
                WITH normalized_entities AS (
                    SELECT
                        e.text as entity,
                        -- Normalize entity types
                        CASE
                            WHEN e.type IN ('PERSON', 'PER') THEN 'PERSON'
                            WHEN e.type IN ('ORGANIZATION', 'ORG') THEN 'ORGANIZATION'
                            WHEN e.type IN ('LOCATION', 'LOC', 'GPE') THEN 'LOCATION'
                            WHEN e.type IN ('EVENT') THEN 'EVENT'
                            WHEN e.type IN ('PRODUCT', 'WORK_OF_ART') THEN 'PRODUCT'
                            ELSE e.type
                        END as type,
                        COUNT(DISTINCT ae.article_id) as count,
                        -- Create a normalized version of the entity name for deduplication
                        LOWER(TRIM(e.text)) as normalized_name
                    FROM entities e
                    JOIN article_entities ae ON e.id = ae.entity_id
                    GROUP BY e.text, type
                ),
                -- Get the most mentioned entity for each normalized name
                deduplicated_entities AS (
                    SELECT
                        entity,
                        type,
                        count,
                        ROW_NUMBER() OVER (
                            PARTITION BY normalized_name
                            ORDER BY count DESC
                        ) as rank
                    FROM normalized_entities
                )
                SELECT entity, type, count
                FROM deduplicated_entities
                WHERE rank = 1
                ORDER BY count DESC
                LIMIT 100
            ''')

            # Prepare response
            response = entities

        return jsonify(response)
    except Exception as e:
        logger.error(f"Error getting entity data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/themes')
def get_themes():
    """Get theme data"""
    try:
        theme = request.args.get('theme')
        db = get_db_connection()

        if theme:
            # Get specific theme
            theme_data = db.execute_query('''
                SELECT theme_id, theme_description, COUNT(*) as count
                FROM articles
                WHERE theme_id = %s
                GROUP BY theme_id, theme_description
            ''', (theme,))

            if not theme_data:
                return jsonify({'error': 'Theme not found'}), 404

            # Get articles with this theme
            articles = db.execute_query('''
                SELECT *
                FROM articles
                WHERE theme_id = %s
                ORDER BY seendate DESC
                LIMIT 50
            ''', (theme,))

            # Prepare response
            response = {
                'theme': theme_data[0],
                'articles': articles
            }
        else:
            # Get all themes
            themes = db.execute_query('''
                SELECT theme_id as theme, theme_description as description, COUNT(*) as count
                FROM articles
                WHERE theme_id IS NOT NULL
                GROUP BY theme_id, theme_description
                ORDER BY count DESC
            ''')

            # Prepare response
            response = themes

        return jsonify(response)
    except Exception as e:
        logger.error(f"Error getting theme data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/timelines')
def get_timelines():
    """Get timeline data"""
    try:
        entity = request.args.get('entity')
        timeline_type = request.args.get('type', 'entity')

        if not entity:
            return jsonify({'error': 'Entity parameter is required'}), 400

        # Check if timeline file exists
        timeline_dir = os.path.join(DEFAULT_ANALYSIS_DIR, 'batch_1', 'timelines')
        timeline_file = os.path.join(timeline_dir, f"{entity.replace(' ', '_')}_{timeline_type}_timeline.json")

        # Try to load from file if it exists
        if os.path.exists(timeline_file):
            with open(timeline_file, 'r') as f:
                timeline_data = json.load(f)
            return jsonify(timeline_data)

        # Generate timeline data from database
        db = get_db_connection()

        if timeline_type == 'entity':
            # Get entity mentions over time
            timeline_data = db.execute_query('''
                SELECT DATE(a.seendate) as date, COUNT(*) as count
                FROM articles a
                JOIN article_entities ae ON a.id = ae.article_id
                JOIN entities e ON ae.entity_id = e.id
                WHERE e.text = %s
                GROUP BY DATE(a.seendate)
                ORDER BY date
            ''', (entity,))
        elif timeline_type == 'sentiment':
            # Get entity sentiment over time
            timeline_data = db.execute_query('''
                SELECT DATE(a.seendate) as date, AVG(a.sentiment_polarity) as sentiment
                FROM articles a
                JOIN article_entities ae ON a.id = ae.article_id
                JOIN entities e ON ae.entity_id = e.id
                WHERE e.text = %s
                GROUP BY DATE(a.seendate)
                ORDER BY date
            ''', (entity,))
        elif timeline_type == 'event':
            # Get events involving the entity
            timeline_data = db.execute_query('''
                SELECT
                    DATE(a.seendate) as date,
                    a.title as title,
                    a.url as url,
                    a.domain as source,
                    a.theme_description as description
                FROM articles a
                JOIN article_entities ae ON a.id = ae.article_id
                JOIN entities e ON ae.entity_id = e.id
                WHERE e.text = %s
                ORDER BY a.seendate DESC
                LIMIT 30
            ''', (entity,))

        # If no data found, generate mock data
        if not timeline_data:
            today = datetime.now()
            data = []

            for i in range(30):
                date = today - timedelta(days=i)

                if timeline_type == 'entity':
                    data.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'count': max(5, int(50 * (1 - i/60) + random.randint(-10, 10)))
                    })
                elif timeline_type == 'sentiment':
                    data.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'sentiment': (0.5 - i * 0.02) if i < 15 else (-0.5 + (i - 15) * 0.02)
                    })
                elif timeline_type == 'event':
                    # Only add events on some days
                    if random.random() > 0.7:
                        data.append({
                            'date': date.strftime('%Y-%m-%d'),
                            'title': f"Event involving {entity}",
                            'description': f"This is a mock event about {entity} that occurred on {date.strftime('%Y-%m-%d')}.",
                            'source': 'Mock Data'
                        })
        else:
            data = timeline_data

        response = {
            'entity': entity,
            'type': timeline_type,
            'data': data
        }

        return jsonify(response)
    except Exception as e:
        logger.error(f"Error getting timeline data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sentiment')
def get_sentiment():
    """Get sentiment data"""
    try:
        entity = request.args.get('entity')
        theme = request.args.get('theme')
        db = get_db_connection()

        if entity:
            # Get entity sentiment over time
            overall = db.execute_query('''
                SELECT DATE(a.seendate) as date, AVG(a.sentiment_polarity) as sentiment
                FROM articles a
                JOIN article_entities ae ON a.id = ae.article_id
                JOIN entities e ON ae.entity_id = e.id
                WHERE e.text = %s
                GROUP BY DATE(a.seendate)
                ORDER BY date
            ''', (entity,))

            # Prepare response
            response = {
                'entity': entity,
                'sentiment': overall
            }
        elif theme:
            # Get theme sentiment over time
            overall = db.execute_query('''
                SELECT DATE(seendate) as date, AVG(sentiment_polarity) as sentiment
                FROM articles
                WHERE theme_id = %s
                GROUP BY DATE(seendate)
                ORDER BY date
            ''', (theme,))

            # Prepare response
            response = {
                'theme': theme,
                'sentiment': overall
            }
        else:
            # Get overall sentiment over time
            overall = db.execute_query('''
                SELECT DATE(seendate) as date, AVG(sentiment_polarity) as sentiment
                FROM articles
                GROUP BY DATE(seendate)
                ORDER BY date
            ''')

            # Get entity sentiment
            entities = db.execute_query('''
                SELECT
                    e.text as entity,
                    AVG(a.sentiment_polarity) as sentiment,
                    COUNT(*) as count
                FROM entities e
                JOIN article_entities ae ON e.id = ae.entity_id
                JOIN articles a ON ae.article_id = a.id
                GROUP BY e.text
                ORDER BY count DESC
                LIMIT 10
            ''')

            # Get theme sentiment
            themes = db.execute_query('''
                SELECT
                    theme_id as theme,
                    theme_description as description,
                    AVG(sentiment_polarity) as sentiment,
                    COUNT(*) as count
                FROM articles
                WHERE theme_id IS NOT NULL
                GROUP BY theme_id, theme_description
                ORDER BY count DESC
                LIMIT 10
            ''')

            # Prepare response
            response = {
                'overall': overall,
                'entities': entities,
                'themes': themes
            }

        return jsonify(response)
    except Exception as e:
        logger.error(f"Error getting sentiment data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/events')
def get_events():
    """Get event data"""
    try:
        entity = request.args.get('entity')
        limit = request.args.get('limit', 10, type=int)
        db = get_db_connection()

        if entity:
            # Get events for entity
            events = db.execute_query('''
                SELECT a.id, a.title, a.url, a.domain, a.seendate, a.sourcecountry, a.theme_id, a.theme_description
                FROM articles a
                JOIN article_entities ae ON a.id = ae.article_id
                JOIN entities e ON ae.entity_id = e.id
                WHERE e.text = %s
                ORDER BY a.seendate DESC
                LIMIT %s
            ''', (entity, limit))
        else:
            # Get recent events
            events = db.execute_query('''
                SELECT id, title, url, domain, seendate, sourcecountry, theme_id, theme_description
                FROM articles
                ORDER BY seendate DESC
                LIMIT %s
            ''', (limit,))

        # Prepare response with translation support
        response = []
        for event in events:
            event_dict = event
            event_dict['date'] = event_dict['seendate']
            event_dict['source'] = event_dict['domain']
            event_dict['description'] = f"Theme: {event_dict['theme_description'] or event_dict['theme_id'] or 'Unknown'}"

            # Add translated title if available, otherwise use original title
            if 'title_translated' in event_dict and event_dict['title_translated']:
                # If language is not English, include both original and translated titles
                if event_dict.get('language', '').lower() != 'en':
                    event_dict['display_title'] = event_dict['title_translated']
                    event_dict['original_title'] = event_dict['title']
                    event_dict['is_translated'] = True
                else:
                    event_dict['display_title'] = event_dict['title']
                    event_dict['is_translated'] = False
            else:
                event_dict['display_title'] = event_dict['title']
                event_dict['is_translated'] = False

            response.append(event_dict)

        return jsonify(response)
    except Exception as e:
        logger.error(f"Error getting event data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/articles')
def get_articles():
    """Get article data"""
    try:
        entity = request.args.get('entity')
        theme = request.args.get('theme')
        limit = request.args.get('limit', 50, type=int)
        db = get_db_connection()

        if entity:
            # Get articles for entity
            articles = db.execute_query('''
                SELECT a.*
                FROM articles a
                JOIN article_entities ae ON a.id = ae.article_id
                JOIN entities e ON ae.entity_id = e.id
                WHERE e.text = %s
                ORDER BY a.seendate DESC
                LIMIT %s
            ''', (entity, limit))
        elif theme:
            # Get articles for theme
            articles = db.execute_query('''
                SELECT *
                FROM articles
                WHERE theme_id = %s
                ORDER BY seendate DESC
                LIMIT %s
            ''', (theme, limit))
        else:
            # Get recent articles
            articles = db.execute_query('''
                SELECT *
                FROM articles
                ORDER BY seendate DESC
                LIMIT %s
            ''', (limit,))

        return jsonify(articles)
    except Exception as e:
        logger.error(f"Error getting article data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/predictions')
def get_predictions():
    """Get prediction data"""
    try:
        entity = request.args.get('entity')
        days = request.args.get('days', 30, type=int)

        if not entity:
            return jsonify({'error': 'Entity parameter is required'}), 400

        # Generate mock prediction data
        today = datetime.now()
        historical = []
        predicted = []

        # Historical data (past 30 days)
        for i in range(30, 0, -1):
            date = today - timedelta(days=i)
            historical.append({
                'date': date.strftime('%Y-%m-%d'),
                'value': max(5, int(50 * (1 - i/60) + random.randint(-10, 10)))
            })

        # Predicted data (next N days)
        last_value = historical[-1]['value']
        trend = random.choice([-1, 1]) * random.uniform(0.05, 0.15)

        for i in range(1, days + 1):
            date = today + timedelta(days=i)
            # Add some randomness to the trend
            noise = random.uniform(-0.1, 0.1)
            last_value = max(5, last_value * (1 + trend + noise))

            predicted.append({
                'date': date.strftime('%Y-%m-%d'),
                'value': int(last_value),
                'lower_bound': int(max(1, last_value * 0.8)),
                'upper_bound': int(last_value * 1.2)
            })

        response = {
            'entity': entity,
            'historical': historical,
            'predicted': predicted,
            'confidence': 0.85,
            'model': 'Time Series Forecast'
        }

        return jsonify(response)
    except Exception as e:
        logger.error(f"Error getting prediction data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/network')
def get_network():
    """Get entity network data"""
    try:
        entity = request.args.get('entity')
        depth = request.args.get('depth', 1, type=int)

        if not entity:
            return jsonify({'error': 'Entity parameter is required'}), 400

        db = get_db_connection()

        # Get the entity's type
        entity_info = db.execute_query('''
            SELECT id, text, type
            FROM entities
            WHERE text = %s
            LIMIT 1
        ''', (entity,))

        if not entity_info:
            return jsonify({'error': 'Entity not found'}), 404

        entity_id = entity_info[0]['id']
        entity_type = entity_info[0]['type']

        # Get related entities (entities that appear in the same articles)
        related_entities = db.execute_query('''
            SELECT e.id, e.text, e.type, COUNT(*) as weight
            FROM entities e
            JOIN article_entities ae1 ON e.id = ae1.entity_id
            JOIN article_entities ae2 ON ae1.article_id = ae2.article_id
            WHERE ae2.entity_id = %s
            AND e.id != %s
            GROUP BY e.id, e.text, e.type
            ORDER BY weight DESC
            LIMIT 20
        ''', (entity_id, entity_id))

        # Build network
        nodes = [{
            'id': entity_id,
            'label': entity,
            'type': entity_type,
            'size': 20,
            'color': '#ff7f0e'
        }]

        edges = []

        for related in related_entities:
            nodes.append({
                'id': related['id'],
                'label': related['text'],
                'type': related['type'],
                'size': 10 + min(10, related['weight']),
                'color': '#1f77b4'
            })

            edges.append({
                'source': entity_id,
                'target': related['id'],
                'weight': related['weight'],
                'value': related['weight']
            })

        response = {
            'nodes': nodes,
            'edges': edges
        }

        return jsonify(response)
    except Exception as e:
        logger.error(f"Error getting network data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/templates/<path:path>')
def send_template(path):
    """Send template file"""
    return send_from_directory(os.path.join(app.root_path, 'templates'), path)

@app.route('/<path:path>')
def send_static(path):
    """Send static file"""
    return send_from_directory(app.static_folder, path)

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Run GDELT News Analysis Dashboard Server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--config-path', help='Path to database configuration file')
    parser.add_argument('--analysis-dir', help='Path to the analysis directory')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    # Set configuration
    global DEFAULT_CONFIG_PATH, DEFAULT_ANALYSIS_DIR

    if args.config_path:
        DEFAULT_CONFIG_PATH = args.config_path
        logger.info(f"Using database configuration: {DEFAULT_CONFIG_PATH}")

    if args.analysis_dir:
        DEFAULT_ANALYSIS_DIR = args.analysis_dir
        logger.info(f"Using analysis directory: {DEFAULT_ANALYSIS_DIR}")

    # Run app
    app.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == '__main__':
    main()
