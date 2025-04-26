#!/usr/bin/env python3
"""
GDELT Timeline Generator

This module provides functions for generating timelines of events involving specific entities.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator
import seaborn as sns
from datetime import datetime, timedelta
import logging
from collections import defaultdict
import json

# Set up logging
logger = logging.getLogger(__name__)

class TimelineGenerator:
    """Class for generating timelines of events involving specific entities"""

    def __init__(self, db_manager=None):
        """
        Initialize the timeline generator

        Args:
            db_manager: DatabaseManager instance for accessing stored data
        """
        self.db_manager = db_manager

    def generate_entity_timeline(self, entity_text, start_date=None, end_date=None,
                                output_dir="timelines", min_trust_score=0.5):
        """
        Generate a timeline for a specific entity

        Args:
            entity_text: Text of the entity to generate timeline for
            start_date: Start date for the timeline (None for all data)
            end_date: End date for the timeline (None for all data)
            output_dir: Directory to save the timeline
            min_trust_score: Minimum trust score for articles to include

        Returns:
            Dictionary with timeline data and path to the timeline image
        """
        logger.info(f"Generating timeline for entity: {entity_text}")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Get entity mentions from database
        if self.db_manager and self.db_manager.conn:
            # Get entity ID
            self.db_manager.cursor.execute(
                "SELECT id FROM entities WHERE text = ?",
                (entity_text,)
            )
            result = self.db_manager.cursor.fetchone()

            if not result:
                logger.warning(f"Entity '{entity_text}' not found in database")
                return None

            entity_id = result[0]

            # Get articles mentioning the entity
            query = """
            SELECT a.id, a.url, a.title, a.seendate, a.language, a.domain,
                   a.sourcecountry, a.theme_id, a.theme_description, a.trust_score
            FROM articles a
            JOIN article_entities ae ON a.id = ae.article_id
            WHERE ae.entity_id = ?
            """

            params = [entity_id]

            # Add date filters if provided
            if start_date:
                query += " AND a.seendate >= ?"
                params.append(start_date)

            if end_date:
                query += " AND a.seendate <= ?"
                params.append(end_date)

            # Add trust score filter
            if min_trust_score is not None:
                query += " AND a.trust_score >= ?"
                params.append(min_trust_score)

            # Order by date
            query += " ORDER BY a.seendate"

            # Execute query
            articles_df = pd.read_sql_query(query, self.db_manager.conn, params=params)

            if articles_df.empty:
                logger.warning(f"No articles found for entity '{entity_text}'")
                return None

            logger.info(f"Found {len(articles_df)} articles mentioning '{entity_text}'")
        else:
            # If no database connection, return None
            logger.warning("No database connection available")
            return None

        # Convert seendate to datetime
        articles_df['seendate'] = pd.to_datetime(articles_df['seendate'])

        # Group articles by date
        date_counts = articles_df.groupby(articles_df['seendate'].dt.date).size()

        # Create timeline data
        timeline_data = {
            'entity': entity_text,
            'total_mentions': len(articles_df),
            'date_range': {
                'start_date': articles_df['seendate'].min().strftime('%Y-%m-%d'),
                'end_date': articles_df['seendate'].max().strftime('%Y-%m-%d')
            },
            'mentions_by_date': {str(k): v for k, v in date_counts.to_dict().items()},
            'top_sources': articles_df['domain'].value_counts().head(10).to_dict(),
            'top_themes': articles_df['theme_id'].value_counts().head(5).to_dict(),
            'articles': []
        }

        # Add top articles (limit to 20 for brevity)
        for _, row in articles_df.sort_values('trust_score', ascending=False).head(20).iterrows():
            timeline_data['articles'].append({
                'title': row['title'],
                'url': row['url'],
                'date': row['seendate'].strftime('%Y-%m-%d'),
                'source': row['domain'],
                'trust_score': float(row['trust_score'])
            })

        # Create timeline visualization
        self._create_timeline_visualization(
            entity_text,
            articles_df,
            os.path.join(output_dir, f"{entity_text.replace(' ', '_')}_timeline.png")
        )

        # Save timeline data to JSON
        timeline_json_path = os.path.join(output_dir, f"{entity_text.replace(' ', '_')}_timeline.json")
        with open(timeline_json_path, 'w') as f:
            json.dump(timeline_data, f, indent=2)

        logger.info(f"Generated timeline for '{entity_text}' saved to {output_dir}")

        return timeline_data

    def generate_entity_comparison_timeline(self, entity_list, start_date=None, end_date=None,
                                          output_dir="timelines", min_trust_score=0.5):
        """
        Generate a comparison timeline for multiple entities

        Args:
            entity_list: List of entities to compare
            start_date: Start date for the timeline (None for all data)
            end_date: End date for the timeline (None for all data)
            output_dir: Directory to save the timeline
            min_trust_score: Minimum trust score for articles to include

        Returns:
            Dictionary with comparison data and path to the timeline image
        """
        logger.info(f"Generating comparison timeline for entities: {', '.join(entity_list)}")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Get data for each entity
        entity_data = {}
        all_articles = pd.DataFrame()

        for entity_text in entity_list:
            # Get entity mentions from database
            if self.db_manager and self.db_manager.conn:
                # Get entity ID
                self.db_manager.cursor.execute(
                    "SELECT id FROM entities WHERE text = ?",
                    (entity_text,)
                )
                result = self.db_manager.cursor.fetchone()

                if not result:
                    logger.warning(f"Entity '{entity_text}' not found in database")
                    continue

                entity_id = result[0]

                # Get articles mentioning the entity
                query = """
                SELECT a.id, a.url, a.title, a.seendate, a.language, a.domain,
                       a.sourcecountry, a.theme_id, a.theme_description, a.trust_score
                FROM articles a
                JOIN article_entities ae ON a.id = ae.article_id
                WHERE ae.entity_id = ?
                """

                params = [entity_id]

                # Add date filters if provided
                if start_date:
                    query += " AND a.seendate >= ?"
                    params.append(start_date)

                if end_date:
                    query += " AND a.seendate <= ?"
                    params.append(end_date)

                # Add trust score filter
                if min_trust_score is not None:
                    query += " AND a.trust_score >= ?"
                    params.append(min_trust_score)

                # Order by date
                query += " ORDER BY a.seendate"

                # Execute query
                articles_df = pd.read_sql_query(query, self.db_manager.conn, params=params)

                if articles_df.empty:
                    logger.warning(f"No articles found for entity '{entity_text}'")
                    continue

                # Add entity column
                articles_df['entity'] = entity_text

                # Add to all articles
                all_articles = pd.concat([all_articles, articles_df])

                # Convert seendate to datetime
                articles_df['seendate'] = pd.to_datetime(articles_df['seendate'])

                # Group articles by date
                date_counts = articles_df.groupby(articles_df['seendate'].dt.date).size()

                # Store entity data
                entity_data[entity_text] = {
                    'total_mentions': len(articles_df),
                    'date_range': {
                        'start_date': articles_df['seendate'].min().strftime('%Y-%m-%d'),
                        'end_date': articles_df['seendate'].max().strftime('%Y-%m-%d')
                    },
                    'mentions_by_date': date_counts.to_dict(),
                    'top_sources': articles_df['domain'].value_counts().head(5).to_dict(),
                    'top_themes': articles_df['theme_id'].value_counts().head(3).to_dict()
                }

                logger.info(f"Found {len(articles_df)} articles mentioning '{entity_text}'")
            else:
                # If no database connection, return None
                logger.warning("No database connection available")
                return None

        if all_articles.empty:
            logger.warning("No articles found for any of the entities")
            return None

        # Convert seendate to datetime for all articles
        all_articles['seendate'] = pd.to_datetime(all_articles['seendate'])

        # Create comparison visualization
        comparison_path = os.path.join(output_dir, f"entity_comparison_{'_'.join([e.replace(' ', '_') for e in entity_list])}.png")
        self._create_comparison_visualization(entity_list, all_articles, comparison_path)

        # Create comparison data
        # Convert entity_data to serializable format
        serializable_entity_data = {}
        for entity, data in entity_data.items():
            # Convert date keys to strings in mentions_by_date
            if 'mentions_by_date' in data:
                data['mentions_by_date'] = {str(k): v for k, v in data['mentions_by_date'].items()}
            serializable_entity_data[entity] = data

        comparison_data = {
            'entities': entity_list,
            'entity_data': serializable_entity_data,
            'co_occurrences': self._find_entity_co_occurrences(entity_list),
            'comparison_chart': comparison_path
        }

        # Save comparison data to JSON
        comparison_json_path = os.path.join(output_dir, f"entity_comparison_{'_'.join([e.replace(' ', '_') for e in entity_list])}.json")
        with open(comparison_json_path, 'w') as f:
            json.dump(comparison_data, f, indent=2)

        logger.info(f"Generated comparison timeline saved to {comparison_json_path}")

        return comparison_data

    def generate_event_timeline(self, entity_text, cluster_threshold=3, min_articles=2,
                              output_dir="timelines", min_trust_score=0.5):
        """
        Generate a timeline of significant events involving an entity

        Args:
            entity_text: Text of the entity to generate timeline for
            cluster_threshold: Number of days to consider for event clustering
            min_articles: Minimum number of articles to consider an event significant
            output_dir: Directory to save the timeline
            min_trust_score: Minimum trust score for articles to include

        Returns:
            Dictionary with event timeline data
        """
        logger.info(f"Generating event timeline for entity: {entity_text}")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Get entity mentions from database
        if self.db_manager and self.db_manager.conn:
            # Get entity ID
            self.db_manager.cursor.execute(
                "SELECT id FROM entities WHERE text = ?",
                (entity_text,)
            )
            result = self.db_manager.cursor.fetchone()

            if not result:
                logger.warning(f"Entity '{entity_text}' not found in database")
                return None

            entity_id = result[0]

            # Get articles mentioning the entity
            query = """
            SELECT a.id, a.url, a.title, a.seendate, a.language, a.domain,
                   a.sourcecountry, a.theme_id, a.theme_description, a.trust_score
            FROM articles a
            JOIN article_entities ae ON a.id = ae.article_id
            WHERE ae.entity_id = ?
            """

            params = [entity_id]

            # Add trust score filter
            if min_trust_score is not None:
                query += " AND a.trust_score >= ?"
                params.append(min_trust_score)

            # Order by date
            query += " ORDER BY a.seendate"

            # Execute query
            articles_df = pd.read_sql_query(query, self.db_manager.conn, params=params)

            if articles_df.empty:
                logger.warning(f"No articles found for entity '{entity_text}'")
                return None

            logger.info(f"Found {len(articles_df)} articles mentioning '{entity_text}'")
        else:
            # If no database connection, return None
            logger.warning("No database connection available")
            return None

        # Convert seendate to datetime
        articles_df['seendate'] = pd.to_datetime(articles_df['seendate'])

        # Identify significant events (clusters of articles)
        events = self._identify_events(articles_df, cluster_threshold, min_articles)

        if not events:
            logger.warning(f"No significant events found for entity '{entity_text}'")
            return None

        logger.info(f"Identified {len(events)} significant events for '{entity_text}'")

        # Create event timeline visualization
        event_timeline_path = os.path.join(output_dir, f"{entity_text.replace(' ', '_')}_events.png")
        self._create_event_visualization(entity_text, events, event_timeline_path)

        # Create event timeline data
        event_timeline_data = {
            'entity': entity_text,
            'total_events': len(events),
            'events': events,
            'event_timeline_chart': event_timeline_path
        }

        # Save event timeline data to JSON
        event_json_path = os.path.join(output_dir, f"{entity_text.replace(' ', '_')}_events.json")
        with open(event_json_path, 'w') as f:
            json.dump(event_timeline_data, f, indent=2)

        logger.info(f"Generated event timeline for '{entity_text}' saved to {event_json_path}")

        return event_timeline_data

    def _create_timeline_visualization(self, entity_text, articles_df, output_path):
        """Create a timeline visualization for an entity"""
        # Group articles by date
        date_counts = articles_df.groupby(articles_df['seendate'].dt.date).size()

        # Create the plot
        plt.figure(figsize=(14, 8))

        # Plot the timeline
        ax = date_counts.plot(kind='bar', color='skyblue')

        # Set title and labels
        plt.title(f"Timeline for '{entity_text}'", fontsize=16)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Number of Mentions', fontsize=12)

        # Format x-axis
        plt.xticks(rotation=45, ha='right')

        # Add grid
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        # Add a trend line (7-day moving average)
        if len(date_counts) > 7:
            ma = date_counts.rolling(window=7, min_periods=1).mean()
            plt.plot(range(len(date_counts)), ma, color='red', linewidth=2, label='7-day Moving Average')
            plt.legend()

        # Adjust layout
        plt.tight_layout()

        # Save the plot
        plt.savefig(output_path)
        plt.close()

        logger.info(f"Created timeline visualization for '{entity_text}' at {output_path}")

    def _create_comparison_visualization(self, entity_list, all_articles, output_path):
        """Create a comparison visualization for multiple entities"""
        # Set up the plot
        plt.figure(figsize=(14, 8))

        # Set color palette
        colors = sns.color_palette("husl", len(entity_list))

        # Group by entity and date
        for i, entity in enumerate(entity_list):
            entity_articles = all_articles[all_articles['entity'] == entity]

            if entity_articles.empty:
                continue

            # Group by date
            date_counts = entity_articles.groupby(entity_articles['seendate'].dt.date).size()

            # Plot the timeline
            plt.plot(date_counts.index, date_counts.values, marker='o', linestyle='-',
                    color=colors[i], label=entity, alpha=0.7, markersize=5)

        # Set title and labels
        plt.title(f"Comparison Timeline for {', '.join(entity_list)}", fontsize=16)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Number of Mentions', fontsize=12)

        # Format x-axis
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.gca().xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
        plt.xticks(rotation=45, ha='right')

        # Add grid
        plt.grid(True, linestyle='--', alpha=0.7)

        # Add legend
        plt.legend()

        # Adjust layout
        plt.tight_layout()

        # Save the plot
        plt.savefig(output_path)
        plt.close()

        logger.info(f"Created comparison visualization for {entity_list} at {output_path}")

    def _identify_events(self, articles_df, cluster_threshold, min_articles):
        """
        Identify significant events (clusters of articles)

        Args:
            articles_df: DataFrame containing articles
            cluster_threshold: Number of days to consider for event clustering
            min_articles: Minimum number of articles to consider an event significant

        Returns:
            List of event dictionaries
        """
        # Sort articles by date
        articles_df = articles_df.sort_values('seendate')

        # Initialize events
        events = []
        current_event = {
            'start_date': None,
            'end_date': None,
            'articles': [],
            'themes': set(),
            'sources': set(),
            'peak_date': None,
            'peak_articles': 0
        }

        # Group articles by date
        date_groups = articles_df.groupby(articles_df['seendate'].dt.date)
        date_counts = date_groups.size()

        # Find peaks (dates with more articles than neighbors)
        peaks = []
        for i, (date, count) in enumerate(date_counts.items()):
            is_peak = True

            # Check if count is higher than previous and next day
            if i > 0 and count <= date_counts.iloc[i-1]:
                is_peak = False

            if i < len(date_counts) - 1 and count <= date_counts.iloc[i+1]:
                is_peak = False

            # Check if count meets minimum threshold
            if count < min_articles:
                is_peak = False

            if is_peak:
                peaks.append((date, count))

        # Cluster articles around peaks
        for peak_date, peak_count in peaks:
            # Get articles within cluster_threshold days of peak
            peak_start = peak_date - timedelta(days=cluster_threshold)
            peak_end = peak_date + timedelta(days=cluster_threshold)

            cluster_articles = articles_df[
                (articles_df['seendate'].dt.date >= peak_start) &
                (articles_df['seendate'].dt.date <= peak_end)
            ]

            # Skip if not enough articles
            if len(cluster_articles) < min_articles:
                continue

            # Create event
            event = {
                'start_date': peak_start.strftime('%Y-%m-%d'),
                'end_date': peak_end.strftime('%Y-%m-%d'),
                'peak_date': peak_date.strftime('%Y-%m-%d'),
                'article_count': len(cluster_articles),
                'peak_count': peak_count,
                'themes': cluster_articles['theme_id'].value_counts().head(3).to_dict(),
                'sources': cluster_articles['domain'].value_counts().head(5).to_dict(),
                'top_articles': []
            }

            # Add top articles
            for _, row in cluster_articles.sort_values('trust_score', ascending=False).head(5).iterrows():
                event['top_articles'].append({
                    'title': row['title'],
                    'url': row['url'],
                    'date': row['seendate'].strftime('%Y-%m-%d'),
                    'source': row['domain'],
                    'trust_score': float(row['trust_score'])
                })

            events.append(event)

        # Sort events by date
        events.sort(key=lambda x: x['peak_date'])

        return events

    def _create_event_visualization(self, entity_text, events, output_path):
        """Create an event timeline visualization"""
        # Set up the plot
        plt.figure(figsize=(14, 10))

        # Extract data
        dates = [datetime.strptime(event['peak_date'], '%Y-%m-%d') for event in events]
        counts = [event['peak_count'] for event in events]

        # Plot the events
        plt.scatter(dates, counts, s=[c*20 for c in counts], alpha=0.7, color='blue', edgecolors='black')

        # Connect events with a line
        plt.plot(dates, counts, 'b-', alpha=0.3)

        # Add event labels
        for i, event in enumerate(events):
            date = datetime.strptime(event['peak_date'], '%Y-%m-%d')
            count = event['peak_count']

            # Get top theme
            top_theme = max(event['themes'].items(), key=lambda x: x[1])[0] if event['themes'] else "Unknown"

            # Add label
            plt.annotate(
                f"Event {i+1}: {top_theme}",
                xy=(date, count),
                xytext=(10, 10),
                textcoords='offset points',
                fontsize=9,
                bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5)
            )

        # Set title and labels
        plt.title(f"Significant Events Timeline for '{entity_text}'", fontsize=16)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Number of Articles at Peak', fontsize=12)

        # Format x-axis
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
        plt.xticks(rotation=45, ha='right')

        # Add grid
        plt.grid(True, linestyle='--', alpha=0.7)

        # Adjust layout
        plt.tight_layout()

        # Save the plot
        plt.savefig(output_path)
        plt.close()

        logger.info(f"Created event visualization for '{entity_text}' at {output_path}")

    def _find_entity_co_occurrences(self, entity_list):
        """Find co-occurrences of entities in the same articles"""
        co_occurrences = {}

        if not self.db_manager or not self.db_manager.conn:
            logger.warning("No database connection available")
            return co_occurrences

        # Get entity IDs
        entity_ids = {}
        for entity_text in entity_list:
            self.db_manager.cursor.execute(
                "SELECT id FROM entities WHERE text = ?",
                (entity_text,)
            )
            result = self.db_manager.cursor.fetchone()

            if result:
                entity_ids[entity_text] = result[0]

        # Find co-occurrences
        for i, entity1 in enumerate(entity_list):
            if entity1 not in entity_ids:
                continue

            co_occurrences[entity1] = {}

            for j, entity2 in enumerate(entity_list):
                if i == j or entity2 not in entity_ids:
                    continue

                # Count articles mentioning both entities
                query = """
                SELECT COUNT(DISTINCT a.id)
                FROM articles a
                JOIN article_entities ae1 ON a.id = ae1.article_id
                JOIN article_entities ae2 ON a.id = ae2.article_id
                WHERE ae1.entity_id = ? AND ae2.entity_id = ?
                """

                self.db_manager.cursor.execute(query, (entity_ids[entity1], entity_ids[entity2]))
                count = self.db_manager.cursor.fetchone()[0]

                if count > 0:
                    co_occurrences[entity1][entity2] = count

        # Convert to serializable format (no date objects as keys)
        serializable_co_occurrences = {}
        for entity1, entity_dict in co_occurrences.items():
            serializable_co_occurrences[entity1] = {
                str(entity2): count for entity2, count in entity_dict.items()
            }

        return serializable_co_occurrences

def generate_entity_timeline_report(timeline_data, output_dir="timelines"):
    """
    Generate a markdown report for an entity timeline

    Args:
        timeline_data: Timeline data dictionary
        output_dir: Directory to save the report

    Returns:
        Path to the report file
    """
    if not timeline_data:
        logger.warning("No timeline data provided")
        return None

    entity = timeline_data['entity']

    # Create report content
    report = f"""# Timeline Report for '{entity}'

