from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str
    SCAN_INTERVAL_SECONDS: int = 3600
    MORALIS_API_KEY: str
    DEV_MODE_MOCK_API: bool = False # Por defecto, no usar mocks
    MODEL_PATH: str
    N_GPU_LAYERS: int = 0
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None

    class Config:
        env_file = ".env"

settings = Settings()