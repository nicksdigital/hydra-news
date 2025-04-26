#!/usr/bin/env python3
"""
GDELT Cross-Entity Analyzer

This module provides functions for analyzing events involving multiple entities.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import networkx as nx
import seaborn as sns
from datetime import datetime, timedelta
import logging
import json
from collections import defaultdict

# Set up logging
logger = logging.getLogger(__name__)

class CrossEntityAnalyzer:
    """Class for analyzing events involving multiple entities"""

    def __init__(self, db_manager=None):
        """
        Initialize the cross-entity analyzer

        Args:
            db_manager: DatabaseManager instance for accessing stored data
        """
        self.db_manager = db_manager

    def find_entity_co_occurrences(self, entity_list, start_date=None, end_date=None,
                                 min_trust_score=0.5, output_dir="timelines"):
        """
        Find co-occurrences of entities in the same articles

        Args:
            entity_list: List of entities to analyze
            start_date: Start date for analysis (None for all data)
            end_date: End date for analysis (None for all data)
            min_trust_score: Minimum trust score for articles to include
            output_dir: Directory to save the output

        Returns:
            Dictionary with co-occurrence data
        """
        logger.info(f"Finding co-occurrences for entities: {', '.join(entity_list)}")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        if not self.db_manager or not self.db_manager.conn:
            logger.warning("No database connection available")
            return None

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
            else:
                logger.warning(f"Entity '{entity_text}' not found in database")

        if not entity_ids:
            logger.warning("No valid entities found in database")
            return None

        # Find co-occurrences
        co_occurrences = {}
        entity_pairs = []

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

                params = [entity_ids[entity1], entity_ids[entity2]]

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

                self.db_manager.cursor.execute(query, params)
                count = self.db_manager.cursor.fetchone()[0]

                if count > 0:
                    co_occurrences[entity1][entity2] = count
                    entity_pairs.append((entity1, entity2, count))

        # Create co-occurrence network visualization
        network_chart_path = os.path.join(
            output_dir,
            f"entity_network_{'_'.join([e.replace(' ', '_') for e in entity_list[:3]])}.png"
        )
        self._create_network_visualization(
            entity_list,
            entity_pairs,
            network_chart_path
        )

        # Create co-occurrence matrix visualization
        matrix_chart_path = os.path.join(
            output_dir,
            f"entity_matrix_{'_'.join([e.replace(' ', '_') for e in entity_list[:3]])}.png"
        )
        self._create_matrix_visualization(
            entity_list,
            co_occurrences,
            matrix_chart_path
        )

        # Create co-occurrence results
        co_occurrence_results = {
            'entities': entity_list,
            'co_occurrences': co_occurrences,
            'network_chart': network_chart_path,
            'matrix_chart': matrix_chart_path
        }

        # Save co-occurrence results
        co_occurrence_json_path = os.path.join(
            output_dir,
            f"entity_co_occurrences_{'_'.join([e.replace(' ', '_') for e in entity_list[:3]])}.json"
        )
        with open(co_occurrence_json_path, 'w') as f:
            json.dump(co_occurrence_results, f, indent=2)

        logger.info(f"Saved co-occurrence results to {co_occurrence_json_path}")

        return co_occurrence_results

    def identify_cross_entity_events(self, entity_list, cluster_threshold=3, min_articles=2,
                                   start_date=None, end_date=None, min_trust_score=0.5,
                                   output_dir="timelines"):
        """
        Identify events involving multiple entities

        Args:
            entity_list: List of entities to analyze
            cluster_threshold: Number of days to consider for event clustering
            min_articles: Minimum number of articles to consider an event significant
            start_date: Start date for analysis (None for all data)
            end_date: End date for analysis (None for all data)
            min_trust_score: Minimum trust score for articles to include
            output_dir: Directory to save the output

        Returns:
            Dictionary with cross-entity event data
        """
        logger.info(f"Identifying cross-entity events for: {', '.join(entity_list)}")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        if not self.db_manager or not self.db_manager.conn:
            logger.warning("No database connection available")
            return None

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
            else:
                logger.warning(f"Entity '{entity_text}' not found in database")

        if not entity_ids:
            logger.warning("No valid entities found in database")
            return None

        # Get articles mentioning any of the entities
        placeholders = ', '.join(['?' for _ in entity_ids.values()])
        query = f"""
        SELECT DISTINCT a.id, a.url, a.title, a.seendate, a.language, a.domain,
               a.sourcecountry, a.theme_id, a.theme_description, a.trust_score
        FROM articles a
        JOIN article_entities ae ON a.id = ae.article_id
        WHERE ae.entity_id IN ({placeholders})
        """

        params = list(entity_ids.values())

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

        articles_df = pd.read_sql_query(query, self.db_manager.conn, params=params)

        if articles_df.empty:
            logger.warning(f"No articles found for the specified entities")
            return None

        logger.info(f"Found {len(articles_df)} articles mentioning the specified entities")

        # Get entity mentions for each article
        article_entities = {}
        for article_id in articles_df['id'].unique():
            # Get entities mentioned in the article
            query = """
            SELECT e.text
            FROM entities e
            JOIN article_entities ae ON e.id = ae.entity_id
            WHERE ae.article_id = ?
            """

            self.db_manager.cursor.execute(query, (article_id,))
            results = self.db_manager.cursor.fetchall()

            # Filter to only include entities from the input list
            article_entities[article_id] = [r[0] for r in results if r[0] in entity_list]

        # Add entity mentions to the DataFrame
        articles_df['entities'] = articles_df['id'].map(article_entities)

        # Filter to only include articles mentioning at least 2 entities from the list
        articles_df = articles_df[articles_df['entities'].apply(lambda x: len(x) >= 2)]

        if articles_df.empty:
            logger.warning(f"No articles found mentioning at least 2 of the specified entities")
            return None

        logger.info(f"Found {len(articles_df)} articles mentioning at least 2 of the specified entities")

        # Convert seendate to datetime
        articles_df['seendate'] = pd.to_datetime(articles_df['seendate'])

        # Identify significant events (clusters of articles)
        events = self._identify_cross_entity_events(
            articles_df,
            cluster_threshold,
            min_articles
        )

        if not events:
            logger.warning(f"No significant cross-entity events found")
            return None

        logger.info(f"Identified {len(events)} significant cross-entity events")

        # Create event timeline visualization
        event_timeline_path = os.path.join(
            output_dir,
            f"cross_entity_events_{'_'.join([e.replace(' ', '_') for e in entity_list[:3]])}.png"
        )
        self._create_cross_entity_event_visualization(
            entity_list,
            events,
            event_timeline_path
        )

        # Create event timeline data
        event_timeline_data = {
            'entities': entity_list,
            'total_events': len(events),
            'events': events,
            'event_timeline_chart': event_timeline_path
        }

        # Save event timeline data
        event_json_path = os.path.join(
            output_dir,
            f"cross_entity_events_{'_'.join([e.replace(' ', '_') for e in entity_list[:3]])}.json"
        )
        with open(event_json_path, 'w') as f:
            json.dump(event_timeline_data, f, indent=2)

        logger.info(f"Saved cross-entity event timeline to {event_json_path}")

        return event_timeline_data

    def _identify_cross_entity_events(self, articles_df, cluster_threshold, min_articles):
        """
        Identify significant cross-entity events (clusters of articles)

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

            # Count entity co-occurrences in this cluster
            entity_counts = defaultdict(int)
            entity_pairs = defaultdict(int)

            for _, row in cluster_articles.iterrows():
                # Count individual entities
                for entity in row['entities']:
                    entity_counts[entity] += 1

                # Count entity pairs
                entities = row['entities']
                for i in range(len(entities)):
                    for j in range(i+1, len(entities)):
                        pair = tuple(sorted([entities[i], entities[j]]))
                        entity_pairs[pair] += 1

            # Get top entities and pairs
            top_entities = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)
            top_pairs = sorted(entity_pairs.items(), key=lambda x: x[1], reverse=True)

            # Create event
            event = {
                'start_date': peak_start.strftime('%Y-%m-%d'),
                'end_date': peak_end.strftime('%Y-%m-%d'),
                'peak_date': peak_date.strftime('%Y-%m-%d'),
                'article_count': len(cluster_articles),
                'peak_count': peak_count,
                'entity_counts': {entity: count for entity, count in top_entities},
                'entity_pairs': {f"{pair[0]}-{pair[1]}": count for pair, count in top_pairs[:5]},
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
                    'trust_score': float(row['trust_score']),
                    'entities': row['entities']
                })

            events.append(event)

        # Sort events by date
        events.sort(key=lambda x: x['peak_date'])

        return events

    def _create_network_visualization(self, entity_list, entity_pairs, output_path):
        """Create a network visualization of entity co-occurrences"""
        # Create a graph
        G = nx.Graph()

        # Add nodes (entities)
        for entity in entity_list:
            G.add_node(entity)

        # Add edges (co-occurrences)
        for entity1, entity2, weight in entity_pairs:
            G.add_edge(entity1, entity2, weight=weight)

        # Set up the figure
        plt.figure(figsize=(12, 10))

        # Calculate node sizes based on degree
        node_sizes = [300 * (1 + G.degree(node)) for node in G.nodes()]

        # Calculate edge widths based on weight
        edge_widths = [0.5 + 2 * G[u][v]['weight'] / max(1, max([G[a][b]['weight'] for a, b in G.edges()]))
                      for u, v in G.edges()]

        # Set node colors
        node_colors = sns.color_palette("husl", len(G.nodes()))

        # Draw the graph
        pos = nx.spring_layout(G, seed=42)  # Position nodes using force-directed layout

        # Draw nodes
        nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors, alpha=0.8)

        # Draw edges
        nx.draw_networkx_edges(G, pos, width=edge_widths, alpha=0.5, edge_color='gray')

        # Draw labels
        nx.draw_networkx_labels(G, pos, font_size=10, font_family='sans-serif')

        # Set title
        plt.title(f"Entity Co-occurrence Network", fontsize=16)

        # Remove axis
        plt.axis('off')

        # Add a legend for edge weights
        if entity_pairs:
            max_weight = max([w for _, _, w in entity_pairs])
            legend_elements = [
                plt.Line2D([0], [0], color='gray', lw=0.5 + 2 * (max_weight / 4) / max_weight, alpha=0.5, label=f'{max_weight // 4} co-occurrences'),
                plt.Line2D([0], [0], color='gray', lw=0.5 + 2 * (max_weight / 2) / max_weight, alpha=0.5, label=f'{max_weight // 2} co-occurrences'),
                plt.Line2D([0], [0], color='gray', lw=0.5 + 2 * (3 * max_weight / 4) / max_weight, alpha=0.5, label=f'{3 * max_weight // 4} co-occurrences'),
                plt.Line2D([0], [0], color='gray', lw=0.5 + 2, alpha=0.5, label=f'{max_weight} co-occurrences')
            ]
            plt.legend(handles=legend_elements, loc='lower right')

        # Adjust layout
        plt.tight_layout()

        # Save the plot
        plt.savefig(output_path)
        plt.close()

        logger.info(f"Created network visualization at {output_path}")

    def _create_matrix_visualization(self, entity_list, co_occurrences, output_path):
        """Create a matrix visualization of entity co-occurrences"""
        # Create a matrix of co-occurrences
        matrix = np.zeros((len(entity_list), len(entity_list)))

        # Fill the matrix
        for i, entity1 in enumerate(entity_list):
            for j, entity2 in enumerate(entity_list):
                if i == j:
                    matrix[i, j] = 0  # No self-loops
                elif entity1 in co_occurrences and entity2 in co_occurrences[entity1]:
                    matrix[i, j] = co_occurrences[entity1][entity2]
                elif entity2 in co_occurrences and entity1 in co_occurrences[entity2]:
                    matrix[i, j] = co_occurrences[entity2][entity1]

        # Set up the figure
        plt.figure(figsize=(12, 10))

        # Create heatmap
        sns.heatmap(
            matrix,
            annot=True,
            fmt='.1f',  # Use float format instead of integer
            cmap='YlGnBu',
            xticklabels=entity_list,
            yticklabels=entity_list,
            square=True
        )

        # Set title and labels
        plt.title(f"Entity Co-occurrence Matrix", fontsize=16)
        plt.xlabel('Entity', fontsize=12)
        plt.ylabel('Entity', fontsize=12)

        # Rotate x-axis labels
        plt.xticks(rotation=45, ha='right')

        # Adjust layout
        plt.tight_layout()

        # Save the plot
        plt.savefig(output_path)
        plt.close()

        logger.info(f"Created matrix visualization at {output_path}")

    def _create_cross_entity_event_visualization(self, entity_list, events, output_path):
        """Create a visualization of cross-entity events"""
        # Set up the figure
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

            # Get top entity pair
            top_pair = max(event['entity_pairs'].items(), key=lambda x: x[1]) if event['entity_pairs'] else ('Unknown', 0)

            # Add label
            plt.annotate(
                f"Event {i+1}: {top_pair[0]}",
                xy=(date, count),
                xytext=(10, 10),
                textcoords='offset points',
                fontsize=9,
                bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5)
            )

        # Set title and labels
        plt.title(f"Cross-Entity Events Timeline", fontsize=16)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Number of Articles at Peak', fontsize=12)

        # Format x-axis
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
        plt.xticks(rotation=45, ha='right')

        # Add grid
        plt.grid(True, linestyle='--', alpha=0.7)

        # Add entity legend
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=color, markersize=10,
                      label=entity, alpha=0.7)
            for entity, color in zip(entity_list[:5], sns.color_palette("husl", len(entity_list[:5])))
        ]
        plt.legend(handles=legend_elements, loc='upper right')

        # Adjust layout
        plt.tight_layout()

        # Save the plot
        plt.savefig(output_path)
        plt.close()

        logger.info(f"Created cross-entity event visualization at {output_path}")

