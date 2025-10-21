#!/usr/bin/env python3
"""
Test script to check which Claude models your API key has access to.
"""

import json
import sys

try:
    import anthropic
except ImportError:
    print("Installing anthropic package...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "anthropic", "--user"])
    import anthropic

def test_model_access(api_key, model_name):
    """Test if a specific model is accessible."""
    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model_name,
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )
        return True
    except anthropic.NotFoundError:
        return False
    except Exception as e:
        print(f"  Error: {e}")
        return False

def main():
    print("=" * 60)
    print("CLAUDE API ACCESS TESTER")
    print("=" * 60)

    # Try to load API key from config
    api_key = None
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            api_key = config.get('anthropic_api_key')
    except:
        pass

    # If not in config, ask user
    if not api_key or api_key == "your-api-key-here":
        api_key = input("\nEnter your Anthropic API key: ").strip()
    else:
        print(f"\n✓ Using API key from config.json")

    if not api_key or api_key.startswith("your-"):
        print("✗ Invalid API key")
        sys.exit(1)

    # Models to test
    models = [
        ("claude-3-haiku-20240307", "Claude 3 Haiku (fastest, cheapest)"),
        ("claude-3-sonnet-20240229", "Claude 3 Sonnet (balanced)"),
        ("claude-3-opus-20240229", "Claude 3 Opus (most capable)"),
        ("claude-3-5-sonnet-20240620", "Claude 3.5 Sonnet (June)"),
        ("claude-3-5-sonnet-20241022", "Claude 3.5 Sonnet (October - latest)"),
    ]

    print("\nTesting model access...\n")

    accessible_models = []

    for model_id, description in models:
        print(f"Testing {model_id}...", end=" ")
        if test_model_access(api_key, model_id):
            print(f"✓ ACCESSIBLE - {description}")
            accessible_models.append(model_id)
        else:
            print(f"✗ Not accessible")

    print("\n" + "=" * 60)

    if accessible_models:
        print(f"\n✓ You have access to {len(accessible_models)} model(s):")
        for model in accessible_models:
            print(f"  - {model}")

        print(f"\nRECOMMENDED: Use '{accessible_models[0]}' in your config.json")
        print("\nAdd this line to your config.json:")
        print(f'  "claude_model": "{accessible_models[0]}",')
    else:
        print("\n✗ No Claude models accessible with this API key")
        print("\nPossible issues:")
        print("1. API key is invalid")
        print("2. Account doesn't have API access enabled")
        print("3. Need to add payment method to account")
        print("\nCheck your account at: https://console.anthropic.com/")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
