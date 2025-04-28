# GDELT News Analysis System

This system processes GDELT news data in chunks, extracts entities, analyzes sentiment, and visualizes the results in a web dashboard. It includes an optimization daemon that continuously improves entity extraction over time.

## Components

1. **Data Chunking**: Splits large datasets into manageable chunks of 100 articles each.
2. **Entity Extraction**: Identifies and categorizes named entities (people, organizations, locations) in news articles.
3. **Sentiment Analysis**: Analyzes the sentiment of news articles using Hugging Face transformers.
4. **Dashboard**: Visualizes the extracted entities, sentiment, and other statistics.
5. **Optimization Daemon**: Continuously improves entity extraction by learning from processed data.
6. **Fetcher Daemon**: Continuously fetches new data from GDELT with CPU usage limits.
7. **Continuous Learning Daemon**: Optimizes model parameters through continuous evaluation and adjustment.

## Directory Structure

- `analysis_gdelt_chunks/`: Main output directory
  - `chunks/`: Contains article chunks to be processed
  - `gdelt_news.db`: SQLite database storing processed data
  - `entity_lists/`: Optimized entity lists maintained by the optimization daemon
  - `models/`: Trained models and parameters maintained by the continuous learning daemon

## Scripts

- `python/src/gdelt/analyzer/process_chunk.py`: Processes a single chunk of articles
- `python/src/gdelt/analyzer/simple_entity_extractor.py`: Extracts entities from text
- `python/src/gdelt/analyzer/sentiment_analyzer.py`: Analyzes sentiment in text
- `python/src/gdelt/analyzer/optimization_daemon.py`: Optimizes entity extraction over time
- `python/src/gdelt/analyzer/continuous_learning_daemon.py`: Optimizes model parameters through continuous learning
- `python/src/gdelt/fetcher/daemon_fetcher.py`: Continuously fetches new data from GDELT
- `python/src/gdelt/run_dashboard.py`: Runs the web dashboard
- `process_all_chunks.py`: Processes all chunks with a delay between them
- `run_complete_system.sh`: Runs all components together with CPU usage limits

## How to Run

1. **Install Dependencies**:
   ```
   ./install_dependencies.sh
   ```

2. **Split Data into Chunks**:
   ```
   python -m python.src.gdelt.split_into_small_chunks --input-file dataset_gdelt_enhanced/all_articles.csv --output-dir analysis_gdelt_chunks/chunks --chunk-size 100
   ```

3. **Run the Complete System**:
   ```
   ./run_complete_system.sh
   ```

4. **Access the Dashboard**:
   Open your browser and navigate to `http://127.0.0.1:5001`

## How It Works

1. The system processes article chunks one by one, extracting entities and analyzing sentiment.
2. Processed data is stored in a database (PostgreSQL or SQLite).
3. The dashboard visualizes the data in real-time as it's processed.
4. The optimization daemon runs in the background, continuously improving entity extraction by:
   - Analyzing entity contexts to determine correct entity types
   - Merging similar entities to reduce duplication
   - Updating trust scores based on source diversity
   - Maintaining curated lists of known entities
5. The continuous learning daemon optimizes model parameters through evaluation and adjustment.
6. The fetcher daemon continuously fetches new data from GDELT with CPU usage limits.

## Optimization Features

The system includes two optimization daemons that work together:

### Optimization Daemon
1. **Improved Entity Type Classification**: Learns from context to correctly classify entities.
2. **Entity Deduplication**: Merges similar entities to reduce redundancy.
3. **Trust Score Refinement**: Adjusts trust scores based on source diversity and mention frequency.
4. **Knowledge Base Building**: Maintains growing lists of known entities for better extraction.

### Continuous Learning Daemon
1. **Parameter Optimization**: Continuously adjusts model parameters based on performance metrics.
2. **Performance Evaluation**: Monitors precision, recall, and F1 scores for entity extraction.
3. **Sentiment Analysis Tuning**: Optimizes thresholds for positive, negative, and neutral sentiment.
4. **Trust Score Calibration**: Refines the weights used in trust score calculation.
5. **Adaptive Learning**: Adjusts learning strategies based on historical performance trends.

## Customization

You can customize the system by modifying these parameters in `run_complete_system.sh`:

- `DASHBOARD_PORT`: Port for the web dashboard (default: 5002)
- `CHUNK_DELAY`: Delay in seconds between processing chunks (default: 20)
- `OPTIMIZATION_INTERVAL`: Interval in seconds between optimization runs (default: 300)
- `LEARNING_INTERVAL`: Interval in seconds between learning cycles (default: 600)
- `FETCH_INTERVAL`: Interval in seconds between data fetches (default: 3600)
- `ARTICLES_PER_FETCH`: Number of articles to fetch each time (default: 500)
- `CHUNK_SIZE`: Number of articles per chunk (default: 100)
- `CPU_LIMIT`: CPU usage limit in percentage (default: 50)

## Database Options

The system supports two database backends:

### SQLite (Default)
- Simple setup with no additional configuration
- Good for small to medium datasets
- Limited concurrency (may experience "database is locked" errors with multiple processes)

### PostgreSQL (Recommended for Production)
- Better performance and concurrency handling
- Supports larger datasets
- Eliminates "database is locked" errors
- Requires PostgreSQL server installation

To use PostgreSQL:
1. Install PostgreSQL dependencies: `./install_postgres_deps.sh`
2. Set up PostgreSQL: `./setup_postgres.sh`
3. Run the system as usual: `./run_complete_system.sh`

For detailed PostgreSQL setup instructions, see `README_POSTGRES.md`.

## Troubleshooting

- **Dashboard Not Loading**: Check if the dashboard process is running and the port is available.
- **Entity Extraction Issues**: Check the optimization daemon logs for details.
- **Database Errors**:
  - For SQLite: Reset the database using `python -m python.src.gdelt.analyzer.reset_database`.
  - For PostgreSQL: Check PostgreSQL server status and connection settings in `config/database.json`.

## Performance Considerations

- Processing speed depends on the size of chunks and available system resources.
- The optimization daemon has minimal performance impact as it runs periodically.
- For large datasets, consider increasing the chunk size and optimization interval.
