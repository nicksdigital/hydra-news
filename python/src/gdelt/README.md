# GDELT News Data Fetcher and Analyzer

This package provides tools for fetching, processing, and analyzing news data from the GDELT Project.

## Components

1. **GDELT Data Fetcher**: Fetches news articles from the GDELT API based on themes
2. **GDELT Data Analyzer**: Analyzes and visualizes the fetched dataset
3. **Visualization Tools**: Creates visualizations of the analysis results
4. **Report Generator**: Generates reports from the analysis

## Installation

### Prerequisites

- Python 3.6+
- Required packages:
  - pandas
  - gdeltdoc
  - matplotlib
  - seaborn
  - nltk
  - textblob (optional, for sentiment analysis)
  - scikit-learn (optional, for topic modeling)
  - wordcloud (optional, for word cloud visualization)

### Install Required Packages

```bash
pip install pandas gdeltdoc matplotlib seaborn nltk textblob scikit-learn wordcloud
```

## Usage

### Fetching GDELT News Data

```bash
python -m gdelt.fetch_gdelt --output-dir dataset_gdelt_month --max-themes 30 --languages English French --timespan 1m
```

Options:
- `--themes-file`: Path to themes JSONL file (default: gdelt_useful_themes.jsonl)
- `--output-dir`: Output directory (default: dataset_gdelt_month)
- `--max-themes`: Maximum number of themes to process (default: 30)
- `--max-articles`: Maximum number of articles per theme and language (default: 100)
- `--languages`: Languages to fetch (default: English French)
- `--timespan`: Timespan for fetching articles (default: 1m for 1 month)
- `--delay`: Delay between API calls in seconds (default: 1)
- `--log-file`: Path to log file

### Analyzing GDELT News Data

```bash
python -m gdelt.analyze_gdelt --dataset-dir dataset_gdelt_month --output-dir analysis_gdelt
```

Options:
- `--dataset-dir`: Directory containing the dataset (default: dataset_gdelt_month)
- `--output-dir`: Directory to save the analysis results (default: analysis_gdelt)
- `--log-file`: Path to log file
- `--no-sentiment`: Disable sentiment analysis
- `--no-topics`: Disable topic modeling
- `--n-topics`: Number of topics for topic modeling (default: 10)
- `--split-chunks`: Split dataset into chunks
- `--chunk-size`: Number of articles per chunk (default: 1000)

## Dataset Structure

The fetched dataset is organized as follows:

- `all_articles.csv`: All articles in a single CSV file
- `themes.json`: Mapping of theme IDs to descriptions
- `themes/`: Directory containing CSV files for each theme
- `languages/`: Directory containing CSV files for each language
- `summary.json`: Summary statistics about the dataset

## Analysis Output

The analysis output includes:

- Visualizations of theme distribution, time patterns, source distribution, etc.
- A markdown report summarizing the analysis
- A JSON summary of the analysis results
- CSV exports of the analysis results

## Modules

- `fetch_gdelt.py`: Main script for fetching GDELT news data
- `analyze_gdelt.py`: Main script for analyzing GDELT news data
- `analyzer/core.py`: Core functionality for analyzing GDELT news data
- `analyzer/data_loader.py`: Functions for loading and preprocessing data
- `analyzer/theme_analyzer.py`: Functions for analyzing themes
- `analyzer/time_analyzer.py`: Functions for analyzing time patterns
- `analyzer/source_analyzer.py`: Functions for analyzing sources
- `analyzer/text_analyzer.py`: Functions for analyzing text content
- `analyzer/visualizer.py`: Functions for creating visualizations
- `analyzer/report_generator.py`: Functions for generating reports

## Examples

### Fetch English and French News for the Past Month

```bash
python -m gdelt.fetch_gdelt --output-dir dataset_gdelt_month --languages English French --timespan 1m
```

### Analyze the Dataset with Sentiment Analysis and Topic Modeling

```bash
python -m gdelt.analyze_gdelt --dataset-dir dataset_gdelt_month --output-dir analysis_gdelt
```

### Analyze the Dataset without Sentiment Analysis

```bash
python -m gdelt.analyze_gdelt --dataset-dir dataset_gdelt_month --output-dir analysis_gdelt --no-sentiment
```

### Split the Dataset into Chunks

```bash
python -m gdelt.analyze_gdelt --dataset-dir dataset_gdelt_month --output-dir analysis_gdelt --split-chunks --chunk-size 1000
```
