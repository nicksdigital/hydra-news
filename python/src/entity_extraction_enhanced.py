"""
Enhanced entity extraction for Hydra News content processor.

This module provides advanced entity extraction capabilities using:
1. Named Entity Recognition (NER) with transformers
2. Entity linking to knowledge bases
3. Entity relationship extraction
4. Confidence scoring with multiple models
"""

import os
import re
import json
from typing import Dict, List, Optional, Set, Tuple, Any, Union
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

# Import base content processor classes
from content_processor import ContentEntity, NewsContent

# Try to import advanced NLP libraries, with fallbacks if not available
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import spacy
    SPACY_AVAILABLE = True
    try:
        nlp = spacy.load("en_core_web_lg")
    except:
        try:
            nlp = spacy.load("en_core_web_md")
        except:
            try:
                nlp = spacy.load("en_core_web_sm")
            except:
                SPACY_AVAILABLE = False
                nlp = None
except ImportError:
    SPACY_AVAILABLE = False
    nlp = None

# Entity types mapping
ENTITY_TYPES = {
    "PERSON": "PERSON",
    "ORG": "ORGANIZATION",
    "GPE": "LOCATION",
    "LOC": "LOCATION",
    "FAC": "FACILITY",
    "PRODUCT": "PRODUCT",
    "EVENT": "EVENT",
    "WORK_OF_ART": "WORK_OF_ART",
    "LAW": "LAW",
    "DATE": "DATE",
    "TIME": "TIME",
    "PERCENT": "PERCENT",
    "MONEY": "MONEY",
    "QUANTITY": "QUANTITY",
    "ORDINAL": "ORDINAL",
    "CARDINAL": "CARDINAL",
    "NORP": "NATIONALITY_OR_RELIGIOUS_POLITICAL_GROUP",
    "LANGUAGE": "LANGUAGE",
}

