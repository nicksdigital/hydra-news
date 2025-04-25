#!/usr/bin/env python3
"""
Content Processor Service for Hydra News

This service provides an API for processing news content, including:
- Content extraction and normalization
- Entity and claim detection
- Content entanglement
- Cross-reference verification

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

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify

# Initialize NLTK (in production, this would be done during setup)
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

class ContentProcessor:
    """Class for processing news content"""
    
    def __init__(self):
        """Initialize the content processor"""
        self.content_cache = {}  # Simple in-memory cache
    
    def process_content(self, title: str, content: str, source: str, author: Optional[str] = None, url: Optional[str] = None) -> Dict[str, Any]:
        """
        Process news content to extract entities, claims, and generate hashes.
        
        Args:
            title: The title of the news content
            content: The main text content
            source: The source of the content (e.g., "BBC News")
            author: Optional author name
            url: Optional URL source of the content
            
        Returns:
            A dictionary containing the processed content information
        """
        logger.info(f"Processing content: {title[:30]}...")
        
        # Extract entities
        entities = self._extract_entities(content)
        
        # Extract claims
        claims = self._extract_claims(content, entities)
        
        # Generate content hash (in production, this would use a more complex algorithm)
        content_data = f"{title}|{content}|{source}"
        if author:
            content_data += f"|{author}"
        if url:
            content_data += f"|{url}"
        
        content_hash = hashlib.sha256(content_data.encode('utf-8')).hexdigest()
        
        # Generate entanglement hash (logical interdependencies between content elements)
        entanglement_data = content_hash
        for entity in entities:
            entity_data = f"{entity['name']}|{entity['type']}|{entity['position']['start']}|{entity['position']['end']}"
            entanglement_data += "|" + hashlib.sha256(entity_data.encode('utf-8')).hexdigest()
        
        for claim in claims:
            claim_data = f"{claim['id']}|{claim['text']}|{claim['position']['start']}|{claim['position']['end']}"
            entanglement_data += "|" + hashlib.sha256(claim_data.encode('utf-8')).hexdigest()
        
        entanglement_hash = hashlib.sha256(entanglement_data.encode('utf-8')).hexdigest()
        
        # Create result
        result = {
            "content_hash": content_hash,
            "entanglement_hash": entanglement_hash,
            "entities": entities,
            "claims": claims,
            "timestamp": datetime.now().isoformat()
        }
        
        # Cache the result
        self.content_cache[content_hash] = {
            "title": title,
            "content": content,
            "source": source,
            "author": author,
            "url": url,
            "processed_at": datetime.now().isoformat(),
            **result
        }
        
        return result
    
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
            # Fetch the URL content
            headers = {'User-Agent': 'HydraNews/1.0'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = soup.title.string if soup.title else ""
            title = title.strip()
            
            # Try to extract author
            author = None
            author_meta = soup.find('meta', {'name': 'author'}) or soup.find('meta', {'property': 'author'})
            if author_meta and author_meta.get('content'):
                author = author_meta.get('content')
            
            # Simple extraction of main content (this would be more sophisticated in production)
            content = ""
            main_content_tags = soup.find_all(['article', 'main', 'div', 'section'])
            for tag in main_content_tags:
                text = tag.get_text().strip()
                if len(text.split()) > 100:  # Assume we found the main content
                    content = text
                    break
            
            # Extract source from domain
            source = url.split('/')[2]
            
            return {
                "title": title,
                "content": content,
                "source": source,
                "author": author,
                "url": url
            }
            
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
        
        content_data = self.content_cache[content_hash]
        
        # Process reference URLs
        references = []
        verified_claims = []
        disputed_claims = []
        
        if reference_urls:
            for url in reference_urls:
                try:
                    # Extract content from reference URL
                    reference_data = self.extract_from_url(url)
                    
                    # Process reference content
                    reference_result = self.process_content(
                        reference_data["title"],
                        reference_data["content"],
                        reference_data["source"],
                        reference_data["author"],
                        reference_data["url"]
                    )
                    
                    # Calculate support score (simplified)
                    support_score = self._calculate_reference_support(
                        content_data, self.content_cache[reference_result["content_hash"]]
                    )
                    
                    # Add to references
                    references.append({
                        "url": url,
                        "title": reference_data["title"],
                        "source": reference_data["source"],
                        "content_hash": reference_result["content_hash"],
                        "support_score": support_score if support_score >= 0.4 else None,
                        "dispute_score": (1.0 - support_score) if support_score < 0.4 else None
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing reference URL {url}: {e}")
                    continue
        
        # Process claims
        for claim in content_data.get("claims", []):
            # Check if claim is supported by references
            claim_support_score = 0
            supporting_refs = []
            disputing_refs = []
            
            for ref in references:
                if ref.get("support_score") and ref["support_score"] > 0.6:
                    claim_support_score += ref["support_score"]
                    supporting_refs.append(ref)
                elif ref.get("dispute_score") and ref["dispute_score"] > 0.6:
                    claim_support_score -= ref["dispute_score"]
                    disputing_refs.append(ref)
            
            # Normalize claim support score
            if references:
                claim_support_score /= len(references)
                claim_support_score = max(0, min(1, claim_support_score))
            else:
                claim_support_score = 0.5  # Neutral if no references
            
            # Add to verified or disputed claims
            claim_result = {
                "claim_id": claim["id"],
                "text": claim["text"],
                "score": claim_support_score,
            }
            
            if claim_support_score >= 0.5:
                claim_result["supporting_references"] = supporting_refs
                verified_claims.append(claim_result)
            else:
                claim_result["disputed_by"] = disputing_refs
                disputed_claims.append(claim_result)
        
        # Calculate overall verification score
        verification_score = 0.5  # Default neutral score
        total_claims = len(verified_claims) + len(disputed_claims)
        
        if total_claims > 0:
            verified_score_sum = sum(claim["score"] for claim in verified_claims)
            disputed_score_sum = sum(claim["score"] for claim in disputed_claims)
            verification_score = (verified_score_sum - disputed_score_sum) / total_claims
            verification_score = (verification_score + 1) / 2  # Scale from [-1,1] to [0,1]
        
        # Create verification result
        result = {
            "content_hash": content_hash,
            "verification_score": verification_score,
            "verified_claims": verified_claims,
            "disputed_claims": disputed_claims,
            "references": references,
            "timestamp": datetime.now().isoformat()
        }
        
        return result
    
    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities from text"""
        entities = []
        
        # Tokenize content into sentences
        sentences = sent_tokenize(text)
        
        current_pos = 0
        for sentence in sentences:
            # Tokenize words and tag parts of speech
            tokens = word_tokenize(sentence)
            tagged = nltk.pos_tag(tokens)
            
            # Extract named entities
            chunks = nltk.ne_chunk(tagged)
            
            # Process named entity chunks
            for chunk in chunks:
                if hasattr(chunk, 'label'):
                    # This is a named entity
                    entity_name = ' '.join([token for token, pos in chunk.leaves()])
                    entity_type = chunk.label()
                    
                    # Find position in original text
                    start_pos = text.find(entity_name, current_pos)
                    if start_pos != -1:
                        end_pos = start_pos + len(entity_name)
                        
                        # Get context (surrounding text)
                        context_start = max(0, start_pos - 50)
                        context_end = min(len(text), end_pos + 50)
                        context = text[context_start:context_end]
                        
                        # Create entity
                        entity = {
                            "name": entity_name,
                            "type": str(entity_type),
                            "context": context,
                            "confidence": 0.85,  # Simplified confidence score
                            "position": {
                                "start": start_pos,
                                "end": end_pos
                            }
                        }
                        entities.append(entity)
            
            current_pos += len(sentence)
        
        return entities
    
    def _extract_claims(self, text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract factual claims from text"""
        claims = []
        
        # Tokenize content into sentences
        sentences = sent_tokenize(text)
        
        current_pos = 0
        for sentence in sentences:
            # Simple claim detection heuristics
            is_claim = False
            claim_type = "statement"
            
            # Look for claim indicators
            claim_indicators = [
                "is", "are", "was", "were", "will be", "according to", 
                "said", "claimed", "reported", "stated", "announced", 
                "confirmed", "revealed"
            ]
            
            for indicator in claim_indicators:
                if f" {indicator} " in f" {sentence} ":
                    is_claim = True
                    break
            
            if is_claim:
                # Find entities in this claim
                claim_entities = []
                for entity in entities:
                    if current_pos <= entity["position"]["start"] < current_pos + len(sentence):
                        claim_entities.append({
                            "name": entity["name"],
                            "type": entity["type"]
                        })
                
                # Only consider it a claim if it has at least one entity
                if claim_entities:
                    # Find position in original text
                    start_pos = text.find(sentence, current_pos)
                    if start_pos != -1:
                        end_pos = start_pos + len(sentence)
                        
                        # Create claim
                        claim = {
                            "id": hashlib.md5(sentence.encode('utf-8')).hexdigest()[:16],
                            "text": sentence,
                            "entities": claim_entities,
                            "source_text": "Article Content",
                            "confidence": 0.75,  # Simplified confidence score
                            "type": claim_type,
                            "position": {
                                "start": start_pos,
                                "end": end_pos
                            }
                        }
                        claims.append(claim)
            
            current_pos += len(sentence)
        
        return claims
    
    def _calculate_reference_support(self, content1: Dict[str, Any], content2: Dict[str, Any]) -> float:
        """Calculate how much one content supports another"""
        
        # Compare entities
        entity_match_score = 0
        if content1.get("entities") and content2.get("entities"):
            content1_entities = {e["name"].lower(): e for e in content1["entities"]}
            content2_entities = {e["name"].lower(): e for e in content2["entities"]}
            
            # Count matching entities
            matches = 0
            for name in content1_entities:
                if name in content2_entities:
                    matches += 1
            
            total_entities = len(content1_entities) + len(content2_entities)
            if total_entities > 0:
                entity_match_score = (2 * matches) / total_entities
        
        # Compare claims
        claim_match_score = 0
        if content1.get("claims") and content2.get("claims"):
            # For each claim in content1, find the best matching claim in content2
            total_score = 0
            for claim1 in content1["claims"]:
                best_match = 0
                for claim2 in content2["claims"]:
                    # Calculate Jaccard similarity between claims
                    words1 = set(word_tokenize(claim1["text"].lower()))
                    words2 = set(word_tokenize(claim2["text"].lower()))
                    
                    if not words1 or not words2:
                        continue
                    
                    intersection = words1.intersection(words2)
                    union = words1.union(words2)
                    
                    jaccard_score = len(intersection) / len(union)
                    best_match = max(best_match, jaccard_score)
                
                total_score += best_match
            
            if content1["claims"]:
                claim_match_score = total_score / len(content1["claims"])
        
        # Calculate content similarity
        content_match_score = 0
        if content1.get("content") and content2.get("content"):
            # Tokenize both contents
            words1 = set(word_tokenize(content1["content"].lower()))
            words2 = set(word_tokenize(content2["content"].lower()))
            
            # Calculate Jaccard similarity
            if words1 and words2:
                intersection = words1.intersection(words2)
                union = words1.union(words2)
                content_match_score = len(intersection) / len(union)
        
        # Calculate overall support score (weighted average)
        support_score = (
            (entity_match_score * 0.3) +
            (claim_match_score * 0.5) +
            (content_match_score * 0.2)
        )
        
        return support_score


# Create content processor instance
content_processor = ContentProcessor()


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
        result = content_processor.process_content(
            data['title'],
            data['content'],
            data['source'],
            data.get('author'),
            data.get('url')
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
        result = content_processor.extract_from_url(data['url'])
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
        result = content_processor.verify_content(
            data['content_hash'],
            data.get('reference_urls', [])
        )
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error verifying content: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Content Processor Service for Hydra News')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to run the server on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    # Start the server
    logger.info(f"Starting Content Processor Service on {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)
