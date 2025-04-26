"""
Tests for the cross-reference validation module.

This module contains unit tests for the cross-reference validation functionality, including:
- External trusted source verification
- Fact-checking API integration
- Source reliability scoring
- Verification score calculation
"""

import unittest
import os
import sys
import json
from datetime import datetime
from unittest.mock import patch, MagicMock, mock_open

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import the modules to test
from content_processor import ContentProcessor, NewsContent, ContentEntity, ContentClaim
try:
    from cross_reference_validation import (
        ExternalTrustedSourceVerifier, 
        DEFAULT_TRUSTED_SOURCES,
        FACT_CHECK_APIS
    )
    EXTERNAL_TRUSTED_SOURCE_VERIFICATION_AVAILABLE = True
except ImportError:
    EXTERNAL_TRUSTED_SOURCE_VERIFICATION_AVAILABLE = False


@unittest.skipIf(not EXTERNAL_TRUSTED_SOURCE_VERIFICATION_AVAILABLE, "External trusted source verification not available")
class TestExternalTrustedSourceVerifier(unittest.TestCase):
    """Tests for the ExternalTrustedSourceVerifier class"""

    def setUp(self):
        """Set up test fixtures"""
        self.processor = ContentProcessor()
        self.verifier = ExternalTrustedSourceVerifier(self.processor)
        
        # Sample news content for testing
        self.news_content = NewsContent(
            title="Tech Giants Announce New AI Partnership",
            content="Microsoft and Google have announced a new partnership focused on artificial intelligence. "
                   "The CEOs of both companies, Satya Nadella and Sundar Pichai, made the announcement yesterday in San Francisco. "
                   "The partnership will focus on developing new AI standards that will be implemented by 2025. "
                   "Experts believe this collaboration could accelerate AI innovation significantly.",
            source="Tech News",
            author="Jane Smith"
        )
        
        # Add entities to the news content
        self.news_content.entities = [
            ContentEntity(
                name="Microsoft",
                entity_type="ORGANIZATION",
                context="Microsoft and Google have announced",
                confidence=0.9,
                start_pos=0,
                end_pos=9
            ),
            ContentEntity(
                name="Google",
                entity_type="ORGANIZATION",
                context="Microsoft and Google have announced",
                confidence=0.9,
                start_pos=14,
                end_pos=20
            )
        ]
        
        # Add claims to the news content
        self.news_content.claims = [
            ContentClaim(
                claim_text="Microsoft and Google have announced a new partnership focused on artificial intelligence.",
                entities=[self.news_content.entities[0], self.news_content.entities[1]],
                source_text="Tech Giants Announce New AI Partnership",
                confidence=0.9,
                claim_type="FACTUAL",
                start_pos=0,
                end_pos=82
            ),
            ContentClaim(
                claim_text="The partnership will focus on developing new AI standards that will be implemented by 2025.",
                entities=[],
                source_text="Tech Giants Announce New AI Partnership",
                confidence=0.8,
                claim_type="PREDICTION",
                start_pos=183,
                end_pos=264
            )
        ]
        
        # Process the content
        self.processor.process_content(self.news_content)
    
    def test_trusted_sources_loading(self):
        """Test loading trusted sources"""
        # Check that trusted sources were loaded
        self.assertIsNotNone(self.verifier.trusted_sources)
        self.assertGreater(len(self.verifier.trusted_sources), 0)
        
        # Check that default trusted sources are defined
        self.assertIsNotNone(DEFAULT_TRUSTED_SOURCES)
        self.assertIn("reuters.com", DEFAULT_TRUSTED_SOURCES)
        self.assertIn("bbc.com", DEFAULT_TRUSTED_SOURCES)
    
    def test_fact_check_apis_loading(self):
        """Test loading fact-checking APIs"""
        # Check that fact-checking APIs were loaded
        self.assertIsNotNone(self.verifier.fact_check_apis)
        self.assertGreater(len(self.verifier.fact_check_apis), 0)
        
        # Check that default fact-checking APIs are defined
        self.assertIsNotNone(FACT_CHECK_APIS)
        self.assertIn("google_fact_check", FACT_CHECK_APIS)
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"custom.com": {"name": "Custom Source", "reliability": 0.95}}')
    def test_custom_trusted_sources_loading(self, mock_file, mock_exists):
        """Test loading custom trusted sources"""
        # Mock the existence of the config file
        mock_exists.return_value = True
        
        # Create a new verifier to load the custom sources
        verifier = ExternalTrustedSourceVerifier(self.processor)
        
        # Check that the custom source was loaded
        self.assertIn("custom.com", verifier.trusted_sources)
        self.assertEqual(verifier.trusted_sources["custom.com"]["name"], "Custom Source")
        self.assertEqual(verifier.trusted_sources["custom.com"]["reliability"], 0.95)
    
    @patch('requests.get')
    def test_check_google_fact_check(self, mock_get):
        """Test checking a claim with Google Fact Check API"""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "claims": [
                {
                    "text": "Microsoft and Google have announced a new partnership",
                    "claimant": "Tech News",
                    "claimDate": "2023-05-15T00:00:00Z",
                    "claimReview": [
                        {
                            "publisher": {
                                "name": "Reuters Fact Check",
                                "site": "reuters.com"
                            },
                            "url": "https://reuters.com/fact-check/123",
                            "title": "Fact check: Microsoft and Google partnership",
                            "textualRating": "True",
                            "languageCode": "en"
                        }
                    ]
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Set up the verifier with an API key
        self.verifier.api_keys = {"google_fact_check": "test_api_key"}
        
        # Check a claim
        results = self.verifier._check_google_fact_check("Microsoft and Google have announced a new partnership")
        
        # Check the results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["source"], "Reuters Fact Check")
        self.assertEqual(results[0]["url"], "https://reuters.com/fact-check/123")
        self.assertEqual(results[0]["rating"], "True")
        self.assertTrue(results[0]["is_trusted"])
        self.assertTrue(results[0]["supports"])
        self.assertFalse(results[0]["disputes"])
    
    def test_rating_indicators(self):
        """Test rating indicators for support and dispute"""
        # Test support indicators
        self.assertTrue(self.verifier._rating_indicates_support("True"))
        self.assertTrue(self.verifier._rating_indicates_support("Mostly True"))
        self.assertTrue(self.verifier._rating_indicates_support("The claim is accurate"))
        self.assertFalse(self.verifier._rating_indicates_support("False"))
        
        # Test dispute indicators
        self.assertTrue(self.verifier._rating_indicates_dispute("False"))
        self.assertTrue(self.verifier._rating_indicates_dispute("Mostly False"))
        self.assertTrue(self.verifier._rating_indicates_dispute("The claim is misleading"))
        self.assertFalse(self.verifier._rating_indicates_dispute("True"))
    
    def test_extract_domain(self):
        """Test extracting domain from URL"""
        # Test various URL formats
        self.assertEqual(self.verifier._extract_domain("https://www.example.com/path"), "example.com")
        self.assertEqual(self.verifier._extract_domain("http://subdomain.example.com"), "subdomain.example.com")
        self.assertEqual(self.verifier._extract_domain("www.example.com/path?query=value"), "example.com")
        self.assertEqual(self.verifier._extract_domain("example.com"), "example.com")
        self.assertEqual(self.verifier._extract_domain("https://example.com:8080/path"), "example.com")
    
    @patch('cross_reference_validation.ExternalTrustedSourceVerifier._check_external_sources')
    def test_verify_content(self, mock_check_external):
        """Test content verification with external sources"""
        # Mock the external sources check
        mock_check_external.return_value = [
            {
                'claim_id': self.news_content.claims[0].id,
                'source': 'Reuters Fact Check',
                'url': 'https://reuters.com/fact-check/123',
                'title': 'Fact check: Microsoft and Google partnership',
                'rating': 'True',
                'confidence': 0.9,
                'is_trusted': True,
                'supports': True,
                'disputes': False
            }
        ]
        
        # Verify the content
        result = self.verifier.verify_content(self.news_content, [])
        
        # Check the verification result
        self.assertIsNotNone(result)
        self.assertEqual(result["content_hash"], self.news_content.content_hash)
        self.assertIn("external_references", result)
        self.assertEqual(len(result["external_references"]), 1)
        self.assertGreaterEqual(result["verification_score"], 0.0)
        self.assertLessEqual(result["verification_score"], 1.0)
    
    def test_simulate_fact_check_response(self):
        """Test simulating a fact-check response"""
        # Simulate a fact-check response
        results = self.verifier._simulate_fact_check_response("Microsoft and Google have announced a new partnership")
        
        # Check the results
        self.assertEqual(len(results), 1)
        self.assertIn(results[0]["source"], [source_info["name"] for source_info in DEFAULT_TRUSTED_SOURCES.values()])
        self.assertTrue(results[0]["url"].startswith("https://"))
        self.assertIn("rating", results[0])
        self.assertEqual(results[0]["confidence"], 0.8)
        self.assertTrue(results[0]["is_trusted"])
        self.assertIsNotNone(results[0]["supports"])
        self.assertIsNotNone(results[0]["disputes"])
    
    def test_update_verification_score(self):
        """Test updating verification score based on external references"""
        # Create a verification result
        verification_result = {
            'content_hash': self.news_content.content_hash,
            'verification_score': 0.7,
            'verified_claims': [],
            'disputed_claims': [],
            'references': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Create external references
        external_references = [
            {
                'claim_id': self.news_content.claims[0].id,
                'source': 'Reuters Fact Check',
                'url': 'https://reuters.com/fact-check/123',
                'title': 'Fact check: Microsoft and Google partnership',
                'rating': 'True',
                'confidence': 0.9,
                'is_trusted': True,
                'supports': True,
                'disputes': False
            },
            {
                'claim_id': self.news_content.claims[0].id,
                'source': 'BBC Fact Check',
                'url': 'https://bbc.com/fact-check/123',
                'title': 'Fact check: Microsoft and Google partnership',
                'rating': 'True',
                'confidence': 0.9,
                'is_trusted': True,
                'supports': True,
                'disputes': False
            }
        ]
        
        # Update the verification score
        self.verifier._update_verification_score(verification_result, external_references)
        
        # Check that the score was updated
        self.assertNotEqual(verification_result["verification_score"], 0.7)
        self.assertIn("score_explanation", verification_result)
        self.assertEqual(verification_result["score_explanation"]["trusted_supporting_sources"], 2)
        self.assertEqual(verification_result["score_explanation"]["trusted_disputing_sources"], 0)


if __name__ == '__main__':
    unittest.main()
