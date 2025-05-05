# Pydantic-AI Agent Examples

This repository contains articles and a comprehensive example about building AI agents using Pydantic-AI, FastAPI, and Streamlit.

## Overview

This project explores the capabilities of Pydantic-AI for building structured AI agents. It includes:

1. A series of articles on AI, agents, FastAPI, and Streamlit demos
2. A comprehensive example demonstrating Pydantic-AI in action
3. Evaluation tests showing how to ensure agent quality
4. Project documentation and PRD

## Documentation

Full project documentation is available in the [docs directory](docs/index.md):

- [Product Requirements Document](docs/prd.md)
- [Technical Architecture](docs/architecture.md)
- [User Stories](docs/user_stories.md)
- [Development Roadmap](docs/roadmap.md)
- [Project Plan](cursor-rules.md)

## Articles

The following articles are included in this repository:

1. [Understanding Pydantic-AI: A Powerful Tool for Building AI Agents](docs/articles/01-pydantic-ai-introduction.md)
2. Building AI Agents with FastAPI (coming soon)
3. Creating Interactive AI Demos with Streamlit (coming soon)

## Example

This repository features a comprehensive Bank Support Agent example that demonstrates the key capabilities of Pydantic-AI:

> **Note:** This example is inspired by and adapted from the official [Pydantic-AI documentation](https://ai.pydantic.dev/). It was chosen because it effectively demonstrates the framework's core capabilities in a practical context.

- **Structured Outputs**: Using Pydantic models to validate agent responses
- **Dependency Injection**: Providing context and services to the agent
- **Tool Functions**: Allowing the agent to interact with external systems
- **Asynchronous Execution**: Non-blocking operations with async/await

See the [example README](src/README.md) for detailed instructions on running the bank support agent example.

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

```bash
# Run the bank support agent example
python -m src.bank_support
```

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
