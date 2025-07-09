"""
Core audio processing with WhisperX integration.
Handles transcription, diarization, alignment, and translation.
"""

import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import torch
import whisperx
from pyannote.audio import Pipeline

from app.config.settings import get_settings
from app.utils.audio_utils import convert_audio_format, get_audio_duration
from app.utils.error_handlers import AudioProcessingError

logger = logging.getLogger(__name__)
settings = get_settings()


class AudioProcessor:
    """
    Main audio processing class integrating WhisperX pipeline.
    Handles model loading, transcription, alignment, and diarization.
    """

    def __init__(self):
        self.device = settings.whisperx.device
        self.compute_type = settings.whisperx.compute_type
        self.batch_size = settings.whisperx.batch_size

        # Model instances
        self.whisper_model = None
        self.alignment_model = None
        self.alignment_metadata = None
        self.diarization_pipeline = None

        # Supported languages for alignment
        self.alignment_languages = {
            "en",
            "fr",
            "de",
            "es",
            "it",
            "ja",
            "zh",
            "nl",
            "uk",
            "pt",
        }

        logger.info(f"AudioProcessor initialized with device: {self.device}")

    async def initialize_models(self) -> None:
        """
        Initialize all required models.
        TODO: Implement model caching and lazy loading.
        """
        try:
            logger.info("Loading WhisperX transcription model...")
            await self._load_whisper_model()

            logger.info("Loading speaker diarization model...")
            await self._load_diarization_model()

            logger.info("All models loaded successfully")

        except Exception as e:
            logger.error(f"Model initialization failed: {e}")
            raise AudioProcessingError(f"Failed to initialize models: {e}")

    async def _load_whisper_model(self) -> None:
        """Load WhisperX transcription model."""
        try:
            self.whisper_model = whisperx.load_model(
                settings.whisperx.model_size,
                device=self.device,
                compute_type=self.compute_type,
                language=None,  # Will be detected per audio
            )
        except Exception as e:
            raise AudioProcessingError(f"Failed to load Whisper model: {e}")

    async def _load_diarization_model(self) -> None:
        """Load pyannote speaker diarization model."""
        try:
            if settings.diarization.use_auth_token:
                self.diarization_pipeline = Pipeline.from_pretrained(
                    settings.diarization.model_name,
                    use_auth_token=settings.diarization.use_auth_token,
                )
            else:
                self.diarization_pipeline = Pipeline.from_pretrained(
                    settings.diarization.model_name,
                )

            # Move to specified device
            if self.device == "cuda" and torch.cuda.is_available():
                self.diarization_pipeline = self.diarization_pipeline.to(
                    torch.device("cuda")
                )

        except Exception as e:
            raise AudioProcessingError(f"Failed to load diarization model: {e}")

    async def _load_alignment_model(self, language: str) -> None:
        """Load alignment model for specific language."""
        if language not in self.alignment_languages:
            logger.warning(f"Alignment not supported for language: {language}")
            self.alignment_model = None
            self.alignment_metadata = None
            return

        try:
            self.alignment_model, self.alignment_metadata = whisperx.load_align_model(
                language_code=language,
                device=self.device,
            )
        except Exception as e:
            logger.error(f"Failed to load alignment model for {language}: {e}")
            self.alignment_model = None
            self.alignment_metadata = None

    async def process_audio(
        self,
        audio_path: Path,
        language: str = "auto",
        diarize: bool = True,
        align: bool = True,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None,
    ) -> Dict:
        """
        Process audio file through complete WhisperX pipeline.

        Args:
            audio_path: Path to audio file
            language: Language code or "auto" for detection
            diarize: Perform speaker diarization
            align: Perform word-level alignment
            min_speakers: Minimum number of speakers for diarization
            max_speakers: Maximum number of speakers for diarization

        Returns:
            Dictionary containing transcription results
        """
        if not self.whisper_model:
            raise AudioProcessingError("Whisper model not loaded")

        try:
            logger.info(f"Processing audio: {audio_path}")

            # Convert audio to required format
            converted_path = await self._prepare_audio(audio_path)

            # Load audio
            audio = whisperx.load_audio(str(converted_path))
            duration = get_audio_duration(converted_path)

            logger.info(f"Audio loaded: {duration:.2f}s")

            # Step 1: Transcription
            logger.info("Starting transcription...")
            result = self.whisper_model.transcribe(
                audio,
                batch_size=self.batch_size,
                language=None if language == "auto" else language,
            )

            detected_language = result.get("language", language)
            logger.info(
                f"Transcription complete. Detected language: {detected_language}"
            )

            # Step 2: Word-level alignment
            if align and detected_language in self.alignment_languages:
                logger.info("Starting word alignment...")

                # Load alignment model if needed
                if not self.alignment_model or (
                    self.alignment_metadata
                    and self.alignment_metadata.get("language") != detected_language
                ):
                    await self._load_alignment_model(detected_language)

                if self.alignment_model:
                    result = whisperx.align(
                        result["segments"],
                        self.alignment_model,
                        self.alignment_metadata,
                        audio,
                        self.device,
                        return_char_alignments=settings.whisperx.return_char_alignments,
                    )
                    logger.info("Word alignment complete")
                else:
                    logger.warning("Alignment model not available, skipping alignment")

            # Step 3: Speaker diarization
            diarization_result = None
            if diarize and self.diarization_pipeline:
                logger.info("Starting speaker diarization...")

                diarization_result = self.diarization_pipeline(
                    str(converted_path),
                    min_speakers=min_speakers or settings.diarization.min_speakers,
                    max_speakers=max_speakers or settings.diarization.max_speakers,
                )

                # Assign speakers to segments
                result = whisperx.assign_word_speakers(
                    diarization_result,
                    result,
                )
                logger.info("Speaker diarization complete")

            # Cleanup temporary file
            if converted_path != audio_path:
                converted_path.unlink(missing_ok=True)

            # Prepare final result
            final_result = {
                "segments": result.get("segments", []),
                "language": detected_language,
                "duration": duration,
                "word_count": self._count_words(result.get("segments", [])),
                "speaker_count": self._count_speakers(result.get("segments", [])),
                "diarization_enabled": diarize and diarization_result is not None,
                "alignment_enabled": align and self.alignment_model is not None,
            }

            logger.info(
                f"Audio processing complete: {final_result['word_count']} words, "
                f"{final_result['speaker_count']} speakers"
            )

            return final_result

        except Exception as e:
            logger.error(f"Audio processing failed: {e}", exc_info=True)
            raise AudioProcessingError(f"Audio processing failed: {e}")

    async def _prepare_audio(self, audio_path: Path) -> Path:
        """
        Prepare audio file for processing.
        Converts to WAV format if needed.
        """
        # Check if file exists
        if not audio_path.exists():
            raise AudioProcessingError(f"Audio file not found: {audio_path}")

        # Check file size
        file_size = audio_path.stat().st_size
        if file_size > settings.max_file_size:
            raise AudioProcessingError(
                f"File too large: {file_size} bytes (max: {settings.max_file_size})"
            )

        # Check if conversion is needed
        if audio_path.suffix.lower() == ".wav":
            return audio_path

        # Convert to WAV format
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = Path(temp_file.name)

            await convert_audio_format(audio_path, temp_path, target_format="wav")
            logger.debug(f"Audio converted from {audio_path.suffix} to WAV")

            return temp_path

        except Exception as e:
            raise AudioProcessingError(f"Audio conversion failed: {e}")

    def _count_words(self, segments: List[Dict]) -> int:
        """Count total words in segments."""
        total_words = 0
        for segment in segments:
            if "words" in segment:
                total_words += len(segment["words"])
            elif "text" in segment:
                total_words += len(segment["text"].split())
        return total_words

    def _count_speakers(self, segments: List[Dict]) -> int:
        """Count unique speakers in segments."""
        speakers = set()
        for segment in segments:
            if "speaker" in segment and segment["speaker"] is not None:
                speakers.add(segment["speaker"])
        return len(speakers)

    async def transcribe_with_timestamps(
        self,
        audio_path: Path,
        language: str = "auto",
    ) -> List[Dict]:
        """
        Simplified transcription with timestamps only.
        Faster processing without alignment or diarization.
        """
        if not self.whisper_model:
            raise AudioProcessingError("Whisper model not loaded")

        try:
            # Convert audio if needed
            converted_path = await self._prepare_audio(audio_path)

            # Load and transcribe audio
            audio = whisperx.load_audio(str(converted_path))
            result = self.whisper_model.transcribe(
                audio,
                batch_size=self.batch_size,
                language=None if language == "auto" else language,
            )

            # Cleanup
            if converted_path != audio_path:
                converted_path.unlink(missing_ok=True)

            return result.get("segments", [])

        except Exception as e:
            logger.error(f"Fast transcription failed: {e}")
            raise AudioProcessingError(f"Transcription failed: {e}")

    async def detect_language(self, audio_path: Path) -> Tuple[str, float]:
        """
        Detect language of audio file.

        Returns:
            Tuple of (language_code, confidence)
        """
        if not self.whisper_model:
            raise AudioProcessingError("Whisper model not loaded")

        try:
            # Convert audio if needed
            converted_path = await self._prepare_audio(audio_path)

            # Load audio (first 30 seconds for detection)
            audio = whisperx.load_audio(str(converted_path))
            if len(audio) > 30 * 16000:  # 30 seconds at 16kHz
                audio = audio[: 30 * 16000]

            # Detect language
            result = self.whisper_model.transcribe(
                audio,
                batch_size=1,
                language=None,
            )

            # Cleanup
            if converted_path != audio_path:
                converted_path.unlink(missing_ok=True)

            language = result.get("language", "unknown")

            # WhisperX doesn't provide confidence scores directly
            # Use segment length as proxy for confidence
            segments = result.get("segments", [])
            confidence = min(1.0, len(segments) / 10.0) if segments else 0.0

            return language, confidence

        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            raise AudioProcessingError(f"Language detection failed: {e}")

    async def get_audio_info(self, audio_path: Path) -> Dict:
        """
        Get basic information about audio file.
        """
        try:
            duration = get_audio_duration(audio_path)
            file_size = audio_path.stat().st_size

            # Basic format detection
            format_info = {
                "format": audio_path.suffix.lower().lstrip("."),
                "duration": duration,
                "file_size": file_size,
            }

            # Try to get more detailed info with librosa
            try:
                import librosa

                y, sr = librosa.load(str(audio_path), sr=None)
                format_info.update(
                    {
                        "sample_rate": sr,
                        "channels": 1 if y.ndim == 1 else y.shape[0],
                        "samples": len(y) if y.ndim == 1 else y.shape[1],
                    }
                )
            except ImportError:
                logger.debug("librosa not available for detailed audio info")
            except Exception as e:
                logger.debug(f"Failed to get detailed audio info: {e}")

            return format_info

        except Exception as e:
            raise AudioProcessingError(f"Failed to get audio info: {e}")

    async def validate_audio_quality(self, audio_path: Path) -> Dict:
        """
        Validate audio quality for optimal transcription.

        Returns:
            Dictionary with quality metrics and recommendations
        """
        try:
            info = await self.get_audio_info(audio_path)

            quality_report = {
                "duration": info["duration"],
                "file_size": info["file_size"],
                "recommendations": [],
                "warnings": [],
            }

            # Duration checks
            if info["duration"] < 1.0:
                quality_report["warnings"].append("Audio is very short (< 1s)")
            elif info["duration"] > 3600:  # 1 hour
                quality_report["warnings"].append(
                    "Audio is very long (> 1h), consider splitting"
                )

            # File size checks
            if info["file_size"] > settings.max_file_size * 0.8:
                quality_report["warnings"].append(
                    "Large file size may cause processing delays"
                )

            # Sample rate checks (if available)
            if "sample_rate" in info:
                sr = info["sample_rate"]
                if sr < 16000:
                    quality_report["recommendations"].append(
                        f"Low sample rate ({sr}Hz), consider resampling to 16kHz+"
                    )
                elif sr > 48000:
                    quality_report["recommendations"].append(
                        f"High sample rate ({sr}Hz), can downsample to save processing time"
                    )

            return quality_report

        except Exception as e:
            logger.error(f"Audio quality validation failed: {e}")
            return {
                "duration": 0,
                "file_size": 0,
                "recommendations": [],
                "warnings": ["Could not analyze audio quality"],
            }

    async def cleanup(self) -> None:
        """Cleanup resources and models."""
        try:
            # Clear model references
            self.whisper_model = None
            self.alignment_model = None
            self.alignment_metadata = None
            self.diarization_pipeline = None

            # Clear CUDA cache if using GPU
            if self.device == "cuda" and torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.info("AudioProcessor cleanup complete")

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


