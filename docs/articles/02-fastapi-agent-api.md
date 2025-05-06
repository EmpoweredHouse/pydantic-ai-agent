# Building an API for Your Pydantic-AI Agent with FastAPI

## Introduction

In the [previous article](01-pydantic-ai-introduction.md), we explored Pydantic-AI as a powerful framework for building AI agents with structured outputs, dependency injection, and built-in evaluation capabilities. We focused on creating a bank support agent that could answer customer questions, check account balances, and block cards when necessary.

This article shows a concrete example of how to build a FastAPI service around a Pydantic-AI agent. We'll walk through the implementation details, show how conversation history is stored in a database, and demonstrate both blocking and streaming response patterns with real code examples.

## Key Ideas

The core ideas behind our API implementation include:

1. **Communication Layer**: Using FastAPI to create a bridge between clients and the Pydantic-AI agent
2. **Conversation History**: Storing threads and messages in a database to maintain context
3. **Dual Interfaces**: Supporting both blocking and streaming response patterns
4. **Simplicity**: Using straightforward approaches to authentication and user identification
5. **Modularity**: Organizing code in a way that separates concerns and improves maintainability

## Architecture Overview

We've organized our codebase following a modular approach:

```
service/
├── main.py                # Application entry point
├── api/                   # API routes and handlers
├── db/                    # Database operations
├── models/                # Data models (API and DB)
├── dependencies/          # FastAPI dependencies
└── middleware/            # HTTP middleware
```

This structure enables a clean separation of concerns, where each component has a single responsibility. Rather than diving into the implementation details of each file, let's explore the key architectural patterns.

## Simplifying Authentication

Instead of implementing a complex authentication system, we've taken a lightweight approach:

1. **API Key Authentication**: A simple middleware checks for a valid API key in request headers, securing the API from unauthorized access.

2. **User Identification via Headers**: Clients provide a user ID in the `X-User-ID` header, delegating user authentication while still allowing thread ownership.

This pragmatic approach works well for internal APIs or microservices architectures where authentication might be handled elsewhere.

## Conversation Management

The API organizes conversations into **threads**, which store a series of messages between the user and the agent. This allows us to:

1. Maintain conversation context over time
2. Associate messages with specific users
3. Pass previous messages to the agent for contextual responses

When a query is sent to the agent, we:
- Validate the thread ID and user ownership
- Retrieve the thread's message history
- Send the query and history to the Pydantic-AI agent
- Store the result back in the database

## Agent Integration

The integration with Pydantic-AI follows a pattern where we:

1. Load conversation history from the database
2. Determine the agent type and select the appropriate agent instance
3. Create agent-specific dependencies
4. Execute the agent with the query, message history, and dependencies
5. Process and store the agent's response

Here's a simplified overview of how we interact with the agent:

```python
# Get the appropriate agent based on thread type
agent_type = AgentType(thread.agent_type)
selected_agent = AGENT_MAP.get(agent_type.value)

# Create agent dependencies
agent_deps = create_agent_dependencies(thread.user_id, agent_type)

# Run the agent with message history
agent_result = await selected_agent.run(
    query, 
    message_history=list(message_history),
    deps=agent_deps
)

# Process and store the response
new_messages = await agent_result.new_messages()
result_message = await save_agent_messages(
    session_factory=session_factory, 
    thread_id=thread.id, 
    model_messages=new_messages,
)
```

For streaming responses, we use a slightly different approach:

```python
# Run the agent in streaming mode
async with selected_agent.run_stream(
    query, 
    message_history=list(message_history),
    deps=agent_deps
) as result:
    # Stream tokens with validation
    async for message, last in result.stream_structured(debounce_by=0.01):
        try:
            profile = await result.validate_structured_output(  
                message,
                allow_partial=not last,
            )
            # Yield the validated token
            yield TextDeltaChunk(message_id=message_id, token=json.dumps(profile))
        except ValidationError:
            continue
```

An important implementation detail is that our agent's output uses TypedDict rather than a Pydantic model:

