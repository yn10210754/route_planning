# backend/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    gaode_key: str = ""
    backend_cors_origins: list[str] = ["*"]

    def ensure_gaode_key(self) -> str:
        if not self.gaode_key:
            raise ValueError("GAODE_KEY environment variable is required")
        return self.gaode_key

settings = Settings()
