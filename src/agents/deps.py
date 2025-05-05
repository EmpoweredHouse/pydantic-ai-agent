from dataclasses import dataclass
from typing import List, Dict, Any

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