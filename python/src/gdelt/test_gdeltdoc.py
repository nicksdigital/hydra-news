#!/usr/bin/env python3
"""
Simple test script for the gdeltdoc module
"""

import pandas as pd
from gdeltdoc import GdeltDoc, Filters

def main():
    print("Testing GDELT API with gdeltdoc module...")
    
    # Initialize the client
    client = GdeltDoc()
    
    # Test 1: Basic search with minimal parameters
    print("\nTest 1: Basic search with minimal parameters")
    try:
        filters = Filters(
            timespan="1d",  # Last day
            num_records=5
        )
        
        articles = client.article_search(filters)
        print(f"Success! Found {len(articles)} articles")
        
        if not articles.empty:
            print("\nSample article:")
            print(f"Title: {articles.iloc[0]['title']}")
            print(f"URL: {articles.iloc[0]['url']}")
            print(f"Source: {articles.iloc[0]['domain']}")
            print(f"Language: {articles.iloc[0]['language']}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Search with keyword
    print("\nTest 2: Search with keyword")
    try:
        filters = Filters(
            keyword="climate",
            timespan="1d",
            num_records=5
        )
        
        articles = client.article_search(filters)
        print(f"Success! Found {len(articles)} articles about 'climate'")
        
        if not articles.empty:
            print("\nSample article:")
            print(f"Title: {articles.iloc[0]['title']}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Search with domain
    print("\nTest 3: Search with domain")
    try:
        filters = Filters(
            domain="bbc.com",
            timespan="1d",
            num_records=5
        )
        
        articles = client.article_search(filters)
        print(f"Success! Found {len(articles)} articles from 'bbc.com'")
        
        if not articles.empty:
            print("\nSample article:")
            print(f"Title: {articles.iloc[0]['title']}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\nTests completed!")

if __name__ == "__main__":
    main()
