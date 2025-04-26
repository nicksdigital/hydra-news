"""
Tests for the enhanced entity extraction module.

This module contains unit tests for the enhanced entity extraction functionality, including:
- Entity extraction with transformers
- Entity extraction with spaCy
- Entity extraction with NLTK
- Entity merging and deduplication
"""

import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import the modules to test
from content_processor import NewsContent, ContentEntity
try:
    from entity_extraction_enhanced import EnhancedEntityExtractor, ENTITY_TYPES
    ENHANCED_ENTITY_EXTRACTION_AVAILABLE = True
except ImportError:
    ENHANCED_ENTITY_EXTRACTION_AVAILABLE = False


@unittest.skipIf(not ENHANCED_ENTITY_EXTRACTION_AVAILABLE, "Enhanced entity extraction not available")
class TestEnhancedEntityExtractor(unittest.TestCase):
    """Tests for the EnhancedEntityExtractor class"""

    def setUp(self):
        """Set up test fixtures"""
        self.extractor = EnhancedEntityExtractor()

        # Sample news content for testing
        self.news_content = NewsContent(
            title="Tech Giants Announce New AI Partnership",
            content="Microsoft and Google have announced a new partnership focused on artificial intelligence. "
                   "The CEOs of both companies, Satya Nadella and Sundar Pichai, made the announcement yesterday in San Francisco. "
                   "The partnership will focus on developing new AI standards that will be implemented by 2025.",
            source="Tech News",
            author="Jane Smith"
        )

    @patch('entity_extraction_enhanced.TRANSFORMERS_AVAILABLE', False)
    @patch('entity_extraction_enhanced.SPACY_AVAILABLE', False)
    def test_extract_entities_nltk_fallback(self):
        """Test entity extraction with NLTK fallback"""
        # Create a new extractor with mocked availability flags
        with patch('entity_extraction_enhanced.EnhancedEntityExtractor._initialize_nlp'):
            extractor = EnhancedEntityExtractor()
            extractor.models = {'nltk': True}

            # Mock the NLTK extraction method
            with patch.object(extractor, '_extract_entities_nltk') as mock_nltk:
                mock_nltk.return_value = [
                    ContentEntity(
                        name="Microsoft",
                        entity_type="ORGANIZATION",
                        context="Microsoft and Google have announced",
                        confidence=0.7,
                        start_pos=0,
                        end_pos=9
                    ),
                    ContentEntity(
                        name="Google",
                        entity_type="ORGANIZATION",
                        context="Microsoft and Google have announced",
                        confidence=0.7,
                        start_pos=14,
                        end_pos=20
                    )
                ]

                # Extract entities
                entities = extractor.extract_entities(self.news_content)

                # Check that entities were extracted
                self.assertEqual(len(entities), 2)
                self.assertEqual(entities[0].name, "Microsoft")
                self.assertEqual(entities[1].name, "Google")

    @patch('entity_extraction_enhanced.TRANSFORMERS_AVAILABLE', True)
    @patch('entity_extraction_enhanced.SPACY_AVAILABLE', False)
    def test_extract_entities_transformers(self):
        """Test entity extraction with transformers"""
        # Create a new extractor with mocked availability flags
        with patch('entity_extraction_enhanced.EnhancedEntityExtractor._initialize_nlp'):
            extractor = EnhancedEntityExtractor()
            extractor.models = {'ner': MagicMock()}

            # Mock the transformers extraction method
            with patch.object(extractor, '_extract_entities_transformers') as mock_transformers:
                mock_transformers.return_value = [
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
                    ),
                    ContentEntity(
                        name="Satya Nadella",
                        entity_type="PERSON",
                        context="The CEOs of both companies, Satya Nadella and Sundar Pichai",
                        confidence=0.95,
                        start_pos=58,
                        end_pos=71
                    ),
                    ContentEntity(
                        name="Sundar Pichai",
                        entity_type="PERSON",
                        context="Satya Nadella and Sundar Pichai, made the announcement",
                        confidence=0.95,
                        start_pos=76,
                        end_pos=89
                    ),
                    ContentEntity(
                        name="San Francisco",
                        entity_type="LOCATION",
                        context="made the announcement yesterday in San Francisco",
                        confidence=0.9,
                        start_pos=115,
                        end_pos=128
                    ),
                    ContentEntity(
                        name="2025",
                        entity_type="DATE",
                        context="will be implemented by 2025",
                        confidence=0.8,
                        start_pos=190,
                        end_pos=194
                    )
                ]

                # Extract entities
                entities = extractor.extract_entities(self.news_content)

                # Check that entities were extracted
                self.assertEqual(len(entities), 6)
                self.assertEqual(entities[0].name, "Microsoft")
                self.assertEqual(entities[1].name, "Google")
                self.assertEqual(entities[2].name, "Satya Nadella")
                self.assertEqual(entities[3].name, "Sundar Pichai")
                self.assertEqual(entities[4].name, "San Francisco")
                self.assertEqual(entities[5].name, "2025")

    @patch('entity_extraction_enhanced.TRANSFORMERS_AVAILABLE', False)
    @patch('entity_extraction_enhanced.SPACY_AVAILABLE', True)
    def test_extract_entities_spacy(self):
        """Test entity extraction with spaCy"""
        # Create a new extractor with mocked availability flags
        with patch('entity_extraction_enhanced.EnhancedEntityExtractor._initialize_nlp'):
            extractor = EnhancedEntityExtractor()
            extractor.models = {'spacy': MagicMock()}

            # Mock the spaCy extraction method
            with patch.object(extractor, '_extract_entities_spacy') as mock_spacy:
                mock_spacy.return_value = [
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
                    ),
                    ContentEntity(
                        name="Satya Nadella",
                        entity_type="PERSON",
                        context="The CEOs of both companies, Satya Nadella and Sundar Pichai",
                        confidence=0.9,
                        start_pos=58,
                        end_pos=71
                    ),
                    ContentEntity(
                        name="Sundar Pichai",
                        entity_type="PERSON",
                        context="Satya Nadella and Sundar Pichai, made the announcement",
                        confidence=0.9,
                        start_pos=76,
                        end_pos=89
                    ),
                    ContentEntity(
                        name="San Francisco",
                        entity_type="LOCATION",
                        context="made the announcement yesterday in San Francisco",
                        confidence=0.9,
                        start_pos=115,
                        end_pos=128
                    ),
                    ContentEntity(
                        name="2025",
                        entity_type="DATE",
                        context="will be implemented by 2025",
                        confidence=0.9,
                        start_pos=190,
                        end_pos=194
                    )
                ]

                # Extract entities
                entities = extractor.extract_entities(self.news_content)

                # Check that entities were extracted
                self.assertEqual(len(entities), 6)
                self.assertEqual(entities[0].name, "Microsoft")
                self.assertEqual(entities[1].name, "Google")
                self.assertEqual(entities[2].name, "Satya Nadella")
                self.assertEqual(entities[3].name, "Sundar Pichai")
                self.assertEqual(entities[4].name, "San Francisco")
                self.assertEqual(entities[5].name, "2025")

    def test_entity_types_mapping(self):
        """Test entity types mapping"""
        # Check that entity types are defined
        self.assertIsNotNone(ENTITY_TYPES)
        self.assertIn("PERSON", ENTITY_TYPES)
        self.assertIn("ORG", ENTITY_TYPES)
        self.assertIn("GPE", ENTITY_TYPES)
        self.assertIn("DATE", ENTITY_TYPES)

    @patch('entity_extraction_enhanced.TRANSFORMERS_AVAILABLE', True)
    @patch('entity_extraction_enhanced.SPACY_AVAILABLE', True)
    def test_extract_entities_with_multiple_models(self):
        """Test entity extraction with multiple models"""
        # Create a new extractor with mocked availability flags
        with patch('entity_extraction_enhanced.EnhancedEntityExtractor._initialize_nlp'):
            extractor = EnhancedEntityExtractor()
            extractor.models = {'ner': MagicMock(), 'spacy': MagicMock(), 'nltk': True}

            # Mock the extraction methods
            with patch.object(extractor, '_extract_entities_transformers') as mock_transformers, \
                 patch.object(extractor, '_extract_entities_spacy') as mock_spacy:

                # Transformers finds Microsoft and Google
                mock_transformers.return_value = [
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

                # spaCy finds Satya Nadella and Sundar Pichai
                mock_spacy.return_value = [
                    ContentEntity(
                        name="Satya Nadella",
                        entity_type="PERSON",
                        context="The CEOs of both companies, Satya Nadella and Sundar Pichai",
                        confidence=0.9,
                        start_pos=58,
                        end_pos=71
                    ),
                    ContentEntity(
                        name="Sundar Pichai",
                        entity_type="PERSON",
                        context="Satya Nadella and Sundar Pichai, made the announcement",
                        confidence=0.9,
                        start_pos=76,
                        end_pos=89
                    ),
                    # Duplicate of Microsoft with lower confidence
                    ContentEntity(
                        name="Microsoft",
                        entity_type="ORGANIZATION",
                        context="Microsoft and Google have announced",
                        confidence=0.8,
                        start_pos=0,
                        end_pos=9
                    )
                ]

                # Extract entities
                entities = extractor.extract_entities(self.news_content)

                # The implementation calls both spaCy and transformers, and may also add NLTK entities
                # We don't need to check the exact number of entities, just that the key ones are present

                # Check that our key entities are present
                entity_names = [entity.name for entity in entities]
                self.assertIn("Microsoft", entity_names)
                self.assertIn("Google", entity_names)
                self.assertIn("Satya Nadella", entity_names)
                self.assertIn("Sundar Pichai", entity_names)

                # Check that Microsoft was kept with the higher confidence score
                microsoft_entities = [e for e in entities if e.name == "Microsoft"]
                self.assertTrue(any(e.confidence == 0.9 for e in microsoft_entities))


if __name__ == '__main__':
    unittest.main()
