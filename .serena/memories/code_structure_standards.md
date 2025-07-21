# Code Structure and Naming Standards

## Standardized File Structure

### **Schema Organization**
Following domain-driven design principles, all schemas are consolidated in the `app/schemas/` directory:

- **`app/schemas/database.py`** - SQLAlchemy database models (User, TranscriptionJob, etc.)
- **`app/schemas/graph.py`** - Neo4j graph models (Nodes, Relationships, etc.)
- **`app/schemas/api.py`** - FastAPI request/response models (Pydantic models)
- **`app/schemas/__init__.py`** - Package initialization and exports

### **Service Naming Convention**
Following Python naming conventions for consistency:

- **File names**: Descriptive without redundant suffixes
  - ✅ `transcription.py`, `diarization.py`, `graph.py`, `cache.py`
  - ❌ `transcription_service.py`, `graph_service.py`

- **Class names**: Always include "Service" suffix
  - ✅ `TranscriptionService`, `GraphService`, `CacheService`
  - ❌ `TranscriptionHandler`, `GraphManager`

### **Import Patterns**
Standardized import structure for consistency:

```python
# Schema imports
from app.schemas.database import User, TranscriptionJob
from app.schemas.graph import SpeakerNode, TopicNode, GraphService
from app.schemas.api import TranscriptionRequest, GraphStatsResponse

# Service imports
from app.services.transcription import TranscriptionService
from app.services.graph import GraphService
from app.services.cache import CacheService
```

## Directory Structure Standards

### **Current Structure**
```
app/
├── schemas/               # All schema definitions
│   ├── database.py        # SQLAlchemy models
│   ├── graph.py           # Neo4j models
│   ├── api.py             # FastAPI models
│   └── __init__.py        # Package exports
├── services/              # Business logic services
│   ├── transcription.py   # TranscriptionService
│   ├── graph.py           # GraphService
│   ├── cache.py           # CacheService
│   └── diarization.py     # DiarizationService
├── db/                    # Database infrastructure
│   ├── base.py            # SQLAlchemy base
│   ├── session.py         # DB session management
│   └── graph_session.py   # Graph DB session management
└── api/                   # API layer
    └── v1/endpoints/      # API endpoints
```

## Best Practices

### **Schema Separation**
- **Database Models**: Persistent data storage (SQLAlchemy)
- **Graph Models**: Graph database entities (Neo4j)
- **API Models**: Request/response contracts (Pydantic)

### **Service Layer**
- **Single Responsibility**: Each service handles one domain
- **Async/Await**: All service methods are async
- **Dependency Injection**: Services injected via FastAPI dependencies
- **Error Handling**: Comprehensive error handling and logging

### **Testing Standards**
- **Unit Tests**: Test individual service methods
- **Integration Tests**: Test API endpoints and database interactions
- **Mock Strategy**: Mock external dependencies (databases, APIs)
- **Fixtures**: Reusable test data and configurations

### **Code Quality**
- **Type Hints**: All functions and methods have type annotations
- **Docstrings**: All classes and methods have descriptive docstrings
- **Logging**: Comprehensive logging for debugging and monitoring
- **Constants**: Configuration-driven, no hardcoded values

## Python Version Requirements

### **Python 3.12+**
- **Required Version**: Python 3.12 or higher
- **Features Used**: Modern async/await patterns, type hints, and performance improvements
- **Configuration**: Specified in `pyproject.toml` as `requires-python = ">=3.12"`

### **Benefits of Python 3.12**
- **Performance**: Significant improvements in async performance
- **Type System**: Enhanced type checking and inference
- **Error Messages**: Better error messages and debugging
- **Standard Library**: Latest features and security updates

### **Usage Examples**
```python
# Import database schemas
from app.schemas.database import User, TranscriptionJob

# Import graph schemas
from app.schemas.graph import SpeakerNode, NodeType

# Import API schemas
from app.schemas.api import TranscriptionRequest, GraphStatsResponse

# Import services
from app.services.transcription import TranscriptionService
from app.services.graph import GraphService
```

This standardized structure follows industry best practices and ensures consistent, maintainable code organization with modern Python 3.12+ features.