class EnhancedEntityExtractor:
    """Enhanced entity extraction with multiple NLP models"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the entity extractor with configuration"""
        self.config = config or {}
        self.models = {}
        
        # Initialize NLP components
        self._initialize_nlp()
        
    def _initialize_nlp(self) -> None:
        """Initialize NLP components for entity extraction"""
        # Initialize transformers models if available
        if TRANSFORMERS_AVAILABLE:
            try:
                # Use specified model or default to a good general NER model
                model_name = self.config.get('ner_model', 'dbmdz/bert-large-cased-finetuned-conll03-english')
                self.models['ner'] = pipeline('ner', model=model_name, aggregation_strategy="simple")
                print(f"Loaded transformer NER model: {model_name}")
            except Exception as e:
                print(f"Error loading transformer NER model: {e}")
        
        # Initialize spaCy if available
        if SPACY_AVAILABLE and nlp is not None:
            self.models['spacy'] = nlp
            print(f"Loaded spaCy model: {nlp.meta['name']}")
        
        # Always make sure NLTK is available as fallback
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('averaged_perceptron_tagger')
            nltk.data.find('maxent_ne_chunker')
            nltk.data.find('words')
            self.models['nltk'] = True
            print("NLTK models loaded successfully")
        except LookupError:
            try:
                nltk.download('punkt')
                nltk.download('averaged_perceptron_tagger')
                nltk.download('maxent_ne_chunker')
                nltk.download('words')
                self.models['nltk'] = True
                print("NLTK models downloaded successfully")
            except Exception as e:
                print(f"Error loading NLTK models: {e}")
                self.models['nltk'] = False
    
    def extract_entities(self, news_content: NewsContent) -> List[ContentEntity]:
        """
        Extract entities from news content using the best available models
        
        Args:
            news_content: The news content to extract entities from
            
        Returns:
            A list of extracted entities
        """
        entities = []
        
        # Try using spaCy first (if available)
        if SPACY_AVAILABLE and 'spacy' in self.models:
            entities.extend(self._extract_entities_spacy(news_content))
        
        # Try using transformers next (if available)
        if TRANSFORMERS_AVAILABLE and 'ner' in self.models:
            entities.extend(self._extract_entities_transformers(news_content))
        
        # Fall back to NLTK if needed or to supplement other models
        if self.models.get('nltk', False):
            # Only use NLTK if we don't have any entities yet
            if not entities:
                entities.extend(self._extract_entities_nltk(news_content))
            # Otherwise, use NLTK to supplement with entity types that might be missed
            else:
                nltk_entities = self._extract_entities_nltk(news_content)
                # Add NLTK entities that don't overlap with existing ones
                for nltk_entity in nltk_entities:
                    # Check if this entity overlaps with any existing entity
                    overlaps = False
                    for entity in entities:
                        if (nltk_entity.start_pos <= entity.end_pos and 
                            nltk_entity.end_pos >= entity.start_pos):
                            overlaps = True
                            break
                    
                    if not overlaps:
                        entities.append(nltk_entity)
        
        # Merge duplicate entities and keep the one with highest confidence
        merged_entities = {}
        for entity in entities:
            key = f"{entity.name.lower()}|{entity.entity_type}|{entity.start_pos}|{entity.end_pos}"
            if key not in merged_entities or entity.confidence > merged_entities[key].confidence:
                merged_entities[key] = entity
        
        return list(merged_entities.values())
    
    def _extract_entities_spacy(self, news_content: NewsContent) -> List[ContentEntity]:
        """Extract entities using spaCy"""
        entities = []
        
        try:
            # Process the content with spaCy
            doc = self.models['spacy'](news_content.content)
            
            # Extract named entities
            for ent in doc.ents:
                # Map spaCy entity types to our types
                entity_type = ent.label_
                if entity_type not in ENTITY_TYPES:
                    entity_type = "MISC"
                else:
                    entity_type = ENTITY_TYPES[entity_type]
                
                # Get context (surrounding text)
                start_pos = ent.start_char
                end_pos = ent.end_char
                context_start = max(0, start_pos - 50)
                context_end = min(len(news_content.content), end_pos + 50)
                context = news_content.content[context_start:context_end]
                
                # Create entity
                entity = ContentEntity(
                    name=ent.text,
                    entity_type=entity_type,
                    context=context,
                    confidence=0.9,  # spaCy doesn't provide confidence scores directly
                    start_pos=start_pos,
                    end_pos=end_pos
                )
                entities.append(entity)
                
        except Exception as e:
            print(f"Error extracting entities with spaCy: {e}")
        
        return entities
    
    def _extract_entities_transformers(self, news_content: NewsContent) -> List[ContentEntity]:
        """Extract entities using transformers"""
        entities = []
        
        try:
            # Split content into chunks to avoid token limits
            # Most transformer models have a limit of 512 tokens
            chunks = self._split_into_chunks(news_content.content, max_length=400)
            
            offset = 0
            for chunk in chunks:
                # Process chunk with transformer model
                ner_results = self.models['ner'](chunk)
                
                for result in ner_results:
                    entity_name = result['word']
                    entity_type = result['entity_group']
                    
                    # Map to our entity types
                    if entity_type not in ENTITY_TYPES:
                        entity_type = "MISC"
                    else:
                        entity_type = ENTITY_TYPES[entity_type]
                    
                    # Adjust positions for the full text
                    start_pos = offset + result['start']
                    end_pos = offset + result['end']
                    
                    # Get context
                    context_start = max(0, start_pos - 50)
                    context_end = min(len(news_content.content), end_pos + 50)
                    context = news_content.content[context_start:context_end]
                    
                    entity = ContentEntity(
                        name=entity_name,
                        entity_type=entity_type,
                        context=context,
                        confidence=result['score'],
                        start_pos=start_pos,
                        end_pos=end_pos
                    )
                    entities.append(entity)
                
                offset += len(chunk)
                
        except Exception as e:
            print(f"Error extracting entities with transformers: {e}")
        
        return entities
    
    def _extract_entities_nltk(self, news_content: NewsContent) -> List[ContentEntity]:
        """Extract entities using NLTK"""
        entities = []
        
        try:
            # Tokenize content into sentences
            sentences = sent_tokenize(news_content.content)
            
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
                        
                        # Map NLTK entity types to our types
                        if entity_type not in ENTITY_TYPES:
                            entity_type = "MISC"
                        else:
                            entity_type = ENTITY_TYPES[entity_type]
                        
                        # Find position in original text
                        start_pos = news_content.content.find(entity_name, current_pos)
                        if start_pos != -1:
                            end_pos = start_pos + len(entity_name)
                            
                            # Get context (surrounding text)
                            context_start = max(0, start_pos - 50)
                            context_end = min(len(news_content.content), end_pos + 50)
                            context = news_content.content[context_start:context_end]
                            
                            # Create entity
                            entity = ContentEntity(
                                name=entity_name,
                                entity_type=entity_type,
                                context=context,
                                confidence=0.7,  # NLTK is less accurate than other models
                                start_pos=start_pos,
                                end_pos=end_pos
                            )
                            entities.append(entity)
                
                current_pos += len(sentence)
                
        except Exception as e:
            print(f"Error extracting entities with NLTK: {e}")
        
        return entities
    
    def _split_into_chunks(self, text: str, max_length: int = 400) -> List[str]:
        """Split text into chunks of maximum length, trying to preserve sentence boundaries"""
        chunks = []
        sentences = sent_tokenize(text)
        
        current_chunk = ""
        for sentence in sentences:
            # If adding this sentence would exceed max_length, start a new chunk
            if len(current_chunk) + len(sentence) > max_length and current_chunk:
                chunks.append(current_chunk)
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
