"""
Configuration settings for Kodex Code Review Agent.
Loads configuration from environment variables and .env file.
Configured for live Vectorize Hindsight Cloud and Groq production endpoints.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)


@dataclass
class Config:
    # Flask Server Settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "5000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

    # Groq API Configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    # Using openai/gpt-oss-120b as verified on Groq API
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    GROQ_FALLBACK_MODEL: str = os.getenv("GROQ_FALLBACK_MODEL", "qwen/qwen3.8-27b")
    GROQ_TEMPERATURE: float = float(os.getenv("GROQ_TEMPERATURE", "0.2"))
    GROQ_MAX_TOKENS: int = int(os.getenv("GROQ_MAX_TOKENS", "2500"))

    # Hindsight API Configuration (Live Vectorize Cloud)
    HINDSIGHT_BASE_URL: str = os.getenv(
        "HINDSIGHT_BASE_URL",
        "https://api.hindsight.vectorize.io"
    )
    HINDSIGHT_API_KEY: str = os.getenv("HINDSIGHT_API_KEY", "")
    HINDSIGHT_BANK_ID: str = os.getenv("HINDSIGHT_BANK_ID", "repo-standards")
    HINDSIGHT_TIMEOUT: float = float(os.getenv("HINDSIGHT_TIMEOUT", "30.0"))

    # Fallback simulation mode (only if network fails completely)
    ALLOW_MOCK_FALLBACK: bool = os.getenv("ALLOW_MOCK_FALLBACK", "false").lower() in ("true", "1", "yes")


config = Config()
