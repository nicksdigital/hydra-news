#!/usr/bin/env python3
"""
Enhanced Content Processor Service for Hydra News

This service provides an API for processing news content, including:
- Advanced entity extraction with transformers
- Improved claim detection with fine-tuned models
- Cross-reference validation with trusted sources
- Multimedia content support
- Content entanglement and verification

It exposes a REST API that the Go backend can call.
"""

import argparse
import hashlib
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union

# Import base content processor
from content_processor import (
    ContentProcessor,
    CrossReferenceVerifier,
    NewsContent,
    EXTERNAL_TRUSTED_SOURCE_VERIFICATION_AVAILABLE
)

# Import enhanced content processor
from enhanced_content_processor import (
    EnhancedContentProcessor,
    EnhancedCrossReferenceVerifier,
    EnhancedNewsContent,
    MultimediaContent
)

# Import external trusted source verifier if available
if EXTERNAL_TRUSTED_SOURCE_VERIFICATION_AVAILABLE:
    from cross_reference_validation import ExternalTrustedSourceVerifier

from flask import Flask, request, jsonify
import nltk

# Initialize NLTK
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('maxent_ne_chunker')
    nltk.download('words')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('content_processor')

# Create Flask app
app = Flask(__name__)


class ContentProcessorService:
    """Service wrapper for enhanced content processor"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the content processor service"""
        self.config = config or {}

        # Initialize the content processor
        try:
            logger.info("Initializing Enhanced Content Processor...")
            self.processor = EnhancedContentProcessor(self.config)

            # Try to use external trusted source verifier if available
            if EXTERNAL_TRUSTED_SOURCE_VERIFICATION_AVAILABLE:
                logger.info("Initializing External Trusted Source Verifier...")
                self.verifier = ExternalTrustedSourceVerifier(self.processor)
                logger.info("External Trusted Source Verifier initialized successfully")
            else:
                logger.info("External Trusted Source Verifier not available, using Enhanced Cross Reference Verifier")
                self.verifier = EnhancedCrossReferenceVerifier(self.processor)

            logger.info("Enhanced Content Processor initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Enhanced Content Processor: {e}")
            logger.info("Falling back to basic Content Processor")
            self.processor = ContentProcessor(self.config)
            self.verifier = CrossReferenceVerifier(self.processor)

        self.content_cache = {}  # Simple in-memory cache

    def process_content(self, title: str, content: str, source: str, author: Optional[str] = None,
                       url: Optional[str] = None, html_content: Optional[str] = None) -> Dict[str, Any]:
        """
        Process news content to extract entities, claims, and generate hashes.

        Args:
            title: The title of the news content
            content: The main text content
            source: The source of the content (e.g., "BBC News")
            author: Optional author name
            url: Optional URL source of the content
            html_content: Optional HTML content for multimedia extraction

        Returns:
            A dictionary containing the processed content information
        """
        logger.info(f"Processing content: {title[:30]}...")

        try:
            # Create NewsContent object
            if isinstance(self.processor, EnhancedContentProcessor):
                news_content = EnhancedNewsContent(
                    title=title,
                    content=content,
                    source=source,
                    author=author,
                    url=url,
                    html_content=html_content,
                    publish_date=datetime.now()  # Use current time as default
                )
            else:
                news_content = NewsContent(
                    title=title,
                    content=content,
                    source=source,
                    author=author,
                    url=url,
                    html_content=html_content,
                    publish_date=datetime.now()
                )

            # Process the content
            processed_content = self.processor.process_content(news_content)

            # Convert to dictionary
            result = processed_content.to_dict()

            # Cache the result
            self.content_cache[result["content_hash"]] = processed_content

            return result

        except Exception as e:
            logger.error(f"Error processing content: {e}")
            raise

    def extract_from_url(self, url: str) -> Dict[str, Any]:
        """
        Extract content from a URL.

        Args:
            url: The URL to extract content from

        Returns:
            A dictionary containing the extracted content
        """
        logger.info(f"Extracting content from URL: {url}")

        try:
            # Process URL through content processor
            news_content = self.processor.process_url(url)

            if not news_content:
                raise ValueError(f"Could not extract content from URL: {url}")

            # Convert to dictionary
            result = news_content.to_dict()

            # Cache the result
            self.content_cache[result["content_hash"]] = news_content

            return result

        except Exception as e:
            logger.error(f"Error extracting content from URL: {e}")
            raise

    def verify_content(self, content_hash: str, reference_urls: List[str] = None) -> Dict[str, Any]:
        """
        Verify content by cross-referencing with other sources.

        Args:
            content_hash: The hash of the content to verify
            reference_urls: Optional list of URLs to use for cross-referencing

        Returns:
            A dictionary containing the verification result
        """
        logger.info(f"Verifying content with hash: {content_hash}")

        # Check if content exists in cache
        if content_hash not in self.content_cache:
            logger.error(f"Content with hash {content_hash} not found")
            raise ValueError(f"Content with hash {content_hash} not found")

        content = self.content_cache[content_hash]

        try:
            # Use the verifier to cross-reference content
            reference_urls = reference_urls or []
            verification_result = self.verifier.verify_content(content, reference_urls)

            return verification_result

        except Exception as e:
            logger.error(f"Error verifying content: {e}")
            raise


