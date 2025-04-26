#!/usr/bin/env python3
"""
GDELT Dataset Analyzer

This script analyzes the filtered GDELT dataset and generates a report.
"""

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import re
from datetime import datetime

# Configuration
DATASET_DIR = "dataset_gdelt_en_fr"
OUTPUT_DIR = "analysis_gdelt_en_fr"

def load_dataset():
    """Load the dataset from CSV and JSON files"""
    # Load all articles
    articles_path = os.path.join(DATASET_DIR, "all_articles.csv")
    articles = pd.read_csv(articles_path)
    
    # Load theme information
    themes_path = os.path.join(DATASET_DIR, "themes.json")
    with open(themes_path, 'r') as f:
        themes = json.load(f)
    
    # Load summary
    summary_path = os.path.join(DATASET_DIR, "summary.json")
    with open(summary_path, 'r') as f:
        summary = json.load(f)
    
    return articles, themes, summary

def preprocess_articles(articles, themes):
    """Preprocess the articles dataframe"""
    # Convert seendate to datetime
    articles['seendate'] = pd.to_datetime(articles['seendate'])
    
    # Extract date components
    articles['date'] = articles['seendate'].dt.date
    articles['hour'] = articles['seendate'].dt.hour
    articles['day_of_week'] = articles['seendate'].dt.day_name()
    
    # Add theme description
    articles['theme_description'] = articles['theme_id'].map(themes)
    
    # Extract top-level domain
    articles['tld'] = articles['domain'].apply(lambda x: x.split('.')[-1] if pd.notna(x) else None)
    
    return articles

def analyze_themes(articles, themes):
    """Analyze theme distribution"""
    # Count articles per theme
    theme_counts = articles['theme_id'].value_counts().reset_index()
    theme_counts.columns = ['theme_id', 'count']
    
    # Add theme description
    theme_counts['description'] = theme_counts['theme_id'].map(themes)
    
    return theme_counts

def analyze_time_patterns(articles):
    """Analyze time patterns in the articles"""
    # Articles by date
    date_counts = articles['date'].value_counts().sort_index()
    
    # Articles by hour of day
    hour_counts = articles['hour'].value_counts().sort_index()
    
    # Articles by day of week
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_counts = articles['day_of_week'].value_counts()
    day_counts = day_counts.reindex(day_order)
    
    return date_counts, hour_counts, day_counts

def analyze_domains(articles):
    """Analyze domain distribution"""
    # Top domains
    domain_counts = articles['domain'].value_counts().head(20)
    
    # Top TLDs
    tld_counts = articles['tld'].value_counts().head(10)
    
    return domain_counts, tld_counts

def analyze_languages(articles):
    """Analyze language distribution"""
    # Language counts
    language_counts = articles['language'].value_counts()
    
    return language_counts

def analyze_countries(articles):
    """Analyze source country distribution"""
    # Country counts
    country_counts = articles['sourcecountry'].value_counts().head(15)
    
    return country_counts

def create_visualizations(articles, theme_counts, date_counts, hour_counts, 
                         day_counts, domain_counts, tld_counts, language_counts, 
                         country_counts):
    """Create visualizations of the analysis results"""
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Set the style
    sns.set(style="whitegrid")
    
    # 1. Theme distribution
    plt.figure(figsize=(12, 8))
    sns.barplot(x='count', y='theme_id', data=theme_counts.head(20), palette='viridis')
    plt.title('Top 20 Themes by Article Count')
    plt.xlabel('Number of Articles')
    plt.ylabel('Theme')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'theme_distribution.png'))
    plt.close()
    
    # 2. Articles by date
    plt.figure(figsize=(12, 6))
    date_counts.plot(kind='bar', color='skyblue')
    plt.title('Articles by Date')
    plt.xlabel('Date')
    plt.ylabel('Number of Articles')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'articles_by_date.png'))
    plt.close()
    
    # 3. Articles by hour of day
    plt.figure(figsize=(12, 6))
    hour_counts.plot(kind='bar', color='lightgreen')
    plt.title('Articles by Hour of Day')
    plt.xlabel('Hour')
    plt.ylabel('Number of Articles')
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'articles_by_hour.png'))
    plt.close()
    
    # 4. Articles by day of week
    plt.figure(figsize=(12, 6))
    day_counts.plot(kind='bar', color='salmon')
    plt.title('Articles by Day of Week')
    plt.xlabel('Day of Week')
    plt.ylabel('Number of Articles')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'articles_by_day.png'))
    plt.close()
    
    # 5. Top domains
    plt.figure(figsize=(12, 8))
    sns.barplot(x=domain_counts.values, y=domain_counts.index, palette='Blues_d')
    plt.title('Top 20 Domains')
    plt.xlabel('Number of Articles')
    plt.ylabel('Domain')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'top_domains.png'))
    plt.close()
    
    # 6. Top TLDs
    plt.figure(figsize=(10, 6))
    sns.barplot(x=tld_counts.values, y=tld_counts.index, palette='Greens_d')
    plt.title('Top 10 Top-Level Domains')
    plt.xlabel('Number of Articles')
    plt.ylabel('TLD')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'top_tlds.png'))
    plt.close()
    
    # 7. Language distribution
    plt.figure(figsize=(10, 6))
    sns.barplot(x=language_counts.values, y=language_counts.index, palette='Reds_d')
    plt.title('Language Distribution')
    plt.xlabel('Number of Articles')
    plt.ylabel('Language')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'language_distribution.png'))
    plt.close()
    
    # 8. Country distribution
    plt.figure(figsize=(10, 8))
    sns.barplot(x=country_counts.values, y=country_counts.index, palette='Purples_d')
    plt.title('Top 15 Source Countries')
    plt.xlabel('Number of Articles')
    plt.ylabel('Country')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'country_distribution.png'))
    plt.close()

