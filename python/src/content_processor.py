"""
Content processor for Hydra News system.

This module handles the processing of news content, including:
- Content extraction and normalization
- Entity recognition and fact extraction
- Cross-reference verification
- Content entanglement preparation
"""

import hashlib
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any, Union
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
import requests
from bs4 import BeautifulSoup

# Initialize NLTK (in production, this would be done during setup)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('maxent_ne_chunker')
    nltk.download('words')

class ContentEntity:
    """Class representing an entity extracted from content"""
    
    def __init__(
        self, 
        name: str, 
        entity_type: str, 
        context: str, 
        confidence: float,
        start_pos: int,
        end_pos: int
    ):
        self.name = name
        self.entity_type = entity_type
        self.context = context
        self.confidence = confidence
        self.start_pos = start_pos
        self.end_pos = end_pos
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert the entity to a dictionary"""
        return {
            'name': self.name,
            'type': self.entity_type,
            'context': self.context,
            'confidence': self.confidence,
            'position': {
                'start': self.start_pos,
                'end': self.end_pos
            }
        }


class ContentClaim:
    """Class representing a factual claim extracted from content"""
    
    def __init__(
        self,
        claim_text: str,
        entities: List[ContentEntity],
        source_text: str,
        confidence: float,
        claim_type: str,
        start_pos: int,
        end_pos: int
    ):
        self.claim_text = claim_text
        self.entities = entities
        self.source_text = source_text
        self.confidence = confidence
        self.claim_type = claim_type
        self.start_pos = start_pos
        self.end_pos = end_pos
        # Generate unique identifier for the claim
        self.id = self._generate_id()
        
    def _generate_id(self) -> str:
        """Generate a unique identifier for the claim"""
        # Combine claim text and entities for a unique hash
        claim_data = self.claim_text + ''.join([e.name for e in self.entities])
        return hashlib.sha256(claim_data.encode('utf-8')).hexdigest()[:16]
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert the claim to a dictionary"""
        return {
            'id': self.id,
            'text': self.claim_text,
            'entities': [e.to_dict() for e in self.entities],
            'source_text': self.source_text,
            'confidence': self.confidence,
            'type': self.claim_type,
            'position': {
                'start': self.start_pos,
                'end': self.end_pos
            }
        }


