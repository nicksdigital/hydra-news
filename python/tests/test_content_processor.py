"""
Tests for the content processor module.

This module contains unit tests for the content processor functionality, including:
- Entity extraction
- Claim detection
- Content processing
- Cross-reference verification
"""

import unittest
import os
import sys
import json
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import the modules to test
from content_processor import (
    ContentProcessor, 
    NewsContent, 
    ContentEntity, 
    ContentClaim,
    CrossReferenceVerifier
)

class TestContentEntity(unittest.TestCase):
    """Tests for the ContentEntity class"""

    def test_content_entity_creation(self):
        """Test creating a ContentEntity"""
        entity = ContentEntity(
            name="John Doe",
            entity_type="PERSON",
            context="John Doe is the CEO of the company.",
            confidence=0.9,
            start_pos=0,
            end_pos=8
        )
        
        self.assertEqual(entity.name, "John Doe")
        self.assertEqual(entity.entity_type, "PERSON")
        self.assertEqual(entity.context, "John Doe is the CEO of the company.")
        self.assertEqual(entity.confidence, 0.9)
        self.assertEqual(entity.start_pos, 0)
        self.assertEqual(entity.end_pos, 8)
    
    def test_content_entity_to_dict(self):
        """Test converting a ContentEntity to a dictionary"""
        entity = ContentEntity(
            name="John Doe",
            entity_type="PERSON",
            context="John Doe is the CEO of the company.",
            confidence=0.9,
            start_pos=0,
            end_pos=8
        )
        
        entity_dict = entity.to_dict()
        
        self.assertEqual(entity_dict["name"], "John Doe")
        self.assertEqual(entity_dict["type"], "PERSON")
        self.assertEqual(entity_dict["context"], "John Doe is the CEO of the company.")
        self.assertEqual(entity_dict["confidence"], 0.9)
        self.assertEqual(entity_dict["position"]["start"], 0)
        self.assertEqual(entity_dict["position"]["end"], 8)


class TestContentClaim(unittest.TestCase):
    """Tests for the ContentClaim class"""

    def test_content_claim_creation(self):
        """Test creating a ContentClaim"""
        entity = ContentEntity(
            name="John Doe",
            entity_type="PERSON",
            context="John Doe is the CEO of the company.",
            confidence=0.9,
            start_pos=0,
            end_pos=8
        )
        
        claim = ContentClaim(
            claim_text="John Doe is the CEO of the company.",
            entities=[entity],
            source_text="Company News",
            confidence=0.8,
            claim_type="FACTUAL",
            start_pos=10,
            end_pos=48
        )
        
        self.assertEqual(claim.claim_text, "John Doe is the CEO of the company.")
        self.assertEqual(len(claim.entities), 1)
        self.assertEqual(claim.entities[0].name, "John Doe")
        self.assertEqual(claim.source_text, "Company News")
        self.assertEqual(claim.confidence, 0.8)
        self.assertEqual(claim.claim_type, "FACTUAL")
        self.assertEqual(claim.start_pos, 10)
        self.assertEqual(claim.end_pos, 48)
        self.assertIsNotNone(claim.id)
    
    def test_content_claim_to_dict(self):
        """Test converting a ContentClaim to a dictionary"""
        entity = ContentEntity(
            name="John Doe",
            entity_type="PERSON",
            context="John Doe is the CEO of the company.",
            confidence=0.9,
            start_pos=0,
            end_pos=8
        )
        
        claim = ContentClaim(
            claim_text="John Doe is the CEO of the company.",
            entities=[entity],
            source_text="Company News",
            confidence=0.8,
            claim_type="FACTUAL",
            start_pos=10,
            end_pos=48
        )
        
        claim_dict = claim.to_dict()
        
        self.assertEqual(claim_dict["text"], "John Doe is the CEO of the company.")
        self.assertEqual(len(claim_dict["entities"]), 1)
        self.assertEqual(claim_dict["entities"][0]["name"], "John Doe")
        self.assertEqual(claim_dict["source_text"], "Company News")
        self.assertEqual(claim_dict["confidence"], 0.8)
        self.assertEqual(claim_dict["type"], "FACTUAL")
        self.assertEqual(claim_dict["position"]["start"], 10)
        self.assertEqual(claim_dict["position"]["end"], 48)
        self.assertIsNotNone(claim_dict["id"])