# Utility functions for audio processing


async def estimate_processing_time(audio_duration: float, options: Dict) -> float:
    """
    Estimate processing time based on audio duration and options.

    Args:
        audio_duration: Duration in seconds
        options: Processing options (diarize, align, etc.)

    Returns:
        Estimated processing time in seconds
    """
    # Base transcription time (real-time factor)
    base_factor = 0.1  # 10% of audio duration for transcription

    # Additional time for processing steps
    factors = {
        "diarize": 0.15,  # 15% additional for diarization
        "align": 0.05,  # 5% additional for alignment
        "translate": 0.02,  # 2% additional for translation
        "summarize": 0.03,  # 3% additional for summarization
    }

    total_factor = base_factor
    for option, factor in factors.items():
        if options.get(option, False):
            total_factor += factor

    # Add base overhead
    estimated_time = max(5.0, audio_duration * total_factor + 2.0)

    return estimated_time


def get_supported_languages() -> List[Dict[str, str]]:
    """Get list of supported languages for transcription."""
    # WhisperX supported languages
    languages = [
        {"code": "auto", "name": "Auto-detect"},
        {"code": "en", "name": "English"},
        {"code": "zh", "name": "Chinese"},
        {"code": "de", "name": "German"},
        {"code": "es", "name": "Spanish"},
        {"code": "ru", "name": "Russian"},
        {"code": "ko", "name": "Korean"},
        {"code": "fr", "name": "French"},
        {"code": "ja", "name": "Japanese"},
        {"code": "pt", "name": "Portuguese"},
        {"code": "tr", "name": "Turkish"},
        {"code": "pl", "name": "Polish"},
        {"code": "ca", "name": "Catalan"},
        {"code": "nl", "name": "Dutch"},
        {"code": "ar", "name": "Arabic"},
        {"code": "sv", "name": "Swedish"},
        {"code": "it", "name": "Italian"},
        {"code": "id", "name": "Indonesian"},
        {"code": "hi", "name": "Hindi"},
        {"code": "fi", "name": "Finnish"},
        {"code": "vi", "name": "Vietnamese"},
        {"code": "he", "name": "Hebrew"},
        {"code": "uk", "name": "Ukrainian"},
        {"code": "el", "name": "Greek"},
        {"code": "ms", "name": "Malay"},
        {"code": "cs", "name": "Czech"},
        {"code": "ro", "name": "Romanian"},
        {"code": "da", "name": "Danish"},
        {"code": "hu", "name": "Hungarian"},
        {"code": "ta", "name": "Tamil"},
        {"code": "no", "name": "Norwegian"},
        {"code": "th", "name": "Thai"},
        {"code": "ur", "name": "Urdu"},
        {"code": "hr", "name": "Croatian"},
        {"code": "bg", "name": "Bulgarian"},
        {"code": "lt", "name": "Lithuanian"},
        {"code": "la", "name": "Latin"},
        {"code": "mi", "name": "Maori"},
        {"code": "ml", "name": "Malayalam"},
        {"code": "cy", "name": "Welsh"},
        {"code": "sk", "name": "Slovak"},
        {"code": "te", "name": "Telugu"},
        {"code": "fa", "name": "Persian"},
        {"code": "lv", "name": "Latvian"},
        {"code": "bn", "name": "Bengali"},
        {"code": "sr", "name": "Serbian"},
        {"code": "az", "name": "Azerbaijani"},
        {"code": "sl", "name": "Slovenian"},
        {"code": "kn", "name": "Kannada"},
        {"code": "et", "name": "Estonian"},
        {"code": "mk", "name": "Macedonian"},
        {"code": "br", "name": "Breton"},
        {"code": "eu", "name": "Basque"},
        {"code": "is", "name": "Icelandic"},
        {"code": "hy", "name": "Armenian"},
        {"code": "ne", "name": "Nepali"},
        {"code": "mn", "name": "Mongolian"},
        {"code": "bs", "name": "Bosnian"},
        {"code": "kk", "name": "Kazakh"},
        {"code": "sq", "name": "Albanian"},
        {"code": "sw", "name": "Swahili"},
        {"code": "gl", "name": "Galician"},
        {"code": "mr", "name": "Marathi"},
        {"code": "pa", "name": "Punjabi"},
        {"code": "si", "name": "Sinhala"},
        {"code": "km", "name": "Khmer"},
        {"code": "sn", "name": "Shona"},
        {"code": "yo", "name": "Yoruba"},
        {"code": "so", "name": "Somali"},
        {"code": "af", "name": "Afrikaans"},
        {"code": "oc", "name": "Occitan"},
        {"code": "ka", "name": "Georgian"},
        {"code": "be", "name": "Belarusian"},
        {"code": "tg", "name": "Tajik"},
        {"code": "sd", "name": "Sindhi"},
        {"code": "gu", "name": "Gujarati"},
        {"code": "am", "name": "Amharic"},
        {"code": "yi", "name": "Yiddish"},
        {"code": "lo", "name": "Lao"},
        {"code": "uz", "name": "Uzbek"},
        {"code": "fo", "name": "Faroese"},
        {"code": "ht", "name": "Haitian Creole"},
        {"code": "ps", "name": "Pashto"},
        {"code": "tk", "name": "Turkmen"},
        {"code": "nn", "name": "Nynorsk"},
        {"code": "mt", "name": "Maltese"},
        {"code": "sa", "name": "Sanskrit"},
        {"code": "lb", "name": "Luxembourgish"},
        {"code": "my", "name": "Myanmar"},
        {"code": "bo", "name": "Tibetan"},
        {"code": "tl", "name": "Tagalog"},
        {"code": "mg", "name": "Malagasy"},
        {"code": "as", "name": "Assamese"},
        {"code": "tt", "name": "Tatar"},
        {"code": "haw", "name": "Hawaiian"},
        {"code": "ln", "name": "Lingala"},
        {"code": "ha", "name": "Hausa"},
        {"code": "ba", "name": "Bashkir"},
        {"code": "jw", "name": "Javanese"},
        {"code": "su", "name": "Sundanese"},
    ]

    return languages
