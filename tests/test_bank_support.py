"""
Evaluation tests for the bank support agent using pydantic_evals.
"""
import asyncio
import os
import logfire
import pytest

from pydantic import BaseModel
from typing import Dict, Any, List

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Evaluator, LLMJudge
from src.agents.bank_support import SupportOutput, support_agent
from src.agents.deps import SupportDependencies, DatabaseConn

os.environ["LOGFIRE_IGNORE_NO_CONFIG"] = "1"

logfire.configure(
    send_to_logfire="if-token-present",
    environment="development",
    service_name="evaluations",
)


class BankQueryInputs(BaseModel):
    """Model for bank query inputs."""
    query: str


# Create test database connection that returns predictable values
class TestDatabaseConn(DatabaseConn):
    """Test database connection with predictable responses."""
    
    async def customer_name(self, id: int) -> str:
        """Get the customer's name from the test database."""
        return "Test Customer"
    
    async def customer_balance(self, id: int, include_pending: bool = True) -> float:
        """Get the customer's balance from the test database."""
        return 1000.00 if not include_pending else 950.00
    
    async def recent_transactions(self, id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get the customer's recent transactions from the test database."""
        return [
            {"date": "2023-06-15", "description": "Test Transaction 1", "amount": -50.00},
            {"date": "2023-06-14", "description": "Test Transaction 2", "amount": 100.00},
        ][:limit]
    
    async def block_card(self, id: int) -> bool:
        """Block the customer's card."""
        return True


# Create test dependencies
test_deps = SupportDependencies(customer_id=999, db=TestDatabaseConn())


@pytest.fixture
def bank_support_dataset() -> Dataset[BankQueryInputs, SupportOutput]:
    """Create a dataset for testing the bank support agent."""
    # Create cases
    cases = [
        Case(
            name="balance_inquiry",
            inputs=BankQueryInputs(query="What's my current balance?"),
            expected_output=SupportOutput(
                support_advice="Your current account balance, including pending transactions, is $950.00.",
                block_card=False,
                risk_level=1,
                follow_up_actions=[]
            ),
            metadata={"category": "balance", "expected_risk": "low"}
        ),
        Case(
            name="lost_card",
            inputs=BankQueryInputs(query="I lost my card, can you help me?"),
            expected_output=SupportOutput(
                support_advice="I'll help you block your card immediately to prevent unauthorized transactions.",
                block_card=True,
                risk_level=8,
                follow_up_actions=["Issue replacement card", "Review recent transactions"]
            ),
            metadata={"category": "security", "expected_risk": "high"}
        ),
        Case(
            name="travel_notification",
            inputs=BankQueryInputs(query="I'm traveling to Europe next week, do I need to notify the bank?"),
            expected_output=SupportOutput(
                support_advice="Yes, it's a good idea to notify the bank of your travel plans to avoid any disruption to your card services.",
                block_card=False,
                risk_level=4,
                follow_up_actions=["Add travel notification to account"]
            ),
            metadata={"category": "travel", "expected_risk": "medium"}
        ),
        Case(
            name="transaction_history",
            inputs=BankQueryInputs(query="Can I see my recent transactions?"),
            expected_output=SupportOutput(
                support_advice="Here are your recent transactions: a purchase at Test Transaction 1 for $50.00 on 2023-06-15 and a deposit of $100.00 for Test Transaction 2 on 2023-06-14.",
                block_card=False,
                risk_level=1,
                follow_up_actions=[]
            ),
            metadata={"category": "transactions", "expected_risk": "low"}
        ),
        Case(
            name="suspicious_activity",
            inputs=BankQueryInputs(query="I see some transactions I don't recognize on my account"),
            expected_output=SupportOutput(
                support_advice="I'm going to block your card immediately to protect your account. Let's review the suspicious transactions together.",
                block_card=True,
                risk_level=9,
                follow_up_actions=["Review suspicious transactions", "Issue new card", "File fraud report"]
            ),
            metadata={"category": "security", "expected_risk": "high"}
        ),
    ]
    
    # Create dataset
    return Dataset(cases=cases)


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
    
    async def evaluate_async(self, ctx):
        """Async version of evaluate method."""
        return self.evaluate(ctx)


class CardBlockEvaluator(Evaluator):
    """Evaluator for card blocking decisions."""
    
    def __init__(self):
        super().__init__()
    
    def name(self):
        """Return the name of the evaluator."""
        return "card_block"
    
    def evaluate(self, ctx):
        """Evaluate if card blocking decision is appropriate."""
        category = ctx.metadata.get("category")
        if not category or not hasattr(ctx.output, "block_card"):
            return None
        
        # Security issues should block the card
        if category == "security" and ctx.output.block_card:
            return 1.0
        # Non-security issues should not block the card
        elif category != "security" and not ctx.output.block_card:
            return 1.0
        # Wrong decision
        else:
            return 0.0
    
    async def evaluate_async(self, ctx):
        """Async version of evaluate method."""
        return self.evaluate(ctx)


# Define simplified LLM Judge prompts
HELPFULNESS_RUBRIC = """
Rate the helpfulness of the response from 0.0 to 1.0:
- 1.0: Excellent, fully addresses the customer's concern
- 0.5: Partially addresses the concern
- 0.0: Not helpful at all
"""

CLARITY_RUBRIC = """
Rate the clarity of the response from 0.0 to 1.0:
- 1.0: Crystal clear and easy to understand
- 0.5: Somewhat clear but could be improved
- 0.0: Confusing or unclear
"""


async def run_agent_with_query(query: str) -> SupportOutput:
    """Run the bank support agent with a query."""
    result = await support_agent.run(query, deps=test_deps)
    return result.output


@pytest.mark.asyncio
async def test_bank_support_agent(bank_support_dataset):
    """Test the bank support agent with the evaluation dataset."""
    # Add rule-based evaluators to the dataset
    bank_support_dataset.add_evaluator(RiskLevelEvaluator())
    bank_support_dataset.add_evaluator(CardBlockEvaluator())
    
    # Add LLM Judge evaluators for subjective assessment
    bank_support_dataset.add_evaluator(
        LLMJudge(
            # name="helpfulness_score",
            rubric=HELPFULNESS_RUBRIC,
            model="openai:gpt-4o-mini"  # Use a smaller, faster model for evaluation
        )
    )
    
    bank_support_dataset.add_evaluator(
        LLMJudge(
            # name="clarity_score",
            rubric=CLARITY_RUBRIC,
            model="openai:gpt-4o-mini"
        )
    )
    
    # Define async function to run with the dataset
    async def evaluate_query(inputs: BankQueryInputs) -> SupportOutput:
        return await run_agent_with_query(inputs.query)
    
    # Run evaluations
    eval_results = await bank_support_dataset.evaluate(evaluate_query)
    
    # Print the evaluation results to console
    eval_results.print(include_input=True, include_output=True, include_expected_output=True)


if __name__ == "__main__":
    # Run the tests directly
    dataset = bank_support_dataset()
    asyncio.run(test_bank_support_agent(dataset)) 