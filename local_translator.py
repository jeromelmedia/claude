#!/usr/bin/env python3
"""
Local Translation Module using NLLB-200
Provides offline translation capabilities for video content
"""

import os
import re
from typing import Optional
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

class LocalTranslator:
    """Local translation using NLLB-200 model"""

    def __init__(self):
        self.translator = None
        self.tokenizer = None
        self.model = None
        self.max_length = 512  # NLLB-200 max sequence length

    def initialize(self):
        """Initialize the NLLB-200 translation model"""
        if self.translator is not None:
            return  # Already initialized

        print("\nInitializing NLLB-200 translation model...")
        print("This may take a moment on first run (downloading ~2.5GB model)...")

        try:
            model_name = "facebook/nllb-200-distilled-600M"

            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

            # Create translation pipeline
            self.translator = pipeline(
                "translation",
                model=self.model,
                tokenizer=self.tokenizer,
                src_lang="eng_Latn",  # English
                tgt_lang="kor_Hang",  # Korean
                max_length=self.max_length
            )

            print("✓ NLLB-200 model loaded successfully")

        except Exception as e:
            print(f"✗ Error loading NLLB-200 model: {e}")
            print("Translation will be skipped.")
            self.translator = None

    def chunk_text(self, text: str, max_chunk_size: int = 400) -> list:
        """
        Split text into chunks that respect sentence boundaries.
        For long-form content (6000+ words), uses intelligent chunking.

        Args:
            text: Text to chunk
            max_chunk_size: Maximum characters per chunk (leaving buffer for tokenization)

        Returns:
            List of text chunks
        """
        # If text is short enough, return as single chunk
        if len(text) <= max_chunk_size:
            return [text]

        # Split into sentences (handles ., !, ?, and newlines)
        sentence_pattern = r'(?<=[.!?\n])\s+'
        sentences = re.split(sentence_pattern, text)

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            # If adding this sentence would exceed max, save current chunk and start new one
            if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                # Add space if chunk is not empty
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence

        # Add the last chunk if it exists
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def translate(self, text: str, target_lang: str = "korean") -> Optional[str]:
        """
        Translate text to target language using NLLB-200
        Handles long texts by chunking intelligently

        Args:
            text: Text to translate
            target_lang: Target language (currently only 'korean' supported)

        Returns:
            Translated text or None if translation fails
        """
        if not text or not text.strip():
            return None

        # Initialize if needed
        if self.translator is None:
            self.initialize()

        if self.translator is None:
            return None  # Model failed to load

        try:
            # Handle long texts with chunking
            chunks = self.chunk_text(text)

            if len(chunks) > 1:
                print(f"  Translating in {len(chunks)} chunks...")

            translated_chunks = []

            for i, chunk in enumerate(chunks, 1):
                if len(chunks) > 1:
                    print(f"  Chunk {i}/{len(chunks)}...", end=" ")

                # Translate chunk
                result = self.translator(chunk, max_length=self.max_length)
                translated_text = result[0]['translation_text']
                translated_chunks.append(translated_text)

                if len(chunks) > 1:
                    print("✓")

            # Combine all chunks
            final_translation = " ".join(translated_chunks)

            return final_translation

        except Exception as e:
            print(f"  ✗ Translation error: {e}")
            return None

# Global translator instance
_translator = None

def get_translator() -> LocalTranslator:
    """Get or create global translator instance"""
    global _translator
    if _translator is None:
        _translator = LocalTranslator()
    return _translator

def translate_text(text: str, target_lang: str = "korean") -> Optional[str]:
    """
    Convenience function to translate text

    Args:
        text: Text to translate
        target_lang: Target language (default: korean)

    Returns:
        Translated text or None if translation fails
    """
    translator = get_translator()
    return translator.translate(text, target_lang)
