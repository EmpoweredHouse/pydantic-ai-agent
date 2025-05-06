"""Database error classes."""

# Database errors
class DatabaseError(Exception):
    """Base class for database-related errors."""
    
    def __init__(self, message: str = "A database error occurred"):
        self.message = message
        super().__init__(self.message)

class RecordNotFoundError(DatabaseError):
    """Raised when a requested database record is not found."""
    
    def __init__(self, message: str = "The requested record was not found"):
        self.message = message
        super().__init__(self.message)
        
class RecordCreationError(DatabaseError):
    """Raised when a record cannot be created in the database."""
    
    def __init__(self, message: str = "Could not create the requested record"):
        self.message = message
        super().__init__(self.message)
        
class ThreadNotFoundError(DatabaseError):
    """Raised when a requested thread is not found in the database."""
    
    def __init__(self, message: str = "The requested thread was not found"):
        self.message = message
        super().__init__(self.message) 