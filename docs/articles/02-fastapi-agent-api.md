# Building an API for Your Pydantic-AI Agent with FastAPI

## Introduction

After getting our Pydantic-AI agent working in the console, I faced a familiar challenge: how do I expose this to users? While a command-line interface works for development, real users need something more accessible. This is where FastAPI comes in.

In the [previous article](01-pydantic-ai-introduction.md), we built a bank support agent with structured outputs and dependency injection. Now, we'll take that agent and wrap it in a proper API service that handles conversation history, provides both blocking and streaming endpoints, and follows best practices for production deployment.

What surprised me most about this integration was how naturally Pydantic-AI and FastAPI fit together. Both use Pydantic for validation, both leverage async/await for performance, and both emphasize type safety. It's almost as if they were designed to work together—which makes sense given their shared heritage.

## Key Ideas

When designing this API, I wanted to keep a few core principles in mind:

1. **Keep It Simple**: Avoid overengineering; focus on a clean, functional API
2. **Maintain Context**: Store conversation history to provide continuity
3. **Dual Response Patterns**: Support both blocking and streaming for different client needs
4. **Pragmatic Authentication**: Use a lightweight approach suitable for internal or microservice architectures
5. **Modular Design**: Organize code to make maintenance and extension straightforward

Let me walk you through how these principles shaped the implementation.

## Architecture Overview

After some experimentation, I settled on this modular structure for the codebase:

```
service/
├── main.py                # Application entry point
├── api/                   # API routes and handlers
├── db/                    # Database operations
├── models/                # Data models (API and DB)
├── dependencies/          # FastAPI dependencies
└── middleware/            # HTTP middleware
```

This organization provides clear separation of concerns, with each component focused on a specific responsibility. I've found this structure scales well as applications grow—what starts as a simple demo can evolve into a complex service without major restructuring.

## Simplifying Authentication

Authentication is an area where it's easy to overengineer. For this implementation, I chose a pragmatic approach for the sake of simplicity:

1. **API Key Authentication**: A simple middleware checks for a valid API key in request headers, securing the API from unauthorized access.

2. **User Identification via Headers**: Clients provide a user ID in the `X-User-ID` header, delegating user authentication while still allowing thread ownership.

This approach works surprisingly well for internal services, microservices architectures, or systems where authentication is handled by an API gateway. It's one of those "just enough" solutions that avoids unnecessary complexity.

## Conversation Management

The core of our API revolves around **threads**—conversations between users and the agent. Each thread contains a series of messages that provide context for the agent's responses.

When I first implemented this, I tried to keep everything in memory for simplicity. But I quickly realized that persistence was essential for a proper conversational experience. Users expect to be able to continue conversations later, reference past interactions, and maintain context over time.

The database schema reflects this straightforward model:

```
Thread
├── id: UUID
├── user_id: UUID
├── agent_type: String
├── created_at: DateTime
└── updated_at: DateTime

Message
├── id: UUID
├── thread_id: UUID (foreign key to Thread)
├── role: String (user/assistant/system)
├── content: String
├── created_at: DateTime
└── metadata: JSON
```

This simple schema handles the core requirements while remaining flexible enough for future extensions.

## Agent Integration

Integrating the Pydantic-AI agent with our API service turned out to be surprisingly straightforward. The key steps are:

1. Load conversation history from the database
2. Create agent-specific dependencies (like database connections)
3. Run the agent with the user's query and conversation history
4. Save the new messages back to the database
5. Return a structured response to the client

Here's a simplified version of the integration:

```python
async def run_agent_query(
    thread_id: UUID,
    query: str,
    session_factory: Callable,
) -> AgentResponse:
    """Run an agent query and return the response."""
    try:
        # Load thread and validate user access
        thread = await get_thread_or_404(thread_id, session_factory)
        
        # Load message history
        message_history = await get_message_history(thread_id, session_factory)
        
        # Get the appropriate agent
        agent_type = AgentType(thread.agent_type)
        selected_agent = AGENT_MAP.get(agent_type.value)
        
        # Create agent dependencies
        agent_deps = create_agent_dependencies(thread.user_id, agent_type)
        
        # Run the agent
        agent_result = await selected_agent.run(
            query, 
            message_history=list(message_history),
            deps=agent_deps
        )
        
        # Save messages to database
        new_messages = await agent_result.new_messages()
        result_message = await save_agent_messages(
            session_factory=session_factory, 
            thread_id=thread.id, 
            model_messages=new_messages,
        )
        
        # Return the response
        return AgentResponse(
            thread_id=thread_id,
            message_id=result_message.id,
            response=result_message.content,
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the error
        logger.exception(f"Error running agent query: {str(e)}")
        # Raise a 500 error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running agent query: {str(e)}",
        )
```

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

## The Streaming Challenge

One of the most interesting challenges I faced was implementing streaming responses. While traditional request-response patterns are straightforward, streaming requires a different approach, especially when working with structured outputs.

The key insight was to use Pydantic-AI's streaming capabilities while implementing a custom protocol for delivering structured data incrementally. Here's the approach I took:

