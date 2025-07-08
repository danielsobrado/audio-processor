# Translation Feature Documentation

## Overview

The audio processor now supports translation of transcribed text into different target languages using Hugging Face's transformers library. This feature is configurable and can be enabled/disabled via environment variables.

## Configuration

### Environment Variables

The translation feature is controlled by the following environment variables:

```bash
# Enable/disable translation feature
TRANSLATION_ENABLED=true

# Translation provider (currently only 'huggingface' is supported)
TRANSLATION_PROVIDER=huggingface

# Hugging Face model name for translation
TRANSLATION_MODEL_NAME=Helsinki-NLP/opus-mt-en-es

# Device for translation (cpu or cuda)
TRANSLATION_DEVICE=cpu
```

### Supported Models

The system supports any Hugging Face translation model that works with the `transformers` pipeline. Some popular options:

#### Single Language Pair Models
- **English to Spanish**: `Helsinki-NLP/opus-mt-en-es`
- **English to French**: `Helsinki-NLP/opus-mt-en-fr`
- **English to German**: `Helsinki-NLP/opus-mt-en-de`
- **English to Italian**: `Helsinki-NLP/opus-mt-en-it`
- **Spanish to English**: `Helsinki-NLP/opus-mt-es-en`
- **French to English**: `Helsinki-NLP/opus-mt-fr-en`

#### Multilingual Models
- **Many-to-many**: `facebook/mbart-large-50-many-to-many-mmt`
- **T5-based**: `google/mt5-small`

## API Usage

### Basic Translation Request

To request translation, include the `translate=true` parameter and specify the `target_language`:

```bash
curl -X POST "http://localhost:8000/api/v1/transcribe" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@audio.wav" \
  -F "language=en" \
  -F "translate=true" \
  -F "target_language=es"
```

### URL-based Translation Request

```bash
curl -X POST "http://localhost:8000/api/v1/transcribe" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "audio_url=https://example.com/audio.mp3" \
  -d "language=en" \
  -d "translate=true" \
  -d "target_language=fr"
```

### Parameters

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `translate` | No | Enable translation | `true` or `false` |
| `target_language` | Yes* | Target language code | `es`, `fr`, `de`, etc. |

*Required when `translate=true`

### Response Format

When translation is enabled, the response includes additional translation data in the Deepgram-compatible format:

```json
{
  "request_id": "uuid-here",
  "metadata": {
    "model": "large-v2",
    "language": "en",
    "duration": 45.6,
    "translations": {
      "es": "Hola, este es el texto traducido."
    }
  },
  "results": {
    "channels": [
      {
        "alternatives": [
          {
            "transcript": "Hello, this is the transcribed text.",
            "confidence": 0.95
          }
        ]
      }
    ]
  }
}
```

## Error Handling

### Common Errors

1. **Translation disabled**: HTTP 400 - "Translation feature is currently disabled."
2. **Missing target language**: HTTP 400 - "The 'target_language' parameter is required when 'translate' is set to true."
3. **Model loading failed**: The service will log errors and return the original text without translation.

### Fallback Behavior

If translation fails for any reason (model not loaded, network issues, etc.), the system will:
- Log the error
- Return the original transcribed text
- Continue processing other features (summarization, etc.)
- Not fail the entire transcription job

## Performance Considerations

### Model Loading

- Translation models are loaded once per Celery worker startup
- Initial model loading can take 30-60 seconds depending on model size
- Models are cached in memory for the lifetime of the worker process

### Processing Speed

- **CPU Translation**: Slower but works on any machine
- **GPU Translation**: Much faster with CUDA-enabled GPUs
- **Model Size**: Smaller models (e.g., Helsinki-NLP) are faster than large multilingual models

### Resource Usage

- **Memory**: Translation models typically use 0.5-2GB RAM
- **Disk**: Models are downloaded and cached locally
- **GPU**: CUDA models will use GPU memory if available

## Development and Testing

### Local Testing

1. Install dependencies:
```bash
pip install torch transformers
```

2. Enable translation in your environment:
```bash
export TRANSLATION_ENABLED=true
export TRANSLATION_MODEL_NAME=Helsinki-NLP/opus-mt-en-es
export TRANSLATION_DEVICE=cpu
```

3. Run the test script:
```bash
python scripts/test_translation.py
```

### Unit Tests

Run the translation-specific tests:

```bash
pytest tests/unit/test_translation_service.py -v
pytest tests/integration/test_transcription_translation.py -v
```

### Integration Testing

The integration tests include:
- API endpoint validation
- Parameter validation
- Error handling
- Response format verification

## Production Deployment

### Docker Configuration

Add translation dependencies to your Dockerfile:

```dockerfile
RUN pip install torch transformers
```

### Environment Configuration

Set environment variables in your production environment:

```yaml
# docker-compose.yml
environment:
  - TRANSLATION_ENABLED=true
  - TRANSLATION_MODEL_NAME=Helsinki-NLP/opus-mt-en-es
  - TRANSLATION_DEVICE=cpu
```

### Kubernetes Configuration

```yaml
# deployment.yaml
env:
- name: TRANSLATION_ENABLED
  value: "true"
- name: TRANSLATION_MODEL_NAME
  value: "Helsinki-NLP/opus-mt-en-es"
- name: TRANSLATION_DEVICE
  value: "cpu"
```

### Performance Tuning

1. **GPU Usage**: Set `TRANSLATION_DEVICE=cuda` if GPUs are available
2. **Model Selection**: Choose appropriate models for your language pairs
3. **Worker Scaling**: Consider model memory usage when scaling workers
4. **Caching**: Models are automatically cached locally

## Monitoring and Logging

### Log Messages

The translation service logs important events:

```
INFO: TranslationService initialized with model 'Helsinki-NLP/opus-mt-en-es' on device 'cpu'
INFO: Loading translation model: Helsinki-NLP/opus-mt-en-es...
INFO: Translation model loaded successfully.
INFO: Translating transcript to 'es'...
```

### Error Monitoring

Monitor these error patterns:
- Model loading failures
- Translation timeout errors
- Memory allocation errors
- CUDA device errors

### Metrics

Consider tracking:
- Translation success rate
- Translation latency
- Model loading time
- Memory usage per worker

## Troubleshooting

### Common Issues

1. **Model not loading**
   - Check internet connectivity for model download
   - Verify model name is correct
   - Check available disk space

2. **CUDA errors**
   - Verify CUDA installation
   - Check GPU memory availability
   - Fall back to CPU if needed

3. **Translation quality issues**
   - Try different models for your language pair
   - Check source language detection accuracy
   - Consider multilingual models for better coverage

4. **Performance issues**
   - Use GPU acceleration when available
   - Choose smaller, faster models
   - Monitor worker memory usage

### Getting Help

1. Check logs for specific error messages
2. Run the test script to verify configuration
3. Test with different models if translation quality is poor
4. Monitor resource usage during processing
