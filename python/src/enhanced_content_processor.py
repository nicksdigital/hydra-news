"""
Enhanced content processor for Hydra News system.

This module extends the basic content processor with:
- Advanced entity extraction using transformers
- Improved claim detection with fine-tuned models
- Cross-reference validation with trusted sources
- Multimedia content support
"""

import hashlib
import json
import os
import tempfile
import time
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional, Set, Tuple, Any, Union
import numpy as np

# Import base content processor classes
from content_processor import (
    ContentEntity, ContentClaim, NewsContent, 
    ContentProcessor, CrossReferenceVerifier
)

# Import necessary libraries
import nltk
import requests
from bs4 import BeautifulSoup
import torch
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity

# Conditional imports (try/except) for non-essential libraries
try:
    from transformers import (
        AutoTokenizer, AutoModel, AutoModelForTokenClassification,
        AutoModelForSequenceClassification, pipeline
    )
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

# Constants
ENTITY_TYPES = [
    "PERSON", "ORGANIZATION", "LOCATION", "DATE", "TIME", 
    "MONEY", "PERCENT", "FACILITY", "GPE", "NORP", "PRODUCT", "EVENT", 
    "WORK_OF_ART", "LAW", "LANGUAGE", "FAC", "QUANTITY"
]

CLAIM_TYPES = [
    "FACTUAL", "OPINION", "PREDICTION", "QUOTE", "STATISTIC", 
    "COMPARATIVE", "NORMATIVE", "CAUSAL", "POLICY"
]


class MultimediaContent:
    """Class representing multimedia content (images, videos) in news articles"""
    
    def __init__(
        self,
        content_type: str,  # "image" or "video"
        url: str,
        content_hash: str,
        caption: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        local_path: Optional[str] = None,
        embedding: Optional[np.ndarray] = None
    ):
        self.content_type = content_type
        self.url = url
        self.content_hash = content_hash
        self.caption = caption
        self.metadata = metadata or {}
        self.local_path = local_path
        self.embedding = embedding
        self.entities: List[ContentEntity] = []
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        result = {
            'content_type': self.content_type,
            'url': self.url,
            'content_hash': self.content_hash,
            'caption': self.caption,
            'metadata': self.metadata
        }
        
        if self.entities:
            result['entities'] = [e.to_dict() for e in self.entities]
            
        return result


class EnhancedNewsContent(NewsContent):
    """Enhanced news content with multimedia support"""
    
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
        super().__init__(title, content, source, url, author, publish_date, html_content)
        self.multimedia: List[MultimediaContent] = []
        self.embedding: Optional[np.ndarray] = None
        self.keywords: List[str] = []
        self.summary: Optional[str] = None
        self.topic_classification: Optional[Dict[str, float]] = None
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        result = super().to_dict()
        
        if self.multimedia:
            result['multimedia'] = [m.to_dict() for m in self.multimedia]
            
        if self.keywords:
            result['keywords'] = self.keywords
            
        if self.summary:
            result['summary'] = self.summary
            
        if self.topic_classification:
            result['topic_classification'] = self.topic_classification
            
        return result


