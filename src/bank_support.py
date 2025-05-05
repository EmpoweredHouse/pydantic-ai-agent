"""
Example demonstrating Pydantic-AI for a bank support agent with dependency injection and tools.
"""
from dataclasses import dataclass
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from typing import List, Dict, Any
from dotenv import load_dotenv
import asyncio

# Load environment variables from .env file
load_dotenv()


# Simulate a database connection
class DatabaseConn:
    """Simulated database connection for the bank."""
    
    async def customer_name(self, id: int) -> str:
        """Get the customer's name from the database."""
        # In a real app, this would query a database
        return "John Doe"
    
    async def customer_balance(self, id: int, include_pending: bool = True) -> float:
        """Get the customer's balance from the database."""
        # In a real app, this would query a database
        return 1234.56 if not include_pending else 1123.45
    
    async def recent_transactions(self, id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get the customer's recent transactions from the database."""
        # In a real app, this would query a database
        return [
            {"date": "2023-06-15", "description": "Grocery Store", "amount": -78.52},
            {"date": "2023-06-14", "description": "Salary Deposit", "amount": 2500.00},
            {"date": "2023-06-12", "description": "Restaurant", "amount": -45.67},
            {"date": "2023-06-10", "description": "Gas Station", "amount": -35.40},
            {"date": "2023-06-08", "description": "Online Shopping", "amount": -112.99},
        ][:limit]
    
    async def block_card(self, id: int) -> bool:
        """Block the customer's card."""
        # In a real app, this would update the database
        return True


@dataclass
class SupportDependencies:
    """Dependencies for the bank support agent."""
    customer_id: int
    db: DatabaseConn


class SupportOutput(BaseModel):
    """Structured output for the bank support agent."""
    support_advice: str = Field(description='Advice returned to the customer')
    block_card: bool = Field(description="Whether to block the customer's card")
    risk_level: int = Field(description='Risk level of query', ge=0, le=10)
    follow_up_actions: List[str] = Field(description='List of follow-up actions to take', default_factory=list)


# Create a bank support agent
support_agent = Agent(
    'openai:gpt-4o',  # You can change this to another model if preferred
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
    """Add customer information to the system prompt."""
    customer_name = await ctx.deps.db.customer_name(id=ctx.deps.customer_id)
    return f"The customer's name is {customer_name}."


@support_agent.tool
async def get_balance(
    ctx: RunContext[SupportDependencies], include_pending: bool = True
) -> float:
    """Get the customer's current account balance.
    
    Args:
        include_pending: Whether to include pending transactions in the balance calculation.
    """
    balance = await ctx.deps.db.customer_balance(
        id=ctx.deps.customer_id,
        include_pending=include_pending,
    )
    return balance


@support_agent.tool
async def get_recent_transactions(
    ctx: RunContext[SupportDependencies], limit: int = 5
) -> List[Dict[str, Any]]:
    """Get the customer's recent transactions.
    
    Args:
        limit: Maximum number of transactions to return (default: 5).
    """
    transactions = await ctx.deps.db.recent_transactions(
        id=ctx.deps.customer_id,
        limit=limit,
    )
    return transactions


@support_agent.tool
async def block_customer_card(ctx: RunContext[SupportDependencies]) -> bool:
    """Block the customer's card for security reasons.
    Only use this when there is a security concern or the card is reported lost/stolen.
    """
    success = await ctx.deps.db.block_card(id=ctx.deps.customer_id)
    return success


async def main() -> None:
    """Run the example."""
    print("Bank Support Agent\n")
    print("This example demonstrates a bank support agent with dependency injection and tools.\n")
    
    # Create dependencies
    deps = SupportDependencies(customer_id=123, db=DatabaseConn())
    
    # Example queries to demonstrate the agent
    queries = [
        "What's my current balance?",
        "I want to see my recent transactions.",
        "I think someone stole my card. I see strange transactions.",
        "Can you help me understand why my balance is lower than expected?",
        "I'm going abroad next week. Should I notify the bank?"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\nExample {i}: '{query}'\n")
        
        try:
            # Run the agent with the query
            result = await support_agent.run(query, deps=deps)
            support = result.output
            
            print("--- Agent Response ---")
            print(f"Support Advice: {support.support_advice}")
            print(f"Block Card: {'Yes' if support.block_card else 'No'}")
            print(f"Risk Level: {support.risk_level}/10")
            
            if support.follow_up_actions:
                print("\nFollow-up Actions:")
                for action in support.follow_up_actions:
                    print(f"- {action}")
                    
            print("-----------------------")
            
        except Exception as e:
            print(f"Error processing query: {e}")
    
    # Interactive mode
    print("\nNow you can ask your own questions (type 'quit' to exit):")
    
    while True:
        query = input("\n> ")
        if query.lower() in ('quit', 'exit', 'q'):
            break
            
        try:
            result = await support_agent.run(query, deps=deps)
            support = result.output
            
            print("\n--- Agent Response ---")
            print(f"Support Advice: {support.support_advice}")
            print(f"Block Card: {'Yes' if support.block_card else 'No'}")
            print(f"Risk Level: {support.risk_level}/10")
            
            if support.follow_up_actions:
                print("\nFollow-up Actions:")
                for action in support.follow_up_actions:
                    print(f"- {action}")
                    
            print("-----------------------")
            
        except Exception as e:
            print(f"Error processing query: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 