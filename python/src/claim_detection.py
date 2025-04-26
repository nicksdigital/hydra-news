"""
Advanced claim detection for Hydra News content processor.

This module provides improved claim detection capabilities using:
1. Fine-tuned language models for claim detection
2. Contextual analysis for claim classification
3. Confidence scoring with multiple models
4. Entity-based claim extraction
"""

import re
import nltk
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from nltk.tokenize import sent_tokenize, word_tokenize

# Import base content processor classes
from content_processor import ContentEntity, ContentClaim, NewsContent

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

# Claim type definitions
CLAIM_TYPES = {
    "FACTUAL": "A statement presented as a fact that can be verified",
    "OPINION": "A subjective statement expressing a viewpoint",
    "PREDICTION": "A statement about future events",
    "QUOTE": "A statement attributed to someone else",
    "STATISTIC": "A numerical fact or figure",
    "COMPARISON": "A statement comparing two or more entities",
    "CAUSAL": "A statement asserting a cause-effect relationship",
    "NORMATIVE": "A statement about what should be done",
}

# Claim indicators (words and phrases that often signal claims)
CLAIM_INDICATORS = {
    "FACTUAL": [
        "is", "are", "was", "were", "will be", "has been", "have been",
        "according to", "research shows", "studies indicate", "evidence suggests",
        "data shows", "experts say", "scientists found", "analysis reveals",
    ],
    "OPINION": [
        "believe", "think", "feel", "suggest", "argue", "claim", "consider",
        "in my opinion", "in my view", "I believe", "I think", "I feel",
        "arguably", "presumably", "seemingly", "apparently", "likely",
    ],
    "PREDICTION": [
        "will", "going to", "expected to", "projected to", "forecast",
        "predict", "anticipate", "foresee", "estimate", "project",
        "in the future", "by next year", "in the coming", "soon",
    ],
    "QUOTE": [
        "said", "stated", "claimed", "reported", "announced", "declared",
        "mentioned", "noted", "added", "commented", "explained", "described",
        "\"", "'", "according to", "in the words of", "as stated by",
    ],
    "STATISTIC": [
        "percent", "%", "increased", "decreased", "reduced", "grew",
        "rose", "fell", "dropped", "number", "amount", "rate", "level",
        "statistics show", "data indicates", "survey found", "poll shows",
    ],
    "COMPARISON": [
        "more than", "less than", "better than", "worse than", "higher than",
        "lower than", "compared to", "in contrast to", "versus", "unlike",
        "similar to", "different from", "as opposed to", "relative to",
    ],
    "CAUSAL": [
        "because", "since", "due to", "as a result of", "consequently",
        "therefore", "thus", "hence", "leads to", "causes", "affects",
        "impacts", "influences", "results in", "contributes to",
    ],
    "NORMATIVE": [
        "should", "must", "need to", "ought to", "have to", "required",
        "necessary", "important", "essential", "critical", "vital",
        "recommended", "advised", "suggested", "proposed",
    ],
}

