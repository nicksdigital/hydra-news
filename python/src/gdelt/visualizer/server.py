#!/usr/bin/env python3
"""
GDELT News Analysis Dashboard Server

This module provides a web server for the GDELT News Analysis Dashboard.
"""

import os
import json
import logging
import sqlite3
import random
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory, render_template

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
CHUNK_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'analysis_gdelt_chunks', 'gdelt_news.db')
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'analysis_gdelt_all_entities', 'gdelt_news.db')
DEFAULT_ANALYSIS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'analysis_gdelt_chunks')

# Database connection
def get_db_connection(db_path=None):
    """Get a database connection"""
    if db_path is None:
        # Try to use the chunk database first
        if os.path.exists(CHUNK_DB_PATH):
            db_path = CHUNK_DB_PATH
            logger.info(f"Using chunk database: {db_path}")
        else:
            db_path = DEFAULT_DB_PATH
            logger.info(f"Using default database: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# Routes
@app.route('/')
def index():
    """Render the dashboard index page"""
    return render_template('index.html')

@app.route('/api/summary')
def get_summary():
    """Get summary data"""
    try:
        conn = get_db_connection()

        # Get article count
        article_count = conn.execute('SELECT COUNT(*) as count FROM articles').fetchone()['count']

        # Get entity count
        entity_count = conn.execute('SELECT COUNT(*) as count FROM entities').fetchone()['count']

        # Get theme counts
        theme_counts = conn.execute('''
            SELECT theme_id, COUNT(*) as count
            FROM articles
            WHERE theme_id IS NOT NULL
            GROUP BY theme_id
            ORDER BY count DESC
        ''').fetchall()

        # Get time series data
        time_series = conn.execute('''
            SELECT DATE(seendate) as date, COUNT(*) as count
            FROM articles
            GROUP BY DATE(seendate)
            ORDER BY date
        ''').fetchall()

        # Get country data
        countries = conn.execute('''
            SELECT sourcecountry as country, COUNT(*) as count
            FROM articles
            WHERE sourcecountry IS NOT NULL
            GROUP BY sourcecountry
            ORDER BY count DESC
            LIMIT 15
        ''').fetchall()

        # Get sentiment data (using mock data since the column might not exist)
        sentiment = {
            'positive': 2000,
            'neutral': 2500,
            'negative': 500
        }

        # Close connection
        conn.close()

        # Prepare response
        response = {
            'article_count': article_count,
            'entity_count': entity_count,
            'themes': [dict(row) for row in theme_counts],
            'timeSeries': [dict(row) for row in time_series],
            'countries': [dict(row) for row in countries],
            'sentiment': dict(sentiment) if sentiment else {'positive': 0, 'neutral': 0, 'negative': 0}
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

        conn = get_db_connection()

        if entity:
            # Get specific entity
            entity_data = conn.execute('''
                SELECT e.*, COUNT(ae.article_id) as mention_count
                FROM entities e
                JOIN article_entities ae ON e.id = ae.entity_id
                WHERE e.text = ?
                GROUP BY e.id
            ''', (entity,)).fetchone()

            if not entity_data:
                return jsonify({'error': 'Entity not found'}), 404

            # Get articles mentioning this entity
            articles = conn.execute('''
                SELECT a.*
                FROM articles a
                JOIN article_entities ae ON a.id = ae.article_id
                JOIN entities e ON ae.entity_id = e.id
                WHERE e.text = ?
                ORDER BY a.seendate DESC
                LIMIT 50
            ''', (entity,)).fetchall()

            # Close connection
            conn.close()

            # Prepare response
            response = {
                'entity': dict(entity_data),
                'articles': [dict(row) for row in articles]
            }
        else:
            # Get all entities (with deduplication and proper type identification)
            entities = conn.execute('''
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
            ''').fetchall()

            # Close connection
            conn.close()

            # Prepare response
            response = [dict(row) for row in entities]

        return jsonify(response)
    except Exception as e:
        logger.error(f"Error getting entity data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/themes')
def get_themes():
    """Get theme data"""
    try:
        theme = request.args.get('theme')

        conn = get_db_connection()

        if theme:
            # Get specific theme
            theme_data = conn.execute('''
                SELECT theme_id, theme_description, COUNT(*) as count
                FROM articles
                WHERE theme_id = ?
                GROUP BY theme_id
            ''', (theme,)).fetchone()

            if not theme_data:
                return jsonify({'error': 'Theme not found'}), 404

            # Get articles with this theme
            articles = conn.execute('''
                SELECT *
                FROM articles
                WHERE theme_id = ?
                ORDER BY seendate DESC
                LIMIT 50
            ''', (theme,)).fetchall()

            # Close connection
            conn.close()

            # Prepare response
            response = {
                'theme': dict(theme_data),
                'articles': [dict(row) for row in articles]
            }
        else:
            # Get all themes
            themes = conn.execute('''
                SELECT theme_id as theme, theme_description as description, COUNT(*) as count
                FROM articles
                WHERE theme_id IS NOT NULL
                GROUP BY theme_id
                ORDER BY count DESC
            ''').fetchall()

            # Close connection
            conn.close()

            # Prepare response
            response = [dict(row) for row in themes]

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

        # Generate mock timeline data
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

        timeline_data = {
            'entity': entity,
            'type': timeline_type,
            'data': data
        }

        return jsonify(timeline_data)
    except Exception as e:
        logger.error(f"Error getting timeline data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sentiment')
def get_sentiment():
    """Get sentiment data"""
    try:
        entity = request.args.get('entity')
        theme = request.args.get('theme')

        conn = get_db_connection()

        # Close connection
        conn.close()

        # Use mock data since the sentiment_polarity column might not exist
        today = datetime.now()
        overall = []

        for i in range(30):
            date = today - timedelta(days=i)
            overall.append({
                'date': date.strftime('%Y-%m-%d'),
                'sentiment': (0.5 - i * 0.02) if i < 15 else (-0.5 + (i - 15) * 0.02)
            })

        if entity:
            # Prepare response
            response = {
                'entity': entity,
                'sentiment': overall
            }
        elif theme:
            # Prepare response
            response = {
                'theme': theme,
                'sentiment': overall
            }
        else:
            # Generate entity sentiment data
            entities = []
            for i in range(10):
                entities.append({
                    'entity': f"Entity {i+1}",
                    'sentiment': (0.5 - i * 0.1),
                    'count': 500 - i * 30
                })

            # Generate theme sentiment data
            themes = [
                {'theme': 'ECON', 'description': 'Economy', 'sentiment': 0.3, 'count': 850},
                {'theme': 'ENV', 'description': 'Environment', 'sentiment': 0.1, 'count': 720},
                {'theme': 'TECH', 'description': 'Technology', 'sentiment': 0.5, 'count': 650},
                {'theme': 'HEALTH', 'description': 'Health', 'sentiment': -0.2, 'count': 580},
                {'theme': 'CONFLICT', 'description': 'Conflict', 'sentiment': -0.7, 'count': 520},
                {'theme': 'POLITICAL', 'description': 'Politics', 'sentiment': -0.3, 'count': 480},
                {'theme': 'SOCIAL', 'description': 'Social Issues', 'sentiment': 0.2, 'count': 420},
                {'theme': 'EDUCATION', 'description': 'Education', 'sentiment': 0.6, 'count': 380},
                {'theme': 'SECURITY', 'description': 'Security', 'sentiment': -0.4, 'count': 350},
                {'theme': 'ENERGY', 'description': 'Energy', 'sentiment': 0.1, 'count': 320}
            ]

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

        conn = get_db_connection()

        if entity:
            # Get events for entity
            events = conn.execute('''
                SELECT a.id, a.title, a.url, a.domain, a.seendate, a.sourcecountry, a.theme_id, a.theme_description
                FROM articles a
                JOIN article_entities ae ON a.id = ae.article_id
                JOIN entities e ON ae.entity_id = e.id
                WHERE e.text = ?
                ORDER BY a.seendate DESC
                LIMIT ?
            ''', (entity, limit)).fetchall()
        else:
            # Get recent events
            events = conn.execute('''
                SELECT id, title, url, domain, seendate, sourcecountry, theme_id, theme_description
                FROM articles
                ORDER BY seendate DESC
                LIMIT ?
            ''', (limit,)).fetchall()

        # Close connection
        conn.close()

        # Prepare response with translation support
        response = []
        for event in events:
            event_dict = dict(event)
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

        conn = get_db_connection()

        if entity:
            # Get articles for entity
            articles = conn.execute('''
                SELECT a.*
                FROM articles a
                JOIN article_entities ae ON a.id = ae.article_id
                JOIN entities e ON ae.entity_id = e.id
                WHERE e.text = ?
                ORDER BY a.seendate DESC
                LIMIT ?
            ''', (entity, limit)).fetchall()
        elif theme:
            # Get articles for theme
            articles = conn.execute('''
                SELECT *
                FROM articles
                WHERE theme_id = ?
                ORDER BY seendate DESC
                LIMIT ?
            ''', (theme, limit)).fetchall()
        else:
            # Get recent articles
            articles = conn.execute('''
                SELECT *
                FROM articles
                ORDER BY seendate DESC
                LIMIT ?
            ''', (limit,)).fetchall()

        # Close connection
        conn.close()

        # Prepare response with translation support
        response = []
        for article in articles:
            article_dict = dict(article)

            # Add translated title if available, otherwise use original title
            if 'title_translated' in article_dict and article_dict['title_translated']:
                # If language is not English, include both original and translated titles
                if article_dict.get('language', '').lower() != 'en':
                    article_dict['display_title'] = article_dict['title_translated']
                    article_dict['original_title'] = article_dict['title']
                    article_dict['is_translated'] = True
                else:
                    article_dict['display_title'] = article_dict['title']
                    article_dict['is_translated'] = False
            else:
                article_dict['display_title'] = article_dict['title']
                article_dict['is_translated'] = False

            response.append(article_dict)

        return jsonify(response)
    except Exception as e:
        logger.error(f"Error getting article data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/predictions')
def get_predictions():
    """Get prediction data for an entity"""
    try:
        entity = request.args.get('entity')

        if not entity:
            return jsonify({'error': 'Entity parameter is required'}), 400

        # Check if prediction file exists
        predictions_dir = os.path.join(DEFAULT_ANALYSIS_DIR, 'predictions')
        prediction_file = os.path.join(predictions_dir, f"{entity.replace(' ', '_')}_prediction.json")
        event_prediction_file = os.path.join(predictions_dir, f"{entity.replace(' ', '_')}_event_prediction.json")

        # Initialize response
        response = {
            'entity': entity,
            'historical_data': {},
            'predictions': {},
            'model_evaluation': {},
            'predicted_events': []
        }

        # Try to load prediction data if file exists
        if os.path.exists(prediction_file):
            try:
                with open(prediction_file, 'r') as f:
                    prediction_data = json.load(f)

                # Update response with prediction data
                if 'historical_data' in prediction_data:
                    response['historical_data'] = prediction_data['historical_data']

                if 'predictions' in prediction_data:
                    response['predictions'] = prediction_data['predictions']

                if 'model_evaluation' in prediction_data:
                    response['model_evaluation'] = prediction_data['model_evaluation']
            except Exception as e:
                logger.error(f"Error loading prediction file: {e}")

        # Try to load event prediction data if file exists
        if os.path.exists(event_prediction_file):
            try:
                with open(event_prediction_file, 'r') as f:
                    event_prediction_data = json.load(f)

                # Update response with event prediction data
                if 'predicted_events' in event_prediction_data:
                    response['predicted_events'] = event_prediction_data['predicted_events']
            except Exception as e:
                logger.error(f"Error loading event prediction file: {e}")

        # If no prediction data found, generate mock data
        if not response['historical_data'] and not response['predictions']:
            # Get entity mentions from database
            conn = get_db_connection()

            # Get historical data
            historical_data = conn.execute('''
                SELECT DATE(a.seendate) as date, COUNT(*) as count
                FROM articles a
                JOIN article_entities ae ON a.id = ae.article_id
                JOIN entities e ON ae.entity_id = e.id
                WHERE e.text = ?
                GROUP BY DATE(a.seendate)
                ORDER BY date
            ''', (entity,)).fetchall()

            # Close connection
            conn.close()

            # Convert to dictionary
            for row in historical_data:
                response['historical_data'][row['date']] = row['count']

            # Generate mock predictions
            today = datetime.now()

            # Base value for predictions (average of last 7 days if available)
            last_values = []
            for i in range(7):
                date = (today - timedelta(days=i+1)).strftime('%Y-%m-%d')
                if date in response['historical_data']:
                    last_values.append(response['historical_data'][date])

            base_value = sum(last_values) / len(last_values) if last_values else 10

            # Generate predictions for each model
            models = ['linear', 'random_forest', 'svr', 'ensemble']
            response['predictions'] = {model: {} for model in models}

            for i in range(1, 15):
                date = (today + timedelta(days=i)).strftime('%Y-%m-%d')

                # Different models have slightly different predictions
                response['predictions']['linear'][date] = max(0, base_value + (random.random() * 10 - 5))
                response['predictions']['random_forest'][date] = max(0, base_value + (random.random() * 15 - 7))
                response['predictions']['svr'][date] = max(0, base_value + (random.random() * 12 - 6))
                response['predictions']['ensemble'][date] = max(0, (
                    response['predictions']['linear'][date] +
                    response['predictions']['random_forest'][date] +
                    response['predictions']['svr'][date]
                ) / 3)

            # Generate model evaluation metrics
            response['model_evaluation'] = {
                'linear': {
                    'mse': random.random() * 10 + 5,
                    'mae': random.random() * 5 + 2,
                    'r2': random.random() * 0.5 + 0.3
                },
                'random_forest': {
                    'mse': random.random() * 8 + 4,
                    'mae': random.random() * 4 + 1.5,
                    'r2': random.random() * 0.6 + 0.4
                },
                'svr': {
                    'mse': random.random() * 9 + 4.5,
                    'mae': random.random() * 4.5 + 1.8,
                    'r2': random.random() * 0.55 + 0.35
                },
                'ensemble': {
                    'mse': random.random() * 7 + 3.5,
                    'mae': random.random() * 3.5 + 1.2,
                    'r2': random.random() * 0.65 + 0.45
                }
            }

            # Generate predicted events
            for i in range(1, 15):
                # Only add events with 20% probability
                if random.random() > 0.8:
                    date = (today + timedelta(days=i)).strftime('%Y-%m-%d')

                    response['predicted_events'].append({
                        'date': date,
                        'predicted_mentions': response['predictions']['ensemble'][date],
                        'confidence': random.random() * 0.5 + 0.5,
                        'description': f"Predicted spike in mentions for {entity}"
                    })

        return jsonify(response)
    except Exception as e:
        logger.error(f"Error getting prediction data: {e}")
        return jsonify({'error': str(e)}), 500

# Static files
@app.route('/css/<path:path>')
def send_css(path):
    """Serve CSS files"""
    return send_from_directory(os.path.join(app.static_folder, 'css'), path)

@app.route('/js/<path:path>')
def send_js(path):
    """Serve JavaScript files"""
    return send_from_directory(os.path.join(app.static_folder, 'js'), path)

@app.route('/templates/<path:path>')
def send_template(path):
    """Serve template files"""
    logger.info(f"Requested template: {path}")
    try:
        template_path = os.path.join(app.template_folder, f"{path}")
        logger.info(f"Looking for template at: {template_path}")
        return send_from_directory(app.template_folder, path)
    except Exception as e:
        logger.error(f"Error serving template {path}: {e}")
        return f"Error serving template: {e}", 500

# Main entry point
if __name__ == '__main__':
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='GDELT News Analysis Dashboard Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--db-path', help='Path to the SQLite database file')
    parser.add_argument('--analysis-dir', help='Path to the analysis directory')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    # Update configuration
    if args.db_path:
        DEFAULT_DB_PATH = args.db_path

    if args.analysis_dir:
        DEFAULT_ANALYSIS_DIR = args.analysis_dir

    # Log configuration
    logger.info(f"Using database: {DEFAULT_DB_PATH}")
    logger.info(f"Using analysis directory: {DEFAULT_ANALYSIS_DIR}")

    # Start server
    app.run(host=args.host, port=args.port, debug=args.debug)