```python
class SupportOutput(TypedDict, total=False):
    """Structured output for the bank support agent."""
    support_advice: Annotated[str, Field(description='Advice returned to the customer')]
    block_card: Annotated[bool, Field(description="Whether to block the customer's card")]
    risk_level: Annotated[int, Field(description='Risk level of query', ge=0, le=10)]
    follow_up_actions: NotRequired[Annotated[List[str], Field(description='List of follow-up actions to take')]]
```

We use TypedDict for the agent's output specifically to support streaming structured output. Not all types are supported with partial validation in Pydantic, so for model-like structures that need to be built incrementally during streaming, TypedDict is currently the best choice.

## Data Models

Throughout our implementation, we use various models to ensure type safety and data validation. Here's an overview of the key models:

### API Request/Response Models

| Model | Purpose |
|-------|---------|
| `ThreadCreateRequest` | Input for creating a new conversation thread |
| `ThreadResponse` | Output for thread information |
| `ThreadDetailResponse` | Detailed thread info including messages |
| `AgentRequest` | Input for agent queries with thread ID and query text |
| `AgentResponse` | Output from blocking agent queries |

### Streaming Event Models

| Model | Purpose |
|-------|---------|
| `StreamEvent` | Base event type for all streaming events |
| `MessageCreatedChunk` | Signals creation of a new message |
| `MessageStartedChunk` | Indicates agent has started generating a response |
| `TextDeltaChunk` | Contains a token generated by the agent |
| `MessageCompleteChunk` | Signals completion of the full message |
| `DoneEvent` | Indicates the stream has completed |

### Agent Models

| Model | Purpose |
|-------|---------|
| `SupportOutput` (TypedDict) | Structured output from the bank support agent |
| `SupportDependencies` | Dependencies required by the agent |
| `ModelMessage` | Representation of conversation history messages |

### Database Models

| Model | Purpose |
|-------|---------|
| `Thread` | Stores conversation thread information |
| `Message` | Stores individual messages within threads |
| `AgentType` | Enum of supported agent types |

Using Pydantic models throughout the codebase provides strong type checking, automatic validation, and self-documenting code. For the API layer, these models ensure that incoming requests are validated and outgoing responses match the expected format.

## Response Patterns

One of the more interesting aspects of our implementation is the support for two different response patterns:

### Blocking Responses

The `/agent/query` endpoint provides a traditional request-response pattern, where the client waits for the agent to complete its processing before receiving the full response.

### Streaming Responses

The `/agent/stream` endpoint delivers responses incrementally as they're generated, using a streaming response pattern. This provides a more interactive experience, particularly for longer responses.

In our implementation, we've built a structured streaming system that delivers typed events as the agent generates its response:

1. First, we emit a `MessageCreatedChunk` for the user's message
2. Then, a `MessageStartedChunk` to indicate the agent is generating a response
3. As the agent generates content, we emit `TextDeltaChunk` events with tokens
4. Finally, we emit a `MessageCompleteChunk` and `DoneEvent` when generation is complete

This approach allows clients to show real-time feedback while maintaining the structured nature of the agent's response.

## API Response Examples

To better understand how these endpoints work in practice, let's look at some real examples:

### Blocking Response Example

Let's start with creating thread:
```bash
curl -X POST "http://localhost:8000/api/v1/threads" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -H "X-User-ID: $USER_ID" \
  -d '{"agent_type": "bank_support"}'
```

Thread response:
```json
{
    "id":"c68ac24e-4118-4294-ae01-cc549d888d18",
    "user_id":"123e4567-e89b-12d3-a456-426614174000",
    "agent_type":"bank_support",
    "created_at":"2025-05-06T13:38:56",
    "updated_at":"2025-05-06T13:38:56"
}
```

Now ask agent a question:
```bash
curl -X POST "http://localhost:8000/api/v1/agent/query" \
  -H "X-API-Key: $API_KEY" \
  -H "X-User-ID: $USER_ID" \
  -d '{"query": "What is my account balance?", "thread_id": "c68ac24e-4118-4294-ae01-cc549d888d18"}'
```

