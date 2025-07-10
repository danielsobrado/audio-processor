# PowerShell script to set up OpenRouter environment variables for LLM-based processing
Write-Host "Setting up OpenRouter LLM environment variables..." -ForegroundColor Green

# Basic OpenRouter configuration
$env:GRAPH_LLM_PROVIDER = "openrouter"
$env:GRAPH_LLM_MODEL = "openai/gpt-3.5-turbo"
$env:GRAPH_ENABLED = "true"

# Enable all LLM-based processing methods
$env:GRAPH_ENTITY_EXTRACTION_METHOD = "llm_based"
$env:GRAPH_TOPIC_EXTRACTION_METHOD = "llm_based"
$env:GRAPH_SENTIMENT_ANALYSIS_ENABLED = "true"
$env:GRAPH_RELATIONSHIP_EXTRACTION_METHOD = "llm_based"

# LLM parameters
$env:GRAPH_LLM_MAX_TOKENS = "1000"
$env:GRAPH_LLM_TEMPERATURE = "0.1"
$env:GRAPH_LLM_BATCH_SIZE = "5"

# Graph database configuration
$env:GRAPH_DATABASE_TYPE = "neo4j"
$env:GRAPH_DATABASE_URL = "bolt://localhost:7687"
$env:GRAPH_DATABASE_USERNAME = "neo4j"
$env:GRAPH_DATABASE_PASSWORD = "password"

# Application settings
$env:DEBUG = "true"
$env:ENVIRONMENT = "development"
$env:LOG_LEVEL = "INFO"

Write-Host "Environment variables set successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "NOTE: You still need to set your OpenRouter API key:" -ForegroundColor Yellow
Write-Host "`$env:OPENROUTER_API_KEY = 'your-api-key-here'" -ForegroundColor Yellow
Write-Host ""
Write-Host "Current environment variables set:" -ForegroundColor Cyan
Write-Host "  GRAPH_LLM_PROVIDER: $env:GRAPH_LLM_PROVIDER" -ForegroundColor White
Write-Host "  GRAPH_LLM_MODEL: $env:GRAPH_LLM_MODEL" -ForegroundColor White
Write-Host "  GRAPH_ENABLED: $env:GRAPH_ENABLED" -ForegroundColor White
Write-Host ""
Write-Host "Then you can run the tests:" -ForegroundColor Cyan
Write-Host "  python verify_openrouter_config.py" -ForegroundColor Cyan
Write-Host "  python test_openrouter_config.py" -ForegroundColor Cyan
Write-Host "  python test_llm_graph_advanced.py" -ForegroundColor Cyan
