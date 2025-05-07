# Pydantic-AI Agent Examples

This repository contains articles and a comprehensive example about building AI agents using Pydantic-AI, FastAPI, and Streamlit.

## Overview

This project explores the capabilities of Pydantic-AI for building structured AI agents. It includes:

1. A series of articles on AI, agents, FastAPI, and Streamlit demos
2. A comprehensive example demonstrating Pydantic-AI in action with a FastAPI service
3. Evaluation tests showing how to ensure agent quality
4. Project documentation and PRD


## Articles

The following articles are included in this repository:

1. [Understanding Pydantic-AI: A Powerful Tool for Building AI Agents](docs/articles/01-pydantic-ai-introduction.md)
2. [Building an API for Your Pydantic-AI Agent with FastAPI](docs/articles/02-fastapi-agent-api.md)
3. [Building an Interactive Demo for Your Pydantic-AI Agent with Streamlit](docs/articles/03-streamlit-frontend.md)

## Example

This repository features a comprehensive Bank Support Agent example that demonstrates the key capabilities of Pydantic-AI:

> **Note:** This example is inspired by and adapted from the official [Pydantic-AI documentation](https://ai.pydantic.dev/). It was chosen because it effectively demonstrates the framework's core capabilities in a practical context.

The example includes:

- **Bank Support Agent**: A Pydantic-AI agent that can answer account questions, check balances, and more
- **FastAPI Service**: A complete API implementation with thread management and message history
- **Streamlit Frontend**: An interactive chat interface for engaging with the agent
- **Streaming Support**: Both blocking and streaming response patterns for real-time feedback
- **Database Integration**: SQLAlchemy models for persistent conversation storage

Key features demonstrated include:

- **Structured Outputs**: Using TypedDict for validated, structured agent responses
- **Dependency Injection**: Providing context and services to the agent
- **Tool Functions**: Allowing the agent to interact with external systems
- **Asynchronous Execution**: Non-blocking operations with async/await
- **Conversation History**: Maintaining context across multiple interactions

## Getting Started

### Prerequisites

- Python 3.10 or higher
- OpenAI API key (or other supported LLM provider)
- `uv` for dependency management

### Installing uv

`uv` is a fast Python package installer and resolver. To install it:

```bash
# Install with pip
pip install uv

# Or on macOS with Homebrew
brew install uv
```

### Installation with uv

1. Clone this repository
   ```bash
   git clone https://github.com/yourusername/pydantic-ai-agent.git
   cd pydantic-ai-agent
   ```

2. Create a virtual environment with uv
   ```bash
   uv venv
   ```

3. Activate the virtual environment
   ```bash
   # On Windows
   .venv\Scripts\activate
   
   # On macOS/Linux
   source .venv/bin/activate
   ```

4. Install dependencies with uv
   ```bash
   uv pip install -e .
   ```

5. Copy environment variables and add your API keys
   ```bash
   cp .env.example .env
   # Edit .env to add your API keys
   ```

### Running the Example

To run the bank support agent in the console:

```bash
# Run the bank support agent example
uv run python -m src.run_agent
```

To run the FastAPI server:

```bash
# Start the API server
uv run uvicorn src.service.main:app --reload --log-level debug
```

Once the server is running, you can:
- Access the API documentation at http://localhost:8000/docs
- Use the API endpoints at http://localhost:8000/api/v1/...

To run the Streamlit frontend (with the API server already running):

```bash
# Start the Streamlit frontend
uv run streamlit run streamlit_app.py
```

The Streamlit app will automatically open in your browser at http://localhost:8501, providing an interactive chat interface for the bank support agent.

### Running Evaluation Tests

The evaluation tests are located in the tests directory and can be run with:

```bash
python -m pytest tests/test_bank_support.py
```

## Why Pydantic-AI?

Pydantic-AI provides several advantages over other frameworks:

- **Built by the Pydantic Team**: Created by the developers behind Pydantic, the validation layer used by many AI libraries
- **Type Safety**: Strong typing throughout your codebase
- **Python-Centric Design**: Uses standard Python patterns instead of custom abstractions
- **Multiple LLM Providers**: Support for OpenAI, Anthropic, Google, and others
- **Dependency Injection**: Built-in system for providing data and services to your agents
- **Evaluation Framework**: Tools for testing and evaluating your agents

## Project Status

This project is currently in development. See the [roadmap](docs/roadmap.md) for planned features and timeline.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