class NewsContent:
    """Class representing a news article or content item"""
    
    def __init__(
        self,
        title: str,
        content: str,
        source: str,
        url: Optional[str] = None,
        author: Optional[str] = None,
        publish_date: Optional[datetime] = None,
        html_content: Optional[str] = None
    ):
        self.title = title
        self.content = content
        self.source = source
        self.url = url
        self.author = author
        self.publish_date = publish_date
        self.html_content = html_content
        self.entities: List[ContentEntity] = []
        self.claims: List[ContentClaim] = []
        self.content_hash: Optional[str] = None
        self.entanglement_hash: Optional[str] = None
        self.processed: bool = False
        # Generate content hash
        self._generate_content_hash()
        
    def _generate_content_hash(self) -> None:
        """Generate a hash of the content"""
        # Combine title, content, source for the hash
        content_data = f"{self.title}|{self.content}|{self.source}"
        if self.author:
            content_data += f"|{self.author}"
        if self.publish_date:
            content_data += f"|{self.publish_date.isoformat()}"
            
        self.content_hash = hashlib.sha256(content_data.encode('utf-8')).hexdigest()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert the news content to a dictionary"""
        result = {
            'title': self.title,
            'content': self.content,
            'source': self.source,
            'url': self.url,
            'author': self.author,
            'content_hash': self.content_hash,
            'processed': self.processed
        }
        
        if self.publish_date:
            result['publish_date'] = self.publish_date.isoformat()
            
        if self.entities:
            result['entities'] = [e.to_dict() for e in self.entities]
            
        if self.claims:
            result['claims'] = [c.to_dict() for c in self.claims]
            
        if self.entanglement_hash:
            result['entanglement_hash'] = self.entanglement_hash
            
        return result


class ContentProcessor:
    """Processes news content for verification and entanglement"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        # Initialize NLP components
        self._initialize_nlp()
        
    def _initialize_nlp(self) -> None:
        """Initialize NLP components for content processing"""
        # In a production version, this might initialize more complex NLP models
        # For now, we just make sure NLTK is ready
        nltk.data.find('tokenizers/punkt')
        
    def process_url(self, url: str) -> Optional[NewsContent]:
        """Fetch and process content from a URL"""
        try:
            # Fetch the URL content
            response = requests.get(url, headers={'User-Agent': 'HydraNews/1.0'})
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract basic metadata
            title = soup.title.string if soup.title else ""
            
            # Simple extraction of main content (this would be more sophisticated in production)
            article_content = ""
            main_content_tags = soup.find_all(['article', 'main', 'div'])
            for tag in main_content_tags:
                if tag.get_text().strip():
                    article_content = tag.get_text().strip()
                    if len(article_content.split()) > 100:  # Assume we found the main content
                        break
            
            # Extract source from domain
            source = url.split('/')[2]
            
            # Create a NewsContent object
            news_content = NewsContent(
                title=title,
                content=article_content,
                source=source,
                url=url,
                html_content=response.text
            )
            
            # Process the content
            self.process_content(news_content)
            
            return news_content
            
        except Exception as e:
            print(f"Error processing URL {url}: {e}")
            return None
        
    def process_content(self, news_content: NewsContent) -> NewsContent:
        """Process a news content object"""
        if news_content.processed:
            return news_content
        
        # Extract entities
        self._extract_entities(news_content)
        
        # Extract claims
        self._extract_claims(news_content)
        
        # Generate entanglement hash
        self._generate_entanglement_hash(news_content)
        
        news_content.processed = True
        return news_content
    
    def _extract_entities(self, news_content: NewsContent) -> None:
        """Extract named entities from the content"""
        entities = []
        
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
                            confidence=0.85,  # Simplified confidence score
                            start_pos=start_pos,
                            end_pos=end_pos
                        )
                        entities.append(entity)
            
            current_pos += len(sentence)
        
        news_content.entities = entities
    
    def _extract_claims(self, news_content: NewsContent) -> None:
        """Extract factual claims from the content"""
        claims = []
        
        # In a real implementation, this would use more sophisticated NLP
        # For now, we'll use a simple heuristic approach
        
        # Tokenize content into sentences
        sentences = sent_tokenize(news_content.content)
        
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
                            confidence=0.75,  # Simplified confidence score
                            claim_type=claim_type,
                            start_pos=start_pos,
                            end_pos=end_pos
                        )
                        claims.append(claim)
            
            current_pos += len(sentence)
        
        news_content.claims = claims
    
    def _generate_entanglement_hash(self, news_content: NewsContent) -> None:
        """Generate a logical entanglement hash for the content"""
        # Combine content hash with entity and claim hashes
        # This creates interdependencies that make tampering detectable
        
        entanglement_data = news_content.content_hash
        
        # Add entity data
        for entity in news_content.entities:
            entity_data = f"{entity.name}|{entity.entity_type}|{entity.start_pos}|{entity.end_pos}"
            entanglement_data += "|" + hashlib.sha256(entity_data.encode('utf-8')).hexdigest()
        
        # Add claim data
        for claim in news_content.claims:
            claim_data = f"{claim.id}|{claim.claim_text}|{claim.start_pos}|{claim.end_pos}"
            entanglement_data += "|" + hashlib.sha256(claim_data.encode('utf-8')).hexdigest()
        
        # Generate final entanglement hash
        news_content.entanglement_hash = hashlib.sha256(entanglement_data.encode('utf-8')).hexdigest()


