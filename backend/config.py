"""
Configuration management for the Roof Design Validation System
Handles environment variables, API keys, and application settings
"""

import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv
from cors_config import parse_allowed_origin_regex, parse_allowed_origins

# Load environment variables from .env file
load_dotenv()

@dataclass
class Config:
    """Application configuration settings"""
    
    # Required parameters (no defaults)
    openai_api_key: str
    database_url: str
    jwt_secret_key: str
    
    # Optional parameters (with defaults)
    openai_api_base: str = "https://api.openai.com/v1"
    openai_main_model: str = "gpt-5.1"
    openai_summary_model: str = "gpt-5-mini"
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True
    environment: str = "development"
    allowed_origins: list = None
    allowed_origin_regex: Optional[str] = None
    track_api_costs: bool = True
    log_level: str = "INFO"
    frontend_url: str = "http://localhost:3000"
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required but not set")
        
        if not self.database_url:
            raise ValueError("DATABASE_URL is required but not set")
        
        if not self.jwt_secret_key:
            raise ValueError("JWT_SECRET_KEY is required but not set")
        
        if self.allowed_origins is None:
            self.allowed_origins = [
                "http://localhost:3000",
                "http://127.0.0.1:3000"
            ]

def get_config() -> Config:
    """
    Load configuration from environment variables
    
    Returns:
        Config: Application configuration object
        
    Raises:
        ValueError: If required environment variables are missing
    """
    
    # Required configuration
    openai_api_key = (
        os.getenv("OPENAI_API_KEY")
        or os.getenv("NAVIGATOR_API_KEY")
        or os.getenv("MISTRAL_API_KEY")
        or os.getenv("GPT52_API_KEY")
    )
    if not openai_api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is required. "
            "Please set it in your .env file or environment."
        )
    
    # Database configuration
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError(
            "DATABASE_URL environment variable is required. "
            "Please set it in your .env file or environment."
        )
    
    # JWT Secret configuration
    jwt_secret_key = os.getenv("JWT_SECRET_KEY")
    if not jwt_secret_key:
        raise ValueError(
            "JWT_SECRET_KEY environment variable is required. "
            "Please set it in your .env file or environment."
        )
    
    # Optional configuration with defaults
    config = Config(
        openai_api_key=openai_api_key,
        openai_api_base=(
            os.getenv("OPENAI_API_BASE")
            or os.getenv("NAVIGATOR_BASE_URL")
            or os.getenv("MISTRAL_API_BASE")
            or "https://api.openai.com/v1"
        ),
        openai_main_model=os.getenv("OPENAI_MAIN_MODEL", "gpt-5.1"),
        openai_summary_model=os.getenv("OPENAI_SUMMARY_MODEL", "gpt-5-mini"),
        database_url=database_url,
        jwt_secret_key=jwt_secret_key,
        host=os.getenv("HOST", "0.0.0.0"),  # Changed for cloud deployment
        port=int(os.getenv("PORT", "8000")),
        debug=os.getenv("DEBUG", "false").lower() == "true",  # Changed default for production
        environment=os.getenv("ENVIRONMENT", "production"),  # Changed default
        track_api_costs=os.getenv("TRACK_API_COSTS", "true").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        frontend_url=os.getenv("FRONTEND_URL", "http://localhost:3000")
    )
    
    # Parse allowed origins with strict validation.
    # Wildcards are forbidden because CORS credentials are enabled.
    origins_str = os.getenv("ALLOWED_ORIGINS", "")
    config.allowed_origins = parse_allowed_origins(origins_str)
    config.allowed_origin_regex = parse_allowed_origin_regex(os.getenv("ALLOWED_ORIGIN_REGEX", ""))
    
    return config

# Global configuration instance
settings = get_config()
