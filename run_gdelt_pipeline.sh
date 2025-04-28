#!/bin/bash
# GDELT Analysis Pipeline Runner
# This script provides an easy way to run the GDELT analysis pipeline

# Set default values
DATASET_DIR="dataset_gdelt_enhanced"
ANALYSIS_DIR="analysis_gdelt_enhanced"
MAX_ARTICLES=4000
TIMESPAN="1m"
TOP_ENTITIES=50
MIN_MENTIONS=3
DAYS_TO_PREDICT=14
DAYS_BACK=30
PORT=5000

# Function to display help
show_help() {
    echo "GDELT Analysis Pipeline Runner"
    echo ""
    echo "Usage: $0 [options] [command]"
    echo ""
    echo "Commands:"
    echo "  fetch       Fetch data from GDELT"
    echo "  analyze     Analyze the fetched data"
    echo "  events      Run event detection"
    echo "  predict     Run prediction models"
    echo "  dashboard   Start the dashboard"
    echo "  all         Run the entire pipeline"
    echo ""
    echo "Options:"
    echo "  -h, --help                 Show this help message"
    echo "  -d, --dataset-dir DIR      Set dataset directory (default: $DATASET_DIR)"
    echo "  -a, --analysis-dir DIR     Set analysis directory (default: $ANALYSIS_DIR)"
    echo "  -m, --max-articles NUM     Set maximum number of articles to fetch (default: $MAX_ARTICLES)"
    echo "  -t, --timespan SPAN        Set timespan for fetching articles (default: $TIMESPAN)"
    echo "  -e, --top-entities NUM     Set number of top entities to analyze (default: $TOP_ENTITIES)"
    echo "  -n, --min-mentions NUM     Set minimum number of mentions for an entity (default: $MIN_MENTIONS)"
    echo "  -p, --days-to-predict NUM  Set number of days to predict (default: $DAYS_TO_PREDICT)"
    echo "  -b, --days-back NUM        Set number of days to look back for event detection (default: $DAYS_BACK)"
    echo "  --port NUM                 Set port for the dashboard (default: $PORT)"
    echo "  -i, --incremental          Enable incremental fetching"
    echo "  --no-sentiment             Disable sentiment analysis"
    echo "  --no-topics                Disable topic modeling"
    echo "  --no-entities              Disable entity extraction"
    echo "  --no-browser               Do not open browser automatically"
    echo ""
    echo "Examples:"
    echo "  $0 fetch                   Fetch data from GDELT"
    echo "  $0 analyze                 Analyze the fetched data"
    echo "  $0 all                     Run the entire pipeline"
    echo "  $0 -m 1000 -t 7d fetch     Fetch 1000 articles from the last 7 days"
    echo "  $0 -e 20 events            Run event detection for top 20 entities"
    echo "  $0 dashboard               Start the dashboard"
}

# Parse command line arguments
POSITIONAL_ARGS=()
INCREMENTAL=""
NO_SENTIMENT=""
NO_TOPICS=""
NO_ENTITIES=""
NO_BROWSER=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -d|--dataset-dir)
            DATASET_DIR="$2"
            shift 2
            ;;
        -a|--analysis-dir)
            ANALYSIS_DIR="$2"
            shift 2
            ;;
        -m|--max-articles)
            MAX_ARTICLES="$2"
            shift 2
            ;;
        -t|--timespan)
            TIMESPAN="$2"
            shift 2
            ;;
        -e|--top-entities)
            TOP_ENTITIES="$2"
            shift 2
            ;;
        -n|--min-mentions)
            MIN_MENTIONS="$2"
            shift 2
            ;;
        -p|--days-to-predict)
            DAYS_TO_PREDICT="$2"
            shift 2
            ;;
        -b|--days-back)
            DAYS_BACK="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        -i|--incremental)
            INCREMENTAL="--incremental"
            shift
            ;;
        --no-sentiment)
            NO_SENTIMENT="--no-sentiment"
            shift
            ;;
        --no-topics)
            NO_TOPICS="--no-topics"
            shift
            ;;
        --no-entities)
            NO_ENTITIES="--no-entities"
            shift
            ;;
        --no-browser)
            NO_BROWSER="--no-browser"
            shift
            ;;
        -*|--*)
            echo "Unknown option $1"
            show_help
            exit 1
            ;;
        *)
            POSITIONAL_ARGS+=("$1")
            shift
            ;;
    esac
