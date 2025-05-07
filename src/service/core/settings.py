"""API configuration settings."""

from typing import List, Union

from pydantic import Field, field_validator, AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """API server configuration settings."""
    
    MODE: str = "dev"
    HOST: str = "0.0.0.0"
    PORT: int = 8080

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Bank Support Agent"
    
    # Security
    API_BASE_URL: str = Field(default="http://localhost:8000", description="API base URL")
    API_KEY: str = Field(default="", description="API key for accessing the API")
    API_KEY_NAME: str = "X-API-Key"
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
        
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        elif isinstance(v, str):
            return [v]
        raise ValueError(v)
    
    # SQLite Database
    DB_PATH: str = Field(default="./sqlite.db", description="SQLite database path")
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Get the SQLite database URI."""
        return f"sqlite+aiosqlite:///{self.DB_PATH}"
    
    # Agent
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
    
    # Logging
    LOGFIRE_TOKEN: str = Field(default="", description="Logfire token")
    LOGFIRE_SEND_TO_LOGFIRE: bool = Field(default=False, description="Send logs to Logfire")
    LOGFIRE_ENVIRONMENT: str = Field(default="development", description="Logfire environment")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        arbitrary_types_allowed=True
    )

    def is_dev(self) -> bool:
        return self.MODE == "dev"

settings = Settings() 