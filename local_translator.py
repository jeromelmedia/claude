#!/usr/bin/env python3
"""
Local Translation Module using Opus-MT
Provides offline English-to-Korean translation without API calls
"""

from transformers import MarianMTModel, MarianTokenizer


class LocalTranslator:
    """Local offline translator using Opus-MT (Helsinki-NLP)"""

    def __init__(self):
        """Initialize the translator and load the Opus-MT model"""
        self.model_name = "Helsinki-NLP/opus-mt-en-ko"
        self.tokenizer = None
        self.model = None

        # Load the model
        self._load_model()

    def _load_model(self):
        """Load the Opus-MT English->Korean model"""
        print("\nInitializing local translator (Opus-MT)...")
        print(f"Loading model: {self.model_name}")

        try:
            # Load tokenizer and model
            self.tokenizer = MarianTokenizer.from_pretrained(self.model_name)
            self.model = MarianMTModel.from_pretrained(self.model_name)

            print("Model loaded successfully")
            print("Local translator ready\n")
        except Exception as e:
            print(f"Error loading model: {e}")
            raise RuntimeError(f"Failed to initialize Opus-MT translator: {e}")

    def translate(self, text: str, label: str = "text") -> str:
        """
        Translate English text to Korean

        Args:
            text: English text to translate
            label: Description of what's being translated (for logging)

        Returns:
            Korean translation
        """
        if not text or not text.strip():
            return ""

        print(f"Translating {label} to Korean (Opus-MT)...")
        print(f"  Input length: {len(text)} characters")

        # Tokenize the input text
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)

        # Generate translation
        translated = self.model.generate(**inputs)

        # Decode the output
        translation = self.tokenizer.decode(translated[0], skip_special_tokens=True)

        print(f"  Output length: {len(translation)} characters")
        print(f"Korean {label}: {translation[:100]}..." if len(translation) > 100 else f"Korean {label}: {translation}")

        return translation

    def translate_in_chunks(self, text: str, chunk_size: int = 1000, label: str = "text") -> str:
        """
        Translate long text by splitting into chunks

        Args:
            text: English text to translate
            chunk_size: Maximum words per chunk
            label: Description of what's being translated

        Returns:
            Korean translation
        """
        print(f"\nTranslating {label} to Korean (Opus-MT, chunked)...")
        print(f"  Total length: {len(text)} characters")

        # Split into sentences first to avoid breaking mid-sentence
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)

        # Group sentences into chunks
        chunks = []
        current_chunk = []
        current_word_count = 0

        for sentence in sentences:
            sentence_words = len(sentence.split())

            if current_word_count + sentence_words > chunk_size and current_chunk:
                # Start new chunk
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_word_count = sentence_words
            else:
                current_chunk.append(sentence)
                current_word_count += sentence_words

        # Add final chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        print(f"  Split into {len(chunks)} chunks")

        # Translate each chunk
        translated_chunks = []
        for i, chunk in enumerate(chunks, 1):
            print(f"  Translating chunk {i}/{len(chunks)} ({len(chunk)} chars)...")
            # Tokenize and translate
            inputs = self.tokenizer(chunk, return_tensors="pt", padding=True, truncation=True, max_length=512)
            translated = self.model.generate(**inputs)
            translation = self.tokenizer.decode(translated[0], skip_special_tokens=True)
            translated_chunks.append(translation)

        # Combine translations
        full_translation = '\n\n'.join(translated_chunks)

        print(f"  Translation complete: {len(full_translation)} characters\n")

        return full_translation


# Create a global instance for easy import
_translator = None

def get_translator() -> LocalTranslator:
    """Get or create the global translator instance"""
    global _translator
    if _translator is None:
        _translator = LocalTranslator()
    return _translator


def translate_text(text: str, label: str = "text") -> str:
    """
    Convenience function to translate text using the global translator

    Args:
        text: English text to translate
        label: Description of what's being translated

    Returns:
        Korean translation
    """
    translator = get_translator()
    return translator.translate(text, label)


def translate_text_chunked(text: str, chunk_size: int = 1000, label: str = "text") -> str:
    """
    Convenience function to translate long text using the global translator

    Args:
        text: English text to translate
        chunk_size: Maximum words per chunk
        label: Description of what's being translated

    Returns:
        Korean translation
    """
    translator = get_translator()
    return translator.translate_in_chunks(text, chunk_size, label)


if __name__ == "__main__":
    # Test the translator
    print("Testing Local Translator")
    print("=" * 50)

    translator = LocalTranslator()

    # Test short translation
    test_text = "Hello, how are you today? This is a test of the translation system."
    result = translator.translate(test_text, "test")

    print("\n" + "=" * 50)
    print(f"Original: {test_text}")
    print(f"Translated: {result}")
    print("=" * 50)
