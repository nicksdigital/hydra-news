#!/usr/bin/env python3
"""
GDELT Analyzer Core

This module provides the main functionality for analyzing GDELT news data.
"""

import os
import logging
import argparse
import pandas as pd
from datetime import datetime

# Import analyzer modules
from .data_loader import load_dataset, preprocess_articles, split_dataset_into_chunks
from .theme_analyzer import analyze_themes, analyze_theme_by_language, analyze_theme_correlations, analyze_theme_trends_over_time
from .time_analyzer import analyze_time_patterns, analyze_publication_delay, analyze_time_series
from .source_analyzer import analyze_domains, analyze_languages, analyze_countries, analyze_source_diversity
from .text_analyzer import analyze_sentiment, analyze_sentiment_by_theme, extract_keywords, build_topic_model, get_topic_words, assign_topics_to_articles
from .visualizer import create_all_visualizations
from .report_generator import generate_report, generate_json_summary, generate_csv_exports
from .entity_extractor import EntityExtractor
from .database_manager import DatabaseManager
from .trust_scorer import TrustScorer
from .timeline_generator import TimelineGenerator, generate_entity_timeline_report, generate_event_timeline_report
from .event_sentiment_analyzer import EventSentimentAnalyzer
from .cross_entity_analyzer import CrossEntityAnalyzer
from .predictive_event_detector import PredictiveEventDetector
from .timeline_sentiment_visualizer import TimelineSentimentVisualizer
from .timeline_report_generator import (
    generate_event_sentiment_report,
    generate_cross_entity_report,
    generate_prediction_report,
    generate_event_prediction_report,
    generate_sentiment_comparison_report,
    generate_advanced_timeline_summary
)

# Set up logging
logger = logging.getLogger(__name__)

def setup_logging(log_file=None, level=logging.INFO):
    """Set up logging configuration"""
    handlers = [logging.StreamHandler()]

    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=handlers
    )

