# Understanding Pydantic-AI: A Powerful Alternative to LangChain and LlamaIndex

## Introduction

My journey into AI frameworks began like many others—with excitement, confusion, and a lot of trial and error. After months of building agents with LangChain and LlamaIndex, I kept running into the same issues: complex abstractions that were hard to reason about, inconsistent type hints that led to runtime errors, and testing challenges that made iterative development frustrating.

That's when I discovered Pydantic-AI, a framework that immediately felt different. Created by the team behind Pydantic (the validation layer used by virtually every major AI framework), it brings a refreshingly straightforward approach to building AI agents. In this article, I'll share what I've learned about Pydantic-AI, how it compares to alternatives, and why it's become my go-to framework for building production AI applications.

## What is Pydantic-AI?

[Pydantic-AI](https://ai.pydantic.dev/) is a Python agent framework designed to make it less painful to build production-grade applications with Generative AI. It's developed by the same team behind Pydantic - the validation layer used by OpenAI SDK, Anthropic SDK, LangChain, LlamaIndex, AutoGPT, and many other popular AI tools.

The key idea is simple but powerful: instead of parsing free-form text responses from AI models, you define schemas for the expected outputs using Pydantic models, and Pydantic-AI handles the interaction with the LLM, ensuring it generates responses that match those schemas.

## Why I Chose Pydantic-AI Over Alternatives

Having invested significant time in both LangChain and LlamaIndex, switching frameworks wasn't a decision I made lightly. Here are the key advantages that convinced me to make the switch:

### 1. Python-Centric Design

While other frameworks introduce their own concepts and abstractions, Pydantic-AI leverages Python's native syntax and familiar control flow. This means you can build AI agents using standard Python best practices, making your code more maintainable and easier to understand.

I found this particularly refreshing. Instead of learning yet another framework-specific abstraction, I could focus on writing good Python code using patterns I already knew well.

### 2. Type Safety Throughout

Dealing with runtime errors in production AI applications taught me to value type safety. Pydantic-AI is designed to make type checking as powerful and informative as possible. This is a significant advantage over other frameworks where type hints may be incomplete or inconsistent.

With proper IDE integration, you get autocompletion, error detection, and refactoring support across your entire codebase. This has probably saved me hundreds of hours of debugging already.

### 3. Model Agnostic

When I first started with AI frameworks, I committed heavily to OpenAI's ecosystem. Then I needed to try Anthropic's models, and soon after, Google's Gemini. Each switch meant significant code changes.

Pydantic-AI supports multiple LLM providers out of the box, including OpenAI, Anthropic, Gemini, Deepseek, Ollama, Groq, Cohere, and Mistral. This gives you the flexibility to switch between providers without changing your core application logic—a feature I've come to appreciate as the AI landscape continues to evolve rapidly.

### 4. Dependency Injection System

One feature I particularly appreciate is Pydantic-AI's optional dependency injection system. Coming from a background in web development with FastAPI, this pattern felt immediately familiar and practical.

The dependency injection system makes it much easier to test your agents and iterate on their development. You can inject mock data or services during testing, making your tests faster and more reliable—something that was always a pain point with other frameworks.

### 5. Built for Production

Unlike some experimental frameworks, Pydantic-AI is explicitly designed for production use. It integrates with Pydantic Logfire for real-time debugging, performance monitoring, and behavior tracking - essential features for maintaining AI applications in production.

After deploying several agents to production, I've come to value these capabilities more and more.

## Getting Started with Pydantic-AI

Let's start with a simple "Hello World" example to understand the basics of Pydantic-AI:

```python
from pydantic_ai import Agent

agent = Agent(
    'google-gla:gemini-1.5-flash',
    system_prompt='Be concise, reply with one sentence.',
)

result = agent.run_sync('Where does "hello world" come from?')
print(result.output)
# Output: "The first known use of "hello, world" was in a 1974 textbook about the C programming language."
```

This simple example demonstrates a few key concepts:
1. Creating an Agent with a specified model
2. Providing a system prompt to guide the model's responses
3. Running the agent and getting a result

But the real power of Pydantic-AI comes when we start using structured outputs and tools.

## Building a Comprehensive Bank Support Agent

For this series of articles, I wanted to create an example that goes beyond basic tutorials—something that demonstrates real-world patterns while remaining accessible. I've chosen to build a bank support agent that can answer customer questions, access account information, and perform actions like blocking a card.

> **Note:** This bank support agent example is inspired by and adapted from the official [Pydantic-AI documentation](https://ai.pydantic.dev/). I've chosen to build upon this example because it effectively demonstrates the core capabilities of the framework while providing a practical use case. You can find the original example at [https://ai.pydantic.dev/examples/bank-support/](https://ai.pydantic.dev/examples/bank-support/).

Let's look at how we define structured outputs, dependency injection, and tools in our bank support agent:

```python
from dataclasses import dataclass
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from typing import List, Dict, Any

# Simulate a database connection
class DatabaseConn:
    async def customer_name(self, id: int) -> str:
        # In a real app, this would query a database
        return "John Doe"
    
    async def customer_balance(self, id: int, include_pending: bool) -> float:
        # In a real app, this would query a database
        return 1234.56 if not include_pending else 1123.45
    
    async def recent_transactions(self, id: int, limit: int = 5) -> List[Dict[str, Any]]:
        # In a real app, this would query a database
        return [
            {"date": "2023-06-15", "description": "Grocery Store", "amount": -78.52},
            {"date": "2023-06-14", "description": "Salary Deposit", "amount": 2500.00},
        ][:limit]

@dataclass
class SupportDependencies:
    customer_id: int
    db: DatabaseConn

class SupportOutput(BaseModel):
    support_advice: str = Field(description='Advice returned to the customer')
    block_card: bool = Field(description="Whether to block the customer's card")
    risk_level: int = Field(description='Risk level of query', ge=0, le=10)
    follow_up_actions: List[str] = Field(description='List of follow-up actions to take', default_factory=list)

support_agent = Agent(
    'openai:gpt-4o',
    deps_type=SupportDependencies,
    output_type=SupportOutput,
    system_prompt=(
        'You are a support agent at First National Bank. '
        'Provide helpful and accurate information to customers. '
        'Assess the risk level of their query and recommend appropriate actions.'
    ),
)

@support_agent.system_prompt
async def add_customer_info(ctx: RunContext[SupportDependencies]) -> str:
    customer_name = await ctx.deps.db.customer_name(id=ctx.deps.customer_id)
    return f"The customer's name is {customer_name}."

@support_agent.tool
async def get_balance(
    ctx: RunContext[SupportDependencies], include_pending: bool = True
) -> float:
    """Get the customer's current account balance."""
    return await ctx.deps.db.customer_balance(
        id=ctx.deps.customer_id,
        include_pending=include_pending,
    )

@support_agent.tool
async def get_recent_transactions(
    ctx: RunContext[SupportDependencies], limit: int = 5
) -> List[Dict[str, Any]]:
    """Get the customer's recent transactions."""
    return await ctx.deps.db.recent_transactions(
        id=ctx.deps.customer_id,
        limit=limit,
    )

@support_agent.tool
async def block_customer_card(ctx: RunContext[SupportDependencies]) -> bool:
    """Block the customer's card for security reasons.
    Only use this when there is a security concern or the card is reported lost/stolen.
    """
    return await ctx.deps.db.block_card(id=ctx.deps.customer_id)
```

This example demonstrates several key features of Pydantic-AI:

1. **Structured Output**: We define a `SupportOutput` model with fields for advice, card blocking decisions, risk level assessment, and follow-up actions.

2. **Dependency Injection**: The `SupportDependencies` class allows us to inject a database connection and customer ID, which can be accessed in system prompts and tools.

3. **Dynamic System Prompts**: We add dynamic information to the system prompt using the `@support_agent.system_prompt` decorator.

4. **Tool Functions**: We define tools for getting the customer's balance, recent transactions, and blocking their card.

## The Testing Challenge: Evaluating AI Agents

One of my biggest frustrations with other frameworks was testing. When your agent can produce different responses each time, how do you verify it's working correctly?

Pydantic-AI's evaluation framework (pydantic_evals) helps address this challenge by providing tools to systematically test and evaluate your agents. The full documentation for the evaluation framework can be found at [https://ai.pydantic.dev/evals/](https://ai.pydantic.dev/evals/).

### Dependency Injection for Testing

The dependency injection system I mentioned earlier really shines when it comes to testing. It allows you to easily swap out production dependencies (like database connections or external APIs) with test mocks that return predictable values.

Here's how we set up testing dependencies for our bank support agent:

```python
# Create a test database connection that returns predictable values
class TestDatabaseConn(DatabaseConn):
    """Test database connection with predictable responses."""
    
    async def customer_name(self, id: int) -> str:
        return "Test Customer"
    
    async def customer_balance(self, id: int, include_pending: bool = True) -> float:
        return 1000.00 if not include_pending else 950.00
    
    async def recent_transactions(self, id: int, limit: int = 5) -> List[Dict[str, Any]]:
        return [
            {"date": "2023-06-15", "description": "Test Transaction 1", "amount": -50.00},
            {"date": "2023-06-14", "description": "Test Transaction 2", "amount": 100.00},
        ][:limit]
    
    async def block_card(self, id: int) -> bool:
        return True

# Create test dependencies
test_deps = SupportDependencies(customer_id=999, db=TestDatabaseConn())

# Use these dependencies when running the agent in tests
result = await support_agent.run("What's my balance?", deps=test_deps)
```

This approach has several advantages:
1. Tests run quickly and reliably without external dependencies
2. Test results are deterministic and reproducible
3. You can simulate different scenarios by modifying the test dependencies
4. No risk of affecting production data during testing

### Building Evaluation Tests

Pydantic-AI provides a structured framework for evaluating your agents, centered around three main components:

1. **Case**: A single test case containing inputs, expected outputs, and metadata.
2. **Dataset**: A collection of cases that can be evaluated together.
3. **Evaluators**: Components that assess specific aspects of agent responses.

Here's a simplified example of how we evaluate our bank support agent:

```python
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import LLMJudge

# Create test cases with expected outputs
cases = [
    Case(
        name="balance_inquiry",
        inputs={"query": "What's my current balance?"},
        expected_output=SupportOutput(
            support_advice="Your current balance is $950.00.",
            block_card=False,
            risk_level=1,
            follow_up_actions=[]
        ),
        metadata={"category": "balance", "expected_risk": "low"}
    ),
    Case(
        name="lost_card",
        inputs={"query": "I lost my card, can you help me?"},
        expected_output=SupportOutput(
            support_advice="I'll block your card immediately.",
            block_card=True,
            risk_level=8,
            follow_up_actions=["Issue replacement card"]
        ),
        metadata={"category": "security", "expected_risk": "high"}
    ),
]

# Create a dataset
dataset = Dataset(cases=cases)

# Add custom rule-based evaluators
dataset.add_evaluator(RiskLevelEvaluator())
dataset.add_evaluator(CardBlockEvaluator())

# Add LLM Judge for subjective evaluation
helpfulness_rubric = """
Rate the helpfulness of the response from 0.0 to 1.0:
- 1.0: Excellent, fully addresses the customer's concern
- 0.5: Partially addresses the concern
- 0.0: Not helpful at all
"""

# Add the LLM Judge to your dataset
dataset.add_evaluator(
    LLMJudge(
        name="helpfulness_score",
        rubric=helpfulness_rubric,
        model="openai:gpt-4o-mini"  # Use a smaller model for evaluation
    )
)

# Run evaluations
eval_results = await dataset.evaluate(evaluate_function)

# Print the results with comparison to expected outputs
eval_results.print(include_input=True, include_output=True, include_expected_output=True)
```

This evaluation framework has transformed how I approach agent development. Instead of manually checking responses during development, I can now specify expected behaviors and automatically verify them.

## Taking It Further: From Console to Web Application

### Using Expected Outputs for Evaluation

A powerful feature of Pydantic-AI's evaluation framework is the ability to define expected outputs for each test case. This provides a clear baseline for comparison and makes it easier to identify when your agent's behavior deviates from expectations.

When you define expected outputs:

1. **Structured comparison**: The framework compares each field of the output model against your expectations
2. **Exact matching**: You can verify that critical fields like `block_card` and `risk_level` meet your exact requirements
3. **Flexible text matching**: For text fields like `support_advice`, you can use custom evaluators to check for semantic similarity rather than exact matches

This approach is particularly valuable for regression testing, ensuring that your agent's behavior remains consistent as you make changes to your models or prompts.

### Creating Custom Rule-Based Evaluators

Pydantic-AI makes it easy to create custom evaluators for specific aspects of your agent's behavior. For example, we created evaluators to check if the risk level and card blocking decisions match our expectations:

```python
class RiskLevelEvaluator(Evaluator):
    """Evaluator for risk level assessment."""
    
    def __init__(self, risk_thresholds=None):
        super().__init__()
        self.risk_thresholds = risk_thresholds or {
            "low": (0, 3),
            "medium": (4, 6),
            "high": (7, 10)
        }
    
    def name(self):
        """Return the name of the evaluator."""
        return "risk_level"
    
    def evaluate(self, ctx):
        """Evaluate if the risk level matches the expected category."""
        expected_risk = ctx.metadata.get("expected_risk")
        if not expected_risk or not hasattr(ctx.output, "risk_level"):
            return None
        
        risk_level = ctx.output.risk_level
        min_val, max_val = self.risk_thresholds[expected_risk]
        
        # Return 1.0 for perfect match, 0.5 for close, 0.0 for incorrect
        if min_val <= risk_level <= max_val:
            return 1.0
        elif abs(risk_level - min_val) <= 1 or abs(risk_level - max_val) <= 1:
            return 0.5
        else:
            return 0.0
```

### Using LLM Judge for Subjective Evaluation

While expected outputs are great for objective criteria, some aspects of AI responses are inherently subjective. This is where LLM Judge comes in - it uses another language model to evaluate the outputs of your agent based on customized rubrics.

With LLM Judge, you can:

1. **Define custom rubrics**: Create evaluation criteria for subjective qualities like helpfulness or clarity.

2. **Get numerical scores**: LLM Judge provides normalized scores (0.0-1.0) that can be tracked over time.

3. **Use any LLM provider**: You can use smaller, faster models for evaluation to keep costs down. For example, you might use `gpt-4o` for your main agent but `gpt-4o-mini` for your evaluators to reduce costs.

4. **Isolate evaluation concerns**: By using a different model for evaluation than the one used in your agent, you can avoid potential biases where a model might favorably evaluate its own output.

Here's a simple example of an LLM Judge implementation:

```python
from pydantic_evals.evaluators import LLMJudge

# Simple, clear rubric for the LLM Judge
helpfulness_rubric = """
Rate the helpfulness of the response from 0.0 to 1.0:
- 1.0: Excellent, fully addresses the customer's concern
- 0.5: Partially addresses the concern
- 0.0: Not helpful at all
"""

# Add the LLM Judge to your dataset
dataset.add_evaluator(
    LLMJudge(
        name="helpfulness_score",
        rubric=helpfulness_rubric,
        model="openai:gpt-4o-mini"  # Use a smaller model for evaluation
    )
)
```

The key is to keep your rubrics clear and focused on a single aspect of evaluation. This makes it easier for the LLM to provide consistent, meaningful scores.

### Comprehensive Evaluation Reports

When you run your evaluations, Pydantic-AI generates detailed reports that show inputs, expected outputs, actual outputs, and evaluation scores. Here's an example of what these reports look like:

```
                                                 Evaluation Summary: evaluate_query                                                    
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Case ID             ┃ Inputs                ┃ Expected Output      ┃ Outputs               ┃ Scores            ┃ Assertions ┃ Duration ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━┩
│ balance_inquiry     │ query="What's my      │ support_advice='Your │ support_advice='Your  │ risk_level: 1.00  │ ✔✔         │     2.9s │
│                     │ current balance?"     │ current account      │ current account       │ card_block: 1.00  │            │          │
│                     │                       │ balance, including   │ balance, including    │                   │            │          │
│                     │                       │ pending              │ pending transactions, │                   │            │          │
│                     │                       │ transactions, is     │ is $950.00. If you    │                   │            │          │
│                     │                       │ $950.00.'            │ have any further      │                   │            │          │
│                     │                       │ block_card=False     │ questions or need     │                   │            │          │
│                     │                       │ risk_level=1         │ assistance, feel free │                   │            │          │
│                     │                       │ follow_up_actions=[] │ to reach out!'        │                   │            │          │
│                     │                       │                      │ block_card=False      │                   │            │          │
│                     │                       │                      │ risk_level=0          │                   │            │          │
│                     │                       │                      │ follow_up_actions=[]  │                   │            │          │
```

These reports make it easy to:
1. **Identify mismatches** between expected and actual outputs
2. **Track performance** across different test cases
3. **Diagnose issues** with specific aspects of your agent's behavior
4. **Monitor trends** over time as you make changes to your agent

### Integration with Logfire

One of the many advantages of using Pydantic-AI is its integration with Logfire for monitoring and visualization. When you run evaluations with Logfire configured, all your test results are automatically tracked and visualized in the Logfire dashboard.

This integration gives you:
1. **Historical tracking** of evaluation results over time
2. **Visual representations** of agent performance
3. **Alerts and notifications** when performance drops below thresholds
4. **Detailed debugging** of specific test failures
5. **Centralized monitoring** across your entire AI application

By combining expected outputs with LLM Judge evaluators and viewing the results through Logfire, you get a complete picture of your agent's performance across both objective and subjective criteria.

## Debugging and Monitoring with Pydantic Logfire

One significant advantage of using Pydantic-AI is its integration with Pydantic Logfire, a powerful debugging and monitoring tool specifically designed for LLM applications. Unlike many other LLM frameworks, Pydantic-AI comes with built-in support for comprehensive observability through Logfire.

### What is Pydantic Logfire?

Pydantic Logfire is an observability platform that uses OpenTelemetry to provide insights into your application's behavior. It's similar to LangChain's LangSmith but offers deeper integration with Pydantic-AI and broader application monitoring capabilities.

Key benefits include:

1. **End-to-end visibility**: Track the entire flow of your LLM application, from user input to final response, including all intermediate steps and tool calls.

2. **Performance monitoring**: Identify bottlenecks and slow operations in your application, whether they're related to LLM calls, database operations, or other components.

3. **Behavior analysis**: Understand how your agents behave in production by examining their inputs, outputs, and decision-making processes.

4. **Error tracking**: Quickly identify and diagnose issues in your application, with detailed context about what went wrong.

### Setting Up Logfire with Pydantic-AI

Adding Logfire to your Pydantic-AI application is remarkably simple:

```python
import logfire
from pydantic_ai import Agent

# Configure Logfire
logfire.configure(
    send_to_logfire='if-token-present',  # Only send data if LOGFIRE_TOKEN is set
    environment='development',
    service_name='bank-support-agent'
)

# Create your agent with instrumentation enabled
agent = Agent(
    'openai:gpt-4o',
    deps_type=SupportDependencies,
    output_type=SupportOutput,
    system_prompt='You are a support agent...',
    instrument=True  # Enable Logfire instrumentation
)
```

That's it! With this minimal setup, you'll get comprehensive logging and monitoring of your agent's behavior.

### Monitoring Beyond LLMs with OpenTelemetry

One of the most powerful aspects of Logfire is its use of OpenTelemetry, which allows you to monitor your entire application stack:

```python
# Instrument database connections
logfire.instrument_asyncpg()  # For PostgreSQL
logfire.instrument_requests()  # For HTTP requests
logfire.instrument_fastapi()   # For FastAPI applications

# Add custom traces
with logfire.span("custom_operation"):
    # Your code here
    pass
```

This gives you a holistic view of your application's behavior, not just the LLM components.

## Taking It Further: From Console to Web Application

Having a well-structured AI agent is only the first step. To be truly useful, the agent needs to be accessible to users through an intuitive interface.

In the next article, we'll explore how to build a FastAPI web service around our bank support agent, including:

1. API design for conversational agents
2. Managing conversation history in a database
3. Implementing both blocking and streaming response patterns
4. Setting up proper error handling and logging

Then, in the final article, we'll create a Streamlit frontend that provides a user-friendly interface to interact with our agent through the API.

By the end of this series, you'll have a complete, production-ready AI agent system that demonstrates best practices for each layer of the stack.

## Conclusion: Why Pydantic-AI Might Be Right for You

After working with multiple AI frameworks, I've found Pydantic-AI to be the most developer-friendly and production-ready option. Its focus on type safety, familiar Python patterns, and built-in testing tools has significantly improved my development experience.

Whether you're building your first AI agent or migrating from another framework, Pydantic-AI offers a clean, well-designed approach that scales from simple prototypes to complex production systems.

In the next article, we'll dive into building a FastAPI service around our agent, turning it from a console application into a proper web service. Stay tuned!

## Resources

- [Pydantic-AI Documentation](https://ai.pydantic.dev/)
- [Pydantic-AI GitHub Repository](https://github.com/pydantic/pydantic-ai)
- [Pydantic-AI GitHub Repository](https://github.com/pydantic/ai)
- [Pydantic-Evals Documentation](https://ai.pydantic.dev/evals/) - [Pydantic Documentation](https://docs.pydantic.dev/)
- [Pydantic Logfire Documentation](https://docs.logfire.dev/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/) 
