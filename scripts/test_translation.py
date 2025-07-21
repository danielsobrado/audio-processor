"""
Test script to verify translation functionality.
Run this to test the translation service independently.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.translation import TranslationService


async def test_translation():
    """Test the translation service with a sample text."""

    # Set environment variables for testing
    os.environ["TRANSLATION_ENABLED"] = "true"
    os.environ["TRANSLATION_MODEL_NAME"] = "Helsinki-NLP/opus-mt-en-es"
    os.environ["TRANSLATION_DEVICE"] = "cpu"

    try:
        # Initialize the translation service
        print("Initializing TranslationService...")
        service = TranslationService()

        # Initialize the model
        print("Loading translation model...")
        await service.initialize_model()

        if not service.pipeline:
            print(
                "Translation model not loaded. Check if transformers and torch are installed."
            )
            return

        # Test translation
        test_text = "Hello, this is a test message for translation."
        target_language = "es"  # Spanish

        print(f"Translating: '{test_text}'")
        print(f"Target language: {target_language}")

        translated_text = await service.translate_text(
            text=test_text, target_language=target_language
        )

        print(f"Translation result: '{translated_text}'")

        # Test with longer text
        longer_text = """
        Welcome to our audio processing service. This platform provides
        state-of-the-art speech recognition, speaker diarization, and
        translation capabilities. We support multiple languages and can
        process both uploaded files and URLs.
        """

        print("\nTranslating longer text...")
        translated_longer = await service.translate_text(
            text=longer_text.strip(), target_language=target_language
        )

        print(f"Longer translation result: '{translated_longer}'")

    except Exception as e:
        print(f"Translation test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("Testing Translation Service")
    print("=" * 50)
    asyncio.run(test_translation())
