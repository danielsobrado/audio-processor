# Code Structure and Naming Standards

## Standardized File Structure

### **Models Organization**
Following domain-driven design principles, all models are consolidated in the `app/models/` directory:

- **`app/models/database.py`** - SQLAlchemy database models (User, TranscriptionJob, etc.)
- **`app/models/graph.py`** - Neo4j graph models (Nodes, Relationships, etc.)
- **`app/models/api.py`** - FastAPI request/response models (Pydantic models)
- **`app/models/__init__.py`** - Package initialization and exports

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
# Models imports
from app.models.database import User, TranscriptionJob
from app.models.graph import SpeakerNode, TopicNode, GraphService
from app.models.api import TranscriptionRequest, GraphStatsResponse

# Service imports
from app.services.transcription import TranscriptionService
from app.services.graph import GraphService
from app.services.cache import CacheService
```

## Directory Structure Standards

### **Current Structure**
```
app/
├── models/                 # All model definitions
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
│   └── neo4j_session.py   # Neo4j session management
└── api/                   # API layer
    └── v1/endpoints/      # API endpoints
```

### **Migration from Old Structure**
**Files Moved:**
- `app/db/models.py` → `app/models/database.py`
- `app/db/neo4j_models.py` → `app/models/graph.py`
- `app/models/responses.py` → `app/models/api.py`
- `app/services/graph_service.py` → `app/services/graph.py`

**Import Updates:**
- `from app.db.models import` → `from app.models.database import`
- `from app.db.neo4j_models import` → `from app.models.graph import`
- `from app.services.graph_service import` → `from app.services.graph import`

## Best Practices

### **Model Separation**
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

## Migration Checklist

### **Completed**
- ✅ Created standardized model structure
- ✅ Renamed service files to follow convention
- ✅ Updated import statements
- ✅ Created comprehensive API models
- ✅ Maintained backward compatibility

### **Benefits**
- **Consistency**: All services follow same naming pattern
- **Clarity**: Clear separation of concerns
- **Maintainability**: Easy to find and update code
- **Scalability**: Structure supports growth
- **Developer Experience**: Intuitive organization

### **Usage Examples**
```python
# Import database models
from app.models.database import User, TranscriptionJob

# Import graph models
from app.models.graph import SpeakerNode, NodeType

# Import API models
from app.models.api import TranscriptionRequest, GraphStatsResponse

# Import services
from app.services.transcription import TranscriptionService
from app.services.graph import GraphService
```

This standardized structure follows industry best practices and ensures consistent, maintainable code organization.
