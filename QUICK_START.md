# GDELT News Analysis System - Quick Start Guide

This guide will help you get started with the GDELT News Analysis System quickly.

## Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Pipeline

The easiest way to run the system is using the provided bash script:

### Fetch Data

Fetch news articles from GDELT:

```bash
./run_gdelt_pipeline.sh fetch
```

For a smaller dataset (faster for testing):

```bash
./run_gdelt_pipeline.sh -m 1000 -t 7d fetch
```

### Analyze Data

Process the fetched data and extract entities:

```bash
./run_gdelt_pipeline.sh analyze
```

### Run Event Detection

Detect significant events in the data:

```bash
./run_gdelt_pipeline.sh events
```

### Run Prediction Models

Create prediction models for future entity mentions:

```bash
./run_gdelt_pipeline.sh predict
```

### Start the Dashboard

Visualize the analysis results:

```bash
./run_gdelt_pipeline.sh dashboard
```

### Run the Entire Pipeline

Run all steps in sequence:

```bash
./run_gdelt_pipeline.sh all
```

## Common Options

- `-m, --max-articles NUM`: Set maximum number of articles to fetch (default: 4000)
- `-t, --timespan SPAN`: Set timespan for fetching articles (default: 1m)
- `-e, --top-entities NUM`: Set number of top entities to analyze (default: 50)
- `-i, --incremental`: Enable incremental fetching (only fetch new articles)
- `--no-browser`: Do not open browser automatically when starting dashboard

For a complete list of options:

```bash
./run_gdelt_pipeline.sh --help
```

## Example Workflows

### Quick Test Run

For a quick test of the system with a small dataset:

```bash
# Fetch a small dataset
./run_gdelt_pipeline.sh -m 500 -t 3d fetch

# Analyze with fewer entities
./run_gdelt_pipeline.sh -e 10 analyze

# Run event detection
./run_gdelt_pipeline.sh events

# Start the dashboard
./run_gdelt_pipeline.sh dashboard
```

### Production Run

For a comprehensive analysis with a larger dataset:

```bash
# Fetch a larger dataset
./run_gdelt_pipeline.sh -m 5000 -t 30d fetch

# Analyze with more entities
./run_gdelt_pipeline.sh -e 100 analyze

# Run event detection with more historical data
./run_gdelt_pipeline.sh -b 60 events

# Run prediction with longer forecast
./run_gdelt_pipeline.sh -p 30 predict

# Start the dashboard
./run_gdelt_pipeline.sh dashboard
```

### Incremental Updates

For regular updates to an existing dataset:

```bash
# Fetch only new articles
./run_gdelt_pipeline.sh -i fetch

# Re-analyze with the new data
./run_gdelt_pipeline.sh analyze

# Update event detection and predictions
./run_gdelt_pipeline.sh events
./run_gdelt_pipeline.sh predict

# Start the dashboard
./run_gdelt_pipeline.sh dashboard
```

## Troubleshooting

- **Data Fetching Issues**: Try reducing the number of articles or timespan
- **Memory Errors**: Reduce the number of entities to analyze
- **Dashboard Not Starting**: Check if the port is already in use and try a different port
- **Missing Dependencies**: Make sure all dependencies are installed with `pip install -r requirements.txt`

## Next Steps

After getting familiar with the basic functionality, you can:

1. Customize the data fetching by modifying keywords in `python/src/gdelt/fetch_gdelt_enhanced.py`
2. Adjust event detection parameters in `python/src/gdelt/analyzer/event_detection/`
3. Explore the prediction models in `python/src/gdelt/analyzer/prediction/`
4. Customize the dashboard in `python/src/gdelt/visualizer/`
