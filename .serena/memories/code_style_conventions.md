# Code Style and Conventions

## Type Hints
- **Required everywhere** - all functions, methods, and variables
- Follow FastAPI patterns: `def create_application() -> FastAPI:`
- Use `Optional[Type]` for nullable values
- Import types from `typing` module: `List[str]`, `Dict[str, Any]`

## Docstrings
- **Triple quotes** for all functions and classes
- **Google/NumPy style** with Args/Returns sections:
```python
def submit_transcription_job(
    self,
    request: TranscriptionRequest,
    audio_file: Optional[UploadFile] = None,
) -> str:
    """
    Submit a new transcription job.

    Args:
        request: The transcription request model.
        audio_file: The uploaded audio file, if any.

    Returns:
        The request ID of the created job.
    """
```

## Naming Conventions
- **snake_case** for variables, functions, files
- **PascalCase** for classes
- **UPPER_CASE** for constants
- **Descriptive names**: `submit_transcription_job`, `validate_environment`

## Configuration Pattern
- **Pydantic BaseSettings** for all configuration
- **Environment variables** with Field() mapping
- **Validators** for data validation and parsing
- **Nested configuration classes** for organization
- **Feature flags** for optional functionality

## Error Handling
- **Comprehensive logging** with context
- **Try/catch with cleanup** in service methods
- **Structured error responses**
- **Exception chaining** with `exc_info=True`

## Async Patterns
- **async/await** throughout the application
- **Async database sessions**
- **Background task submission** with Celery
- **Async file operations**
