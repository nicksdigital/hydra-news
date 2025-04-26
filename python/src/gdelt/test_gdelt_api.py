#!/usr/bin/env python3
"""
Test script for GDELT API
"""

import pandas as pd
from gdeltdoc import GdeltDoc, Filters

def test_basic_search():
    """Test a basic search with minimal parameters"""
    print("Testing basic search...")
    
    client = GdeltDoc()
    
    # Try a simple search with just a timespan
    filters = Filters(
        timespan="1d",  # Last day
        num_records=10
    )
    
    try:
        articles = client.article_search(filters)
        print(f"Found {len(articles)} articles")
        if not articles.empty:
            print("\nSample article:")
            print(articles.iloc[0])
            print("\nColumns:", articles.columns.tolist())
            print("\nLanguages found:", articles['language'].unique())
    except Exception as e:
        print(f"Error: {e}")

def test_keyword_search():
    """Test a keyword search"""
    print("\nTesting keyword search...")
    
    client = GdeltDoc()
    
    # Try a keyword search
    filters = Filters(
        keyword="climate change",
        timespan="1d",  # Last day
        num_records=10
    )
    
    try:
        articles = client.article_search(filters)
        print(f"Found {len(articles)} articles for keyword 'climate change'")
        if not articles.empty:
            print("\nSample article:")
            print(articles.iloc[0])
    except Exception as e:
        print(f"Error: {e}")

def test_domain_search():
    """Test a domain search"""
    print("\nTesting domain search...")
    
    client = GdeltDoc()
    
    # Try a domain search
    filters = Filters(
        domain="cnn.com",
        timespan="1d",  # Last day
        num_records=10
    )
    
    try:
        articles = client.article_search(filters)
        print(f"Found {len(articles)} articles from domain 'cnn.com'")
        if not articles.empty:
            print("\nSample article:")
            print(articles.iloc[0])
    except Exception as e:
        print(f"Error: {e}")

def test_language_search():
    """Test a language search"""
    print("\nTesting language search...")
    
    client = GdeltDoc()
    
    # Try searches with different language codes
    for lang_code in ["en", "english", "fr", "french"]:
        print(f"\nTrying language code: {lang_code}")
        
        filters = Filters(
            language=lang_code,
            timespan="1d",  # Last day
            num_records=10
        )
        
        try:
            articles = client.article_search(filters)
            print(f"Found {len(articles)} articles in language '{lang_code}'")
            if not articles.empty:
                print("Sample languages found:", articles['language'].unique())
        except Exception as e:
            print(f"Error with language '{lang_code}': {e}")

if __name__ == "__main__":
    test_basic_search()
    test_keyword_search()
    test_domain_search()
    test_language_search()