class EnhancedContentProcessor(ContentProcessor):
    """Enhanced content processor with advanced NLP and multimedia support"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.config = config or {}
        
        # Initialize enhanced NLP components
        self._initialize_enhanced_nlp()
        
        # Set up multimedia processing
        self._initialize_multimedia_processing()
        
    def _initialize_enhanced_nlp(self) -> None:
        """Initialize enhanced NLP components"""
        self.models = {}
        
        # Only initialize if transformers is available
        if not TRANSFORMERS_AVAILABLE:
            print("Warning: transformers library not available. Using basic NLP instead.")
            return
            
        # Initialize spaCy if available (for enhanced NER)
        self.nlp = None
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_trf")
                print("Loaded spaCy transformer model for enhanced NER")
            except:
                try:
                    self.nlp = spacy.load("en_core_web_lg")
                    print("Loaded spaCy large model for enhanced NER")
                except:
                    print("Warning: spaCy models not available")
        
        # Initialize models based on configuration
        model_config = self.config.get('models', {})
        
        # Entity recognition model (default: NER transformer)
        ner_model_name = model_config.get('ner', 'dbmdz/bert-large-cased-finetuned-conll03-english')
        try:
            self.models['ner'] = pipeline('ner', model=ner_model_name, aggregation_strategy="simple")
            print(f"Loaded NER model: {ner_model_name}")
        except Exception as e:
            print(f"Error loading NER model: {e}")
            
        # Claim detection model (text classification)
        claim_model_name = model_config.get('claim_detection', 'roberta-base')
        try:
            self.models['claim'] = pipeline('text-classification', model=claim_model_name)
            print(f"Loaded claim detection model: {claim_model_name}")
        except Exception as e:
            print(f"Error loading claim detection model: {e}")
            
        # Text embedding model for semantic search
        embedding_model_name = model_config.get('embedding', 'sentence-transformers/all-MiniLM-L6-v2')
        try:
            self.models['embedding'] = pipeline('feature-extraction', model=embedding_model_name)
            print(f"Loaded embedding model: {embedding_model_name}")
        except Exception as e:
            print(f"Error loading embedding model: {e}")
            
        # Summarization model
        summary_model_name = model_config.get('summarization', 'facebook/bart-large-cnn')
        try:
            self.models['summarization'] = pipeline('summarization', model=summary_model_name)
            print(f"Loaded summarization model: {summary_model_name}")
        except Exception as e:
            print(f"Error loading summarization model: {e}")
            
        # Topic classification model
        topic_model_name = model_config.get('topic', 'facebook/bart-large-mnli')
        try:
            self.models['topic'] = pipeline('zero-shot-classification', model=topic_model_name)
            print(f"Loaded topic classification model: {topic_model_name}")
        except Exception as e:
            print(f"Error loading topic classification model: {e}")
    
    def _initialize_multimedia_processing(self) -> None:
        """Initialize multimedia processing components"""
        # Set up image processing if available
        try:
            from transformers import ViTFeatureExtractor, ViTForImageClassification
            from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer
            
            # Image classification
            self.models['image_classifier'] = pipeline('image-classification')
            
            # Image captioning
            self.models['image_captioning'] = VisionEncoderDecoderModel.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
            self.models['image_processor'] = ViTImageProcessor.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
            self.models['caption_tokenizer'] = AutoTokenizer.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
            
            print("Initialized multimedia processing components")
        except Exception as e:
            print(f"Warning: multimedia processing not fully available: {e}")
    
    def process_url(self, url: str) -> Optional[EnhancedNewsContent]:
        """Enhanced process_url that extracts multimedia content"""
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
            
            # Create an EnhancedNewsContent object
            news_content = EnhancedNewsContent(
                title=title,
                content=article_content,
                source=source,
                url=url,
                html_content=response.text
            )
            
            # Extract multimedia content
            self._extract_multimedia(news_content, soup)
            
            # Process the content
            self.process_content(news_content)
            
            return news_content
            
        except Exception as e:
            print(f"Error processing URL {url}: {e}")
            return None
    
    def process_content(self, news_content: Union[NewsContent, EnhancedNewsContent]) -> Union[NewsContent, EnhancedNewsContent]:
        """Process content with enhanced NLP capabilities"""
        if news_content.processed:
            return news_content
        
        # Convert to EnhancedNewsContent if needed
        if not isinstance(news_content, EnhancedNewsContent):
            enhanced_content = EnhancedNewsContent(
                title=news_content.title,
                content=news_content.content,
                source=news_content.source,
                url=news_content.url,
                author=news_content.author,
                publish_date=news_content.publish_date,
                html_content=news_content.html_content
            )
            news_content = enhanced_content
        
        # Extract entities using enhanced methods
        self._extract_entities_enhanced(news_content)
        
        # Extract claims using enhanced methods
        self._extract_claims_enhanced(news_content)
        
        # Generate text embedding
        self._generate_embedding(news_content)
        
        # Extract keywords
        self._extract_keywords(news_content)
        
        # Generate summary
        self._generate_summary(news_content)
        
        # Classify content by topic
        self._classify_topic(news_content)
        
        # Process multimedia content
        for multimedia in getattr(news_content, 'multimedia', []):
            self._process_multimedia(multimedia)
        
        # Generate entanglement hash
        self._generate_entanglement_hash_enhanced(news_content)
        
        news_content.processed = True
        return news_content
    
    def _extract_entities_enhanced(self, news_content: EnhancedNewsContent) -> None:
        """Extract entities using advanced NLP models"""
        entities = []
        
        # Use spaCy if available
        if self.nlp is not None:
            doc = self.nlp(news_content.content)
            for ent in doc.ents:
                # Map spaCy entity types to our types
                entity_type = ent.label_
                if entity_type not in ENTITY_TYPES:
                    entity_type = "MISC"
                
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
                
        # Use transformers NER model if available
        elif 'ner' in self.models:
            # Process in chunks to handle long texts
            max_length = 512
            chunks = self._split_text_into_chunks(news_content.content, max_length)
            
            offset = 0
            for chunk in chunks:
                ner_results = self.models['ner'](chunk)
                
                for result in ner_results:
                    entity_name = result['word']
                    entity_type = result['entity_group']
                    if entity_type not in ENTITY_TYPES:
                        entity_type = "MISC"
                    
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
        
        # Fall back to basic NER if no advanced models are available
        else:
            super()._extract_entities(news_content)
            return
        
        # Merge duplicate entities and keep the one with highest confidence
        merged_entities = {}
        for entity in entities:
            key = f"{entity.name.lower()}|{entity.entity_type}"
            if key not in merged_entities or entity.confidence > merged_entities[key].confidence:
                merged_entities[key] = entity
        
        news_content.entities = list(merged_entities.values())
    
    def _extract_claims_enhanced(self, news_content: EnhancedNewsContent) -> None:
        """Extract claims using advanced models"""
        claims = []
        
        # Tokenize content into sentences
        sentences = nltk.sent_tokenize(news_content.content)
        
        # Use transformers for claim detection if available
        if 'claim' in self.models:
            current_pos = 0
            for sentence in sentences:
                # Skip very short sentences
                if len(sentence.split()) < 5:
                    current_pos += len(sentence)
                    continue
                
                # Classify the sentence
                classification = self.models['claim'](sentence)
                
                # Extract the prediction
                prediction = classification[0]
                label = prediction['label']
                score = prediction['score']
                
                # Determine if this is a claim (depends on the model used)
                is_claim = (
                    'claim' in label.lower() or 
                    'fact' in label.lower() or 
                    score > 0.7  # High confidence threshold
                )
                
                if is_claim:
                    # Find position in original text
                    start_pos = news_content.content.find(sentence, current_pos)
                    if start_pos == -1:
                        current_pos += len(sentence)
                        continue
                    
                    end_pos = start_pos + len(sentence)
                    
                    # Find entities in this claim
                    claim_entities = []
                    for entity in news_content.entities:
                        if start_pos <= entity.start_pos < end_pos:
                            claim_entities.append(entity)
                    
                    # Only consider it a claim if it has at least one entity
                    if claim_entities:
                        # Determine claim type (simplified)
                        claim_type = "FACTUAL"
                        if "opinion" in label.lower():
                            claim_type = "OPINION"
                        elif "prediction" in label.lower():
                            claim_type = "PREDICTION"
                        elif "quote" in label.lower() or any(q in sentence for q in ['"', "'"]):
                            claim_type = "QUOTE"
                        
                        # Create claim
                        claim = ContentClaim(
                            claim_text=sentence,
                            entities=claim_entities,
                            source_text=news_content.title,
                            confidence=score,
                            claim_type=claim_type,
                            start_pos=start_pos,
                            end_pos=end_pos
                        )
                        claims.append(claim)
                
                current_pos += len(sentence)
        
        # Fall back to basic claim extraction if no advanced model is available
        else:
            super()._extract_claims(news_content)
            return
        
        news_content.claims = claims
    
    def _generate_embedding(self, news_content: EnhancedNewsContent) -> None:
        """Generate a text embedding for the content"""
        if 'embedding' not in self.models:
            return
        
        # Generate embedding for title and content
        text = news_content.title + ". " + news_content.content
        
        # Truncate if too long (depends on model's max length)
        max_length = 512
        if len(text.split()) > max_length:
            words = text.split()
            text = " ".join(words[:max_length])
        
        # Generate embedding
        embedding = self.models['embedding'](text)
        
        # Average all token embeddings to get a single vector
        if isinstance(embedding, list) and len(embedding) > 0:
            # Get first item if it's a batch
            if isinstance(embedding[0], list):
                embedding = embedding[0]
            
            # Convert to numpy array
            embedding_array = np.array(embedding)
            
            # Average across tokens (dimension 0)
            news_content.embedding = np.mean(embedding_array, axis=0)
    
    def _extract_keywords(self, news_content: EnhancedNewsContent) -> None:
        """Extract keywords from the content"""
        # Simple keyword extraction using TF-IDF principles
        # In production, would use more sophisticated methods
        
        # Tokenize and lowercase
        tokens = nltk.word_tokenize(news_content.content.lower())
        
        # Remove stopwords and punctuation
        try:
            from nltk.corpus import stopwords
            stop_words = set(stopwords.words('english'))
        except:
            # Basic stopwords if NLTK data is not available
            stop_words = {
                'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what',
                'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your',
                'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
                'he', 'she', 'it', 'they', 'them', 'their', 'this', 'that', 'these', 'those'
            }
        
        punctuation = set('.,;:!?"\'()[]{}')
        
        filtered_tokens = [
            token for token in tokens 
            if token not in stop_words and token not in punctuation and len(token) > 2
        ]
        
        # Count frequency
        from collections import Counter
        token_counts = Counter(filtered_tokens)
        
        # Get top keywords
        keywords = [word for word, count in token_counts.most_common(10)]
        news_content.keywords = keywords
    
    def _generate_summary(self, news_content: EnhancedNewsContent) -> None:
        """Generate a summary of the content"""
        if 'summarization' not in self.models:
            return
        
        # Skip if content is too short
        if len(news_content.content.split()) < 50:
            news_content.summary = news_content.content
            return
        
        # Truncate if too long (model-specific)
        max_length = 1024
        if len(news_content.content.split()) > max_length:
            words = news_content.content.split()
            content = " ".join(words[:max_length])
        else:
            content = news_content.content
        
        # Generate summary
        summary = self.models['summarization'](
            content, 
            max_length=150,
            min_length=30,
            do_sample=False
        )
        
        if summary and len(summary) > 0:
            news_content.summary = summary[0]['summary_text']
    
    def _classify_topic(self, news_content: EnhancedNewsContent) -> None:
        """Classify the content by topic"""
        if 'topic' not in self.models:
            return
        
        # Define potential topics
        topics = [
            "Politics", "Business", "Technology", "Science", "Health", 
            "Entertainment", "Sports", "Environment", "Education", "World"
        ]
        
        # Get the title and start of content
        text = news_content.title
        if len(news_content.content) > 0:
            # Add first few sentences of content
            sentences = nltk.sent_tokenize(news_content.content)
            text += " " + " ".join(sentences[:3])
        
        # Classify
        topic_result = self.models['topic'](text, topics)
        
        # Convert to dictionary of topic -> score
        scores = {
            label: score 
            for label, score in zip(topic_result['labels'], topic_result['scores'])
        }
        
        news_content.topic_classification = scores
    
    def _extract_multimedia(self, news_content: EnhancedNewsContent, soup: BeautifulSoup) -> None:
        """Extract multimedia content from HTML"""
        # Extract images
        images = soup.find_all('img')
        for img in images:
            # Skip tiny or icon images
            if img.get('width') and int(img.get('width')) < 100:
                continue
            if img.get('height') and int(img.get('height')) < 100:
                continue
            
            # Get image URL
            img_url = img.get('src', '')
            if not img_url:
                continue
                
            # Make absolute URL if needed
            if img_url.startswith('/'):
                base_url = '/'.join(news_content.url.split('/')[:3])
                img_url = base_url + img_url
            elif not img_url.startswith(('http://', 'https://')):
                base_url = '/'.join(news_content.url.split('/')[:-1])
                img_url = base_url + '/' + img_url
            
            # Get caption if available
            caption = None
            caption_element = img.get('alt') or img.get('title')
            if caption_element:
                caption = caption_element
            else:
                # Look for figcaption near the image
                parent = img.parent
                if parent and parent.name == 'figure':
                    caption_element = parent.find('figcaption')
                    if caption_element:
                        caption = caption_element.get_text().strip()
            
            # Create a placeholder hash (would download and hash the image in production)
            content_hash = hashlib.sha256(img_url.encode('utf-8')).hexdigest()
            
            # Create multimedia object
            multimedia = MultimediaContent(
                content_type="image",
                url=img_url,
                content_hash=content_hash,
                caption=caption,
                metadata={
                    'width': img.get('width'),
                    'height': img.get('height'),
                }
            )
            
            news_content.multimedia.append(multimedia)
        
        # Extract videos (simplistic approach)
        videos = soup.find_all(['video', 'iframe'])
        for video in videos:
            # Get video URL
            video_url = None
            if video.name == 'video':
                video_url = video.get('src')
                if not video_url:
                    source = video.find('source')
                    if source:
                        video_url = source.get('src')
            else:  # iframe
                video_url = video.get('src')
            
            if not video_url:
                continue
                
            # Make absolute URL if needed
            if video_url.startswith('/'):
                base_url = '/'.join(news_content.url.split('/')[:3])
                video_url = base_url + video_url
            elif not video_url.startswith(('http://', 'https://')):
                base_url = '/'.join(news_content.url.split('/')[:-1])
                video_url = base_url + '/' + video_url
            
            # Create a placeholder hash
            content_hash = hashlib.sha256(video_url.encode('utf-8')).hexdigest()
            
            # Create multimedia object
            multimedia = MultimediaContent(
                content_type="video",
                url=video_url,
                content_hash=content_hash,
                metadata={
                    'width': video.get('width'),
                    'height': video.get('height'),
                }
            )
            
            news_content.multimedia.append(multimedia)
    
    def _process_multimedia(self, multimedia: MultimediaContent) -> None:
        """Process a multimedia object (extract features, captions, etc.)"""
        # Skip if we don't have the necessary models
        if 'image_classifier' not in self.models and multimedia.content_type == "image":
            return
        
        # For now, only process images
        if multimedia.content_type != "image":
            return
            
        try:
            # Download the image
            response = requests.get(multimedia.url, stream=True)
            if response.status_code != 200:
                return
                
            # Process with image classifier
            img = Image.open(BytesIO(response.content))
            
            # Classification
            classification = self.models['image_classifier'](img)
            
            # Add classification to metadata
            multimedia.metadata['classification'] = [
                {'label': result['label'], 'score': result['score']}
                for result in classification
            ]
            
            # Generate caption if not already present
            if not multimedia.caption and 'image_captioning' in self.models:
                # Preprocess image
                pixel_values = self.models['image_processor'](img, return_tensors="pt").pixel_values
                
                # Generate caption
                with torch.no_grad():
                    output_ids = self.models['image_captioning'].generate(
                        pixel_values,
                        max_length=16,
                        num_beams=4,
                        return_dict_in_generate=True
                    ).sequences
                
                # Decode caption
                caption = self.models['caption_tokenizer'].batch_decode(
                    output_ids, skip_special_tokens=True
                )[0]
                
                multimedia.caption = caption
                
            # Extract entities from caption if available
            if multimedia.caption and self.nlp:
                doc = self.nlp(multimedia.caption)
                
                for ent in doc.ents:
                    entity_type = ent.label_
                    if entity_type not in ENTITY_TYPES:
                        entity_type = "MISC"
                    
                    entity = ContentEntity(
                        name=ent.text,
                        entity_type=entity_type,
                        context=multimedia.caption,
                        confidence=0.85,
                        start_pos=ent.start_char,
                        end_pos=ent.end_char
                    )
                    
                    multimedia.entities.append(entity)
                    
        except Exception as e:
            print(f"Error processing multimedia: {e}")
    
    def _generate_entanglement_hash_enhanced(self, news_content: EnhancedNewsContent) -> None:
        """Generate enhanced entanglement hash including multimedia"""
        # Start with basic entanglement hash
        super()._generate_entanglement_hash(news_content)
        
        # If no additional data, we're done
        if not hasattr(news_content, 'multimedia') or not news_content.multimedia:
            return
            
        # Add multimedia data to the entanglement
        entanglement_data = news_content.entanglement_hash
        
        for multimedia in news_content.multimedia:
            media_data = f"{multimedia.content_type}|{multimedia.url}|{multimedia.content_hash}"
            if multimedia.caption:
                media_data += f"|{multimedia.caption}"
            
            entanglement_data += "|" + hashlib.sha256(media_data.encode('utf-8')).hexdigest()
            
            # Add entity data for multimedia
            for entity in multimedia.entities:
                entity_data = f"{entity.name}|{entity.entity_type}"
                entanglement_data += "|" + hashlib.sha256(entity_data.encode('utf-8')).hexdigest()
        
        # Generate final entanglement hash
        news_content.entanglement_hash = hashlib.sha256(entanglement_data.encode('utf-8')).hexdigest()
    
    def _split_text_into_chunks(self, text: str, max_length: int) -> List[str]:
        """Split text into chunks of maximum length while respecting sentence boundaries"""
        sentences = nltk.sent_tokenize(text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If adding this sentence would exceed max_length, start a new chunk
            if len(current_chunk) + len(sentence) > max_length and current_chunk:
                chunks.append(current_chunk)
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        # Add the last chunk if not empty
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks


class EnhancedCrossReferenceVerifier(CrossReferenceVerifier):
    """Enhanced verifier with trusted source support and similarity matching"""
    
    def __init__(self, content_processor: Union[ContentProcessor, EnhancedContentProcessor]):
        super().__init__(content_processor)
        self.trusted_sources = self._load_trusted_sources()
        
    def _load_trusted_sources(self) -> Dict[str, float]:
        """Load trusted sources with trust scores"""
        # In production, this would load from a database or API
        # For now, use a simple hardcoded list
        return {
            "reuters.com": 0.9,
            "apnews.com": 0.9,
            "bbc.com": 0.85,
            "npr.org": 0.85,
            "nytimes.com": 0.8,
            "washingtonpost.com": 0.8,
            "economist.com": 0.8,
            "wsj.com": 0.8,
            "theguardian.com": 0.8,
            "cnn.com": 0.7,
            "nbcnews.com": 0.7,
            "cbsnews.com": 0.7,
            "abcnews.go.com": 0.7,
            "politico.com": 0.7,
            "thehill.com": 0.7
        }
    
    def _get_source_trust_score(self, source: str) -> float:
        """Get trust score for a source"""
        # Check if domain matches any trusted source
        for domain, score in self.trusted_sources.items():
            if domain in source:
                return score
        
        # Default score for unknown sources
        return 0.5
    
    def verify_content(self, content: Union[NewsContent, EnhancedNewsContent], reference_urls: List[str]) -> Dict[str, Any]:
        """Enhanced verification using semantic similarity and trust scores"""
        # Check cache first
        if content.content_hash in self.verification_cache:
            return self.verification_cache[content.content_hash]
        
        verification_result = {
            'content_hash': content.content_hash,
            'verification_score': 0.0,
            'verified_claims': [],
            'disputed_claims': [],
            'references': [],
            'timestamp': datetime.now().isoformat(),
            'trusted_source_boost': 0.0
        }
        
        # Convert to EnhancedNewsContent if needed
        if not isinstance(content, EnhancedNewsContent) and isinstance(self.content_processor, EnhancedContentProcessor):
            content = self.content_processor.process_content(content)
        
        # Apply trust boost for trusted sources
        source_trust = self._get_source_trust_score(content.source)
        verification_result['trusted_source_boost'] = source_trust - 0.5  # Normalize to [-0.5, 0.5]
        
        # Process reference URLs
        reference_contents = []
        for url in reference_urls:
            ref_content = self.content_processor.process_url(url)
            if ref_content:
                reference_contents.append(ref_content)
                
                # Add reference metadata
                ref_trust = self._get_source_trust_score(ref_content.source)
                verification_result['references'].append({
                    'url': url,
                    'title': ref_content.title,
                    'source': ref_content.source,
                    'content_hash': ref_content.content_hash,
                    'trust_score': ref_trust
                })
        
        # Verify each claim
        for claim in content.claims:
            claim_verification = self._verify_claim_enhanced(claim, reference_contents)
            
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
            
            # Apply trusted source boost (limited impact)
            verification_score += verification_result['trusted_source_boost'] * 0.2
            
            verification_result['verification_score'] = max(0.0, min(1.0, verification_score))
        else:
            # If no claims, score based solely on source trust
            verification_result['verification_score'] = source_trust
        
        # Cache result
        self.verification_cache[content.content_hash] = verification_result
        
        return verification_result
    
    def _verify_claim_enhanced(self, claim: ContentClaim, reference_contents: List[Union[NewsContent, EnhancedNewsContent]]) -> Dict[str, Any]:
        """Verify a claim with semantic matching and trust weighting"""
        verification_result = {
            'verification_score': 0.0,
            'supporting_references': [],
            'disputed_by': []
        }
        
        if not reference_contents:
            return verification_result
        
        # Check if content processor has embedding capability
        has_embeddings = (
            hasattr(self.content_processor, 'models') and 
            'embedding' in getattr(self.content_processor, 'models', {})
        )
        
        # For each reference, check if it supports or disputes the claim
        supporting_score_total = 0.0
        disputing_score_total = 0.0
        
        for ref_content in reference_contents:
            # Apply trust weighting
            source_trust = self._get_source_trust_score(ref_content.source)
            
            # Use semantic similarity if available
            if has_embeddings:
                similarity_score = self._calculate_semantic_similarity(claim, ref_content)
                support_score = similarity_score * source_trust
            else:
                # Fall back to text matching
                support_score = self._calculate_claim_support(claim, ref_content) * source_trust
            
            # Determine if supporting or disputing
            if support_score >= 0.6:
                supporting_score_total += support_score
                verification_result['supporting_references'].append({
                    'title': ref_content.title,
                    'source': ref_content.source,
                    'url': ref_content.url,
                    'content_hash': ref_content.content_hash,
                    'support_score': support_score,
                    'trust_score': source_trust
                })
            elif support_score <= 0.3:
                dispute_score = 1.0 - support_score
                disputing_score_total += dispute_score
                verification_result['disputed_by'].append({
                    'title': ref_content.title,
                    'source': ref_content.source,
                    'url': ref_content.url,
                    'content_hash': ref_content.content_hash,
                    'dispute_score': dispute_score,
                    'trust_score': source_trust
                })
        
        # Calculate verification score
        total_score = supporting_score_total - disputing_score_total
        total_refs = len(reference_contents)
        
        if total_refs > 0:
            verification_result['verification_score'] = (total_score / total_refs + 1) / 2  # Normalize to [0,1]
        
        verification_result['verification_score'] = max(0.0, min(1.0, verification_result['verification_score']))
        
        return verification_result
    
    def _calculate_semantic_similarity(self, claim: ContentClaim, reference: Union[NewsContent, EnhancedNewsContent]) -> float:
        """Calculate semantic similarity between claim and reference"""
        # If reference doesn't have embedding, generate it
        if not hasattr(reference, 'embedding') or reference.embedding is None:
            if hasattr(self.content_processor, '_generate_embedding'):
                self.content_processor._generate_embedding(reference)
            else:
                # Fall back to text matching if can't generate embedding
                return self._calculate_claim_support(claim, reference)
        
        # Generate claim embedding
        claim_embedding = None
        if hasattr(self.content_processor, 'models') and 'embedding' in self.content_processor.models:
            embedding_result = self.content_processor.models['embedding'](claim.claim_text)
            if isinstance(embedding_result, list) and len(embedding_result) > 0:
                # Average token embeddings
                embedding_array = np.array(embedding_result[0])
                claim_embedding = np.mean(embedding_array, axis=0)
        
        if claim_embedding is None or reference.embedding is None:
            # Fall back to text matching
            return self._calculate_claim_support(claim, reference)
        
        # Calculate cosine similarity
        similarity = cosine_similarity(
            claim_embedding.reshape(1, -1),
            reference.embedding.reshape(1, -1)
        )[0][0]
        
        # Normalize to [0, 1]
        similarity = (similarity + 1) / 2
        
        return similarity
