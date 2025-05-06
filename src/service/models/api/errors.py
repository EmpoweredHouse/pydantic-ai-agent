"""API error exception classes.

This module contains custom exception classes for API-related errors
in the application.
"""

# Thread permission errors
class ThreadPermissionError(Exception):
    """Raised when a user attempts to access a thread they don't own."""
    
    def __init__(self, message: str = "You don't have permission to access this thread"):
        self.message = message
        super().__init__(self.message)


# Agent errors
class AgentTypeError(Exception):
    """
    Raised when there's an issue with the agent type.
    
    This can occur when:
    - A thread has no agent type specified
    - The agent type is invalid or unsupported
    - There's a configuration issue with the agent
    """
    
    def __init__(self, message: str = "Invalid or missing agent type"):
        self.message = message
        super().__init__(self.message)


# Model response errors
class EmptyResponseError(Exception):
    """Raised when a model produces an empty response."""
    
    def __init__(self, message: str = "The model produced an empty response"):
        self.message = message
        super().__init__(self.message)


class ModelResponseFormatError(Exception):
    """Raised when a model produces a response with incorrect format."""
    
    def __init__(self, message: str = "The model response has an incorrect format"):
        self.message = message
        super().__init__(self.message) 