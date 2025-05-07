"""
Entry point for the Streamlit application.
This file imports and runs the main app from the src/ directory.
"""

# Import the main function from client_app in src/
from src.client.client_app import main

# Run the main function when this script is executed
if __name__ == "__main__":
    main() 