# Create content processor instance with configuration
config = {
    'models': {
        'ner': 'dbmdz/bert-large-cased-finetuned-conll03-english',
        'claim_detection': 'roberta-base',
        'embedding': 'sentence-transformers/all-MiniLM-L6-v2',
        'summarization': 'facebook/bart-large-cnn',
        'topic': 'facebook/bart-large-mnli',
    },
    'trusted_sources': {
        'reuters.com': 0.9,
        'apnews.com': 0.9,
        'bbc.com': 0.85,
        'npr.org': 0.85,
        'nytimes.com': 0.8,
        'washingtonpost.com': 0.8
    }
}

content_processor_service = ContentProcessorService(config)


# API Routes
@app.route('/api/process', methods=['POST'])
def process_content():
    """API endpoint for processing content"""
    data = request.json

    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Validate required fields
    if not all(field in data for field in ['title', 'content', 'source']):
        return jsonify({"error": "Missing required fields (title, content, source)"}), 400

    try:
        result = content_processor_service.process_content(
            data['title'],
            data['content'],
            data['source'],
            data.get('author'),
            data.get('url'),
            data.get('html_content')
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error processing content: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/extract', methods=['POST'])
def extract_from_url():
    """API endpoint for extracting content from a URL"""
    data = request.json

    if not data or 'url' not in data:
        return jsonify({"error": "URL is required"}), 400

    try:
        result = content_processor_service.extract_from_url(data['url'])
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error extracting from URL: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/verify', methods=['POST'])
def verify_content():
    """API endpoint for verifying content"""
    data = request.json

    if not data or 'content_hash' not in data:
        return jsonify({"error": "Content hash is required"}), 400

    try:
        result = content_processor_service.verify_content(
            data['content_hash'],
            data.get('reference_urls', [])
        )
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error verifying content: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    # Check if using external trusted source verifier
    using_external_verifier = False
    if EXTERNAL_TRUSTED_SOURCE_VERIFICATION_AVAILABLE:
        using_external_verifier = isinstance(content_processor_service.verifier, ExternalTrustedSourceVerifier)

    return jsonify({
        "status": "ok",
        "time": datetime.now().isoformat(),
        "enhanced_processor": isinstance(content_processor_service.processor, EnhancedContentProcessor),
        "enhanced_verifier": isinstance(content_processor_service.verifier, EnhancedCrossReferenceVerifier),
        "external_trusted_source_verifier": using_external_verifier,
        "features": {
            "enhanced_entity_extraction": hasattr(content_processor_service.processor, "entity_extractor") and
                                         content_processor_service.processor.entity_extractor is not None,
            "improved_claim_detection": hasattr(content_processor_service.processor, "claim_detector") and
                                       content_processor_service.processor.claim_detector is not None,
            "external_trusted_source_verification": using_external_verifier
        }
    })


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Enhanced Content Processor Service for Hydra News')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to run the server on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')

    args = parser.parse_args()

    # Start the server
    logger.info(f"Starting Enhanced Content Processor Service on {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)
