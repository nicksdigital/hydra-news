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

# Try to import transformers for Hugging Face models
try:
    from transformers import pipeline, AutoModelForTokenClassification, AutoTokenizer, RobertaTokenizerFast, RobertaForTokenClassification
    import torch
    TRANSFORMERS_AVAILABLE = True

    # Try to load the Hugging Face NER model
    try:
        logger.info("Loading Hugging Face NER model: AventIQ-AI/roberta-named-entity-recognition")
        # Initialize the model and tokenizer
        global ner_model, ner_tokenizer, device
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Device set to use {device}")

        model_name = "AventIQ-AI/roberta-named-entity-recognition"
        ner_tokenizer = RobertaTokenizerFast.from_pretrained(model_name)
        ner_model = RobertaForTokenClassification.from_pretrained(model_name).to(device)

        # Define the label list according to the model documentation
        global label_list
        label_list = ["O", "B-PER", "I-PER", "B-ORG", "I-ORG", "B-LOC", "I-LOC", "B-MISC", "I-MISC"]

        logger.info("Loaded Hugging Face NER model successfully")
    except Exception as e:
        logger.warning(f"Error loading Hugging Face NER model: {e}")
        TRANSFORMERS_AVAILABLE = False
        ner_model = None
        ner_tokenizer = None
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    ner_model = None
    ner_tokenizer = None
    logger.warning("Transformers not available. Falling back to spaCy or NLTK for entity extraction.")

