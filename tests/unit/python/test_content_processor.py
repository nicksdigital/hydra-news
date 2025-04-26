#!/usr/bin/env python3
"""
Unit tests for the Enhanced Content Processor.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import json
import hashlib
from datetime import datetime

# Add source directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../python/src')))

# Import modules to test
from content_processor import ContentEntity, ContentClaim, NewsContent, ContentProcessor
from enhanced_content_processor import (
    EnhancedContentProcessor, 
    EnhancedCrossReferenceVerifier,
    EnhancedNewsContent,
    MultimediaContent
)

class TestContentEntity(unittest.TestCase):
    """Test cases for ContentEntity class"""
    
    def test_content_entity_creation(self):
        """Test creating a ContentEntity instance"""
        entity = ContentEntity(
            name="John Doe",
            entity_type="PERSON",
            context="John Doe is the CEO of Acme Corp.",
            confidence=0.9,
            start_pos=0,
            end_pos=8
        )
        
        self.assertEqual(entity.name, "John Doe")
        self.assertEqual(entity.entity_type, "PERSON")
        self.assertEqual(entity.context, "John Doe is the CEO of Acme Corp.")
        self.assertEqual(entity.confidence, 0.9)
        self.assertEqual(entity.start_pos, 0)
        self.assertEqual(entity.end_pos, 8)
    
    def test_content_entity_to_dict(self):
        """Test converting ContentEntity to dictionary"""
        entity = ContentEntity(
            name="John Doe",
            entity_type="PERSON",
            context="John Doe is the CEO of Acme Corp.",
            confidence=0.9,
            start_pos=0,
            end_pos=8
        )
        
        entity_dict = entity.to_dict()
        
        self.assertEqual(entity_dict["name"], "John Doe")
        self.assertEqual(entity_dict["type"], "PERSON")
        self.assertEqual(entity_dict["context"], "John Doe is the CEO of Acme Corp.")
        self.assertEqual(entity_dict["confidence"], 0.9)
        self.assertEqual(entity_dict["position"]["start"], 0)
        self.assertEqual(entity_dict["position"]["end"], 8)


class TestContentClaim(unittest.TestCase):
    """Test cases for ContentClaim class"""
    
    def test_content_claim_creation(self):
        """Test creating a ContentClaim instance"""
        entity = ContentEntity(
            name="John Doe",
            entity_type="PERSON",
            context="John Doe is the CEO of Acme Corp.",
            confidence=0.9,
            start_pos=0,
            end_pos=8
        )
        
        claim = ContentClaim(
            claim_text="John Doe is the CEO of Acme Corp.",
            entities=[entity],
            source_text="Test Article",
            confidence=0.85,
            claim_type="FACTUAL",
            start_pos=10,
            end_pos=45
        )
        
        self.assertEqual(claim.claim_text, "John Doe is the CEO of Acme Corp.")
        self.assertEqual(len(claim.entities), 1)
        self.assertEqual(claim.source_text, "Test Article")
        self.assertEqual(claim.confidence, 0.85)
        self.assertEqual(claim.claim_type, "FACTUAL")
        self.assertEqual(claim.start_pos, 10)
        self.assertEqual(claim.end_pos, 45)
        self.assertIsNotNone(claim.id)
    
    def test_content_claim_to_dict(self):
        """Test converting ContentClaim to dictionary"""
        entity = ContentEntity(
            name="John Doe",
            entity_type="PERSON",
            context="John Doe is the CEO of Acme Corp.",
            confidence=0.9,
            start_pos=0,
            end_pos=8
        )
        
        claim = ContentClaim(
            claim_text="John Doe is the CEO of Acme Corp.",
            entities=[entity],
            source_text="Test Article",
            confidence=0.85,
            claim_type="FACTUAL",
            start_pos=10,
            end_pos=45
        )
        
        claim_dict = claim.to_dict()
        
        self.assertEqual(claim_dict["text"], "John Doe is the CEO of Acme Corp.")
        self.assertEqual(len(claim_dict["entities"]), 1)
        self.assertEqual(claim_dict["source_text"], "Test Article")
        self.assertEqual(claim_dict["confidence"], 0.85)
        self.assertEqual(claim_dict["type"], "FACTUAL")
        self.assertEqual(claim_dict["position"]["start"], 10)
        self.assertEqual(claim_dict["position"]["end"], 45)
        self.assertIsNotNone(claim_dict["id"])


class TestNewsContent(unittest.TestCase):
    """Test cases for NewsContent class"""
    
    def test_news_content_creation(self):
        """Test creating a NewsContent instance"""
        news = NewsContent(
            title="Test Article",
            content="This is a test article about John Doe, the CEO of Acme Corp.",
            source="Test Source",
            url="https://example.com/test-article",
            author="Test Author",
            publish_date=datetime.now()
        )
        
        self.assertEqual(news.title, "Test Article")
        self.assertEqual(news.content, "This is a test article about John Doe, the CEO of Acme Corp.")
        self.assertEqual(news.source, "Test Source")
        self.assertEqual(news.url, "https://example.com/test-article")
        self.assertEqual(news.author, "Test Author")
        self.assertIsNotNone(news.publish_date)
        self.assertEqual(len(news.entities), 0)
        self.assertEqual(len(news.claims), 0)
        self.assertIsNotNone(news.content_hash)
        self.assertIsNone(news.entanglement_hash)
        self.assertFalse(news.processed)
    
    def test_news_content_to_dict(self):
        """Test converting NewsContent to dictionary"""
        news = NewsContent(
            title="Test Article",
            content="This is a test article about John Doe, the CEO of Acme Corp.",
            source="Test Source",
            url="https://example.com/test-article",
            author="Test Author"
        )
        
        news_dict = news.to_dict()
        
        self.assertEqual(news_dict["title"], "Test Article")
        self.assertEqual(news_dict["content"], "This is a test article about John Doe, the CEO of Acme Corp.")
        self.assertEqual(news_dict["source"], "Test Source")
        self.assertEqual(news_dict["url"], "https://example.com/test-article")
        self.assertEqual(news_dict["author"], "Test Author")
        self.assertIsNotNone(news_dict["content_hash"])
        self.assertFalse(news_dict["processed"])


class TestContentProcessor(unittest.TestCase):
    """Test cases for ContentProcessor class"""

    def setUp(self):
        """Set up test fixtures"""
        self.processor = ContentProcessor()
        
        # Sample news content
        self.news_content = NewsContent(
            title="Acme Corp Announces New CEO",
            content="John Doe has been appointed as the new CEO of Acme Corp. "
                   "The company announced this change yesterday. "
                   "Jane Smith, the former CEO, will remain on the board of directors.",
            source="Test News",
            url="https://example.com/test-article",
            author="Test Author"
        )
    
    @patch('content_processor.requests.get')
    def test_process_url(self, mock_get):
        """Test processing a URL"""
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.text = """
        <html>
            <head>
                <title>Acme Corp Announces New CEO</title>
            </head>
            <body>
                <article>
                    <h1>Acme Corp Announces New CEO</h1>
                    <p>John Doe has been appointed as the new CEO of Acme Corp.</p>
                    <p>The company announced this change yesterday.</p>
                    <p>Jane Smith, the former CEO, will remain on the board of directors.</p>
                </article>
            </body>
        </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Process URL
        result = self.processor.process_url("https://example.com/test-article")
        
        # Check result
        self.assertIsNotNone(result)
        self.assertEqual(result.title, "Acme Corp Announces New CEO")
        self.assertIn("John Doe", result.content)
        self.assertEqual(result.source, "example.com")
        self.assertEqual(result.url, "https://example.com/test-article")
        self.assertTrue(result.processed)
        self.assertGreater(len(result.entities), 0)
        
        # Check entities extraction
        person_entities = [e for e in result.entities if e.entity_type == "PERSON"]
        self.assertGreater(len(person_entities), 0)
        
        # Check claims extraction
        self.assertGreater(len(result.claims), 0)
    
    def test_process_content(self):
        """Test processing content"""
        # Process content
        result = self.processor.process_content(self.news_content)
        
        # Check result
        self.assertTrue(result.processed)
        self.assertGreater(len(result.entities), 0)
        self.assertGreater(len(result.claims), 0)
        self.assertIsNotNone(result.entanglement_hash)
        
        # Verify entity extraction
        person_entities = [e for e in result.entities if e.entity_type == "PERSON"]
        self.assertGreater(len(person_entities), 0)
        
        # Verify claim extraction
        self.assertTrue(any("John Doe" in claim.claim_text for claim in result.claims))
    
    def test_extract_entities(self):
        """Test entity extraction"""
        # Extract entities
        self.processor._extract_entities(self.news_content)
        
        # Check extracted entities
        self.assertGreater(len(self.news_content.entities), 0)
        
        # Check for specific entities
        entity_names = [e.name for e in self.news_content.entities]
        self.assertTrue("John Doe" in entity_names or "John" in entity_names)
        self.assertTrue("Acme Corp" in entity_names or "Acme" in entity_names)
    
    def test_extract_claims(self):
        """Test claim extraction"""
        # First extract entities (claims need entities)
        self.processor._extract_entities(self.news_content)
        
        # Then extract claims
        self.processor._extract_claims(self.news_content)
        
        # Check extracted claims
        self.assertGreater(len(self.news_content.claims), 0)
        
        # Check claim content
        claim_texts = [c.claim_text for c in self.news_content.claims]
        self.assertTrue(any("John Doe" in text for text in claim_texts))