## Overview

- **Total Mentions**: {timeline_data['total_mentions']}
- **Date Range**: {timeline_data['date_range']['start_date']} to {timeline_data['date_range']['end_date']}

## Mention Frequency

![Timeline Chart]({entity.replace(' ', '_')}_timeline.png)

## Top Sources

| Source | Mentions |
|--------|----------|
"""

    # Add top sources
    for source, count in timeline_data['top_sources'].items():
        report += f"| {source} | {count} |\n"

    report += """
## Top Themes

| Theme | Mentions |
|-------|----------|
"""

    # Add top themes
    for theme, count in timeline_data['top_themes'].items():
        report += f"| {theme} | {count} |\n"

    report += """
## Top Articles

| Date | Source | Title | Trust Score |
|------|--------|-------|-------------|
"""

    # Add top articles
    for article in timeline_data['articles']:
        report += f"| {article['date']} | {article['source']} | [{article['title']}]({article['url']}) | {article['trust_score']:.2f} |\n"

    # Save report
    report_path = os.path.join(output_dir, f"{entity.replace(' ', '_')}_report.md")
    with open(report_path, 'w') as f:
        f.write(report)

    logger.info(f"Generated timeline report for '{entity}' saved to {report_path}")

    return report_path

def generate_event_timeline_report(event_timeline_data, output_dir="timelines"):
    """
    Generate a markdown report for an event timeline

    Args:
        event_timeline_data: Event timeline data dictionary
        output_dir: Directory to save the report

    Returns:
        Path to the report file
    """
    if not event_timeline_data:
        logger.warning("No event timeline data provided")
        return None

    entity = event_timeline_data['entity']

    # Create report content
    report = f"""# Event Timeline Report for '{entity}'

