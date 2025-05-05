# Pydantic-AI Examples

This directory contains a comprehensive example demonstrating the use of Pydantic-AI for building AI agents.

## Environment Setup

Before running the examples, make sure to set up your environment:

1. Copy the `.env.example` file from the root directory to `.env`
2. Add your API keys to the `.env` file

## Bank Support Agent Example

A comprehensive example showing the capabilities of Pydantic-AI for building a bank support agent.

> **Note:** This example is inspired by and adapted from the official [Pydantic-AI documentation](https://ai.pydantic.dev/). It has been selected and expanded upon because it effectively demonstrates the core capabilities of the framework.

```bash
python -m src.bank_support
```

This example demonstrates the core features of Pydantic-AI:

### Structured Output
- Define Pydantic models for agent outputs
- Validate responses against schemas
- Use Field validators for constraints

### Dependency Injection
- Providing database connections and context
- Dynamic system prompts
- Context-aware behavior

### Tool Functions
- Create tools that the agent can use
- Pass dependencies to tools
- Allow agents to perform actions

### Asynchronous Execution
- Non-blocking API calls
- Parallel processing
- Modern async/await patterns

## Model Selection

By default, the example uses OpenAI's GPT-4o model. You can change the model by:

1. Editing the model name in the code (e.g., change `'openai:gpt-4o'` to `'anthropic:claude-3-opus-20240229'`)
2. Setting the `PYDANTIC_AI_DEFAULT_MODEL` environment variable

Supported model prefixes include:
- `openai:` - OpenAI models (e.g., `openai:gpt-4o`)
- `anthropic:` - Anthropic models (e.g., `anthropic:claude-3-opus-20240229`)
- `google-gla:` - Google Gemini models (e.g., `google-gla:gemini-1.5-flash`)
- `groq:` - Groq models (e.g., `groq:llama3-8b-8192`)
- `mistral:` - Mistral models (e.g., `mistral:mistral-large-latest`)

## Debugging

If you encounter issues:

1. Check your API keys in the `.env` file
2. Make sure you have installed all dependencies
3. Try with a different model if the current one is unavailable
4. Increase the timeout if needed by setting `PYDANTIC_AI_REQUEST_TIMEOUT` in your `.env` file

## Evaluation Tests

The evaluation tests for this example are located in the `tests/` directory. You can run them with:

```bash
python -m pytest tests/test_bank_support.py
```

See the [Pydantic-AI Evals documentation](https://ai.pydantic.dev/evals/) for more information on evaluation. 