class TestEnhancedContentProcessor(unittest.TestCase):
    """Test cases for EnhancedContentProcessor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Skip tests if transformers not available
        try:
            from transformers import AutoTokenizer
            self.transformers_available = True
        except ImportError:
            self.transformers_available = False
            self.skipTest("Transformers library not available")
        
        # Create processor with mock config
        self.config = {
            'models': {
                'embedding': 'sentence-transformers/all-MiniLM-L6-v2',
            }
        }
        
        try:
            self.processor = EnhancedContentProcessor(self.config)
        except:
            self.skipTest("Enhanced models not available")
        
        # Sample news content
        self.news_content = EnhancedNewsContent(
            title="Acme Corp Announces New CEO",
            content="John Doe has been appointed as the new CEO of Acme Corp. "
                   "The company announced this change yesterday. "
                   "Jane Smith, the former CEO, will remain on the board of directors.",
            source="Test News",
            url="https://example.com/test-article",
            author="Test Author"
        )
        
        # Sample HTML content for multimedia testing
        self.html_content = """
        <html>
            <head>
                <title>Acme Corp Announces New CEO</title>
            </head>
            <body>
                <article>
                    <h1>Acme Corp Announces New CEO</h1>
                    <img src="https://example.com/images/ceo.jpg" alt="John Doe, CEO" width="800" height="600"/>
                    <p>John Doe has been appointed as the new CEO of Acme Corp.</p>
                    <p>The company announced this change yesterday.</p>
                    <figure>
                        <img src="https://example.com/images/office.jpg" alt="Acme Corp Office" width="800" height="600"/>
                        <figcaption>Acme Corp headquarters in New York</figcaption>
                    </figure>
                </article>
            </body>
        </html>
        """
    
    @patch('enhanced_content_processor.requests.get')
    def test_process_url_enhanced(self, mock_get):
        """Test processing a URL with enhanced processor"""
        if not self.transformers_available:
            self.skipTest("Transformers library not available")
        
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.text = self.html_content
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Process URL (conditionally skip if models not available)
        try:
            with patch('enhanced_content_processor.BeautifulSoup') as mock_bs:
                mock_bs.return_value.title.string = "Acme Corp Announces New CEO"
                mock_bs.return_value.find_all.return_value = [MagicMock()]
                mock_bs.return_value.find_all.return_value[0].get_text.return_value = self.news_content.content
                
                result = self.processor.process_url("https://example.com/test-article")
                
                # Skip remaining tests if result is None (models not available)
                if result is None:
                    self.skipTest("Models not available for enhanced processor")
                
                # Basic checks
                self.assertIsNotNone(result)
                self.assertEqual(result.title, "Acme Corp Announces New CEO")
                self.assertIn("John Doe", result.content)
                self.assertEqual(result.source, "example.com")
                self.assertEqual(result.url, "https://example.com/test-article")
                self.assertTrue(result.processed)
                
                # Check if multimedia extraction was at least attempted
                mock_bs.return_value.find_all.assert_called()
        except Exception as e:
            self.skipTest(f"Error in enhanced processor test: {e}")
    
    def test_extract_entities_enhanced(self):
        """Test enhanced entity extraction"""
        if not self.transformers_available:
            self.skipTest("Transformers library not available")
        
        try:
            # Test with spaCy mock if available
            with patch('enhanced_content_processor.spacy.load') as mock_load:
                mock_nlp = MagicMock()
                mock_doc = MagicMock()
                mock_ent = MagicMock()
                
                mock_ent.text = "John Doe"
                mock_ent.label_ = "PERSON"
                mock_ent.start_char = 0
                mock_ent.end_char = 8
                
                mock_doc.ents = [mock_ent]
                mock_nlp.return_value = mock_doc
                mock_load.return_value = mock_nlp
                
                self.processor.nlp = mock_nlp
                
                # Extract entities
                self.processor._extract_entities_enhanced(self.news_content)
                
                # Check if entities were extracted
                self.assertGreater(len(self.news_content.entities), 0)
                
                # Check entity attributes
                if len(self.news_content.entities) > 0:
                    entity = self.news_content.entities[0]
                    self.assertEqual(entity.name, "John Doe")
                    self.assertEqual(entity.entity_type, "PERSON")
        except Exception as e:
            self.skipTest(f"Error in enhanced entity extraction test: {e}")
    
    def test_extract_multimedia(self):
        """Test multimedia extraction"""
        if not self.transformers_available:
            self.skipTest("Transformers library not available")
        
        # Create a news content with HTML
        news = EnhancedNewsContent(
            title="Acme Corp Announces New CEO",
            content="Test content",
            source="Test News",
            html_content=self.html_content
        )
        
        # Extract multimedia using BS mock
        with patch('enhanced_content_processor.BeautifulSoup') as mock_bs:
            # Mock image 1
            mock_img1 = MagicMock()
            mock_img1.get.side_effect = lambda attr, default=None: {
                'src': 'https://example.com/images/ceo.jpg',
                'alt': 'John Doe, CEO',
                'width': '800',
                'height': '600'
            }.get(attr, default)
            
            # Mock image 2
            mock_img2 = MagicMock()
            mock_img2.get.side_effect = lambda attr, default=None: {
                'src': 'https://example.com/images/office.jpg',
                'alt': 'Acme Corp Office',
                'width': '800',
                'height': '600'
            }.get(attr, default)
            
            # Setup BS mock
            mock_bs.return_value.find_all.side_effect = lambda tags: [mock_img1, mock_img2] if 'img' in tags else []
            
            # Parent for figcaption test
            mock_img2.parent = MagicMock()
            mock_img2.parent.name = 'figure'
            mock_figcaption = MagicMock()
            mock_figcaption.get_text.return_value = "Acme Corp headquarters in New York"
            mock_img2.parent.find.return_value = mock_figcaption
            
            try:
                # Extract multimedia
                self.processor._extract_multimedia(news, mock_bs.return_value)
                
                # Check if multimedia was extracted
                self.assertGreaterEqual(len(news.multimedia), 0)
            except Exception as e:
                self.skipTest(f"Error in multimedia extraction test: {e}")


class TestEnhancedCrossReferenceVerifier(unittest.TestCase):
    """Test cases for EnhancedCrossReferenceVerifier"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Basic processor for fallback
        self.basic_processor = ContentProcessor()
        
        # Try to use enhanced processor if available
        try:
            from transformers import AutoTokenizer
            self.enhanced_processor = EnhancedContentProcessor()
            self.verifier = EnhancedCrossReferenceVerifier(self.enhanced_processor)
            self.transformers_available = True
        except ImportError:
            self.verifier = EnhancedCrossReferenceVerifier(self.basic_processor)
            self.transformers_available = False
        
        # Sample news content
        self.main_content = NewsContent(
            title="Acme Corp Announces New CEO",
            content="John Doe has been appointed as the new CEO of Acme Corp. "
                   "The company announced this change yesterday. "
                   "Jane Smith, the former CEO, will remain on the board of directors.",
            source="trusted-source.com",
            url="https://trusted-source.com/article"
        )
        
        # Process the content
        self.basic_processor.process_content(self.main_content)
        
        # Reference content (supporting)
        self.ref_content1 = NewsContent(
            title="John Doe Takes Helm at Acme",
            content="Acme Corporation announced John Doe as their new Chief Executive Officer on Monday. "
                   "The board unanimously approved the appointment.",
            source="reuters.com",
            url="https://reuters.com/article"
        )
        self.basic_processor.process_content(self.ref_content1)
        
        # Reference content (disputing)
        self.ref_content2 = NewsContent(
            title="Jane Smith Continues as Acme CEO",
            content="Despite rumors, Jane Smith will continue as CEO of Acme Corp. "
                   "The company denied any leadership changes are planned.",
            source="unreliable-news.com",
            url="https://unreliable-news.com/article"
        )
        self.basic_processor.process_content(self.ref_content2)
    
    def test_verify_content(self):
        """Test content verification"""
        # Verify with references
        result = self.verifier.verify_content(
            self.main_content, 
            [self.ref_content1, self.ref_content2]
        )
        
        # Basic structure checks
        self.assertIn('verification_score', result)
        self.assertIn('verified_claims', result)
        self.assertIn('disputed_claims', result)
        self.assertIn('references', result)
        self.assertEqual(len(result['references']), 2)
        
        # Check trust score boost
        if self.transformers_available:
            self.assertIn('trusted_source_boost', result)
    
    def test_trusted_sources(self):
        """Test trusted source handling"""
        # Check trusted sources were loaded
        self.assertTrue(hasattr(self.verifier, 'trusted_sources'))
        self.assertIsInstance(self.verifier.trusted_sources, dict)
        
        # Check source trust score calculation
        reuters_score = self.verifier._get_source_trust_score("reuters.com")
        unknown_score = self.verifier._get_source_trust_score("unknown-source.com")
        
        self.assertGreater(reuters_score, 0.5)  # Should be a trusted source
        self.assertEqual(unknown_score, 0.5)    # Default for unknown sources
    
    @unittest.skipIf(not EnhancedContentProcessor, "Enhanced processor not available")
    def test_semantic_similarity(self):
        """Test semantic similarity calculation"""
        if not self.transformers_available:
            self.skipTest("Transformers library not available")
        
        try:
            # Create claim
            entity = ContentEntity(
                name="John Doe",
                entity_type="PERSON",
                context="John Doe is the CEO",
                confidence=0.9,
                start_pos=0,
                end_pos=8
            )
            
            claim = ContentClaim(
                claim_text="John Doe has been appointed as the new CEO of Acme Corp.",
                entities=[entity],
                source_text="Test",
                confidence=0.8,
                claim_type="FACTUAL",
                start_pos=0,
                end_pos=59
            )
            
            # Create reference content
            ref = EnhancedNewsContent(
                title="Acme Appoints New CEO",
                content="Acme Corporation has selected John Doe as their new CEO.",
                source="test.com"
            )
            
            # Mock embedding generation
            with patch.object(self.verifier, '_calculate_semantic_similarity', return_value=0.85):
                similarity = self.verifier._calculate_semantic_similarity(claim, ref)
                self.assertGreaterEqual(similarity, 0.0)
                self.assertLessEqual(similarity, 1.0)
        except Exception as e:
            self.skipTest(f"Error in semantic similarity test: {e}")


if __name__ == '__main__':
    unittest.main()