def generate_report(articles, themes, summary, theme_counts, date_counts, 
                   hour_counts, day_counts, domain_counts, tld_counts, 
                   language_counts, country_counts):
    """Generate a markdown report of the analysis"""
    report = f"""# GDELT News Dataset Analysis (English & French Articles)

## Dataset Summary

- **Total Articles**: {summary['total_articles']}
- **Total Themes**: {summary['total_themes']}
- **Languages**: {', '.join(summary['languages'])}
- **Timespan**: {summary['timespan']}
- **Filter Date**: {summary['filter_date']}

## Theme Distribution

The dataset contains articles from {summary['total_themes']} different themes. The top 10 themes are:

| Theme | Description | Count |
|-------|-------------|-------|
"""
    
    # Add top 10 themes
    for _, row in theme_counts.head(10).iterrows():
        report += f"| {row['theme_id']} | {row['description']} | {row['count']} |\n"
    
    report += """
## Temporal Analysis

### Articles by Date

The distribution of articles over the date range:

![Articles by Date](articles_by_date.png)

### Articles by Hour of Day

The distribution of articles by hour of the day:

![Articles by Hour](articles_by_hour.png)

### Articles by Day of Week

The distribution of articles by day of the week:

![Articles by Day](articles_by_day.png)

## Source Analysis

### Top Domains

The top 10 domains by article count:

| Domain | Count |
|--------|-------|
"""
    
    # Add top 10 domains
    for domain, count in domain_counts.head(10).items():
        report += f"| {domain} | {count} |\n"
    
    report += """
### Top TLDs

The top 5 top-level domains:

| TLD | Count |
|-----|-------|
"""
    
    # Add top 5 TLDs
    for tld, count in tld_counts.head(5).items():
        report += f"| {tld} | {count} |\n"
    
    report += """
### Language Distribution

The distribution of articles by language:

| Language | Count |
|----------|-------|
"""
    
    # Add language counts
    for lang, count in language_counts.items():
        report += f"| {lang} | {count} |\n"
    
    report += """
### Country Distribution

The distribution of articles by source country:

![Country Distribution](country_distribution.png)

## Conclusion

This analysis provides an overview of the English and French news articles collected from GDELT over a 1-month period. The dataset covers a wide range of themes and sources, providing a comprehensive view of recent news coverage in these languages.

The dataset is well-suited for:

1. **Training NLP Models**: The articles can be used to train and improve natural language processing models for news analysis.
2. **Cross-lingual Analysis**: The inclusion of both English and French articles enables cross-lingual studies and comparisons.
3. **Theme Classification**: The diverse set of themes allows for training theme classification models.
4. **Source Analysis**: The dataset provides insights into which sources cover which themes.
5. **Temporal Analysis**: The dataset captures temporal patterns in news coverage.

"""
    
    # Save the report
    report_path = os.path.join(OUTPUT_DIR, "report.md")
    with open(report_path, 'w') as f:
        f.write(report)
    
    # Also save an HTML version
    html_report = f"""<!DOCTYPE html>
<html>
<head>
    <title>GDELT News Dataset Analysis</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 1000px; margin: 0 auto; padding: 20px; }}
        h1, h2, h3 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        img {{ max-width: 100%; height: auto; margin: 20px 0; }}
    </style>
</head>
<body>
    {report.replace('# ', '<h1>').replace('## ', '<h2>').replace('### ', '<h3>').replace('\n\n', '</p><p>').replace('![', '<img src="').replace('](', '" alt="').replace(')', '">').replace('|', '').replace('\n', '<br>')}
</body>
</html>
"""
    
    html_path = os.path.join(OUTPUT_DIR, "report.html")
    with open(html_path, 'w') as f:
        f.write(html_report)
    
    print(f"Generated report at {report_path} and {html_path}")

def main():
    # Load the dataset
    print("Loading dataset...")
    articles, themes, summary = load_dataset()
    
    # Preprocess articles
    print("Preprocessing articles...")
    articles = preprocess_articles(articles, themes)
    
    # Analyze themes
    print("Analyzing theme distribution...")
    theme_counts = analyze_themes(articles, themes)
    
    # Analyze time patterns
    print("Analyzing time patterns...")
    date_counts, hour_counts, day_counts = analyze_time_patterns(articles)
    
    # Analyze domains
    print("Analyzing domains...")
    domain_counts, tld_counts = analyze_domains(articles)
    
    # Analyze languages
    print("Analyzing languages...")
    language_counts = analyze_languages(articles)
    
    # Analyze countries
    print("Analyzing countries...")
    country_counts = analyze_countries(articles)
    
    # Create visualizations
    print("Creating visualizations...")
    create_visualizations(articles, theme_counts, date_counts, hour_counts, 
                         day_counts, domain_counts, tld_counts, language_counts, 
                         country_counts)
    
    # Generate report
    print("Generating report...")
    generate_report(articles, themes, summary, theme_counts, date_counts, 
                   hour_counts, day_counts, domain_counts, tld_counts, 
                   language_counts, country_counts)
    
    print("Analysis complete!")

if __name__ == "__main__":
    main()
