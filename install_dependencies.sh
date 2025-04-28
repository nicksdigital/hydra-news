#!/bin/bash
# Script to install dependencies for chunk-based processing

# Activate virtual environment
source venv/bin/activate

# Install transformers and related packages
pip install transformers torch

# Install watchdog for monitoring chunks
pip install watchdog

# Install spaCy and download models (as fallback)
pip install spacy
python -m spacy download en_core_web_sm
python -m spacy download fr_core_news_sm

# Install NLTK and download resources (as fallback)
pip install nltk
python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger'); nltk.download('maxent_ne_chunker'); nltk.download('words')"

echo "Dependencies installed successfully!"
