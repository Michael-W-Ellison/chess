#!/usr/bin/env python3
"""
Simple LLM Integration Test
Tests that the LLM service can load and generate responses
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from services.llm_service import llm_service
from utils.logging_config import setup_logging

# Setup logging
logger = setup_logging()


def test_model_loading():
    """Test that the model loads successfully"""
    print("=" * 60)
    print("Test 1: Model Loading")
    print("=" * 60)
    print()

    success = llm_service.load_model()

    if success:
        print("✓ Model loaded successfully")
        print()

        # Print model info
        info = llm_service.get_model_info()
        print("Model Information:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        print()
        return True
    else:
        print("✗ Failed to load model")
        print()
        print("Possible solutions:")
        print("  1. Download a model: ./scripts/download_model.sh")
        print("  2. Check MODEL_PATH in .env")
        print("  3. Verify model file exists")
        print()
        return False


def test_simple_generation():
    """Test simple text generation"""
    print("=" * 60)
    print("Test 2: Simple Generation")
    print("=" * 60)
    print()

    if not llm_service.is_loaded:
        print("⚠ Skipping - model not loaded")
        return False

    # Simple test prompt
    prompt = """You are a friendly chatbot for kids. Respond naturally.

User: Hi! What's your name?
Assistant:"""

    print("Prompt:")
    print(prompt)
    print()
    print("Generating response...")
    print()

    try:
        response = llm_service.generate(
            prompt,
            max_tokens=50,
            temperature=0.7,
        )

        print("Response:")
        print(response)
        print()
        print(f"✓ Generated {len(response)} characters")
        return True

    except Exception as e:
        print(f"✗ Generation failed: {e}")
        return False


def test_chatbot_style_generation():
    """Test generation with chatbot-style prompt"""
    print("=" * 60)
    print("Test 3: Chatbot Style Generation")
    print("=" * 60)
    print()

    if not llm_service.is_loaded:
        print("⚠ Skipping - model not loaded")
        return False

    # More realistic chatbot prompt
    prompt = """You are Buddy, a friendly AI companion for a 10-year-old child.

PERSONALITY:
- Humor level: 0.6 (moderately funny)
- Energy level: 0.7 (enthusiastic)
- Mood: happy

INSTRUCTIONS:
- Respond naturally as a friend
- Keep responses 2-3 sentences
- Be encouraging and supportive

User: I'm feeling a bit nervous about my test tomorrow. Do you have any advice?
Buddy:"""

    print("Generating chatbot-style response...")
    print()

    try:
        response = llm_service.generate(
            prompt,
            max_tokens=100,
            temperature=0.7,
        )

        print("Response:")
        print(response)
        print()
        print(f"✓ Generated {len(response)} characters")

        # Check response quality
        if len(response) > 20:
            print("✓ Response has reasonable length")
        else:
            print("⚠ Response seems short")

        return True

    except Exception as e:
        print(f"✗ Generation failed: {e}")
        return False


def main():
    """Run all tests"""
    print()
    print("🤖 LLM Service Integration Test")
    print()

    results = []

    # Test 1: Model loading
    results.append(("Model Loading", test_model_loading()))

    # Test 2: Simple generation
    results.append(("Simple Generation", test_simple_generation()))

    # Test 3: Chatbot style
    results.append(("Chatbot Style", test_chatbot_style_generation()))

    # Summary
    print()
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print()

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {name:<30} {status}")

    print()
    print(f"Results: {passed}/{total} tests passed")
    print()

    if passed == total:
        print("🎉 All tests passed! LLM service is working correctly.")
        return 0
    else:
        print("⚠ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
