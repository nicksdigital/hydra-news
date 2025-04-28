#!/bin/bash
# Script to install PostgreSQL dependencies for GDELT News Analysis

echo "Installing PostgreSQL dependencies for GDELT News Analysis..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Activated virtual environment"
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Activated virtual environment"
fi

# Install required Python packages
echo "Installing required Python packages..."
pip install --upgrade pip
pip install psycopg2-binary pandas tqdm nltk transformers torch

# Install PostgreSQL client tools if not already installed
if ! command -v psql &> /dev/null; then
    echo "PostgreSQL client tools not found. Installing..."
    
    # Detect OS
    if [ "$(uname)" == "Darwin" ]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install postgresql
        else
            echo "Homebrew not found. Please install Homebrew or PostgreSQL client tools manually."
            echo "Visit https://brew.sh/ for Homebrew installation instructions."
        fi
    elif [ "$(uname)" == "Linux" ]; then
        # Linux
        if command -v apt-get &> /dev/null; then
            # Debian/Ubuntu
            sudo apt-get update
            sudo apt-get install -y postgresql-client
        elif command -v yum &> /dev/null; then
            # RHEL/CentOS/Fedora
            sudo yum install -y postgresql
        else
            echo "Could not detect package manager. Please install PostgreSQL client tools manually."
        fi
    else
        echo "Unsupported operating system. Please install PostgreSQL client tools manually."
    fi
else
    echo "PostgreSQL client tools already installed"
fi

# Install jq for JSON parsing in shell scripts
if ! command -v jq &> /dev/null; then
    echo "jq not found. Installing..."
    
    # Detect OS
    if [ "$(uname)" == "Darwin" ]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install jq
        else
            echo "Homebrew not found. Please install jq manually."
        fi
    elif [ "$(uname)" == "Linux" ]; then
        # Linux
        if command -v apt-get &> /dev/null; then
            # Debian/Ubuntu
            sudo apt-get update
            sudo apt-get install -y jq
        elif command -v yum &> /dev/null; then
            # RHEL/CentOS/Fedora
            sudo yum install -y jq
        else
            echo "Could not detect package manager. Please install jq manually."
        fi
    else
        echo "Unsupported operating system. Please install jq manually."
    fi
else
    echo "jq already installed"
fi

# Download NLTK data
echo "Downloading NLTK data..."
python -c "import nltk; nltk.download('punkt')"

echo "Installation completed!"
echo "You can now run './setup_postgres.sh' to set up the PostgreSQL database."
