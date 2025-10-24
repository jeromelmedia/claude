#!/usr/bin/env python3
"""
Local Translation Module using Argos Translate
Provides offline English-to-Korean translation without API calls
"""

import argostranslate.package
import argostranslate.translate


class LocalTranslator:
    """Local offline translator using Argos Translate"""

    def __init__(self):
        """Initialize the translator and ensure language packages are installed"""
        self.from_code = "en"
        self.to_code = "ko"
        self.translator = None

        # Ensure language package is installed
        self._ensure_language_package()

    def _ensure_language_package(self):
        """Download and install English->Korean language package if not already installed"""
        print("\nInitializing local translator...")

        # Update package index
        argostranslate.package.update_package_index()
        available_packages = argostranslate.package.get_available_packages()

        # Find English -> Korean package
        en_ko_package = None
        for pkg in available_packages:
            if pkg.from_code == self.from_code and pkg.to_code == self.to_code:
                en_ko_package = pkg
                break

        if not en_ko_package:
            print(f"Error: No English -> Korean translation package available")
            print("Available packages:")
            for pkg in available_packages[:10]:  # Show first 10
                print(f"  {pkg.from_code} -> {pkg.to_code}")
            raise RuntimeError("English->Korean package not found")

        # Check if already installed
        installed_packages = argostranslate.package.get_installed_packages()
        already_installed = False

        for pkg in installed_packages:
            if pkg.from_code == self.from_code and pkg.to_code == self.to_code:
                already_installed = True
                print(f"English -> Korean package already installed")
                break

        # Install if needed
        if not already_installed:
            print(f"Downloading English -> Korean translation package...")
            print(f"Package: {en_ko_package.package_version}")
            argostranslate.package.install_from_path(en_ko_package.download())
            print("Package installed successfully")

        # Get the translator
        installed_packages = argostranslate.package.get_installed_packages()
        for pkg in installed_packages:
            if pkg.from_code == self.from_code and pkg.to_code == self.to_code:
                self.translator = pkg
                break

        if not self.translator:
            raise RuntimeError("Failed to initialize translator")

        print("Local translator ready\n")

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

        print(f"Translating {label} to Korean (local)...")
        print(f"  Input length: {len(text)} characters")

        # Translate using argos-translate
        translation = argostranslate.translate.translate(text, self.from_code, self.to_code)

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
        print(f"\nTranslating {label} to Korean (local, chunked)...")
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
            translation = argostranslate.translate.translate(chunk, self.from_code, self.to_code)
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