class TestNewsContent(unittest.TestCase):
    """Tests for the NewsContent class"""

    def test_news_content_creation(self):
        """Test creating a NewsContent object"""
        news = NewsContent(
            title="Company Announces New CEO",
            content="Company Inc. has announced that John Doe will be the new CEO starting next month.",
            source="Business News",
            url="https://example.com/news/1",
            author="Jane Smith",
            publish_date=datetime(2023, 5, 15)
        )
        
        self.assertEqual(news.title, "Company Announces New CEO")
        self.assertEqual(news.content, "Company Inc. has announced that John Doe will be the new CEO starting next month.")
        self.assertEqual(news.source, "Business News")
        self.assertEqual(news.url, "https://example.com/news/1")
        self.assertEqual(news.author, "Jane Smith")
        self.assertEqual(news.publish_date, datetime(2023, 5, 15))
        self.assertEqual(news.entities, [])
        self.assertEqual(news.claims, [])
        self.assertIsNotNone(news.content_hash)
        self.assertIsNone(news.entanglement_hash)
        self.assertFalse(news.processed)
    
    def test_news_content_to_dict(self):
        """Test converting a NewsContent object to a dictionary"""
        news = NewsContent(
            title="Company Announces New CEO",
            content="Company Inc. has announced that John Doe will be the new CEO starting next month.",
            source="Business News",
            url="https://example.com/news/1",
            author="Jane Smith",
            publish_date=datetime(2023, 5, 15)
        )
        
        # Add an entity
        entity = ContentEntity(
            name="John Doe",
            entity_type="PERSON",
            context="John Doe will be the new CEO",
            confidence=0.9,
            start_pos=35,
            end_pos=43
        )
        news.entities = [entity]
        
        # Add a claim
        claim = ContentClaim(
            claim_text="John Doe will be the new CEO",
            entities=[entity],
            source_text="Company Announces New CEO",
            confidence=0.8,
            claim_type="FACTUAL",
            start_pos=35,
            end_pos=63
        )
        news.claims = [claim]
        
        # Set entanglement hash
        news.entanglement_hash = "abcdef1234567890"
        
        news_dict = news.to_dict()
        
        self.assertEqual(news_dict["title"], "Company Announces New CEO")
        self.assertEqual(news_dict["content"], "Company Inc. has announced that John Doe will be the new CEO starting next month.")
        self.assertEqual(news_dict["source"], "Business News")
        self.assertEqual(news_dict["url"], "https://example.com/news/1")
        self.assertEqual(news_dict["author"], "Jane Smith")
        self.assertEqual(news_dict["publish_date"], "2023-05-15T00:00:00")
        self.assertEqual(len(news_dict["entities"]), 1)
        self.assertEqual(news_dict["entities"][0]["name"], "John Doe")
        self.assertEqual(len(news_dict["claims"]), 1)
        self.assertEqual(news_dict["claims"][0]["text"], "John Doe will be the new CEO")
        self.assertEqual(news_dict["entanglement_hash"], "abcdef1234567890")


class TestContentProcessor(unittest.TestCase):
    """Tests for the ContentProcessor class"""

    def setUp(self):
        """Set up test fixtures"""
        self.processor = ContentProcessor()
        
        # Sample news content for testing
        self.news_content = NewsContent(
            title="Company Announces New CEO",
            content="Company Inc. has announced that John Doe will be the new CEO starting next month. "
                   "The board of directors made the decision after a thorough search. "
                   "John Doe previously worked at Tech Corp as CTO.",
            source="Business News",
            author="Jane Smith",
            publish_date=datetime(2023, 5, 15)
        )
    
    @patch('nltk.ne_chunk')
    @patch('nltk.pos_tag')
    @patch('nltk.word_tokenize')
    def test_extract_entities(self, mock_word_tokenize, mock_pos_tag, mock_ne_chunk):
        """Test entity extraction"""
        # Mock NLTK functions
        mock_word_tokenize.return_value = ["John", "Doe", "is", "the", "CEO"]
        mock_pos_tag.return_value = [("John", "NNP"), ("Doe", "NNP"), ("is", "VBZ"), ("the", "DT"), ("CEO", "NN")]
        
        # Create a mock named entity chunk
        mock_chunk = MagicMock()
        mock_chunk.label.return_value = "PERSON"
        mock_chunk.leaves.return_value = [("John", "NNP"), ("Doe", "NNP")]
        
        # Create a mock parse tree with the named entity chunk
        mock_tree = [mock_chunk, ("is", "VBZ"), ("the", "DT"), ("CEO", "NN")]
        mock_ne_chunk.return_value = mock_tree
        
        # Process the content
        self.processor._extract_entities(self.news_content)
        
        # Check that entities were extracted
        self.assertGreater(len(self.news_content.entities), 0)
        
        # Verify that the entity has the expected properties
        entity = self.news_content.entities[0]
        self.assertEqual(entity.name, "John Doe")
        self.assertEqual(entity.entity_type, "PERSON")
    
    def test_extract_claims(self):
        """Test claim extraction"""
        # Add an entity to the news content
        entity = ContentEntity(
            name="John Doe",
            entity_type="PERSON",
            context="John Doe will be the new CEO",
            confidence=0.9,
            start_pos=35,
            end_pos=43
        )
        self.news_content.entities = [entity]
        
        # Process the content
        self.processor._extract_claims(self.news_content)
        
        # Check that claims were extracted
        self.assertGreater(len(self.news_content.claims), 0)
    
    def test_generate_entanglement_hash(self):
        """Test entanglement hash generation"""
        # Add an entity to the news content
        entity = ContentEntity(
            name="John Doe",
            entity_type="PERSON",
            context="John Doe will be the new CEO",
            confidence=0.9,
            start_pos=35,
            end_pos=43
        )
        self.news_content.entities = [entity]
        
        # Add a claim to the news content
        claim = ContentClaim(
            claim_text="John Doe will be the new CEO",
            entities=[entity],
            source_text="Company Announces New CEO",
            confidence=0.8,
            claim_type="FACTUAL",
            start_pos=35,
            end_pos=63
        )
        self.news_content.claims = [claim]
        
        # Generate entanglement hash
        self.processor._generate_entanglement_hash(self.news_content)
        
        # Check that entanglement hash was generated
        self.assertIsNotNone(self.news_content.entanglement_hash)
    
    @patch('requests.get')
    def test_process_url(self, mock_get):
        """Test processing content from a URL"""
        # Mock the requests.get response
        mock_response = MagicMock()
        mock_response.text = """
        <html>
            <head>
                <title>Company Announces New CEO</title>
            </head>
            <body>
                <article>
                    Company Inc. has announced that John Doe will be the new CEO starting next month.
                    The board of directors made the decision after a thorough search.
                    John Doe previously worked at Tech Corp as CTO.
                </article>
            </body>
        </html>
        """
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Process a URL
        result = self.processor.process_url("https://example.com/news/1")
        
        # Check that a NewsContent object was returned
        self.assertIsNotNone(result)
        self.assertIsInstance(result, NewsContent)
        self.assertEqual(result.title, "Company Announces New CEO")
        self.assertTrue("John Doe" in result.content)
    
    def test_process_content(self):
        """Test processing a NewsContent object"""
        # Process the content
        result = self.processor.process_content(self.news_content)
        
        # Check that the content was processed
        self.assertTrue(result.processed)
        self.assertIsNotNone(result.entanglement_hash)