## Overview

- **Total Events**: {event_timeline_data['total_events']}

## Event Timeline

![Event Timeline Chart]({entity.replace(' ', '_')}_events.png)

## Significant Events

"""

    # Add events
    for i, event in enumerate(event_timeline_data['events']):
        # Get top theme
        top_theme = max(event['themes'].items(), key=lambda x: x[1])[0] if event['themes'] else "Unknown"

        report += f"### Event {i+1}: {top_theme}\n\n"
        report += f"- **Date Range**: {event['start_date']} to {event['end_date']}\n"
        report += f"- **Peak Date**: {event['peak_date']}\n"
        report += f"- **Article Count**: {event['article_count']} (Peak: {event['peak_count']})\n\n"

        report += "#### Top Themes\n\n"
        for theme, count in event['themes'].items():
            report += f"- {theme}: {count} articles\n"

        report += "\n#### Top Sources\n\n"
        for source, count in event['sources'].items():
            report += f"- {source}: {count} articles\n"

        report += "\n#### Key Articles\n\n"
        for article in event['top_articles']:
            report += f"- [{article['title']}]({article['url']}) - {article['source']} ({article['date']}, Trust: {article['trust_score']:.2f})\n"

        report += "\n"

    # Save report
    report_path = os.path.join(output_dir, f"{entity.replace(' ', '_')}_events_report.md")
    with open(report_path, 'w') as f:
        f.write(report)

    logger.info(f"Generated event timeline report for '{entity}' saved to {report_path}")

    return report_path
