from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SCAN_INTERVAL_SECONDS: int = 3600
    MORALIS_API_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()