def generate_cross_entity_report(cross_entity_data, output_dir="timelines"):
    """
    Generate a markdown report for cross-entity analysis

    Args:
        cross_entity_data: Cross-entity analysis results
        output_dir: Directory to save the report

    Returns:
        Path to the report file
    """
    if not cross_entity_data:
        logger.warning("No cross-entity data provided")
        return None

    entity_list = cross_entity_data['entities']

    # Create report content
    report = f"""# Cross-Entity Analysis Report

## Overview

This report analyzes the relationships and events involving the following entities:
{', '.join(entity_list)}

## Entity Co-occurrences

The following visualization shows how often these entities are mentioned together in articles:

![Entity Network](entity_network_{'_'.join([e.replace(' ', '_') for e in entity_list[:3]])}.png)

![Entity Matrix](entity_matrix_{'_'.join([e.replace(' ', '_') for e in entity_list[:3]])}.png)

## Cross-Entity Events

The timeline below shows significant events involving multiple entities:

![Cross-Entity Events](cross_entity_events_{'_'.join([e.replace(' ', '_') for e in entity_list[:3]])}.png)

## Significant Events

"""

    # Add events
    if 'events' in cross_entity_data:
        for i, event in enumerate(cross_entity_data['events']):
            # Get top entity pair
            top_pair = max(event['entity_pairs'].items(), key=lambda x: x[1]) if event['entity_pairs'] else ('Unknown', 0)

            report += f"### Event {i+1}: {top_pair[0]}\n\n"
            report += f"- **Date Range**: {event['start_date']} to {event['end_date']}\n"
            report += f"- **Peak Date**: {event['peak_date']}\n"
            report += f"- **Article Count**: {event['article_count']} (Peak: {event['peak_count']})\n\n"

            report += "#### Entities Involved\n\n"
            for entity, count in event['entity_counts'].items():
                report += f"- {entity}: {count} articles\n"

            report += "\n#### Entity Pairs\n\n"
            for pair, count in event['entity_pairs'].items():
                report += f"- {pair}: {count} articles\n"

            report += "\n#### Top Themes\n\n"
            for theme, count in event['themes'].items():
                report += f"- {theme}: {count} articles\n"

            report += "\n#### Top Sources\n\n"
            for source, count in event['sources'].items():
                report += f"- {source}: {count} articles\n"

            report += "\n#### Key Articles\n\n"
            for article in event['top_articles']:
                entities_str = ', '.join(article['entities'])
                report += f"- [{article['title']}]({article['url']}) - {article['source']} ({article['date']}, Trust: {article['trust_score']:.2f})\n"
                report += f"  - Entities: {entities_str}\n"

            report += "\n"

    # Save report
    report_path = os.path.join(output_dir, f"cross_entity_report_{'_'.join([e.replace(' ', '_') for e in entity_list[:3]])}.md")
    with open(report_path, 'w') as f:
        f.write(report)

    logger.info(f"Generated cross-entity report saved to {report_path}")

    return report_path
