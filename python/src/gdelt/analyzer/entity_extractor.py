#!/usr/bin/env python3
"""
GDELT Entity Extractor

This module provides functions for extracting named entities from GDELT news articles.
"""

import pandas as pd
import numpy as np
import re
import logging
from collections import Counter, defaultdict

# Set up logging
logger = logging.getLogger(__name__)

# Try to import spaCy
try:
    import spacy
    SPACY_AVAILABLE = True
    # Try to load English and French models
    try:
        nlp_en = spacy.load("en_core_web_sm")
        nlp_fr = spacy.load("fr_core_news_sm")
        logger.info("Loaded spaCy models for English and French")
    except OSError:
        logger.warning("spaCy language models not found. Will download them.")
        spacy.cli.download("en_core_web_sm")
        spacy.cli.download("fr_core_news_sm")
        nlp_en = spacy.load("en_core_web_sm")
        nlp_fr = spacy.load("fr_core_news_sm")
        logger.info("Downloaded and loaded spaCy models for English and French")
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy not available. Falling back to NLTK for entity extraction.")

# Try to import NLTK as fallback
if not SPACY_AVAILABLE:
    try:
        import nltk
        from nltk.tokenize import word_tokenize
        from nltk.chunk import ne_chunk
        from nltk.tag import pos_tag
        
        # Download necessary NLTK resources
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('taggers/averaged_perceptron_tagger')
            nltk.data.find('chunkers/maxent_ne_chunker')
            nltk.data.find('corpora/words')
        except LookupError:
            nltk.download('punkt')
            nltk.download('averaged_perceptron_tagger')
            nltk.download('maxent_ne_chunker')
            nltk.download('words')
        
        NLTK_AVAILABLE = True
        logger.info("NLTK loaded for entity extraction")
    except ImportError:
        NLTK_AVAILABLE = False
        logger.warning("Neither spaCy nor NLTK available. Entity extraction will be limited.")

