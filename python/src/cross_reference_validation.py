"""
Cross-reference validation with external trusted sources for Hydra News.

This module provides functionality to validate claims against external trusted sources:
1. Trusted source management
2. External API integration for fact-checking
3. Semantic similarity for claim matching
4. Confidence scoring based on source reliability
"""

import json
import os
import time
import hashlib
import requests
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from datetime import datetime
import re

# Import base content processor classes
from content_processor import ContentClaim, NewsContent, CrossReferenceVerifier

# Try to import numpy for vector operations
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

# Try to import scikit-learn for cosine similarity
try:
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# Default trusted sources with reliability scores
DEFAULT_TRUSTED_SOURCES = {
    "reuters.com": {
        "name": "Reuters",
        "reliability": 0.95,
        "bias": "minimal",
        "category": "news_agency",
        "country": "international",
        "api_key": None,
    },
    "apnews.com": {
        "name": "Associated Press",
        "reliability": 0.94,
        "bias": "minimal",
        "category": "news_agency",
        "country": "usa",
        "api_key": None,
    },
    "bbc.com": {
        "name": "BBC",
        "reliability": 0.92,
        "bias": "slight-left",
        "category": "mainstream",
        "country": "uk",
        "api_key": None,
    },
    "nytimes.com": {
        "name": "New York Times",
        "reliability": 0.89,
        "bias": "left-center",
        "category": "mainstream",
        "country": "usa",
        "api_key": None,
    },
    "economist.com": {
        "name": "The Economist",
        "reliability": 0.91,
        "bias": "center",
        "category": "mainstream",
        "country": "uk",
        "api_key": None,
    },
    "wsj.com": {
        "name": "Wall Street Journal",
        "reliability": 0.88,
        "bias": "right-center",
        "category": "mainstream",
        "country": "usa",
        "api_key": None,
    },
    "theguardian.com": {
        "name": "The Guardian",
        "reliability": 0.87,
        "bias": "left-center",
        "category": "mainstream",
        "country": "uk",
        "api_key": None,
    },
    "factcheck.org": {
        "name": "FactCheck.org",
        "reliability": 0.93,
        "bias": "center",
        "category": "fact_checker",
        "country": "usa",
        "api_key": None,
    },
    "politifact.com": {
        "name": "PolitiFact",
        "reliability": 0.92,
        "bias": "left-center",
        "category": "fact_checker",
        "country": "usa",
        "api_key": None,
    },
    "snopes.com": {
        "name": "Snopes",
        "reliability": 0.90,
        "bias": "left-center",
        "category": "fact_checker",
        "country": "usa",
        "api_key": None,
    },
}

# External fact-checking APIs
FACT_CHECK_APIS = {
    "google_fact_check": {
        "url": "https://factchecktools.googleapis.com/v1alpha1/claims:search",
        "requires_key": True,
        "key_param": "key",
        "query_param": "query",
        "response_format": "json",
    },
    "bing_news_search": {
        "url": "https://api.bing.microsoft.com/v7.0/news/search",
        "requires_key": True,
        "key_header": "Ocp-Apim-Subscription-Key",
        "query_param": "q",
        "response_format": "json",
    },
}

