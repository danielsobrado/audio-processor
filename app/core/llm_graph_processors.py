"""
LLM-based graph processing strategies for entity extraction, topic modeling, 
sentiment analysis, and relationship extraction.
"""

import json
import logging
from typing import Any, Dict, List, Tuple, Optional
from abc import ABC, abstractmethod
from datetime import datetime

from app.config.settings import get_settings
from app.schemas.graph import EntityNode, TopicNode, GraphRelationship, RelationshipType

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate_completion(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate completion from LLM provider."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI provider for LLM-based graph processing."""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", api_base: str = ""):
        self.api_key = api_key
        self.model = model
        self.api_base = api_base
        
    async def generate_completion(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate completion from OpenAI API."""
        try:
            import openai
            
            if self.api_base:
                openai.api_base = self.api_base
            
            client = openai.AsyncOpenAI(api_key=self.api_key)
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts structured information from text."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.1
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise


class AnthropicProvider(LLMProvider):
    """Anthropic provider for LLM-based graph processing."""
    
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        self.api_key = api_key
        self.model = model
        
    async def generate_completion(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate completion from Anthropic API."""
        try:
            import anthropic
            
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            
            response = await client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise


class LocalLLMProvider(LLMProvider):
    """Local LLM provider (e.g., Ollama, vLLM)."""
    
    def __init__(self, api_base: str, model: str = "llama2"):
        self.api_base = api_base
        self.model = model
        
    async def generate_completion(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate completion from local LLM."""
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/v1/completions",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "max_tokens": max_tokens,
                        "temperature": 0.1
                    }
                )
                
                result = response.json()
                return result["choices"][0]["text"]
                
        except Exception as e:
            logger.error(f"Local LLM API error: {e}")
            raise


class OpenRouterProvider(LLMProvider):
    """OpenRouter provider for LLM-based graph processing."""
    
    def __init__(self, api_key: str, model: str = "openai/gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model
        self.api_base = "https://openrouter.ai/api/v1"
        
    async def generate_completion(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate completion from OpenRouter API."""
        try:
            import httpx
            import json
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/audio-processor",  # Optional
                "X-Title": "Audio Processor Graph Analysis"  # Optional
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that extracts structured information from text."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.1
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    content=json.dumps(data),  # Use content=json.dumps() for httpx
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                return result["choices"][0]["message"]["content"]
                
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            raise


class LLMBasedEntityExtractor:
    """Extract entities from text using LLM."""
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider
    
    async def extract_entities(self, text: str) -> List[Tuple[str, str, float]]:
        """Extract entities from text using LLM."""
        prompt = f"""
Extract named entities from the following text. Return the results as a JSON array of objects with the format:
[{{"entity_text": "text", "entity_type": "PERSON|ORGANIZATION|LOCATION|DATE|TIME|MONEY|EMAIL|PHONE|URL", "confidence": 0.0-1.0}}]

Text: "{text}"

Only return the JSON array, no other text.
"""
        
        try:
            response = await self.llm_provider.generate_completion(prompt, max_tokens=500)
            
            # Parse JSON response
            entities_data = json.loads(response.strip())
            
            entities = []
            for entity in entities_data:
                entities.append((
                    entity["entity_text"],
                    entity["entity_type"],
                    entity.get("confidence", 0.8)
                ))
            
            return entities
            
        except Exception as e:
            logger.error(f"LLM entity extraction failed: {e}")
            return []


class LLMBasedTopicModeler:
    """Extract topics from text using LLM."""
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider
    
    async def extract_topics(self, text: str) -> List[Tuple[str, float]]:
        """Extract topics from text using LLM."""
        prompt = f"""
Analyze the following text and identify the main topics being discussed. Return the results as a JSON array of objects with the format:
[{{"topic_name": "topic", "confidence": 0.0-1.0, "keywords": ["keyword1", "keyword2"]}}]

Consider topics like: technology, business, healthcare, education, entertainment, politics, sports, science, etc.

Text: "{text}"

Only return the JSON array, no other text.
"""
        
        try:
            response = await self.llm_provider.generate_completion(prompt, max_tokens=500)
            
            # Parse JSON response
            topics_data = json.loads(response.strip())
            
            topics = []
            for topic in topics_data:
                topics.append((
                    topic["topic_name"],
                    topic.get("confidence", 0.7)
                ))
            
            return topics
            
        except Exception as e:
            logger.error(f"LLM topic extraction failed: {e}")
            return []


class LLMBasedSentimentAnalyzer:
    """Analyze sentiment of text using LLM."""
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text using LLM."""
        prompt = f"""
Analyze the sentiment of the following text. Return the result as a JSON object with the format:
{{"sentiment": "positive|negative|neutral", "confidence": 0.0-1.0, "emotions": ["emotion1", "emotion2"], "intensity": 0.0-1.0}}

Text: "{text}"

Only return the JSON object, no other text.
"""
        
        try:
            response = await self.llm_provider.generate_completion(prompt, max_tokens=300)
            
            # Parse JSON response
            sentiment_data = json.loads(response.strip())
            
            return sentiment_data
            
        except Exception as e:
            logger.error(f"LLM sentiment analysis failed: {e}")
            return {
                "sentiment": "neutral",
                "confidence": 0.5,
                "emotions": [],
                "intensity": 0.5
            }


class LLMBasedRelationshipExtractor:
    """Extract relationships between entities using LLM."""
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider
    
    async def extract_relationships(self, text: str, entities: List[str]) -> List[Dict[str, Any]]:
        """Extract relationships between entities using LLM."""
        entities_str = ", ".join(entities)
        
        prompt = f"""
Given the following text and entities, identify relationships between them. Return the results as a JSON array of objects with the format:
[{{"from_entity": "entity1", "to_entity": "entity2", "relationship_type": "type", "confidence": 0.0-1.0, "context": "relevant text snippet"}}]

Text: "{text}"
Entities: {entities_str}

Common relationship types: WORKS_FOR, LOCATED_IN, PART_OF, RELATED_TO, MENTIONS, DISCUSSES, COLLABORATES_WITH, MANAGES, etc.

Only return the JSON array, no other text.
"""
        
        try:
            response = await self.llm_provider.generate_completion(prompt, max_tokens=800)
            
            # Parse JSON response
            relationships_data = json.loads(response.strip())
            
            return relationships_data
            
        except Exception as e:
            logger.error(f"LLM relationship extraction failed: {e}")
            return []


class LLMGraphProcessorFactory:
    """Factory for creating LLM-based graph processors."""
    
    @staticmethod
    def create_llm_provider(settings) -> LLMProvider:
        """Create LLM provider based on settings."""
        import os
        
        provider = settings.graph.llm_provider.lower()
        
        # Get API key from environment or settings
        api_key = settings.graph.llm_api_key or os.getenv("GRAPH_LLM_API_KEY")
        if not api_key and provider in ["openai", "anthropic", "openrouter"]:
            # Try provider-specific environment variables
            if provider == "openai":
                api_key = os.getenv("OPENAI_API_KEY")
            elif provider == "anthropic":
                api_key = os.getenv("ANTHROPIC_API_KEY")
            elif provider == "openrouter":
                api_key = os.getenv("OPENROUTER_API_KEY")
        
        if provider == "openai":
            if not api_key:
                raise ValueError("OpenAI API key is required but not found in settings or environment")
            return OpenAIProvider(
                api_key=api_key,
                model=settings.graph.llm_model,
                api_base=settings.graph.llm_api_base
            )
        elif provider == "anthropic":
            if not api_key:
                raise ValueError("Anthropic API key is required but not found in settings or environment")
            return AnthropicProvider(
                api_key=api_key,
                model=settings.graph.llm_model
            )
        elif provider == "local":
            return LocalLLMProvider(
                api_base=settings.graph.llm_api_base or "http://localhost:11434",
                model=settings.graph.llm_model
            )
        elif provider == "openrouter":
            if not api_key:
                raise ValueError("OpenRouter API key is required but not found in settings or environment")
            return OpenRouterProvider(
                api_key=api_key,
                model=settings.graph.llm_model
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    @staticmethod
    def create_entity_extractor(settings) -> LLMBasedEntityExtractor:
        """Create LLM-based entity extractor."""
        llm_provider = LLMGraphProcessorFactory.create_llm_provider(settings)
        return LLMBasedEntityExtractor(llm_provider)
    
    @staticmethod
    def create_topic_modeler(settings) -> LLMBasedTopicModeler:
        """Create LLM-based topic modeler."""
        llm_provider = LLMGraphProcessorFactory.create_llm_provider(settings)
        return LLMBasedTopicModeler(llm_provider)
    
    @staticmethod
    def create_sentiment_analyzer(settings) -> LLMBasedSentimentAnalyzer:
        """Create LLM-based sentiment analyzer."""
        llm_provider = LLMGraphProcessorFactory.create_llm_provider(settings)
        return LLMBasedSentimentAnalyzer(llm_provider)
    
    @staticmethod
    def create_relationship_extractor(settings) -> LLMBasedRelationshipExtractor:
        """Create LLM-based relationship extractor."""
        llm_provider = LLMGraphProcessorFactory.create_llm_provider(settings)
        return LLMBasedRelationshipExtractor(llm_provider)
