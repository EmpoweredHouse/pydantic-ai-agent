
import asyncio
from dotenv import load_dotenv

from src.agents.bank_support import support_agent
from src.agents.deps import SupportDependencies, DatabaseConn

# Load environment variables from .env file
load_dotenv()

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
            print(f"Support Advice: {support['support_advice']}")
            print(f"Block Card: {'Yes' if support['block_card'] else 'No'}")
            print(f"Risk Level: {support['risk_level']}/10")
            
            if support['follow_up_actions']:
                print("\nFollow-up Actions:")
                for action in support['follow_up_actions']:
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
            print(f"Support Advice: {support['support_advice']}")
            print(f"Block Card: {'Yes' if support['block_card'] else 'No'}")
            print(f"Risk Level: {support['risk_level']}/10")
            
            if support['follow_up_actions']:
                print("\nFollow-up Actions:")
                for action in support['follow_up_actions']:
                    print(f"- {action}")
                    
            print("-----------------------")
            
        except Exception as e:
            print(f"Error processing query: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 