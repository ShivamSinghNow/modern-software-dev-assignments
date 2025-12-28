"""
Application configuration management.
Centralizes all configuration settings and environment variables.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "Action Item Extractor"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database
    database_dir: Path = Path(__file__).resolve().parents[1] / "data"
    database_path: Optional[Path] = None
    
    # LLM Configuration
    ollama_model: str = "llama3.2"
    ollama_base_url: str = "http://localhost:11434"
    
    # Frontend
    frontend_dir: Path = Path(__file__).resolve().parents[1] / "frontend"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> any:
            """Parse environment variables, handling Path types."""
            if field_name in ("database_dir", "database_path", "frontend_dir"):
                return Path(raw_val)
            return cls.json_loads(raw_val)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set default database path if not provided
        if self.database_path is None:
            self.database_path = self.database_dir / "app.db"
        # Ensure directories exist
        self.database_dir.mkdir(parents=True, exist_ok=True)
        self.frontend_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()