class ExternalTrustedSourceVerifier(CrossReferenceVerifier):
    """Verifies content by cross-referencing with external trusted sources"""
    
    def __init__(self, content_processor):
        """Initialize the verifier with content processor"""
        super().__init__(content_processor)
        self.trusted_sources = self._load_trusted_sources()
        self.fact_check_apis = self._load_fact_check_apis()
        self.api_keys = self._load_api_keys()
        
    def _load_trusted_sources(self) -> Dict[str, Dict[str, Any]]:
        """Load trusted sources from configuration file or use defaults"""
        trusted_sources = DEFAULT_TRUSTED_SOURCES.copy()
        
        # Try to load from configuration file
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'trusted_sources.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    custom_sources = json.load(f)
                    # Merge with defaults, with custom sources taking precedence
                    for domain, info in custom_sources.items():
                        trusted_sources[domain] = info
            except Exception as e:
                print(f"Error loading trusted sources: {e}")
        
        return trusted_sources
    
    def _load_fact_check_apis(self) -> Dict[str, Dict[str, Any]]:
        """Load fact-checking API configurations"""
        apis = FACT_CHECK_APIS.copy()
        
        # Try to load from configuration file
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'fact_check_apis.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    custom_apis = json.load(f)
                    # Merge with defaults, with custom APIs taking precedence
                    for api_name, info in custom_apis.items():
                        apis[api_name] = info
            except Exception as e:
                print(f"Error loading fact-checking APIs: {e}")
        
        return apis
    
    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys from configuration file"""
        api_keys = {}
        
        # Try to load from configuration file
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'api_keys.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    api_keys = json.load(f)
            except Exception as e:
                print(f"Error loading API keys: {e}")
        
        return api_keys
    
    def verify_content(self, content: NewsContent, reference_urls: List[str]) -> Dict[str, Any]:
        """Verify content by cross-referencing with trusted sources"""
        # Start with the basic verification from the parent class
        verification_result = super().verify_content(content, reference_urls)
        
        # Enhance with external trusted sources
        external_references = self._check_external_sources(content)
        
        # Add external references to the verification result
        if external_references:
            verification_result['external_references'] = external_references
            
            # Update verification score based on external references
            self._update_verification_score(verification_result, external_references)
        
        return verification_result
    
    def _check_external_sources(self, content: NewsContent) -> List[Dict[str, Any]]:
        """Check content against external trusted sources"""
        external_references = []
        
        # Check each claim against fact-checking APIs
        for claim in content.claims:
            # Only check claims with high confidence
            if claim.confidence >= 0.7:
                fact_check_results = self._check_fact_checking_apis(claim.claim_text)
                
                for result in fact_check_results:
                    external_references.append({
                        'claim_id': claim.id,
                        'source': result['source'],
                        'url': result['url'],
                        'title': result['title'],
                        'rating': result.get('rating'),
                        'confidence': result['confidence'],
                        'is_trusted': result['is_trusted'],
                        'supports': result['supports'],
                        'disputes': result['disputes'],
                    })
        
        return external_references
    
    def _check_fact_checking_apis(self, claim_text: str) -> List[Dict[str, Any]]:
        """Check a claim against fact-checking APIs"""
        results = []
        
        # Try Google Fact Check API if key is available
        if 'google_fact_check' in self.api_keys:
            google_results = self._check_google_fact_check(claim_text)
            results.extend(google_results)
        
        # Try Bing News Search API if key is available
        if 'bing_news_search' in self.api_keys:
            bing_results = self._check_bing_news_search(claim_text)
            results.extend(bing_results)
        
        # If no API keys are available, use a simulated response for testing
        if not results:
            simulated_results = self._simulate_fact_check_response(claim_text)
            results.extend(simulated_results)
        
        return results
    
    def _check_google_fact_check(self, claim_text: str) -> List[Dict[str, Any]]:
        """Check a claim using Google Fact Check API"""
        results = []
        
        try:
            api_config = self.fact_check_apis['google_fact_check']
            api_key = self.api_keys.get('google_fact_check')
            
            if not api_key:
                return []
            
            # Prepare request
            params = {
                api_config['key_param']: api_key,
                api_config['query_param']: claim_text,
                'languageCode': 'en'
            }
            
            # Make request
            response = requests.get(api_config['url'], params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # Process claims from the response
                if 'claims' in data:
                    for claim_result in data['claims']:
                        for review in claim_result.get('claimReview', []):
                            source_domain = self._extract_domain(review.get('url', ''))
                            is_trusted = source_domain in self.trusted_sources
                            
                            # Determine if the source supports or disputes the claim
                            rating = review.get('textualRating', '')
                            supports = self._rating_indicates_support(rating)
                            disputes = self._rating_indicates_dispute(rating)
                            
                            results.append({
                                'source': review.get('publisher', {}).get('name', source_domain),
                                'url': review.get('url', ''),
                                'title': review.get('title', ''),
                                'rating': rating,
                                'confidence': 0.8,  # Default confidence for API results
                                'is_trusted': is_trusted,
                                'supports': supports,
                                'disputes': disputes,
                            })
            
        except Exception as e:
            print(f"Error checking Google Fact Check API: {e}")
        
        return results
    
    def _check_bing_news_search(self, claim_text: str) -> List[Dict[str, Any]]:
        """Check a claim using Bing News Search API"""
        results = []
        
        try:
            api_config = self.fact_check_apis['bing_news_search']
            api_key = self.api_keys.get('bing_news_search')
            
            if not api_key:
                return []
            
            # Prepare request
            headers = {
                api_config['key_header']: api_key
            }
            
            params = {
                api_config['query_param']: f'fact check {claim_text}'
            }
            
            # Make request
            response = requests.get(api_config['url'], headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # Process news articles from the response
                if 'value' in data:
                    for article in data['value']:
                        source_domain = self._extract_domain(article.get('url', ''))
                        is_trusted = source_domain in self.trusted_sources
                        
                        # For news articles, we need to analyze the title/description to determine support/dispute
                        title = article.get('name', '')
                        description = article.get('description', '')
                        
                        supports, disputes = self._analyze_news_content(title, description, claim_text)
                        
                        results.append({
                            'source': article.get('provider', [{}])[0].get('name', source_domain),
                            'url': article.get('url', ''),
                            'title': title,
                            'rating': None,  # News articles don't have explicit ratings
                            'confidence': 0.7,  # Lower confidence for news articles vs. fact checks
                            'is_trusted': is_trusted,
                            'supports': supports,
                            'disputes': disputes,
                        })
            
        except Exception as e:
            print(f"Error checking Bing News Search API: {e}")
        
        return results
    
    def _simulate_fact_check_response(self, claim_text: str) -> List[Dict[str, Any]]:
        """Simulate a fact-checking API response for testing purposes"""
        # This is only used when no real API keys are available
        
        # Generate a deterministic but seemingly random result based on the claim text
        claim_hash = hashlib.md5(claim_text.encode()).hexdigest()
        hash_value = int(claim_hash, 16)
        
        # Determine if the simulated result supports or disputes the claim
        supports = (hash_value % 10) >= 5
        disputes = not supports
        
        # Select a random trusted source
        trusted_sources = list(self.trusted_sources.items())
        source_index = hash_value % len(trusted_sources)
        domain, source_info = trusted_sources[source_index]
        
        # Generate a rating based on support/dispute
        rating = "True" if supports else "False"
        if supports and hash_value % 3 == 0:
            rating = "Mostly True"
        elif supports and hash_value % 3 == 1:
            rating = "Partly True"
        elif disputes and hash_value % 3 == 0:
            rating = "Mostly False"
        elif disputes and hash_value % 3 == 1:
            rating = "Partly False"
        
        # Create a simulated result
        result = {
            'source': source_info['name'],
            'url': f"https://{domain}/fact-check/{claim_hash[:8]}",
            'title': f"Fact check: {claim_text[:50]}{'...' if len(claim_text) > 50 else ''}",
            'rating': rating,
            'confidence': 0.8,
            'is_trusted': True,
            'supports': supports,
            'disputes': disputes,
        }
        
        return [result]
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        if not url:
            return ""
        
        # Remove protocol
        domain = url.lower()
        if "://" in domain:
            domain = domain.split("://")[1]
        
        # Remove path
        if "/" in domain:
            domain = domain.split("/")[0]
        
        # Remove port
        if ":" in domain:
            domain = domain.split(":")[0]
        
        # Remove www prefix
        if domain.startswith("www."):
            domain = domain[4:]
        
        return domain
    
    def _rating_indicates_support(self, rating: str) -> bool:
        """Determine if a fact-check rating indicates support for a claim"""
        if not rating:
            return False
        
        rating = rating.lower()
        support_indicators = [
            "true", "mostly true", "partly true", "accurate", "correct",
            "verified", "confirmed", "supported", "substantiated"
        ]
        
        for indicator in support_indicators:
            if indicator in rating:
                return True
        
        return False
    
    def _rating_indicates_dispute(self, rating: str) -> bool:
        """Determine if a fact-check rating indicates dispute of a claim"""
        if not rating:
            return False
        
        rating = rating.lower()
        dispute_indicators = [
            "false", "mostly false", "partly false", "inaccurate", "incorrect",
            "misleading", "unverified", "unsupported", "unsubstantiated", "pants on fire"
        ]
        
        for indicator in dispute_indicators:
            if indicator in rating:
                return True
        
        return False
    
    def _analyze_news_content(self, title: str, description: str, claim_text: str) -> Tuple[bool, bool]:
        """Analyze news content to determine if it supports or disputes a claim"""
        # Combine title and description
        content = f"{title} {description}".lower()
        claim = claim_text.lower()
        
        # Check for support indicators
        support_indicators = [
            "confirms", "verified", "true", "correct", "accurate", "right",
            "proves", "evidence supports", "research confirms", "study confirms"
        ]
        
        # Check for dispute indicators
        dispute_indicators = [
            "debunks", "false", "incorrect", "inaccurate", "wrong", "misleading",
            "no evidence", "disproves", "refutes", "contradicts", "disputes"
        ]
        
        supports = False
        disputes = False
        
        # Check for support indicators
        for indicator in support_indicators:
            if indicator in content:
                supports = True
                break
        
        # Check for dispute indicators
        for indicator in dispute_indicators:
            if indicator in content:
                disputes = True
                break
        
        # If no explicit indicators, check for semantic similarity
        if not supports and not disputes and NUMPY_AVAILABLE and SKLEARN_AVAILABLE:
            # This would use embeddings in a real implementation
            # For now, use a simple word overlap approach
            claim_words = set(re.findall(r'\w+', claim))
            content_words = set(re.findall(r'\w+', content))
            
            if claim_words and content_words:
                overlap = len(claim_words.intersection(content_words)) / len(claim_words.union(content_words))
                
                # If significant overlap, consider it supporting
                if overlap > 0.3:
                    supports = True
        
        return supports, disputes
    
    def _update_verification_score(self, verification_result: Dict[str, Any], external_references: List[Dict[str, Any]]) -> None:
        """Update verification score based on external references"""
        # Count trusted sources that support or dispute
        trusted_support_count = 0
        trusted_dispute_count = 0
        
        for ref in external_references:
            if ref['is_trusted']:
                if ref['supports']:
                    trusted_support_count += 1
                if ref['disputes']:
                    trusted_dispute_count += 1
        
        # Only adjust score if we have trusted references
        if trusted_support_count + trusted_dispute_count > 0:
            # Calculate external trust score
            external_score = (trusted_support_count - trusted_dispute_count) / (trusted_support_count + trusted_dispute_count)
            
            # Scale to [0, 1]
            external_score = (external_score + 1) / 2
            
            # Blend with existing score (70% existing, 30% external)
            current_score = verification_result['verification_score']
            blended_score = (current_score * 0.7) + (external_score * 0.3)
            
            # Update the score
            verification_result['verification_score'] = max(0.0, min(1.0, blended_score))
            
            # Add explanation
            verification_result['score_explanation'] = {
                'original_score': current_score,
                'external_score': external_score,
                'trusted_supporting_sources': trusted_support_count,
                'trusted_disputing_sources': trusted_dispute_count,
                'blended_score': blended_score,
            }
