# GDELT News Dataset Generator and Analyzer

This project provides tools to fetch and analyze news articles from the GDELT Global Knowledge Graph (GKG) based on themes. It creates a structured dataset for analysis and visualization.

## Available Datasets

1. **Weekly Dataset**: A dataset of news articles from the past week
   - Located in the `dataset` directory
   - Contains approximately 4,300 articles across 90 themes
   - Analysis available in the `analysis` directory

2. **6-Month Dataset**: A comprehensive dataset spanning 6 months
   - Located in the `dataset_6months` directory
   - Contains approximately 4,000 articles across 41 themes
   - Analysis available in the `analysis_6months` directory
   - Provides deeper insights into trends and patterns over time

## Components

1. **Theme Extraction**: `gdelt_useful_themes.jsonl` - A curated list of useful themes from the GDELT GKG.
2. **Data Fetcher**: `gdelt_data_fetcher.py` - Fetches news articles from the GDELT API based on themes.
3. **Data Analyzer**: `gdelt_data_analyzer.py` - Analyzes and visualizes the dataset.
4. **Integration Script**: `integrate_gdelt_data.py` - Integrates the GDELT dataset with the Hydra News system.

## Getting Started

### Prerequisites

- Python 3.6+
- Required packages: `pandas`, `gdeltdoc`, `matplotlib`, `seaborn`, `tqdm`

### Installation

```bash
pip install pandas gdeltdoc matplotlib seaborn tqdm
```

### Usage

1. **Generate the dataset**:

```bash
python gdelt_data_fetcher.py
```

This will:
- Load themes from `gdelt_useful_themes.jsonl`
- Fetch news articles from the past week for each theme
- Save the results to the `dataset` directory

2. **Analyze the dataset**:

```bash
python gdelt_data_analyzer.py
```

This will:
- Load the dataset from the `dataset` directory
- Analyze the data and generate visualizations
- Save the results to the `analysis` directory
- Generate a report at `analysis/report.md`

## Dataset Structure

The dataset is organized as follows:

- `dataset/all_articles.csv`: All articles in a single CSV file
- `dataset/themes.json`: Mapping of theme IDs to descriptions
- `dataset/themes/`: Directory containing CSV files for each theme
- `dataset/summary.json`: Summary statistics about the dataset

## Analysis

The analysis includes:

- Theme distribution
- Temporal analysis (by date, hour, day of week)
- Source analysis (domains, TLDs, languages, countries)
- Theme relationships

## Example Visualizations

- Theme distribution
- Articles by date/hour/day
- Top domains and TLDs
- Language and country distribution
- Theme correlation matrix

## Integration with Hydra News

This dataset can be used with the Hydra News system to:

1. **Train Claim Detection Models**: The articles can be used to train and improve the claim detection algorithms.
2. **Enhance Entity Extraction**: The diverse set of articles helps improve entity recognition across different domains.
3. **Test Cross-Reference Verification**: The dataset provides real-world examples for testing the cross-reference verification system.
4. **Benchmark System Performance**: Use the dataset to measure the performance and accuracy of the content processing engine.
5. **Develop Visualization Tools**: The analysis results can inform the development of the user interface for displaying verification status.

## Customization

You can customize the data fetcher by modifying the following parameters in `gdelt_data_fetcher.py`:

- `MAX_ARTICLES_PER_THEME`: Maximum number of articles to fetch per theme
- `RATE_LIMIT_DELAY`: Delay between API calls to avoid rate limiting
- `MAX_THEMES`: Maximum number of themes to process

## Acknowledgments

- [GDELT Project](https://www.gdeltproject.org/) for providing the data
- [gdeltdoc](https://github.com/alex9smith/gdelt-doc-api) Python package for the API client
