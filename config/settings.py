"""Configuration settings for the ESG Reporter application."""

import os
from typing import TypedDict
from typing import Optional
try:
    from pydantic import BaseSettings, Field
except ImportError:
    # Fallback for newer pydantic versions
    from pydantic_settings import BaseSettings
    from pydantic import Field


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    # Default to SQLite for development, can switch to MySQL/PostgreSQL for production
    DATABASE_URL: str = Field(
        default="sqlite:///./esg_reporter.db",
        description="Database connection URL"
    )
    DATABASE_TYPE: str = Field(
        default="sqlite",
        description="Database type: sqlite, mysql, postgresql"
    )
    
    # MySQL/PostgreSQL specific settings
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[int] = None
    DB_NAME: Optional[str] = None
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    
    class Config:
        env_file = ".env"
        extra = "ignore"

class OpenAISettings(BaseSettings):
    """OpenAI API configuration."""
    
    OPENAI_API_KEY: str = Field(
        description="OpenAI API key for chatbot functionality"
    )
    OPENAI_MODEL: str = Field(
        default="gpt-4.1",
        description="OpenAI model to use"
    )
    OPENAI_TEMPERATURE: float = Field(
        default=0.1,
        description="Temperature for OpenAI responses"
    )
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class AppSettings(BaseSettings):
    """Main application settings."""
    
    APP_NAME: str = "ESG Mate"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = Field(default=True, description="Debug mode")
    
    # Server settings
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8080, description="Server port")
    
    # File upload settings
    UPLOAD_DIR: str = Field(default="uploads", description="Upload directory")
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024, description="Max file size (10MB)")
    ALLOWED_EXTENSIONS: list = Field(
        default=[".xlsx", ".xls", ".csv", ".json"],
        description="Allowed file extensions"
    )
    
    # Security
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for session management"
    )
    
    # Security
    STORAGE_SECRET_KEY: str = Field(
        default="999555",
        description="Secret key for session management"
    )

    
    class Config:
        env_file = ".env"
        extra = "ignore"

class Settings:
    """Combined settings class."""
    
    def __init__(self):
        self.app = AppSettings()
        self.database = DatabaseSettings()
        
        # Only load OpenAI settings if API key is available
        try:
            self.openai = OpenAISettings()   # 여기서 .env 읽힘
        except Exception:
            self.openai = None


# Global settings instance
settings = Settings()