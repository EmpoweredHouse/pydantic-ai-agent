# Problem Discovery Agent API

FastAPI backend for the Problem Discovery Agent application providing agent functionality through RESTful endpoints.

## Architecture & Directory Structure

```
src/service/
  ├── api/               # API endpoint definitions (primary implementation)
  │   ├── __init__.py    # Main API router
  │   ├── agent.py       # Agent-related endpoints
  │   ├── health.py      # Health check endpoint
  │   └── threads.py     # Thread-related endpoints
  │
  ├── core/              # Core business logic
  │   ├── agent_operations.py   # Core agent implementation
  │   ├── agent_handlers.py     # Agent request handlers
  │   ├── database.py           # Database operations
  │   ├── settings.py           # Application settings
  │   └── thread_handlers.py    # Thread request handlers
  │
  ├── db/                # Database configuration
  │   ├── base.py        # Base models and initialization
  │   └── session.py     # Database session utilities
  │
  ├── dependencies/      # FastAPI dependencies
  │   └── auth.py        # Authentication dependencies
  │
  ├── models/            # Data models (two-layer architecture)
  │   ├── api/           # API models (request/response validation)
  │   │   ├── agent_models.py    # Agent models
  │   │   ├── message_models.py  # Message models
  │   │   ├── thread_models.py   # Thread models
  │   │   ├── stream_models.py   # Streaming response models
  │   │   └── internal.py        # Internal shared models
  │   └── database/      # Database models (ORM)
  │       ├── thread.py  # Thread database model
  │       └── message.py # Message database model
  │
  └── main.py            # FastAPI application factory
```

### Design Principles

1. **Two-Layer Architecture**:
   - API Models (Pydantic): For request/response validation
   - Database Models (SQLAlchemy): For persistence 
   - Direct conversion between layers without intermediaries

2. **Separation of Concerns**:
   - API endpoints in `api/` directory
   - Business logic in `core/` directory
   - Data models in `models/` directory

3. **Clean API Structure**:
   - Each router in its own file
   - Routes delegate to handlers in `core/`
   - API routers combined in `api/__init__.py`

4. **Handler Layer**:
   - `agent_operations.py`: Core agent functionality
   - `agent_handlers.py`: Agent API request handlers
   - `thread_handlers.py`: Thread API request handlers

## Features

- Thread management for agent conversations
- User-specific conversation threads
- Agent interaction API with streaming support
- Cloud-based PostgreSQL storage
- API key authentication

## Setup

### Prerequisites

- Python 3.12+
- Access to Google Cloud SQL PostgreSQL instance
- UV tool for dependency management

### Installation

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Set up Google Cloud SQL connection:
   - Ensure you have the necessary permissions to connect to the GCP SQL server
   - Set the connection parameters in your .env file

3. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Update the values with your actual credentials and settings

### Running the API

For development:
```bash
uvicorn src.service.main:app --reload --log-level debug
```

The API will be available at http://localhost:8000 with documentation at http://localhost:8000/docs

## API Design

Authentication has two layers:
1. **API-level**: `X-API-Key` header for application authentication
2. **User identification**: User IDs passed as parameters for user context

## API Endpoints

All endpoints require the `X-API-Key` header.

### Endpoint Overview

- **Threads**
  - GET `/api/v1/threads?user_id={user_id}` - List user's threads
  - POST `/api/v1/threads` - Create new thread
  - GET `/api/v1/threads/{thread_id}?user_id={user_id}` - Get thread details

- **Agent**
  - POST `/api/v1/agent/query` - Blocking request for complete response
  - POST `/api/v1/agent/stream` - Streaming request for real-time tokens

### Response Types

1. **Blocking Response** (`/api/v1/agent/query`):
   - Returns when processing is complete
   - Format:
     ```json
     {
       "thread_id": "uuid-string",
       "response": "Complete agent response text",
       "message_id": "uuid-string"
     }
     ```

2. **Streaming Response** (`/api/v1/agent/stream`):
   - Server-Sent Events format
   - Real-time incremental updates
   - Event types: `thread_created`, `message_created`, `message_started`, `token`, `message_complete`, `error`, `done`

## Example Usage

```bash
# List threads for a user
curl -X GET "http://localhost:8000/api/v1/threads?user_id=123e4567-e89b-12d3-a456-426614174000" \
     -H "X-API-Key: your_api_key_here"

# Send a query with blocking response
curl -X POST "http://localhost:8000/api/v1/agent/query" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your_api_key_here" \
     -d '{"query": "What is the meaning of life?", "user_id": "123e4567-e89b-12d3-a456-426614174000"}'

# Stream a query with incremental responses
curl -X POST "http://localhost:8000/api/v1/agent/stream" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your_api_key_here" \
     --no-buffer \
     -d '{"query": "What is the meaning of life?", "user_id": "123e4567-e89b-12d3-a456-426614174000"}'
```

## Adding New Endpoints

To add a new endpoint:
1. Create a handler function in the appropriate handlers file
2. Add the endpoint to the appropriate router in the `api/` directory
3. Update the API router in `api/__init__.py` if needed

## Database Configuration

The service has been updated to use SQLite for simplicity.

### SQLite Support

SQLite is implemented with the following features:
- Async SQLite support via `aiosqlite`
- Clean database adapters
- Thread and Message models for storing conversations

### Configuration

Configure the SQLite database path in your `.env` file:
```
DB_PATH=./sqlite.db
```

### Required Dependencies

For SQLite async support, add the following to your requirements.txt:
```
aiosqlite>=0.19.0
```

### Database Adapters

The implementation uses specialized database adapters:

- `SQLiteAdapter`: Base adapter for SQLite operations
- `MessageAdapter`: Specific adapter for Message model
- `ThreadAdapter`: Specific adapter for Thread model

### Usage

```python
from src.service.db.session import get_db
from src.service.db.adapters import message_adapter, thread_adapter

# In FastAPI endpoint
@router.get("/threads/{thread_id}/messages")
async def get_messages(thread_id: str, db: AsyncSession = Depends(get_db)):
    messages = await message_adapter.get_messages_by_thread_id(thread_id, db)
    return [message_adapter.get_message_content(message) for message in messages]
```