# Try to import spaCy as fallback
try:
    import spacy
    SPACY_AVAILABLE = True
    # Try to load English and French models
    try:
        nlp_en = spacy.load("en_core_web_sm")
        nlp_fr = spacy.load("fr_core_news_sm")
        logger.info("Loaded spaCy models for English and French as fallback")
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

        # Try using Hugging Face transformers first
        if TRANSFORMERS_AVAILABLE:
            entities = self._extract_entities_transformers(text)
            if entities:
                return entities

        # Fall back to NLTK for English text
        if NLTK_AVAILABLE and language.lower() == 'english':
            entities = self._extract_entities_nltk(text)
        # Use spaCy if available
        elif SPACY_AVAILABLE:
            entities = self._extract_entities_spacy(text, language)
        # Basic extraction for other cases
        else:
            entities = self._extract_entities_basic(text)

        # Filter out problematic entities
        filtered_entities = []
        for entity in entities:
            # Skip entities with problematic types
            if entity['type'].startswith('LABEL_'):
                # LABEL_0 typically means "not an entity" (O tag)
                if entity['type'] == 'LABEL_0':
                    continue

                # For other LABEL_X, try to map to standard entity types
                try:
                    label_num = int(entity['type'].split('_')[1])
                    if label_num == 1:
                        entity['type'] = 'PERSON'
                    elif label_num == 2:
                        entity['type'] = 'ORGANIZATION'
                    elif label_num == 3:
                        entity['type'] = 'LOCATION'
                    elif label_num == 4:
                        entity['type'] = 'DATE'
                    else:
                        entity['type'] = 'MISC'
                except:
                    entity['type'] = 'MISC'

            # Skip entities that are too long (likely not real entities)
            if len(entity['text'].split()) > 5:
                continue

            # Skip entities with problematic characters
            if '|' in entity['text'] or entity['text'].count(' ') > 5:
                continue

            # Skip entities that are just single characters
            if len(entity['text'].strip()) < 2:
                continue

            # Skip common false positives
            if entity['text'].lower() in ['the', 'a', 'an', 'this', 'that', 'these', 'those', 'it', 'they']:
                continue

            # Ensure entity type is one of the standard types
            standard_types = ['PERSON', 'ORGANIZATION', 'LOCATION', 'DATE', 'TIME', 'MONEY', 'PERCENT', 'FACILITY', 'GPE', 'EVENT', 'MISC']
            if entity['type'] not in standard_types:
                entity['type'] = 'MISC'

            filtered_entities.append(entity)

        return filtered_entities

    def _extract_entities_transformers(self, text):
        """Extract entities using Hugging Face transformers"""
        entities = []

        try:
            # Check if the model and tokenizer are available
            if not ner_model or not ner_tokenizer:
                logger.warning("Hugging Face NER model not available. Falling back to NLTK.")
                return self._extract_entities_nltk(text) if NLTK_AVAILABLE else []

            # Check if text is too long (most models have a limit of 512 tokens)
            if len(text) > 1000:
                text = text[:1000]

            # Extract named entities using the RoBERTa model
            try:
                import torch

                # Tokenize the input text
                tokens = ner_tokenizer(text, return_tensors="pt", truncation=True)
                tokens = {key: val.to(device) for key, val in tokens.items()}

                # Get predictions
                with torch.no_grad():
                    outputs = ner_model(**tokens)

                # Get the predicted labels
                logits = outputs.logits
                predictions = torch.argmax(logits, dim=2)

                # Convert token IDs to tokens
                tokens_list = ner_tokenizer.convert_ids_to_tokens(tokens["input_ids"][0])
                predicted_labels = [label_list[pred] for pred in predictions[0].cpu().numpy()]

                # Process the tokens and labels
                current_entity = None
                current_entity_text = ""
                current_entity_type = ""
                current_entity_start = 0

                # Skip special tokens like [CLS] and [SEP]
                for i, (token, label) in enumerate(zip(tokens_list, predicted_labels)):
                    if token in ["<s>", "</s>", "<pad>"]:
                        continue

                    # Handle beginning of entity
                    if label.startswith("B-"):
                        # If we were tracking an entity, add it to the list
                        if current_entity:
                            entities.append(current_entity)

                        # Start tracking a new entity
                        entity_type = label[2:]  # Remove "B-" prefix
                        current_entity_text = token
                        current_entity_type = entity_type
                        current_entity_start = i

                        # Create the entity dictionary
                        current_entity = {
                            'text': current_entity_text,
                            'type': self._map_entity_type(current_entity_type),
                            'start': current_entity_start,
                            'end': i,
                            'score': 0.9,  # Default score
                            'method': 'transformers'
                        }

                    # Handle inside of entity
                    elif label.startswith("I-") and current_entity and label[2:] == current_entity_type:
                        # Continue the current entity
                        if token.startswith("##"):
                            current_entity_text += token[2:]
                        else:
                            current_entity_text += " " + token

                        # Update the entity
                        current_entity['text'] = current_entity_text
                        current_entity['end'] = i

                    # Handle outside of entity
                    elif label == "O":
                        # If we were tracking an entity, add it to the list
                        if current_entity:
                            entities.append(current_entity)
                            current_entity = None

                # Add the last entity if there is one
                if current_entity:
                    entities.append(current_entity)

                # Filter out problematic entities
                filtered_entities = []
                for entity in entities:
                    # Skip entities that are too short
                    if len(entity['text'].strip()) < 2:
                        continue

                    # Skip entities that are too long
                    if len(entity['text'].split()) > 5:
                        continue

                    # Skip entities with problematic characters
                    if '|' in entity['text'] or entity['text'].count(' ') > 5:
                        continue

                    # Skip common false positives
                    if entity['text'].lower() in ['the', 'a', 'an', 'this', 'that', 'these', 'those', 'it', 'they']:
                        continue

                    filtered_entities.append(entity)

                return filtered_entities

            except Exception as e:
                logger.error(f"Error using Hugging Face NER model: {e}")
                # If the model fails, try using NLTK
                return self._extract_entities_nltk(text) if NLTK_AVAILABLE else []

        except Exception as e:
            logger.error(f"Error extracting entities with transformers: {e}")
            return self._extract_entities_nltk(text) if NLTK_AVAILABLE else []

        return entities

    def _map_entity_type(self, hf_entity_type):
        """Map Hugging Face entity types to standard format"""
        if not hf_entity_type:
            return 'UNKNOWN'

        # Handle label format from some models
        if hf_entity_type.upper().startswith('LABEL_'):
            try:
                label_num = int(hf_entity_type.upper().split('_')[1])
                # Map label numbers to entity types based on common patterns
                if label_num == 1:
                    return 'PERSON'
                elif label_num == 2:
                    return 'ORGANIZATION'
                elif label_num == 3:
                    return 'LOCATION'
                elif label_num == 4:
                    return 'DATE'
                else:
                    return 'MISC'
            except:
                return 'MISC'

        # Common mappings for entity types
        type_mapping = {
            'PER': 'PERSON',
            'PERSON': 'PERSON',
            'B-PER': 'PERSON',
            'I-PER': 'PERSON',
            'ORG': 'ORGANIZATION',
            'ORGANIZATION': 'ORGANIZATION',
            'B-ORG': 'ORGANIZATION',
            'I-ORG': 'ORGANIZATION',
            'LOC': 'LOCATION',
            'LOCATION': 'LOCATION',
            'B-LOC': 'LOCATION',
            'I-LOC': 'LOCATION',
            'GPE': 'LOCATION',
            'PRODUCT': 'PRODUCT',
            'B-PRODUCT': 'PRODUCT',
            'I-PRODUCT': 'PRODUCT',
            'EVENT': 'EVENT',
            'B-EVENT': 'EVENT',
            'I-EVENT': 'EVENT',
            'DATE': 'DATE',
            'B-DATE': 'DATE',
            'I-DATE': 'DATE',
            'TIME': 'TIME',
            'B-TIME': 'TIME',
            'I-TIME': 'TIME',
            'MONEY': 'MONEY',
            'B-MONEY': 'MONEY',
            'I-MONEY': 'MONEY',
            'PERCENT': 'PERCENT',
            'QUANTITY': 'QUANTITY',
            'LANGUAGE': 'LANGUAGE',
            'WORK_OF_ART': 'WORK_OF_ART',
            'LAW': 'LAW',
            'FAC': 'FACILITY',
            'NORP': 'NORP',  # Nationalities, religious or political groups
            'MISC': 'MISC',
            'B-MISC': 'MISC',
            'I-MISC': 'MISC',
        }

        # Normalize the entity type
        normalized_type = hf_entity_type.upper()

        # Return mapped type or original if not in mapping
        return type_mapping.get(normalized_type, normalized_type)

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
            for i, chunk in enumerate(chunks):
                if hasattr(chunk, 'label'):
                    # Named entity
                    entity_type = chunk.label()
                    entity_text = ' '.join([token for token, pos in chunk.leaves()])

                    # Skip if entity text is too long (likely not a real entity)
                    if len(entity_text.split()) > 5:
                        continue

                    # Skip if entity text contains problematic characters
                    if '|' in entity_text or entity_text.count(' ') > 5:
                        continue

                    # Skip if entity text is just a single character
                    if len(entity_text.strip()) < 2:
                        continue

                    # Skip common false positives
                    if entity_text.lower() in ['the', 'a', 'an', 'this', 'that', 'these', 'those', 'it', 'they']:
                        continue

                    # Map entity type to standard format
                    mapped_type = self._map_entity_type(entity_type)

                    entity = {
                        'text': entity_text,
                        'type': mapped_type,
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

        # Pattern for organizations (uppercase words)
        org_pattern = r'\b([A-Z][A-Za-z]+ [A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)\b'
        for match in re.finditer(org_pattern, text):
            entity_text = match.group(0)

            # Skip if entity text is too long (likely not a real entity)
            if len(entity_text.split()) > 5:
                continue

            # Skip if entity text contains problematic characters
            if '|' in entity_text or entity_text.count(' ') > 5:
                continue

            # Skip common false positives
            if entity_text.lower() in ['the', 'a', 'an', 'this', 'that', 'these', 'those', 'it', 'they']:
                continue

            entity = {
                'text': entity_text,
                'type': 'ORGANIZATION',
                'start': match.start(),
                'end': match.end(),
                'method': 'regex'
            }
            entities.append(entity)

        # Pattern for people (Mr./Ms./Dr. followed by capitalized words)
        person_pattern = r'\b((?:Mr\.|Ms\.|Mrs\.|Dr\.|Prof\.) [A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)\b'
        for match in re.finditer(person_pattern, text):
            entity_text = match.group(0)

            # Skip if entity text is too long
            if len(entity_text.split()) > 5:
                continue

            entity = {
                'text': entity_text,
                'type': 'PERSON',
                'start': match.start(),
                'end': match.end(),
                'method': 'regex'
            }
            entities.append(entity)

        # Pattern for locations (capitalized words followed by common location words)
        loc_pattern = r'\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)* (?:City|State|County|Province|Region|Island|Mountain|River|Lake|Ocean|Sea))\b'
        for match in re.finditer(loc_pattern, text):
            entity_text = match.group(0)

            # Skip if entity text is too long
            if len(entity_text.split()) > 5:
                continue

            entity = {
                'text': entity_text,
                'type': 'LOCATION',
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
