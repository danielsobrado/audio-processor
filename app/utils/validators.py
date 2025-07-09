import re

from app.config.settings import get_settings

settings = get_settings()


def is_valid_email(email: str) -> bool:
    """
    Placeholder for an email validation function.
    """
    # Basic regex for email validation
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_transcription_params(
    language: str,
    model: str,
    utt_split: float,
) -> None:
    """
    Validate transcription parameters.

    Args:
        language: Language code.
        model: Transcription model size.
        utt_split: Utterance split threshold.

    Raises:
        ValueError: If any parameter is invalid.
    """

    # Validate language
    # In a real application, you would have a list of supported languages
    if not re.match(r"^[a-z]{2,3}(-[A-Z]{2})?$", language) and language != "auto":
        raise ValueError(f"Invalid language code: {language}")

    # Validate model
    supported_models = ["tiny", "base", "small", "medium", "large-v2", "large-v3"]
    if model not in supported_models:
        raise ValueError(
            f"Unsupported model: {model}. Supported models: {supported_models}"
        )

    # Validate utterance split
    if not 0.1 <= utt_split <= 1.0:
        raise ValueError(
            f"Invalid utterance split threshold: {
                utt_split}. Must be between 0.1 and 1.0."
        )