def analyze_gdelt_dataset(dataset_dir, output_dir, enable_sentiment=True, enable_topics=True,
                     enable_entities=True, enable_database=True, enable_timelines=False,
                     enable_event_sentiment=False, enable_cross_entity=False, enable_predictions=False,
                     db_path=None, n_topics=10, timeline_entities=None):
    """
    Analyze a GDELT dataset

    Args:
        dataset_dir: Directory containing the dataset
        output_dir: Directory to save the analysis results
        enable_sentiment: Whether to enable sentiment analysis
        enable_topics: Whether to enable topic modeling
        enable_entities: Whether to enable entity extraction
        enable_database: Whether to enable database storage
        enable_timelines: Whether to enable timeline generation
        enable_event_sentiment: Whether to enable sentiment analysis by event
        enable_cross_entity: Whether to enable cross-entity event analysis
        enable_predictions: Whether to enable predictive event detection
        db_path: Path to the SQLite database file
        n_topics: Number of topics for topic modeling
        timeline_entities: List of entities to generate timelines for (None for top entities)

    Returns:
        Dictionary with analysis results
    """
    logger.info(f"Starting analysis of GDELT dataset in {dataset_dir}")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Load the dataset
    logger.info("Loading dataset...")
    articles, themes_map, summary = load_dataset(dataset_dir)

    # Preprocess articles
    logger.info("Preprocessing articles...")
    articles = preprocess_articles(articles, themes_map)

    # Initialize results dictionary
    analysis_results = {}

    # Analyze themes
    logger.info("Analyzing theme distribution...")
    # Create a themes map dictionary if themes_map is a list
    if isinstance(themes_map, list):
        themes_dict = {theme['theme']: theme['description'] for theme in themes_map}
    else:
        themes_dict = themes_map
    theme_counts = analyze_themes(articles, themes_dict)
    analysis_results['theme_counts'] = theme_counts

    # Analyze theme correlations
    logger.info("Analyzing theme correlations...")
    theme_corr = analyze_theme_correlations(articles)
    analysis_results['theme_corr'] = theme_corr

    # Analyze theme trends over time
    logger.info("Analyzing theme trends over time...")
    theme_trends = analyze_theme_trends_over_time(articles)
    analysis_results['theme_trends'] = theme_trends

    # Analyze time patterns
    logger.info("Analyzing time patterns...")
    date_counts, hour_counts, day_counts = analyze_time_patterns(articles)
    analysis_results['date_counts'] = date_counts
    analysis_results['hour_counts'] = hour_counts
    analysis_results['day_counts'] = day_counts

    # Analyze time series
    logger.info("Analyzing time series...")
    time_series = analyze_time_series(articles)
    analysis_results['time_series'] = time_series

    # Analyze publication delay
    logger.info("Analyzing publication delay...")
    delay_stats = analyze_publication_delay(articles)
    analysis_results['delay_stats'] = delay_stats

    # Analyze domains
    logger.info("Analyzing domains...")
    domain_counts, tld_counts = analyze_domains(articles)
    analysis_results['domain_counts'] = domain_counts
    analysis_results['tld_counts'] = tld_counts

    # Analyze languages
    logger.info("Analyzing languages...")
    language_counts = analyze_languages(articles)
    analysis_results['language_counts'] = language_counts

    # Analyze countries
    logger.info("Analyzing countries...")
    country_counts = analyze_countries(articles)
    analysis_results['country_counts'] = country_counts

    # Analyze source diversity
    logger.info("Analyzing source diversity...")
    source_diversity = analyze_source_diversity(articles)
    analysis_results['source_diversity'] = source_diversity

    # Sentiment analysis
    if enable_sentiment:
        logger.info("Analyzing sentiment...")
        try:
            sentiment_df = analyze_sentiment(articles)
            if sentiment_df is not None:
                analysis_results['sentiment_df'] = sentiment_df

                # Analyze sentiment by theme
                theme_sentiment = analyze_sentiment_by_theme(sentiment_df)
                analysis_results['theme_sentiment'] = theme_sentiment
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")

    # Extract keywords
    logger.info("Extracting keywords...")
    keywords_df = extract_keywords(articles)
    analysis_results['keywords_df'] = keywords_df

    # Topic modeling
    if enable_topics:
        logger.info("Building topic model...")
        try:
            topic_model_results = build_topic_model(articles, n_topics=n_topics)

            if topic_model_results is not None:
                lda, vectorizer, feature_names, doc_topic_matrix = topic_model_results

                # Get topic words
                topic_words = get_topic_words(lda, feature_names)
                analysis_results['topic_words'] = topic_words

                # Assign topics to articles
                topic_df = assign_topics_to_articles(articles, doc_topic_matrix)
                analysis_results['topic_df'] = topic_df
        except Exception as e:
            logger.error(f"Error in topic modeling: {e}")

    # Create visualizations
    logger.info("Creating visualizations...")
    create_all_visualizations(analysis_results, output_dir)

    # Generate report
    logger.info("Generating report...")
    report_path = generate_report(articles, themes_map, summary, analysis_results, output_dir)

    # Generate JSON summary
    logger.info("Generating JSON summary...")
    summary_path = generate_json_summary(analysis_results, output_dir)

    # Generate CSV exports
    logger.info("Generating CSV exports...")
    exports_dir = generate_csv_exports(articles, analysis_results, output_dir)

    # Entity extraction
    if enable_entities:
        logger.info("Extracting entities...")
        try:
            # Initialize entity extractor
            entity_extractor = EntityExtractor()

            # Extract entities from articles
            entities_df = entity_extractor.extract_entities_from_dataframe(articles)
            analysis_results['entities_df'] = entities_df

            # Calculate entity statistics
            entity_stats_df = entity_extractor.calculate_entity_stats()
            analysis_results['entity_stats_df'] = entity_stats_df

            # Save entity data
            entities_path = os.path.join(output_dir, "entities.csv")
            entities_df.to_csv(entities_path, index=False)
            logger.info(f"Saved {len(entities_df)} entity mentions to {entities_path}")

            entity_stats_path = os.path.join(output_dir, "entity_stats.csv")
            entity_stats_df.to_csv(entity_stats_path, index=False)
            logger.info(f"Saved statistics for {len(entity_stats_df)} entities to {entity_stats_path}")

            # Calculate trust scores for entities
            logger.info("Calculating trust scores for entities...")
            trust_scorer = TrustScorer()
            entity_stats_df = trust_scorer.score_entities(entities_df, entity_stats_df)

            # Save entity trust scores
            entity_trust_path = os.path.join(output_dir, "entity_trust.csv")
            entity_stats_df[['entity', 'type', 'count', 'num_sources', 'source_diversity', 'trust_score']].to_csv(entity_trust_path, index=False)
            logger.info(f"Saved trust scores for {len(entity_stats_df)} entities to {entity_trust_path}")

            # Calculate trust scores for articles based on entities
            logger.info("Calculating trust scores for articles...")
            articles_with_trust = trust_scorer.score_articles(articles)

            # Save article trust scores
            article_trust_path = os.path.join(output_dir, "article_trust.csv")
            articles_with_trust[['url', 'title', 'domain', 'theme_id', 'trust_score']].to_csv(article_trust_path, index=False)
            logger.info(f"Saved trust scores for {len(articles_with_trust)} articles to {article_trust_path}")

            # Update analysis results
            analysis_results['articles_with_trust'] = articles_with_trust
        except Exception as e:
            logger.error(f"Error in entity extraction: {e}")

    # Database storage
    db_manager = None
    if enable_database and enable_entities:
        logger.info("Storing data in database...")
        try:
            # Set default database path if not provided
            if db_path is None:
                db_path = os.path.join(output_dir, "gdelt_news.db")

            # Initialize database manager
            db_manager = DatabaseManager(db_path)

            # Connect to database
            if db_manager.connect():
                # Create tables
                db_manager.create_tables()

                # Store articles
                if 'articles_with_trust' in analysis_results:
                    articles_to_store = analysis_results['articles_with_trust']
                else:
                    articles_to_store = articles

                stored_articles = db_manager.store_articles(articles_to_store)
                logger.info(f"Stored {stored_articles} articles in database")

                # Store entities
                if 'entities_df' in analysis_results and 'entity_stats_df' in analysis_results:
                    stored_entities = db_manager.store_entities(
                        analysis_results['entities_df'],
                        analysis_results['entity_stats_df']
                    )
                    logger.info(f"Stored {stored_entities} entities in database")

                # Get database summary
                db_summary = db_manager.get_database_summary()
                analysis_results['db_summary'] = db_summary

                # Save database summary
                db_summary_path = os.path.join(output_dir, "db_summary.json")
                with open(db_summary_path, 'w') as f:
                    import json
                    json.dump(db_summary, f, indent=2)
                logger.info(f"Saved database summary to {db_summary_path}")
            else:
                logger.error("Failed to connect to database")
        except Exception as e:
            logger.error(f"Error in database storage: {e}")

    # Timeline generation
    if enable_timelines and enable_database and db_manager and db_manager.conn:
        logger.info("Generating entity timelines...")
        try:
            # Create timelines directory
            timelines_dir = os.path.join(output_dir, "timelines")
            os.makedirs(timelines_dir, exist_ok=True)

            # Initialize timeline generator
            timeline_generator = TimelineGenerator(db_manager)

            # Determine which entities to generate timelines for
            if timeline_entities:
                # Use provided list of entities
                entities_to_process = timeline_entities
            elif 'entity_stats_df' in analysis_results:
                # Use top entities by count
                top_entities = analysis_results['entity_stats_df'].sort_values('count', ascending=False).head(10)
                entities_to_process = top_entities['entity'].tolist()
            else:
                # No entities to process
                entities_to_process = []

            # Generate timelines for each entity
            timeline_data = {}
            event_data = {}  # Store event data for later use

            for entity in entities_to_process:
                logger.info(f"Generating timeline for entity: {entity}")

                # Generate entity timeline
                entity_timeline = timeline_generator.generate_entity_timeline(
                    entity,
                    output_dir=timelines_dir
                )

                if entity_timeline:
                    # Generate timeline report
                    report_path = generate_entity_timeline_report(
                        entity_timeline,
                        output_dir=timelines_dir
                    )

                    # Generate event timeline
                    event_timeline = timeline_generator.generate_event_timeline(
                        entity,
                        output_dir=timelines_dir
                    )

                    if event_timeline:
                        # Generate event timeline report
                        event_report_path = generate_event_timeline_report(
                            event_timeline,
                            output_dir=timelines_dir
                        )

                        # Store event data for later use
                        event_data[entity] = event_timeline

                    # Store timeline data
                    timeline_data[entity] = {
                        'entity_timeline': entity_timeline,
                        'event_timeline': event_timeline if 'event_timeline' in locals() else None
                    }

            # Generate comparison timeline for top entities (if multiple entities)
            if len(entities_to_process) > 1:
                logger.info(f"Generating comparison timeline for top entities")

                # Generate comparison timeline
                comparison_data = timeline_generator.generate_entity_comparison_timeline(
                    entities_to_process[:5],  # Limit to top 5 for readability
                    output_dir=timelines_dir
                )

                if comparison_data:
                    timeline_data['comparison'] = comparison_data

            # Add timeline data to analysis results
            analysis_results['timeline_data'] = timeline_data

            # Create timeline index
            timeline_index = {
                'entities': entities_to_process,
                'timelines': {
                    entity: {
                        'entity_timeline': f"{entity.replace(' ', '_')}_timeline.png",
                        'entity_report': f"{entity.replace(' ', '_')}_report.md",
                        'event_timeline': f"{entity.replace(' ', '_')}_events.png",
                        'event_report': f"{entity.replace(' ', '_')}_events_report.md"
                    } for entity in entities_to_process if entity in timeline_data
                }
            }

            # Add comparison timeline if available
            if 'comparison' in timeline_data:
                timeline_index['comparison'] = {
                    'chart': f"entity_comparison_{'_'.join([e.replace(' ', '_') for e in entities_to_process[:5]])}.png",
                    'data': f"entity_comparison_{'_'.join([e.replace(' ', '_') for e in entities_to_process[:5]])}.json"
                }

            # Save timeline index
            index_path = os.path.join(timelines_dir, "timeline_index.json")
            with open(index_path, 'w') as f:
                import json
                json.dump(timeline_index, f, indent=2)

            logger.info(f"Generated timelines for {len(timeline_data)} entities")

            # Create timeline summary report
            summary_path = os.path.join(timelines_dir, "timeline_summary.md")
            with open(summary_path, 'w') as f:
                f.write(f"# Entity Timeline Summary\n\n")
                f.write(f"## Overview\n\n")
                f.write(f"Generated timelines for {len(timeline_data)} entities.\n\n")

                f.write(f"## Entity Timelines\n\n")
                for entity in entities_to_process:
                    if entity in timeline_data:
                        f.write(f"### {entity}\n\n")
                        f.write(f"- [Entity Timeline Report]({entity.replace(' ', '_')}_report.md)\n")
                        f.write(f"- [Event Timeline Report]({entity.replace(' ', '_')}_events_report.md)\n\n")

                if 'comparison' in timeline_data:
                    f.write(f"## Entity Comparison\n\n")
                    f.write(f"- [Comparison Chart](entity_comparison_{'_'.join([e.replace(' ', '_') for e in entities_to_process[:5]])}.png)\n\n")

            logger.info(f"Generated timeline summary at {summary_path}")

            # Advanced Timeline Features

            # 1. Sentiment Analysis by Event
            if enable_event_sentiment and entities_to_process and event_data:
                logger.info("Generating sentiment analysis by event...")

                # Initialize event sentiment analyzer
                event_sentiment_analyzer = EventSentimentAnalyzer(db_manager)

                # Initialize timeline sentiment visualizer
                sentiment_visualizer = TimelineSentimentVisualizer()

                # Generate sentiment analysis for each entity's events
                sentiment_data = {}

                for entity in entities_to_process:
                    if entity not in event_data or not event_data[entity]['events']:
                        continue

                    # Get the most significant event
                    top_event = max(event_data[entity]['events'], key=lambda x: x['article_count'])

                    # Analyze sentiment for the event
                    event_sentiment = event_sentiment_analyzer.analyze_entity_sentiment_over_time(
                        entity,
                        start_date=top_event['start_date'],
                        end_date=top_event['end_date'],
                        output_dir=timelines_dir
                    )

                    if event_sentiment:
                        # Create sentiment visualization
                        daily_sentiment = {datetime.strptime(k, '%Y-%m-%d').date(): v
                                         for k, v in event_sentiment['daily_sentiment'].items()}
                        rolling_sentiment = {datetime.strptime(k, '%Y-%m-%d').date(): v
                                           for k, v in event_sentiment['rolling_sentiment'].items()}

                        sentiment_chart_path = sentiment_visualizer.create_sentiment_timeline_visualization(
                            entity,
                            pd.Series(daily_sentiment),
                            pd.Series(rolling_sentiment),
                            os.path.join(timelines_dir, f"{entity.replace(' ', '_')}_sentiment_timeline.png")
                        )

                        # Generate sentiment report
                        sentiment_report_path = generate_event_sentiment_report(
                            event_sentiment,
                            output_dir=timelines_dir
                        )

                        # Store sentiment data
                        sentiment_data[entity] = event_sentiment

                # Generate sentiment comparison if multiple entities
                if len(sentiment_data) > 1:
                    # Create sentiment comparison visualization
                    comparison_chart_path = sentiment_visualizer.create_entity_sentiment_comparison(
                        list(sentiment_data.keys()),
                        sentiment_data,
                        output_dir=timelines_dir
                    )

                    # Create sentiment heatmap
                    heatmap_path = sentiment_visualizer.create_sentiment_heatmap(
                        list(sentiment_data.keys()),
                        sentiment_data,
                        output_dir=timelines_dir
                    )

                    # Create sentiment distribution
                    distribution_path = sentiment_visualizer.create_sentiment_distribution(
                        list(sentiment_data.keys()),
                        sentiment_data,
                        output_dir=timelines_dir
                    )

                    # Generate sentiment comparison report
                    comparison_report_path = generate_sentiment_comparison_report(
                        list(sentiment_data.keys()),
                        sentiment_data,
                        {
                            'comparison': comparison_chart_path,
                            'heatmap': heatmap_path,
                            'distribution': distribution_path
                        },
                        output_dir=timelines_dir
                    )

                # Add sentiment data to analysis results
                analysis_results['sentiment_data'] = sentiment_data

            # 2. Cross-Entity Event Analysis
            if enable_cross_entity and len(entities_to_process) > 1:
                logger.info("Generating cross-entity event analysis...")

                # Initialize cross-entity analyzer
                cross_entity_analyzer = CrossEntityAnalyzer(db_manager)

                # Find entity co-occurrences
                co_occurrence_data = cross_entity_analyzer.find_entity_co_occurrences(
                    entities_to_process,
                    output_dir=timelines_dir
                )

                # Identify cross-entity events
                cross_entity_events = cross_entity_analyzer.identify_cross_entity_events(
                    entities_to_process,
                    output_dir=timelines_dir
                )

                if cross_entity_events:
                    # Generate cross-entity report
                    cross_entity_report_path = generate_cross_entity_report(
                        cross_entity_events,
                        output_dir=timelines_dir
                    )

                # Add cross-entity data to analysis results
                analysis_results['cross_entity_data'] = {
                    'co_occurrences': co_occurrence_data,
                    'events': cross_entity_events
                }

            # 3. Predictive Event Detection
            if enable_predictions and entities_to_process:
                logger.info("Generating predictive event detection...")

                # Initialize predictive event detector
                predictive_detector = PredictiveEventDetector(db_manager)

                # Generate predictions for each entity
                prediction_data = {}

                for entity in entities_to_process:
                    # Predict entity mentions
                    mention_predictions = predictive_detector.predict_entity_mentions(
                        entity,
                        output_dir=timelines_dir
                    )

                    if mention_predictions:
                        # Generate prediction report
                        prediction_report_path = generate_prediction_report(
                            mention_predictions,
                            output_dir=timelines_dir
                        )

                        # Predict entity events
                        event_predictions = predictive_detector.predict_entity_events(
                            entity,
                            output_dir=timelines_dir
                        )

                        if event_predictions:
                            # Generate event prediction report
                            event_prediction_report_path = generate_event_prediction_report(
                                event_predictions,
                                output_dir=timelines_dir
                            )

                        # Store prediction data
                        prediction_data[entity] = {
                            'mentions': mention_predictions,
                            'events': event_predictions if 'event_predictions' in locals() else None
                        }

                # Add prediction data to analysis results
                analysis_results['prediction_data'] = prediction_data

            # Generate advanced timeline summary
            if enable_event_sentiment or enable_cross_entity or enable_predictions:
                advanced_summary_path = generate_advanced_timeline_summary(
                    entities_to_process,
                    {
                        'sentiment': analysis_results.get('sentiment_data', {}),
                        'cross_entity': [analysis_results.get('cross_entity_data', {})],
                        'predictions': analysis_results.get('prediction_data', {})
                    },
                    output_dir=timelines_dir
                )
        except Exception as e:
            logger.error(f"Error in timeline generation: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            # Close database connection
            if db_manager:
                db_manager.close()
    elif db_manager:
        # Close database connection if it's still open
        db_manager.close()

    logger.info(f"Analysis complete! Results saved to {output_dir}")
    return analysis_results

def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Analyze GDELT news dataset")
    parser.add_argument("--dataset-dir", default="dataset_gdelt_month", help="Directory containing the dataset")
    parser.add_argument("--output-dir", default="analysis_gdelt", help="Directory to save the analysis results")
    parser.add_argument("--log-file", default=None, help="Path to log file")
    parser.add_argument("--no-sentiment", action="store_true", help="Disable sentiment analysis")
    parser.add_argument("--no-topics", action="store_true", help="Disable topic modeling")
    parser.add_argument("--no-entities", action="store_true", help="Disable entity extraction")
    parser.add_argument("--no-database", action="store_true", help="Disable database storage")
    parser.add_argument("--enable-timelines", action="store_true", help="Enable timeline generation")
    parser.add_argument("--enable-event-sentiment", action="store_true", help="Enable sentiment analysis by event")
    parser.add_argument("--enable-cross-entity", action="store_true", help="Enable cross-entity event analysis")
    parser.add_argument("--enable-predictions", action="store_true", help="Enable predictive event detection")
    parser.add_argument("--timeline-entities", nargs="+", help="Entities to generate timelines for")
    parser.add_argument("--db-path", default=None, help="Path to the SQLite database file")
    parser.add_argument("--n-topics", type=int, default=10, help="Number of topics for topic modeling")
    args = parser.parse_args()

    # Set up logging
    log_file = args.log_file or os.path.join(args.output_dir, "analysis.log")
    setup_logging(log_file)

    # Run analysis
    analyze_gdelt_dataset(
        args.dataset_dir,
        args.output_dir,
        enable_sentiment=not args.no_sentiment,
        enable_topics=not args.no_topics,
        enable_entities=not args.no_entities,
        enable_database=not args.no_database,
        enable_timelines=args.enable_timelines,
        enable_event_sentiment=args.enable_event_sentiment,
        enable_cross_entity=args.enable_cross_entity,
        enable_predictions=args.enable_predictions,
        db_path=args.db_path,
        n_topics=args.n_topics,
        timeline_entities=args.timeline_entities
    )

if __name__ == "__main__":
    main()