done

# Restore positional arguments
set -- "${POSITIONAL_ARGS[@]}"

# Check if a command was provided
if [ $# -eq 0 ]; then
    echo "Error: No command specified"
    show_help
    exit 1
fi

COMMAND=$1

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Function to run fetch data
run_fetch() {
    echo "Fetching data from GDELT..."
    python -m python.src.gdelt.fetch_gdelt_enhanced \
        --output-dir "$DATASET_DIR" \
        --max-articles "$MAX_ARTICLES" \
        --timespan "$TIMESPAN" \
        $INCREMENTAL
    
    if [ $? -ne 0 ]; then
        echo "Error: Data fetching failed"
        exit 1
    fi
    
    echo "Data fetching completed successfully"
}

# Function to run analyze data
run_analyze() {
    echo "Analyzing data..."
    python -m python.src.gdelt.analyze_gdelt_all_entities \
        --dataset-dir "$DATASET_DIR" \
        --output-dir "$ANALYSIS_DIR" \
        --top-entities "$TOP_ENTITIES" \
        --min-mentions "$MIN_MENTIONS" \
        $NO_SENTIMENT $NO_TOPICS $NO_ENTITIES
    
    if [ $? -ne 0 ]; then
        echo "Error: Data analysis failed"
        exit 1
    fi
    
    echo "Data analysis completed successfully"
}

# Function to run event detection
run_events() {
    echo "Running event detection..."
    python -m python.src.gdelt.run_advanced_event_detection \
        --db-path "$ANALYSIS_DIR/gdelt_news.db" \
        --output-dir "$ANALYSIS_DIR/events" \
        --top-entities "$TOP_ENTITIES" \
        --min-mentions "$MIN_MENTIONS" \
        --days-back "$DAYS_BACK" \
        --all-analyses
    
    if [ $? -ne 0 ]; then
        echo "Warning: Event detection encountered errors"
    else
        echo "Event detection completed successfully"
    fi
}

# Function to run prediction models
run_predict() {
    echo "Running prediction models..."
    python -m python.src.gdelt.run_enhanced_analysis \
        --predict \
        --analysis-dir "$ANALYSIS_DIR" \
        --days-to-predict "$DAYS_TO_PREDICT" \
        --top-entities "$TOP_ENTITIES"
    
    if [ $? -ne 0 ]; then
        echo "Warning: Prediction encountered errors"
    else
        echo "Prediction completed successfully"
    fi
}

# Function to start dashboard
run_dashboard() {
    echo "Starting dashboard on port $PORT..."
    python -m python.src.gdelt.run_dashboard \
        --port "$PORT" \
        --db-path "$ANALYSIS_DIR/gdelt_news.db" \
        $NO_BROWSER
    
    if [ $? -ne 0 ]; then
        echo "Error: Failed to start dashboard"
        exit 1
    fi
}

# Function to run the full pipeline
run_all() {
    echo "Running full GDELT analysis pipeline..."
    
    # Run fetch data
    run_fetch
    
    # Run analyze data
    run_analyze
    
    # Run event detection
    run_events
    
    # Run prediction models
    run_predict
    
    # Start dashboard
    run_dashboard
}

# Execute the specified command
case $COMMAND in
    fetch)
        run_fetch
        ;;
    analyze)
        run_analyze
        ;;
    events)
        run_events
        ;;
    predict)
        run_predict
        ;;
    dashboard)
        run_dashboard
        ;;
    all)
        run_all
        ;;
    *)
        echo "Error: Unknown command '$COMMAND'"
        show_help
        exit 1
        ;;
esac

exit 0
