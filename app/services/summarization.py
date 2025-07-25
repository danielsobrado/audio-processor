"""
Summarization service for generating summaries of text.
"""

import logging

import httpx

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SummarizationService:
    """
    Service for generating summaries of text by calling an external API.
    """

    def __init__(self):
        self.api_url = settings.summarization.api_url
        self.api_key = settings.summarization.api_key
        self.model = settings.summarization.model

    async def summarize_text(self, text: str) -> str:
        """
        Generate a summary of the given text by calling an external API.

        Args:
            text: The text to summarize.

        Returns:
            The generated summary as a string.

        Raises:
            httpx.HTTPStatusError: If the external API returns an error.
            Exception: For other network or processing errors.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes text.",
                },
                {
                    "role": "user",
                    "content": f"Please summarize the following text:\n\n{text}",
                },
            ],
        }

        try:
            timeout = httpx.Timeout(
                settings.summarization.request_timeout,
                connect=settings.summarization.connect_timeout,
            )
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(self.api_url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                summary = result["choices"][0]["message"]["content"]
                return summary
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during summarization: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Summarization failed: {e}", exc_info=True)
            raise