class EntityExtractor:
    """Class for extracting named entities from text"""
    
    def __init__(self):
        """Initialize the entity extractor"""
        self.entity_counts = Counter()
        self.entity_sources = defaultdict(set)
        self.entity_contexts = defaultdict(list)
        self.entity_types = {}
        
    def extract_entities_from_dataframe(self, df):
        """
        Extract entities from a DataFrame of articles
        
        Args:
            df: DataFrame containing articles with 'title' and 'language' columns
            
        Returns:
            DataFrame with extracted entities
        """
        logger.info("Extracting entities from DataFrame")
        
        # Initialize entity lists
        entities = []
        
        # Process each article
        for idx, row in df.iterrows():
            title = row.get('title', '')
            language = row.get('language', 'English')
            url = row.get('url', '')
            domain = row.get('domain', '')
            theme = row.get('theme_id', '')
            
            if pd.isna(title) or title == '':
                continue
            
            # Extract entities from title
            article_entities = self.extract_entities(title, language)
            
            # Add article information to entities
            for entity in article_entities:
                entity['article_id'] = idx
                entity['article_url'] = url
                entity['article_domain'] = domain
                entity['article_theme'] = theme
                entities.append(entity)
                
                # Update entity statistics
                self.entity_counts[entity['text']] += 1
                self.entity_sources[entity['text']].add(domain)
                self.entity_types[entity['text']] = entity['type']
                
                # Store context (up to 50 chars before and after)
                context = self._get_context(title, entity['text'])
                if context:
                    self.entity_contexts[entity['text']].append(context)
        
        # Convert to DataFrame
        if entities:
            entities_df = pd.DataFrame(entities)
            logger.info(f"Extracted {len(entities_df)} entities from {len(df)} articles")
            return entities_df
        else:
            logger.warning("No entities extracted")
            return pd.DataFrame()
    
    def extract_entities(self, text, language='English'):
        """
        Extract named entities from text
        
        Args:
            text: Text to extract entities from
            language: Language of the text ('English' or 'French')
            
        Returns:
            List of dictionaries with entity information
        """
        if pd.isna(text) or text == '':
            return []
        
        entities = []
        
        # Use spaCy if available
        if SPACY_AVAILABLE:
            entities = self._extract_entities_spacy(text, language)
        # Fall back to NLTK
        elif NLTK_AVAILABLE and language.lower() == 'english':
            entities = self._extract_entities_nltk(text)
        # Basic extraction for other cases
        else:
            entities = self._extract_entities_basic(text)
        
        return entities
    
    def _extract_entities_spacy(self, text, language):
        """Extract entities using spaCy"""
        entities = []
        
        try:
            # Select the appropriate language model
            if language.lower() == 'french':
                doc = nlp_fr(text)
            else:
                doc = nlp_en(text)
            
            # Extract named entities
            for ent in doc.ents:
                entity = {
                    'text': ent.text,
                    'type': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'method': 'spacy'
                }
                entities.append(entity)
        except Exception as e:
            logger.error(f"Error extracting entities with spaCy: {e}")
        
        return entities
    
    def _extract_entities_nltk(self, text):
        """Extract entities using NLTK (English only)"""
        entities = []
        
        try:
            # Tokenize and tag parts of speech
            tokens = word_tokenize(text)
            tagged = pos_tag(tokens)
            
            # Extract named entities
            chunks = ne_chunk(tagged)
            
            # Process named entity chunks
            current_entity = []
            current_type = None
            current_start = 0
            
            for i, chunk in enumerate(chunks):
                if hasattr(chunk, 'label'):
                    # Named entity
                    entity_type = chunk.label()
                    entity_text = ' '.join([token for token, pos in chunk.leaves()])
                    
                    entity = {
                        'text': entity_text,
                        'type': entity_type,
                        'start': text.find(entity_text),
                        'end': text.find(entity_text) + len(entity_text),
                        'method': 'nltk'
                    }
                    entities.append(entity)
            
        except Exception as e:
            logger.error(f"Error extracting entities with NLTK: {e}")
        
        return entities
    
    def _extract_entities_basic(self, text):
        """Basic entity extraction using regex patterns"""
        entities = []
        
        # Simple patterns for organizations (uppercase words)
        org_pattern = r'\b([A-Z][A-Za-z]+ [A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)\b'
        for match in re.finditer(org_pattern, text):
            entity = {
                'text': match.group(0),
                'type': 'ORG',
                'start': match.start(),
                'end': match.end(),
                'method': 'regex'
            }
            entities.append(entity)
        
        return entities
    
    def _get_context(self, text, entity_text):
        """Get context around an entity mention"""
        if pd.isna(text) or text == '':
            return None
        
        try:
            # Find the entity in the text
            start_pos = text.find(entity_text)
            if start_pos == -1:
                return None
            
            end_pos = start_pos + len(entity_text)
            
            # Get context (up to 50 chars before and after)
            context_start = max(0, start_pos - 50)
            context_end = min(len(text), end_pos + 50)
            
            # Extract context
            prefix = text[context_start:start_pos]
            suffix = text[end_pos:context_end]
            
            return {
                'prefix': prefix,
                'entity': entity_text,
                'suffix': suffix
            }
        except Exception as e:
            logger.error(f"Error getting context: {e}")
            return None
    
    def calculate_entity_stats(self):
        """
        Calculate statistics for extracted entities
        
        Returns:
            DataFrame with entity statistics
        """
        logger.info("Calculating entity statistics")
        
        # Create a list of entity stats
        entity_stats = []
        
        for entity, count in self.entity_counts.items():
            # Get entity type
            entity_type = self.entity_types.get(entity, 'UNKNOWN')
            
            # Get number of unique sources
            num_sources = len(self.entity_sources.get(entity, set()))
            
            # Get number of contexts
            num_contexts = len(self.entity_contexts.get(entity, []))
            
            # Calculate source diversity (0-1)
            source_diversity = num_sources / max(1, count)
            
            entity_stats.append({
                'entity': entity,
                'type': entity_type,
                'count': count,
                'num_sources': num_sources,
                'num_contexts': num_contexts,
                'source_diversity': source_diversity
            })
        
        # Convert to DataFrame
        if entity_stats:
            stats_df = pd.DataFrame(entity_stats)
            stats_df = stats_df.sort_values('count', ascending=False)
            logger.info(f"Calculated statistics for {len(stats_df)} entities")
            return stats_df
        else:
            logger.warning("No entity statistics calculated")
            return pd.DataFrame()
    
    def get_entity_contexts(self, entity_text, max_contexts=5):
        """
        Get contexts for a specific entity
        
        Args:
            entity_text: Text of the entity
            max_contexts: Maximum number of contexts to return
            
        Returns:
            List of context dictionaries
        """
        contexts = self.entity_contexts.get(entity_text, [])
        return contexts[:max_contexts]