Response:
```json
{
  "thread_id": "c68ac24e-4118-4294-ae01-cc549d888d18",
  "message_id": "fb0d8cc4-02f5-4a80-b07b-0b5d3221e4bc",
  "response": "{\"support_advice\": \"Your current account balance, including any pending transactions, is $1123.45. If you have any other questions or need further assistance, feel free to ask!\", \"block_card\": false, \"risk_level\": 0, \"follow_up_actions\": []}"
}
```

### Streaming Response Example

```bash
curl -X POST "http://localhost:8000/api/v1/agent/stream" \
  -H "X-API-Key: $API_KEY" \
  -H "X-User-ID: $USER_ID" \
  --no-buffer \
  -d '{"query": "What is my account balance? Respond with poem around 50 words", "thread_id": "c68ac24e-4118-4294-ae01-cc549d888d18"}'
```

The response comes as a series of events:

```json
{"event":"message_created","message":{"id":"1bfdd6e2-e187-48f5-86e8-06b93d6ce230","role":"user"}}
{"event":"message_started","message_id":"a4d03f9f-8375-45e5-9576-4e8deda12cc3"}
{"event":"token","message_id":"a4d03f9f-8375-45e5-9576-4e8deda12cc3","token":"{}"}
{"event":"token","message_id":"a4d03f9f-8375-45e5-9576-4e8deda12cc3","token":"{\"support_advice\": \"In\"}"}
{"event":"token","message_id":"a4d03f9f-8375-45e5-9576-4e8deda12cc3","token":"{\"support_advice\": \"In the realm\"}"}
// ... more tokens as the response builds up
{"event":"token","message_id":"a4d03f9f-8375-45e5-9576-4e8deda12cc3","token":"{\"support_advice\": \"In the realm of digital gold,  \\nYour account's story is softly told.  \\n$1123.45, standing bright,  \\nGlistens in the banking light.  \\nA balance steady, come what may,  \\nGuides your journey every day.\", \"block_card\": false, \"risk_level\": 0, \"follow_up_actions\": []}"}
{"event":"message_complete","message_id":"a4d03f9f-8375-45e5-9576-4e8deda12cc3"}
{"event":"done"}
```

This streaming approach provides immediate feedback to users and better handles long-running requests.

## Exploring the Code

We encourage you to explore the codebase to see the complete implementation. Key files to examine include:

- `api/agent/endpoints.py` - API endpoints for agent queries
- `api/agent/operations.py` - Integration with the Pydantic-AI agent
- `db/database.py` - Database operations

## Running the Application

### Environment Configuration

The application uses environment variables for configuration. Create a `.env` file in the project root with the following variables:

```
# API configuration
API_KEY=your_api_key_here
PROJECT_NAME=Bank Support Agent API
API_V1_STR=/api/v1

# Database configuration
DATABASE_URL=sqlite:///./data/banking_agent.db

# CORS settings (optional)
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# LLM configuration
OPENAI_API_KEY=your_openai_api_key_here
```

Adjust these values according to your environment and requirements.

### Starting the Server

To run the application, use uvicorn with the following command:

```bash
uv run uvicorn src.service.main:app --reload --log-level debug
```
This will start the server with:
- `--reload`: Automatically reload the server when code changes
- `--log-level debug`: Detailed logging for development

Once running, you can access:
- API documentation: http://localhost:8000/docs
- The API endpoints: http://localhost:8000/api/v1/...

## Conclusion

This FastAPI service provides a clean, modular way to expose a Pydantic-AI agent through an API. It maintains conversation history, supports both blocking and streaming responses, and uses simple authentication patterns.

By focusing on modularity, type safety through Pydantic models, and clean interfaces, the code remains maintainable and extensible. We encourage you to adapt these patterns for your own Pydantic-AI agents, or explore our implementation further.

In the next article, we'll build a Streamlit frontend that interacts with this API, providing a user-friendly interface for the bank support agent.

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic-AI Documentation](https://ai.pydantic.dev/)
- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html)
- [Logfire Documentation](https://docs.logfire.dev/) 