```python
async def stream_agent_query(
    thread_id: UUID,
    query: str,
    session_factory: Callable,
) -> AsyncGenerator[AgentResponseChunk, None]:
    """Stream an agent query and yield response chunks."""
    try:
        # Load thread and validate user access
        thread = await get_thread_or_404(thread_id, session_factory)
        
        # User message boilerplate omitted for brevity...
        
        # Load message history
        message_history = await get_message_history(thread_id, session_factory)
        
        # Get the appropriate agent
        agent_type = AgentType(thread.agent_type)
        selected_agent = AGENT_MAP.get(agent_type.value)
        
        # Create agent dependencies
        agent_deps = create_agent_dependencies(thread.user_id, agent_type)
        
        # Signal that the assistant is starting to respond
        message_id = uuid4()
        yield MessageStartedChunk(message_id=message_id)
        
        # Run the agent in streaming mode
        async with selected_agent.run_stream(
            query, 
            message_history=list(message_history),
            deps=agent_deps
        ) as result:
            # Stream tokens with validation
            async for message, last in result.stream_structured(debounce_by=0.000001):
                try:
                    profile = await result.validate_structured_output(  
                        message,
                        allow_partial=not last,
                    )
                    # Yield the validated token
                    yield TextDeltaChunk(message_id=message_id, token=json.dumps(profile))
                except ValidationError:
                    # Skip invalid intermediate tokens
                    continue
                    
        # Final handling and database operations omitted for brevity...
        
        # Signal that we're done
        yield DoneChunk()
        
    except Exception as e:
        # Error handling
        logger.exception(f"Error streaming agent query: {str(e)}")
        yield ErrorChunk(error=str(e))
```

This streaming approach provides several benefits:

1. **Immediate Feedback**: Users see responses as they're generated
2. **Better User Experience**: The application feels more responsive
3. **Graceful Error Handling**: Errors can be communicated mid-stream
4. **Reduced Time-to-First-Token**: Users don't have to wait for complete responses

## API Response Examples

To give you a clearer picture of how these endpoints work in practice, here are some real examples:

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
{"event":"message_started","message_id":"c4cf4543-d564-459e-bad7-e2e385a7d134"}
{"event":"text_delta","message_id":"c4cf4543-d564-459e-bad7-e2e385a7d134","token":"{\"support_advice\":\"D\"}"}
{"event":"text_delta","message_id":"c4cf4543-d564-459e-bad7-e2e385a7d134","token":"{\"support_advice\":\"Digits\"}"}
{"event":"text_delta","message_id":"c4cf4543-d564-459e-bad7-e2e385a7d134","token":"{\"support_advice\":\"Digits dance\"}"}
{"event":"text_delta","message_id":"c4cf4543-d564-459e-bad7-e2e385a7d134","token":"{\"support_advice\":\"Digits dance in\"}"}
{"event":"text_delta","message_id":"c4cf4543-d564-459e-bad7-e2e385a7d134","token":"{\"support_advice\":\"Digits dance in your\"}"}
// ... more streaming events ...
{"event":"text_delta","message_id":"c4cf4543-d564-459e-bad7-e2e385a7d134","token":"{\"support_advice\":\"Digits dance in your account,\\nA balance of $1123.45 stands,\\nLike autumn leaves that gently sway,\\nYour money rests, awaits your command.\",\"block_card\":false,\"risk_level\":1,\"follow_up_actions\":[]}"}
{"event":"message_complete","message_id":"c4cf4543-d564-459e-bad7-e2e385a7d134"}
{"event":"done"}
```

Notice how the structured response builds up token by token, maintaining the TypedDict format throughout. This allows clients to render the response incrementally while preserving the structured nature of the data.

## Lessons Learned and Best Practices

Building this API taught me several valuable lessons:

1. **Keep the Data Model Simple**: Start with the minimum viable schema and extend as needed.

2. **Embrace Async**: FastAPI and Pydantic-AI are both built for asynchronous operations, which significantly improve performance, especially for streaming responses.

3. **Use Dependency Injection**: FastAPI's dependency injection system works beautifully with Pydantic-AI's approach, creating a clean, testable architecture.

4. **Error Handling is Crucial**: AI models can be unpredictable; robust error handling makes your application resilient.

5. **Type Safety Pays Off**: The investment in proper type annotations catches errors early and improves code maintainability.

## What's Next: Building a Frontend

While our API is now complete, users typically don't interact with raw API endpoints. They need an intuitive interface that hides the complexity and presents information in a user-friendly way.

In the next article, we'll build a Streamlit frontend that consumes our API and provides a chat-like interface for interacting with our bank support agent. Streamlit is a perfect match for this type of application—it's Python-based, focuses on rapid development, and has built-in components specifically designed for chat interfaces.

By the end of the next article, we'll have a complete, end-to-end AI agent system with a structured backend and an intuitive frontend, demonstrating how Pydantic-AI, FastAPI, and Streamlit can work together to create powerful AI applications.

## Conclusion

Building an API for our Pydantic-AI agent has shown how well these technologies complement each other. The shared focus on type safety, modern Python patterns, and developer experience makes integration feel natural rather than forced.

What I appreciate most about this approach is how it scales—from simple prototype to production system, the fundamental architecture remains the same. The modular design allows you to start simple and incrementally add complexity as your requirements evolve.

In the next article, we'll complete our journey by building a Streamlit frontend that brings our agent to life with an intuitive chat interface. Stay tuned!

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic-AI Documentation](https://ai.pydantic.dev/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [GitHub Repository](https://github.com/EmpoweredHouse/pydantic-ai-agent) 
