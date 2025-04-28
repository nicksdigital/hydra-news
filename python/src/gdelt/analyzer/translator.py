#!/usr/bin/env python3
"""
Translator for GDELT News Articles

This module provides functionality for translating non-English articles to English.
"""

import logging
import pandas as pd
import re
import time
import os
import json
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import translation libraries
try:
    from transformers import MarianMTModel, MarianTokenizer
    TRANSFORMERS_AVAILABLE = True
    logger.info("Transformers library is available for translation")
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers library not available. Will use simple translation.")

try:
    import googletrans
    from googletrans import Translator
    GOOGLETRANS_AVAILABLE = True
    logger.info("Googletrans library is available for translation")
except ImportError:
    GOOGLETRANS_AVAILABLE = False
    logger.warning("Googletrans library not available.")

class ArticleTranslator:
    """Class for translating articles from various languages to English"""
    
    def __init__(self, cache_dir='translation_cache', max_workers=2, cpu_limit=50):
        """
        Initialize the translator
        
        Args:
            cache_dir: Directory to cache translations
            max_workers: Maximum number of worker threads for translation
            cpu_limit: CPU usage limit in percentage (0-100)
        """
        self.cache_dir = cache_dir
        self.max_workers = max_workers
        self.cpu_limit = cpu_limit
        self.translation_cache = {}
        self.supported_languages = set()
        self.models = {}
        self.tokenizers = {}
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Load translation cache
        self._load_cache()
        
        # Initialize translation backends
        self._initialize_translation_backends()
    
    def _initialize_translation_backends(self):
        """Initialize translation backends"""
        # Initialize Hugging Face models if available
        if TRANSFORMERS_AVAILABLE:
            try:
                # Define supported language pairs
                self.language_pairs = {
                    'es': 'Helsinki-NLP/opus-mt-es-en',  # Spanish to English
                    'fr': 'Helsinki-NLP/opus-mt-fr-en',  # French to English
                    'de': 'Helsinki-NLP/opus-mt-de-en',  # German to English
                    'it': 'Helsinki-NLP/opus-mt-it-en',  # Italian to English
                    'pt': 'Helsinki-NLP/opus-mt-pt-en',  # Portuguese to English
                    'nl': 'Helsinki-NLP/opus-mt-nl-en',  # Dutch to English
                    'ru': 'Helsinki-NLP/opus-mt-ru-en',  # Russian to English
                    'zh': 'Helsinki-NLP/opus-mt-zh-en',  # Chinese to English
                    'ar': 'Helsinki-NLP/opus-mt-ar-en',  # Arabic to English
                    'ja': 'Helsinki-NLP/opus-mt-ja-en',  # Japanese to English
                }
                
                # Load only the most common models to save memory
                common_languages = ['es', 'fr', 'de']
                for lang in common_languages:
                    if lang in self.language_pairs:
                        model_name = self.language_pairs[lang]
                        logger.info(f"Loading translation model for {lang}: {model_name}")
                        self.tokenizers[lang] = MarianTokenizer.from_pretrained(model_name)
                        self.models[lang] = MarianMTModel.from_pretrained(model_name)
                        self.supported_languages.add(lang)
                
                # Add all supported languages to the set
                for lang in self.language_pairs:
                    self.supported_languages.add(lang)
                
                logger.info(f"Initialized Hugging Face translation models for {len(self.models)} languages")
                logger.info(f"Supported languages: {', '.join(sorted(self.supported_languages))}")
                
            except Exception as e:
                logger.error(f"Error initializing Hugging Face translation models: {e}")
        
        # Initialize Google Translate if available
        if GOOGLETRANS_AVAILABLE:
            try:
                self.google_translator = Translator()
                # Add common languages to supported languages
                common_languages = [
                    'af', 'sq', 'am', 'ar', 'hy', 'az', 'eu', 'be', 'bn', 'bs', 'bg', 'ca', 'ceb', 'zh', 'co',
                    'hr', 'cs', 'da', 'nl', 'en', 'eo', 'et', 'fi', 'fr', 'fy', 'gl', 'ka', 'de', 'el', 'gu',
                    'ht', 'ha', 'haw', 'he', 'hi', 'hmn', 'hu', 'is', 'ig', 'id', 'ga', 'it', 'ja', 'jw', 'kn',
                    'kk', 'km', 'ko', 'ku', 'ky', 'lo', 'la', 'lv', 'lt', 'lb', 'mk', 'mg', 'ms', 'ml', 'mt',
                    'mi', 'mr', 'mn', 'my', 'ne', 'no', 'ny', 'ps', 'fa', 'pl', 'pt', 'pa', 'ro', 'ru', 'sm',
                    'gd', 'sr', 'st', 'sn', 'sd', 'si', 'sk', 'sl', 'so', 'es', 'su', 'sw', 'sv', 'tl', 'tg',
                    'ta', 'te', 'th', 'tr', 'uk', 'ur', 'uz', 'vi', 'cy', 'xh', 'yi', 'yo', 'zu'
                ]
                for lang in common_languages:
                    self.supported_languages.add(lang)
                
                logger.info("Initialized Google Translate backend")
            except Exception as e:
                logger.error(f"Error initializing Google Translate: {e}")
    
    def _load_cache(self):
        """Load translation cache from disk"""
        cache_file = os.path.join(self.cache_dir, 'translation_cache.json')
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.translation_cache = json.load(f)
                logger.info(f"Loaded {len(self.translation_cache)} cached translations")
            except Exception as e:
                logger.error(f"Error loading translation cache: {e}")
                self.translation_cache = {}
    
    def _save_cache(self):
        """Save translation cache to disk"""
        cache_file = os.path.join(self.cache_dir, 'translation_cache.json')
        try:
            # Limit cache size to prevent excessive disk usage
            if len(self.translation_cache) > 10000:
                # Keep only the most recent 5000 translations
                cache_items = list(self.translation_cache.items())
                self.translation_cache = dict(cache_items[-5000:])
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.translation_cache, f, ensure_ascii=False)
            logger.info(f"Saved {len(self.translation_cache)} translations to cache")
        except Exception as e:
            logger.error(f"Error saving translation cache: {e}")
    
    @lru_cache(maxsize=1000)
    def _translate_text_huggingface(self, text, source_lang):
        """
        Translate text using Hugging Face models
        
        Args:
            text: Text to translate
            source_lang: Source language code
            
        Returns:
            Translated text
        """
        if not text or pd.isna(text) or text.strip() == '':
            return text
        
        if source_lang not in self.language_pairs:
            logger.warning(f"Unsupported language for Hugging Face translation: {source_lang}")
            return text
        
        try:
            # Load model and tokenizer if not already loaded
            if source_lang not in self.models:
                model_name = self.language_pairs[source_lang]
                logger.info(f"Loading translation model for {source_lang}: {model_name}")
                self.tokenizers[source_lang] = MarianTokenizer.from_pretrained(model_name)
                self.models[source_lang] = MarianMTModel.from_pretrained(model_name)
            
            # Get model and tokenizer
            tokenizer = self.tokenizers[source_lang]
            model = self.models[source_lang]
            
            # Tokenize and translate
            inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
            outputs = model.generate(**inputs)
            translated_text = tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
            
            return translated_text
        
        except Exception as e:
            logger.error(f"Error translating with Hugging Face: {e}")
            return text
    
    @lru_cache(maxsize=1000)
    def _translate_text_google(self, text, source_lang):
        """
        Translate text using Google Translate
        
        Args:
            text: Text to translate
            source_lang: Source language code
            
        Returns:
            Translated text
        """
        if not text or pd.isna(text) or text.strip() == '':
            return text
        
        if not GOOGLETRANS_AVAILABLE:
            return text
        
        try:
            # Add delay to avoid rate limiting
            time.sleep(0.5)
            
            # Translate text
            result = self.google_translator.translate(text, src=source_lang, dest='en')
            return result.text
        
        except Exception as e:
            logger.error(f"Error translating with Google Translate: {e}")
            return text
    
    def _translate_text_simple(self, text, source_lang):
        """
        Simple translation for when no translation service is available
        
        Args:
            text: Text to translate
            source_lang: Source language code
            
        Returns:
            Original text with [UNTRANSLATED] prefix
        """
        return f"[UNTRANSLATED] {text}"
    
    def translate_text(self, text, source_lang):
        """
        Translate text to English
        
        Args:
            text: Text to translate
            source_lang: Source language code
            
        Returns:
            Translated text
        """
        if not text or pd.isna(text) or text.strip() == '':
            return text
        
        # Skip translation for English text
        if source_lang == 'en' or source_lang == 'eng':
            return text
        
        # Normalize language code
        source_lang = source_lang.lower()[:2]
        
        # Check if translation is in cache
        cache_key = f"{source_lang}:{text}"
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]
        
        # Translate using available backends
        translated_text = text
        
        if source_lang in self.models and TRANSFORMERS_AVAILABLE:
            # Use Hugging Face model
            translated_text = self._translate_text_huggingface(text, source_lang)
        elif GOOGLETRANS_AVAILABLE:
            # Fall back to Google Translate
            translated_text = self._translate_text_google(text, source_lang)
        else:
            # Simple translation
            translated_text = self._translate_text_simple(text, source_lang)
        
        # Cache the translation
        self.translation_cache[cache_key] = translated_text
        
        # Periodically save cache
        if len(self.translation_cache) % 100 == 0:
            self._save_cache()
        
        return translated_text
    
    def translate_dataframe(self, df, language_column='language', text_columns=None):
        """
        Translate text columns in a DataFrame
        
        Args:
            df: DataFrame to translate
            language_column: Column containing language codes
            text_columns: List of columns to translate (if None, will translate 'title' and 'description')
            
        Returns:
            DataFrame with translated columns
        """
        if text_columns is None:
            text_columns = ['title', 'description']
        
        # Make a copy to avoid modifying the original
        result_df = df.copy()
        
        # Add translated columns
        for col in text_columns:
            if col in result_df.columns:
                # Add translated column
                translated_col = f"{col}_translated"
                result_df[translated_col] = None
        
        # Process each row
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Create translation tasks
            translation_tasks = []
            
            for idx, row in result_df.iterrows():
                lang = row.get(language_column, 'en')
                
                # Skip English content
                if lang == 'en' or lang == 'eng':
                    for col in text_columns:
                        if col in result_df.columns:
                            result_df.at[idx, f"{col}_translated"] = row.get(col, '')
                    continue
                
                # Create translation tasks for each text column
                for col in text_columns:
                    if col in result_df.columns:
                        text = row.get(col, '')
                        if text and not pd.isna(text):
                            task = executor.submit(self.translate_text, text, lang)
                            translation_tasks.append((idx, col, task))
            
            # Process completed tasks
            for idx, col, task in translation_tasks:
                try:
                    translated_text = task.result()
                    result_df.at[idx, f"{col}_translated"] = translated_text
                except Exception as e:
                    logger.error(f"Error in translation task: {e}")
                    result_df.at[idx, f"{col}_translated"] = result_df.at[idx, col]
        
        # Save cache after processing
        self._save_cache()
        
        return result_df
    
    def is_language_supported(self, language_code):
        """
        Check if a language is supported for translation
        
        Args:
            language_code: Language code to check
            
        Returns:
            True if supported, False otherwise
        """
        if not language_code:
            return False
        
        # Normalize language code
        language_code = language_code.lower()[:2]
        
        return language_code in self.supported_languages

def main():
    """Main function for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Translate articles')
    parser.add_argument('--text', type=str, help='Text to translate')
    parser.add_argument('--lang', type=str, default='es', help='Source language code')
    args = parser.parse_args()
    
    translator = ArticleTranslator()
    
    if args.text:
        translated = translator.translate_text(args.text, args.lang)
        print(f"Original ({args.lang}): {args.text}")
        print(f"Translated (en): {translated}")
    else:
        # Test with sample texts
        samples = {
            'es': 'Hola, ¿cómo estás?',
            'fr': 'Bonjour, comment allez-vous?',
            'de': 'Hallo, wie geht es dir?',
            'it': 'Ciao, come stai?',
            'pt': 'Olá, como vai você?',
            'ru': 'Привет, как дела?',
            'zh': '你好，你好吗？',
            'ja': 'こんにちは、お元気ですか？',
            'ar': 'مرحبا، كيف حالك؟'
        }
        
        for lang, text in samples.items():
            if translator.is_language_supported(lang):
                translated = translator.translate_text(text, lang)
                print(f"Original ({lang}): {text}")
                print(f"Translated (en): {translated}")
                print()

if __name__ == '__main__':
    main()
