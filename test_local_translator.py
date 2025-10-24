#!/usr/bin/env python3
"""
Test script for local_translator module
"""

from local_translator import LocalTranslator

def main():
    print("=" * 60)
    print("TESTING LOCAL TRANSLATOR (OPUS-MT)")
    print("=" * 60)

    # Initialize translator
    translator = LocalTranslator()

    # Test 1: Simple translation
    print("\n### TEST 1: Simple Translation ###")
    test_text_1 = "Hello, how are you today? I hope you're having a great day!"
    result_1 = translator.translate(test_text_1, "greeting")
    print(f"\nOriginal: {test_text_1}")
    print(f"Korean: {result_1}")

    # Test 2: Longer text (like a title)
    print("\n\n### TEST 2: Title Translation ###")
    title = "7 Simple Morning Habits That Will Transform Your Health After 60"
    result_2 = translator.translate(title, "title")
    print(f"\nOriginal: {title}")
    print(f"Korean: {result_2}")

    # Test 3: Description-like text
    print("\n\n### TEST 3: Description Translation ###")
    description = "Discover the scientifically-proven morning routine that can help you feel 10 years younger. These simple habits take just 15 minutes each morning but can dramatically improve your energy, mental clarity, and overall health."
    result_3 = translator.translate(description, "description")
    print(f"\nOriginal: {description}")
    print(f"Korean: {result_3}")

    # Test 4: Chunked translation (simulate script)
    print("\n\n### TEST 4: Chunked Translation (Script Simulation) ###")
    long_text = """
    Good morning! Today we're going to talk about something incredibly important for everyone over 60.
    I'm Dr. Kim, and over my 30 years of practice, I've discovered a simple morning routine that can
    transform your health. Many of my patients have reported feeling years younger after following these
    simple habits. The best part? It takes just 15 minutes each morning. Let me share these secrets with you.

    The first habit is drinking warm lemon water. This simple practice helps wake up your digestive system
    and provides vital vitamin C. I recommend this to all my patients, and they've seen remarkable improvements
    in their energy levels throughout the day.
    """

    result_4 = translator.translate_in_chunks(long_text, chunk_size=50, label="script excerpt")
    print(f"\nOriginal ({len(long_text)} chars):")
    print(long_text[:200] + "...")
    print(f"\nKorean ({len(result_4)} chars):")
    print(result_4[:200] + "...")

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    main()
