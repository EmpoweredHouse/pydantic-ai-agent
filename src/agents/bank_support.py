"""
Example demonstrating Pydantic-AI for a bank support agent with dependency injection and tools.
"""

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from typing import List, Dict, Any

from src.agents.deps import SupportDependencies


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


