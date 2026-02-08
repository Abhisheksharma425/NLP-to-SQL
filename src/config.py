"""Configuration management for the NLP-to-SQL system."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    openai_api_key: str
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0
    llm_max_tokens: int = 1000
    embedding_model: str = "text-embedding-3-small"
    
    # Database Configuration
    database_url: str = "sqlite:///./data/ecommerce.db"
    
    # Example Selection
    max_examples: int = 5
    
    # Self-Correction
    max_correction_attempts: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
