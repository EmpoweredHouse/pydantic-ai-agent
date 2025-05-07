"""Environment setup module that must be imported first.

This module must be imported before any other imports that might use environment variables.
The import order is enforced by the module name starting with '_' to make it sort first.
"""

import os
from dotenv import load_dotenv

# Load environment variables at application startup
load_dotenv(override=True, verbose=True)

# API configuration
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
API_KEY = os.environ.get("API_KEY", "development-api-key")