class CrossReferenceVerifier:
    """Verifies content by cross-referencing with other sources"""
    
    def __init__(self, content_processor: ContentProcessor):
        self.content_processor = content_processor
        self.verification_cache: Dict[str, Dict[str, Any]] = {}
    
    def verify_content(self, content: NewsContent, reference_urls: List[str]) -> Dict[str, Any]:
        """Verify content by cross-referencing with other sources"""
        # Check cache first
        if content.content_hash in self.verification_cache:
            return self.verification_cache[content.content_hash]
        
        verification_result = {
            'content_hash': content.content_hash,
            'verification_score': 0.0,
            'verified_claims': [],
            'disputed_claims': [],
            'references': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Process reference URLs
        reference_contents = []
        for url in reference_urls:
            ref_content = self.content_processor.process_url(url)
            if ref_content:
                reference_contents.append(ref_content)
                verification_result['references'].append({
                    'url': url,
                    'title': ref_content.title,
                    'source': ref_content.source,
                    'content_hash': ref_content.content_hash
                })
        
        # Verify each claim
        for claim in content.claims:
            claim_verification = self._verify_claim(claim, reference_contents)
            
            if claim_verification['verification_score'] >= 0.7:
                verification_result['verified_claims'].append({
                    'claim_id': claim.id,
                    'text': claim.claim_text,
                    'score': claim_verification['verification_score'],
                    'supporting_references': claim_verification['supporting_references']
                })
            elif claim_verification['verification_score'] <= 0.3:
                verification_result['disputed_claims'].append({
                    'claim_id': claim.id,
                    'text': claim.claim_text,
                    'score': claim_verification['verification_score'],
                    'disputed_by': claim_verification['disputed_by']
                })
        
        # Calculate overall verification score
        if content.claims:
            verified_count = len(verification_result['verified_claims'])
            disputed_count = len(verification_result['disputed_claims'])
            total_claims = len(content.claims)
            
            # Score formula: (verified - disputed) / total, bounded to [0, 1]
            verification_score = (verified_count - disputed_count) / total_claims
            verification_result['verification_score'] = max(0.0, min(1.0, verification_score))
        
        # Cache result
        self.verification_cache[content.content_hash] = verification_result
        
        return verification_result
    
    def _verify_claim(self, claim: ContentClaim, reference_contents: List[NewsContent]) -> Dict[str, Any]:
        """Verify a single claim against reference contents"""
        verification_result = {
            'verification_score': 0.0,
            'supporting_references': [],
            'disputed_by': []
        }
        
        if not reference_contents:
            return verification_result
        
        # For each reference, check if it supports or disputes the claim
        supporting_count = 0
        disputing_count = 0
        
        for ref_content in reference_contents:
            # Simple text matching for now - in production would use semantic matching
            claim_support_score = self._calculate_claim_support(claim, ref_content)
            
            if claim_support_score >= 0.7:
                supporting_count += 1
                verification_result['supporting_references'].append({
                    'title': ref_content.title,
                    'source': ref_content.source,
                    'url': ref_content.url,
                    'content_hash': ref_content.content_hash,
                    'support_score': claim_support_score
                })
            elif claim_support_score <= 0.3:
                disputing_count += 1
                verification_result['disputed_by'].append({
                    'title': ref_content.title,
                    'source': ref_content.source,
                    'url': ref_content.url,
                    'content_hash': ref_content.content_hash,
                    'dispute_score': 1.0 - claim_support_score
                })
        
        # Calculate verification score
        total_refs = len(reference_contents)
        verification_result['verification_score'] = (supporting_count - disputing_count) / total_refs
        verification_result['verification_score'] = max(0.0, min(1.0, verification_result['verification_score']))
        
        return verification_result
    
    def _calculate_claim_support(self, claim: ContentClaim, reference: NewsContent) -> float:
        """Calculate how strongly a reference supports a claim"""
        # In production, this would use sophisticated NLP and fact checking
        # For now, use simple text matching
        
        claim_text_normalized = claim.claim_text.lower()
        
        # Check if claim text appears in reference
        if claim_text_normalized in reference.content.lower():
            return 0.9  # Strong support
        
        # Check for entity matches
        entity_match_count = 0
        for claim_entity in claim.entities:
            for ref_entity in reference.entities:
                if claim_entity.name.lower() == ref_entity.name.lower() and claim_entity.entity_type == ref_entity.entity_type:
                    entity_match_count += 1
        
        if entity_match_count > 0:
            entity_match_score = min(1.0, entity_match_count / len(claim.entities))
            return 0.5 + (entity_match_score * 0.4)  # Moderate to strong support
        
        # Check for partial text match using sentence tokenization
        sentences = sent_tokenize(reference.content.lower())
        best_match_score = 0.0
        
        for sentence in sentences:
            # Calculate Jaccard similarity between claim and sentence
            claim_words = set(word_tokenize(claim_text_normalized))
            sentence_words = set(word_tokenize(sentence))
            
            if not claim_words or not sentence_words:
                continue
                
            intersection = claim_words.intersection(sentence_words)
            union = claim_words.union(sentence_words)
            
            jaccard_score = len(intersection) / len(union)
            best_match_score = max(best_match_score, jaccard_score)
        
        return best_match_score
