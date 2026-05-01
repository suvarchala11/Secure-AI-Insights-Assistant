"""
Central configuration — reads from .env file.
Never hardcode secrets; always pull from environment.
"""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    data_dir: Path = Path("./data")
    docs_dir: Path = Path("./docs")

    # Security: cap how many raw rows the LLM ever sees
    max_rows_to_llm: int = 50

    class Config:
        env_file = ".env"


settings = Settings()
