"""
Deepgram-compatible output formatter.
Converts WhisperX results to Deepgram JSON format for API compatibility.
"""

import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DeepgramFormatter:
    """
    Converts WhisperX output to Deepgram-compatible JSON format.
    Ensures compatibility with Omi's existing conversation processing pipeline.
    """
    
    def _apply_smart_formatting(self, text: str) -> str:
        """Apply smart formatting to transcript text."""
        if not text:
            return text
        
        # Basic smart formatting rules
        formatted_text = text
        
        # Capitalize first letter of sentences
        sentences = formatted_text.split(". ")
        formatted_sentences = []
        for sentence in sentences:
            if sentence:
                sentence = sentence.strip()
                if sentence:
                    sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
                formatted_sentences.append(sentence)
        
        formatted_text = ". ".join(formatted_sentences)
        
        # Ensure first character is capitalized
        if formatted_text:
            formatted_text = formatted_text[0].upper() + formatted_text[1:] if len(formatted_text) > 1 else formatted_text.upper()
        
        return formatted_text
    
    def _apply_punctuation(self, text: str) -> str:
        """Apply basic punctuation rules."""
        if not text:
            return text
        
        # Remove extra spaces
        text = " ".join(text.split())
        
        # Ensure text ends with punctuation
        if text and text[-1] not in ".!?":
            text += "."
        
        return text
    
    def _get_supported_languages(self) -> List[str]:
        """Get list of supported language codes."""
        return [
            "en", "zh", "de", "es", "ru", "ko", "fr", "ja", "pt", "tr", "pl",
            "ca", "nl", "ar", "sv", "it", "id", "hi", "fi", "vi", "he", "uk",
            "el", "ms", "cs", "ro", "da", "hu", "ta", "no", "th", "ur", "hr",
            "bg", "lt", "la", "mi", "ml", "cy", "sk", "te", "fa", "lv", "bn",
            "sr", "az", "sl", "kn", "et", "mk", "br", "eu", "is", "hy", "ne",
            "mn", "bs", "kk", "sq", "sw", "gl", "mr", "pa", "si", "km", "sn",
            "yo", "so", "af", "oc", "ka", "be", "tg", "sd", "gu", "am", "yi",
            "lo", "uz", "fo", "ht", "ps", "tk", "nn", "mt", "sa", "lb", "my",
            "bo", "tl", "mg", "as", "tt", "haw", "ln", "ha", "ba", "jw", "su"
        ]
    
    def format_error_response(
        self,
        request_id: str,
        error_message: str,
        error_code: str = "processing_error",
    ) -> Dict:
        """
        Format error response in Deepgram-compatible structure.
        
        Args:
            request_id: Request identifier
            error_message: Human-readable error message
            error_code: Error classification code
        
        Returns:
            Deepgram-compatible error response
        """
        return {
            "metadata": {
                "transaction_key": "deprecated",
                "request_id": request_id,
                "created": datetime.now(timezone.utc).isoformat(),
                "error": {
                    "code": error_code,
                    "message": error_message,
                }
            },
            "results": {
                "channels": [{
                    "alternatives": [{
                        "transcript": "",
                        "confidence": 0.0,
                        "words": [],
                        "paragraphs": {
                            "transcript": "",
                            "paragraphs": []
                        }
                    }]
                }],
                "utterances": []
            }
        }
    
    def add_translation_data(
        self,
        deepgram_response: Dict,
        translations: Dict[str, str],
    ) -> Dict:
        """
        Add translation data to existing Deepgram response.
        
        Args:
            deepgram_response: Base Deepgram response
            translations: Dictionary of language_code -> translated_text
        
        Returns:
            Enhanced response with translation data
        """
        try:
            # Add translations to metadata
            if "translations" not in deepgram_response["metadata"]:
                deepgram_response["metadata"]["translations"] = {}
            
            deepgram_response["metadata"]["translations"].update(translations)
            
            # Add translation alternatives for each language
            channels = deepgram_response["results"]["channels"]
            if channels and channels[0]["alternatives"]:
                base_alternative = channels[0]["alternatives"][0]
                
                for lang_code, translated_text in translations.items():
                    # Create new alternative for each translation
                    translation_alternative = {
                        "transcript": translated_text,
                        "confidence": base_alternative["confidence"],
                        "language": lang_code,
                        "words": [],  # Translation doesn't preserve word timing
                        "paragraphs": {
                            "transcript": translated_text,
                            "paragraphs": [{
                                "sentences": [{
                                    "text": translated_text,
                                    "start": 0.0,
                                    "end": deepgram_response["metadata"]["duration"],
                                }],
                                "speaker": None,
                                "num_words": len(translated_text.split()),
                                "start": 0.0,
                                "end": deepgram_response["metadata"]["duration"],
                            }]
                        }
                    }
                    
                    channels[0]["alternatives"].append(translation_alternative)
            
            return deepgram_response
            
        except Exception as e:
            logger.error(f"Failed to add translation data: {e}")
            return deepgram_response
    
    def add_summary_data(
        self,
        deepgram_response: Dict,
        summary: str,
        summary_type: str = "abstractive",
    ) -> Dict:
        """
        Add summarization data to Deepgram response.
        
        Args:
            deepgram_response: Base Deepgram response
            summary: Generated summary text
            summary_type: Type of summary (abstractive, extractive, etc.)
        
        Returns:
            Enhanced response with summary data
        """
        try:
            # Add summary to metadata
            deepgram_response["metadata"]["summary"] = {
                "text": summary,
                "type": summary_type,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
            
            # Add summary as special result section
            if "summary" not in deepgram_response["results"]:
                deepgram_response["results"]["summary"] = {
                    "text": summary,
                    "type": summary_type,
                    "confidence": 0.8,  # Default confidence for generated content
                }
            
            return deepgram_response
            
        except Exception as e:
            logger.error(f"Failed to add summary data: {e}")
            return deepgram_response
    
    def validate_deepgram_format(self, response: Dict) -> bool:
        """
        Validate that response conforms to Deepgram format.
        
        Args:
            response: Response dictionary to validate
        
        Returns:
            True if format is valid, False otherwise
        """
        try:
            # Check required top-level keys
            required_keys = ["metadata", "results"]
            if not all(key in response for key in required_keys):
                logger.error("Missing required top-level keys")
                return False
            
            # Check metadata structure
            metadata = response["metadata"]
            metadata_required = ["request_id", "created", "duration", "channels"]
            if not all(key in metadata for key in metadata_required):
                logger.error("Missing required metadata keys")
                return False
            
            # Check results structure
            results = response["results"]
            if "channels" not in results:
                logger.error("Missing channels in results")
                return False
            
            channels = results["channels"]
            if not isinstance(channels, list) or not channels:
                logger.error("Channels must be non-empty list")
                return False
            
            # Check channel structure
            for channel in channels:
                if "alternatives" not in channel:
                    logger.error("Missing alternatives in channel")
                    return False
                
                alternatives = channel["alternatives"]
                if not isinstance(alternatives, list) or not alternatives:
                    logger.error("Alternatives must be non-empty list")
                    return False
                
                # Check alternative structure
                for alternative in alternatives:
                    alt_required = ["transcript", "confidence", "words"]
                    if not all(key in alternative for key in alt_required):
                        logger.error("Missing required alternative keys")
                        return False
            
            logger.debug("Deepgram format validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
    
    def get_format_info(self) -> Dict:
        """Get information about the Deepgram format implementation."""
        return {
            "format_version": "1.0",
            "compatible_with": "Deepgram API v1",
            "supported_features": [
                "transcription",
                "word_timestamps",
                "speaker_diarization",
                "punctuation",
                "smart_formatting",
                "utterances",
                "paragraphs",
                "translations",
                "summarization",
            ],
            "model_mappings": list(self.model_info.keys()),
            "supported_languages": self._get_supported_languages(),
        }
    def __init__(self):
        self.model_info = {
            "large-v2": {
                "name": "Whisper Large V2",
                "canonical_name": "whisper-large-v2",
                "architecture": "whisperx",
                "languages": self._get_supported_languages(),
            },
            "large-v3": {
                "name": "Whisper Large V3",
                "canonical_name": "whisper-large-v3",
                "architecture": "whisperx",
                "languages": self._get_supported_languages(),
            },
            "medium": {
                "name": "Whisper Medium",
                "canonical_name": "whisper-medium",
                "architecture": "whisperx",
                "languages": self._get_supported_languages(),
            },
            "small": {
                "name": "Whisper Small",
                "canonical_name": "whisper-small",
                "architecture": "whisperx",
                "languages": self._get_supported_languages(),
            },
            "base": {
                "name": "Whisper Base",
                "canonical_name": "whisper-base",
                "architecture": "whisperx",
                "languages": self._get_supported_languages(),
            },
            "tiny": {
                "name": "Whisper Tiny",
                "canonical_name": "whisper-tiny",
                "architecture": "whisperx",
                "languages": self._get_supported_languages(),
            },
        }


# Utility functions for format conversion

def convert_whisperx_to_deepgram(
    whisperx_result: Dict,
    request_id: str,
    model_name: str = "large-v2",
    **options
) -> Dict:
    """
    Convenience function to convert WhisperX result to Deepgram format.
    
    Args:
        whisperx_result: WhisperX processing result
        request_id: Unique request identifier
        model_name: Model used for processing
        **options: Additional formatting options
    
    Returns:
        Deepgram-compatible response
    """
    formatter = DeepgramFormatter()
    return formatter.format_transcription_result(
        whisperx_result=whisperx_result,
        request_id=request_id,
        model_name=model_name,
        **options
    )


def validate_deepgram_response(response: Dict) -> bool:
    """
    Validate Deepgram response format.
    
    Args:
        response: Response to validate
    
    Returns:
        True if valid, False otherwise
    """
    formatter = DeepgramFormatter()
    return formatter.validate_deepgram_format(response)


def create_error_response(
    request_id: str,
    error_message: str,
    error_code: str = "processing_error"
) -> Dict:
    """
    Create Deepgram-compatible error response.
    
    Args:
        request_id: Request identifier
        error_message: Error description
        error_code: Error classification
    
    Returns:
        Deepgram-compatible error response
    """
    formatter = DeepgramFormatter()
    return formatter.format_error_response(
        request_id=request_id,
        error_message=error_message,
        error_code=error_code,
    )

    
    def format_transcription_result(
        self,
        whisperx_result: Dict,
        request_id: str,
        model_name: str = "large-v2",
        audio_duration: Optional[float] = None,
        audio_data: Optional[bytes] = None,
        punctuate: bool = True,
        diarize: bool = True,
        smart_format: bool = True,
        utterances: bool = True,
    ) -> Dict:
        """
        Convert WhisperX result to Deepgram-compatible format.
        
        Args:
            whisperx_result: Raw WhisperX processing result
            request_id: Unique request identifier
            model_name: Model used for transcription
            audio_duration: Audio duration in seconds
            audio_data: Raw audio data for SHA256 calculation
            punctuate: Whether punctuation was applied
            diarize: Whether diarization was performed
            smart_format: Whether smart formatting was applied
            utterances: Whether to include utterance-level segments
        
        Returns:
            Deepgram-compatible JSON response
        """
        try:
            segments = whisperx_result.get("segments", [])
            detected_language = whisperx_result.get("language", "en")
            
            # Generate metadata
            metadata = self._generate_metadata(
                request_id=request_id,
                model_name=model_name,
                audio_duration=audio_duration or whisperx_result.get("duration", 0),
                audio_data=audio_data,
                detected_language=detected_language,
            )
            
            # Convert segments to Deepgram format
            channels_data = self._convert_channels(
                segments=segments,
                punctuate=punctuate,
                smart_format=smart_format,
            )
            
            # Generate utterances if requested
            utterances_data = []
            if utterances:
                utterances_data = self._generate_utterances(segments)
            
            # Build final response
            response = {
                "metadata": metadata,
                "results": {
                    "channels": channels_data,
                }
            }
            
            # Add utterances if generated
            if utterances_data:
                response["results"]["utterances"] = utterances_data
            
            logger.debug(f"Formatted {len(segments)} segments to Deepgram format")
            return response
            
        except Exception as e:
            logger.error(f"Failed to format Deepgram response: {e}")
            raise ValueError(f"Response formatting failed: {e}")
    
    def _generate_metadata(
        self,
        request_id: str,
        model_name: str,
        audio_duration: float,
        detected_language: str,
        audio_data: Optional[bytes] = None,
    ) -> Dict:
        """Generate Deepgram-compatible metadata section."""
        
        # Calculate SHA256 if audio data available
        sha256_hash = ""
        if audio_data:
            sha256_hash = hashlib.sha256(audio_data).hexdigest()
        
        # Get model info
        model_info = self.model_info.get(model_name, self.model_info["large-v2"])
        
        metadata = {
            "transaction_key": "deprecated",  # Deepgram legacy field
            "request_id": request_id,
            "sha256": sha256_hash,
            "created": datetime.now(timezone.utc).isoformat(),
            "duration": round(audio_duration, 3),
            "channels": 1,  # WhisperX processes mono audio
            "models": [model_name],
            "model_info": {
                model_name: {
                    "name": model_info["name"],
                    "canonical_name": model_info["canonical_name"],
                    "architecture": model_info["architecture"],
                    "languages": [detected_language],  # Only detected language
                }
            }
        }
        
        return metadata
    
    def _convert_channels(
        self,
        segments: List[Dict],
        punctuate: bool = True,
        smart_format: bool = True,
    ) -> List[Dict]:
        """Convert WhisperX segments to Deepgram channels format."""
        
        if not segments:
            return [{
                "alternatives": [{
                    "transcript": "",
                    "confidence": 0.0,
                    "words": [],
                    "paragraphs": {
                        "transcript": "",
                        "paragraphs": []
                    }
                }]
            }]
        
        # Extract all words from segments
        all_words = []
        full_transcript_parts = []
        
        for segment in segments:
            segment_text = segment.get("text", "").strip()
            segment_start = segment.get("start", 0.0)
            segment_end = segment.get("end", 0.0)
            segment_speaker = segment.get("speaker")
            
            # Add segment text to full transcript
            if segment_text:
                full_transcript_parts.append(segment_text)
            
            # Process word-level data if available
            if "words" in segment and segment["words"]:
                for word_data in segment["words"]:
                    word_entry = {
                        "word": word_data.get("word", ""),
                        "start": float(word_data.get("start", segment_start)),
                        "end": float(word_data.get("end", segment_end)),
                        "confidence": float(word_data.get("score", word_data.get("confidence", 0.8))),
                    }
                    
                    # Add speaker information if available
                    word_speaker = word_data.get("speaker", segment_speaker)
                    if word_speaker is not None:
                        word_entry["speaker"] = self._normalize_speaker_id(word_speaker)
                    
                    all_words.append(word_entry)
            else:
                # No word-level data, create word entries from text
                if segment_text:
                    words = segment_text.split()
                    word_duration = (segment_end - segment_start) / max(len(words), 1)
                    
                    for i, word in enumerate(words):
                        word_start = segment_start + (i * word_duration)
                        word_end = word_start + word_duration
                        
                        word_entry = {
                            "word": word,
                            "start": round(word_start, 3),
                            "end": round(word_end, 3),
                            "confidence": 0.8,  # Default confidence
                        }
                        
                        if segment_speaker is not None:
                            word_entry["speaker"] = self._normalize_speaker_id(segment_speaker)
                        
                        all_words.append(word_entry)
        
        # Build full transcript
        full_transcript = " ".join(full_transcript_parts)
        
        # Apply formatting if requested
        if smart_format:
            full_transcript = self._apply_smart_formatting(full_transcript)
        
        if punctuate:
            full_transcript = self._apply_punctuation(full_transcript)
        
        # Calculate overall confidence
        confidences = [w.get("confidence", 0.8) for w in all_words]
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0.8
        
        # Generate paragraphs structure
        paragraphs = self._generate_paragraphs(segments, all_words)
        
        # Build channel alternative
        alternative = {
            "transcript": full_transcript,
            "confidence": round(overall_confidence, 3),
            "words": all_words,
            "paragraphs": {
                "transcript": full_transcript,
                "paragraphs": paragraphs
            }
        }
        
        return [{"alternatives": [alternative]}]
    
    def _generate_utterances(self, segments: List[Dict]) -> List[Dict]:
        """Generate Deepgram-style utterances from WhisperX segments."""
        utterances = []
        
        for i, segment in enumerate(segments):
            segment_text = segment.get("text", "").strip()
            if not segment_text:
                continue
            
            segment_start = float(segment.get("start", 0.0))
            segment_end = float(segment.get("end", 0.0))
            segment_speaker = segment.get("speaker")
            
            # Extract words for this segment
            segment_words = []
            if "words" in segment and segment["words"]:
                for word_data in segment["words"]:
                    word_entry = {
                        "word": word_data.get("word", ""),
                        "start": float(word_data.get("start", segment_start)),
                        "end": float(word_data.get("end", segment_end)),
                        "confidence": float(word_data.get("score", word_data.get("confidence", 0.8))),
                    }
                    
                    word_speaker = word_data.get("speaker", segment_speaker)
                    if word_speaker is not None:
                        word_entry["speaker"] = self._normalize_speaker_id(word_speaker)
                    
                    segment_words.append(word_entry)
            
            # Calculate confidence for utterance
            if segment_words:
                confidences = [w.get("confidence", 0.8) for w in segment_words]
                utterance_confidence = sum(confidences) / len(confidences)
            else:
                utterance_confidence = 0.8
            
            utterance = {
                "start": round(segment_start, 3),
                "end": round(segment_end, 3),
                "confidence": round(utterance_confidence, 3),
                "channel": 0,
                "transcript": segment_text,
                "words": segment_words,
                "id": str(uuid.uuid4()),
            }
            
            # Add speaker if available
            if segment_speaker is not None:
                utterance["speaker"] = self._normalize_speaker_id(segment_speaker)
            
            utterances.append(utterance)
        
        return utterances
    
    def _generate_paragraphs(self, segments: List[Dict], all_words: List[Dict]) -> List[Dict]:
        """Generate paragraph structure from segments."""
        paragraphs = []
        current_speaker = None
        current_paragraph = None
        
        for segment in segments:
            segment_text = segment.get("text", "").strip()
            if not segment_text:
                continue
            
            segment_start = float(segment.get("start", 0.0))
            segment_end = float(segment.get("end", 0.0))
            segment_speaker = self._normalize_speaker_id(segment.get("speaker"))
            
            # Check if we need a new paragraph (speaker change)
            if segment_speaker != current_speaker or current_paragraph is None:
                # Finalize current paragraph
                if current_paragraph:
                    paragraphs.append(current_paragraph)
                
                # Start new paragraph
                current_paragraph = {
                    "sentences": [],
                    "speaker": segment_speaker,
                    "num_words": 0,
                    "start": segment_start,
                    "end": segment_end,
                }
                current_speaker = segment_speaker
            
            # Add sentence to current paragraph
            sentence = {
                "text": segment_text,
                "start": segment_start,
                "end": segment_end,
            }
            
            current_paragraph["sentences"].append(sentence)
            current_paragraph["end"] = segment_end
            current_paragraph["num_words"] += len(segment_text.split())
        
        # Add final paragraph
        if current_paragraph:
            paragraphs.append(current_paragraph)
        
        return paragraphs
    
    def _normalize_speaker_id(self, speaker) -> Optional[int]:
        """Convert speaker identifier to integer format."""
        if speaker is None:
            return None
        
        # Handle string speaker IDs (e.g., "SPEAKER_00", "SPEAKER_01")
        if isinstance(speaker, str):
            if speaker.startswith("SPEAKER_"):
                try:
                    return int(speaker.split("_")[1])
                except (IndexError, ValueError):
                    return 0
            # Try direct conversion
            try:
                return int(speaker)
            except ValueError:
                return 0
        
        # Handle numeric speaker IDs
        try:
            return int(speaker)
        except (ValueError, TypeError):
            return 0