class ClaimDetector:
    """Advanced claim detection with multiple NLP models"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the claim detector with configuration"""
        self.config = config or {}
        self.models = {}
        
        # Initialize NLP components
        self._initialize_nlp()
        
    def _initialize_nlp(self) -> None:
        """Initialize NLP components for claim detection"""
        # Initialize transformers models if available
        if TRANSFORMERS_AVAILABLE:
            try:
                # Use specified model or default to a good general text classification model
                model_name = self.config.get('claim_model', 'facebook/bart-large-mnli')
                self.models['claim'] = pipeline('zero-shot-classification', model=model_name)
                print(f"Loaded transformer claim detection model: {model_name}")
            except Exception as e:
                print(f"Error loading transformer claim detection model: {e}")
        
        # Initialize spaCy if available
        if SPACY_AVAILABLE and nlp is not None:
            self.models['spacy'] = nlp
            print(f"Loaded spaCy model: {nlp.meta['name']}")
        
        # Always make sure NLTK is available as fallback
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('averaged_perceptron_tagger')
            self.models['nltk'] = True
            print("NLTK models loaded successfully")
        except LookupError:
            try:
                nltk.download('punkt')
                nltk.download('averaged_perceptron_tagger')
                self.models['nltk'] = True
                print("NLTK models downloaded successfully")
            except Exception as e:
                print(f"Error loading NLTK models: {e}")
                self.models['nltk'] = False
    
    def extract_claims(self, news_content: NewsContent) -> List[ContentClaim]:
        """
        Extract claims from news content using the best available models
        
        Args:
            news_content: The news content to extract claims from
            
        Returns:
            A list of extracted claims
        """
        claims = []
        
        # Try using transformers first (if available)
        if TRANSFORMERS_AVAILABLE and 'claim' in self.models:
            claims.extend(self._extract_claims_transformers(news_content))
        
        # Try using spaCy next (if available)
        elif SPACY_AVAILABLE and 'spacy' in self.models:
            claims.extend(self._extract_claims_spacy(news_content))
        
        # Fall back to NLTK if needed
        elif self.models.get('nltk', False):
            claims.extend(self._extract_claims_nltk(news_content))
        
        # Merge duplicate claims and keep the one with highest confidence
        merged_claims = {}
        for claim in claims:
            key = f"{claim.claim_text}"
            if key not in merged_claims or claim.confidence > merged_claims[key].confidence:
                merged_claims[key] = claim
        
        return list(merged_claims.values())
    
    def _extract_claims_transformers(self, news_content: NewsContent) -> List[ContentClaim]:
        """Extract claims using transformers zero-shot classification"""
        claims = []
        
        try:
            # Tokenize content into sentences
            sentences = sent_tokenize(news_content.content)
            
            # Define claim categories for zero-shot classification
            claim_categories = list(CLAIM_TYPES.keys())
            
            current_pos = 0
            for sentence in sentences:
                # Skip very short sentences
                if len(sentence.split()) < 5:
                    current_pos += len(sentence)
                    continue
                
                # Classify the sentence
                classification = self.models['claim'](
                    sentence, 
                    candidate_labels=claim_categories + ["NOT_CLAIM"],
                    multi_label=False
                )
                
                # Extract the prediction
                labels = classification['labels']
                scores = classification['scores']
                
                # Get the top prediction
                top_label = labels[0]
                top_score = scores[0]
                
                # Determine if this is a claim (not the NOT_CLAIM category and score above threshold)
                is_claim = top_label != "NOT_CLAIM" and top_score > 0.7
                
                if is_claim:
                    # Find entities in this claim
                    claim_entities = []
                    for entity in news_content.entities:
                        if current_pos <= entity.start_pos < current_pos + len(sentence):
                            claim_entities.append(entity)
                    
                    # Find position in original text
                    start_pos = news_content.content.find(sentence, current_pos)
                    if start_pos != -1:
                        end_pos = start_pos + len(sentence)
                        
                        # Create claim
                        claim = ContentClaim(
                            claim_text=sentence,
                            entities=claim_entities,
                            source_text=news_content.title,
                            confidence=top_score,
                            claim_type=top_label,
                            start_pos=start_pos,
                            end_pos=end_pos
                        )
                        claims.append(claim)
                
                current_pos += len(sentence)
                
        except Exception as e:
            print(f"Error extracting claims with transformers: {e}")
        
        return claims
    
    def _extract_claims_spacy(self, news_content: NewsContent) -> List[ContentClaim]:
        """Extract claims using spaCy"""
        claims = []
        
        try:
            # Process the content with spaCy
            doc = self.models['spacy'](news_content.content)
            
            # Analyze each sentence
            current_pos = 0
            for sent in doc.sents:
                sentence = sent.text.strip()
                
                # Skip very short sentences
                if len(sentence.split()) < 5:
                    current_pos += len(sentence)
                    continue
                
                # Determine if this is a claim using linguistic features
                is_claim = False
                claim_type = "FACTUAL"  # Default
                confidence = 0.7  # Default confidence
                
                # Check for claim indicators in the sentence
                for ctype, indicators in CLAIM_INDICATORS.items():
                    for indicator in indicators:
                        if f" {indicator.lower()} " in f" {sentence.lower()} ":
                            is_claim = True
                            claim_type = ctype
                            confidence = 0.8  # Higher confidence when indicator is found
                            break
                    if is_claim:
                        break
                
                # Additional linguistic features to detect claims
                if not is_claim:
                    # Check for subject-verb-object structure (common in factual claims)
                    has_subject = False
                    has_verb = False
                    has_object = False
                    
                    for token in sent:
                        if token.dep_ in ("nsubj", "nsubjpass"):
                            has_subject = True
                        elif token.pos_ == "VERB":
                            has_verb = True
                        elif token.dep_ in ("dobj", "pobj"):
                            has_object = True
                    
                    if has_subject and has_verb and has_object:
                        is_claim = True
                        claim_type = "FACTUAL"
                        confidence = 0.75
                
                if is_claim:
                    # Find entities in this claim
                    claim_entities = []
                    for entity in news_content.entities:
                        if current_pos <= entity.start_pos < current_pos + len(sentence):
                            claim_entities.append(entity)
                    
                    # Only consider it a claim if it has at least one entity
                    if claim_entities:
                        # Find position in original text
                        start_pos = news_content.content.find(sentence, current_pos)
                        if start_pos != -1:
                            end_pos = start_pos + len(sentence)
                            
                            # Create claim
                            claim = ContentClaim(
                                claim_text=sentence,
                                entities=claim_entities,
                                source_text=news_content.title,
                                confidence=confidence,
                                claim_type=claim_type,
                                start_pos=start_pos,
                                end_pos=end_pos
                            )
                            claims.append(claim)
                
                current_pos += len(sentence)
                
        except Exception as e:
            print(f"Error extracting claims with spaCy: {e}")
        
        return claims
    
    def _extract_claims_nltk(self, news_content: NewsContent) -> List[ContentClaim]:
        """Extract claims using NLTK"""
        claims = []
        
        try:
            # Tokenize content into sentences
            sentences = sent_tokenize(news_content.content)
            
            current_pos = 0
            for sentence in sentences:
                # Skip very short sentences
                if len(sentence.split()) < 5:
                    current_pos += len(sentence)
                    continue
                
                # Simple claim detection heuristics
                is_claim = False
                claim_type = "FACTUAL"  # Default
                confidence = 0.7  # Default confidence
                
                # Check for claim indicators
                for ctype, indicators in CLAIM_INDICATORS.items():
                    for indicator in indicators:
                        if f" {indicator.lower()} " in f" {sentence.lower()} ":
                            is_claim = True
                            claim_type = ctype
                            confidence = 0.75  # Higher confidence when indicator is found
                            break
                    if is_claim:
                        break
                
                if is_claim:
                    # Find entities in this claim
                    claim_entities = []
                    for entity in news_content.entities:
                        if current_pos <= entity.start_pos < current_pos + len(sentence):
                            claim_entities.append(entity)
                    
                    # Only consider it a claim if it has at least one entity
                    if claim_entities:
                        # Find position in original text
                        start_pos = news_content.content.find(sentence, current_pos)
                        if start_pos != -1:
                            end_pos = start_pos + len(sentence)
                            
                            # Create claim
                            claim = ContentClaim(
                                claim_text=sentence,
                                entities=claim_entities,
                                source_text=news_content.title,
                                confidence=confidence,
                                claim_type=claim_type,
                                start_pos=start_pos,
                                end_pos=end_pos
                            )
                            claims.append(claim)
                
                current_pos += len(sentence)
                
        except Exception as e:
            print(f"Error extracting claims with NLTK: {e}")
        
        return claims
    
    def classify_claim_type(self, claim_text: str) -> Tuple[str, float]:
        """
        Classify the type of claim
        
        Args:
            claim_text: The text of the claim
            
        Returns:
            A tuple of (claim_type, confidence)
        """
        # Default values
        claim_type = "FACTUAL"
        confidence = 0.7
        
        # Try using transformers if available
        if TRANSFORMERS_AVAILABLE and 'claim' in self.models:
            try:
                # Classify the claim
                classification = self.models['claim'](
                    claim_text, 
                    candidate_labels=list(CLAIM_TYPES.keys()),
                    multi_label=False
                )
                
                # Extract the prediction
                claim_type = classification['labels'][0]
                confidence = classification['scores'][0]
                
                return claim_type, confidence
                
            except Exception as e:
                print(f"Error classifying claim with transformers: {e}")
        
        # Fall back to rule-based classification
        for ctype, indicators in CLAIM_INDICATORS.items():
            for indicator in indicators:
                if f" {indicator.lower()} " in f" {claim_text.lower()} ":
                    return ctype, 0.8
        
        return claim_type, confidence