class TestCrossReferenceVerifier(unittest.TestCase):
    """Tests for the CrossReferenceVerifier class"""

    def setUp(self):
        """Set up test fixtures"""
        self.processor = ContentProcessor()
        self.verifier = CrossReferenceVerifier(self.processor)
        
        # Sample news content for testing
        self.news_content = NewsContent(
            title="Company Announces New CEO",
            content="Company Inc. has announced that John Doe will be the new CEO starting next month. "
                   "The board of directors made the decision after a thorough search. "
                   "John Doe previously worked at Tech Corp as CTO.",
            source="Business News",
            author="Jane Smith",
            publish_date=datetime(2023, 5, 15)
        )
        
        # Add an entity to the news content
        entity = ContentEntity(
            name="John Doe",
            entity_type="PERSON",
            context="John Doe will be the new CEO",
            confidence=0.9,
            start_pos=35,
            end_pos=43
        )
        self.news_content.entities = [entity]
        
        # Add a claim to the news content
        claim = ContentClaim(
            claim_text="John Doe will be the new CEO",
            entities=[entity],
            source_text="Company Announces New CEO",
            confidence=0.8,
            claim_type="FACTUAL",
            start_pos=35,
            end_pos=63
        )
        self.news_content.claims = [claim]
        
        # Process the content
        self.processor.process_content(self.news_content)
    
    @patch('content_processor.ContentProcessor.process_url')
    def test_verify_content(self, mock_process_url):
        """Test content verification"""
        # Create a mock reference content
        ref_content = NewsContent(
            title="Tech Corp Executive Moves to Company Inc",
            content="John Doe, former CTO of Tech Corp, will be joining Company Inc as CEO next month. "
                   "This move was announced by Company Inc's board of directors yesterday.",
            source="Tech News",
            url="https://example.com/tech-news/1"
        )
        
        # Add an entity to the reference content
        ref_entity = ContentEntity(
            name="John Doe",
            entity_type="PERSON",
            context="John Doe, former CTO of Tech Corp",
            confidence=0.9,
            start_pos=0,
            end_pos=8
        )
        ref_content.entities = [ref_entity]
        
        # Add a claim to the reference content
        ref_claim = ContentClaim(
            claim_text="John Doe will be joining Company Inc as CEO",
            entities=[ref_entity],
            source_text="Tech Corp Executive Moves to Company Inc",
            confidence=0.8,
            claim_type="FACTUAL",
            start_pos=0,
            end_pos=45
        )
        ref_content.claims = [ref_claim]
        
        # Process the reference content
        self.processor.process_content(ref_content)
        
        # Mock the process_url method to return the reference content
        mock_process_url.return_value = ref_content
        
        # Verify the content
        result = self.verifier.verify_content(self.news_content, ["https://example.com/tech-news/1"])
        
        # Check that verification result was returned
        self.assertIsNotNone(result)
        self.assertEqual(result["content_hash"], self.news_content.content_hash)
        self.assertGreaterEqual(result["verification_score"], 0.0)
        self.assertLessEqual(result["verification_score"], 1.0)


if __name__ == '__main__':
    unittest.main()
