# src/core/config.py
import os
import logging
from typing import Optional
from pydantic import BaseSettings

# --- 1. Definiciones ---
logger = logging.getLogger(__name__)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# --- 2. Clase de Configuración ---
class Settings(BaseSettings):
    # --- Database ---
    DATABASE_URL: str = f"sqlite:///{os.path.join(PROJECT_ROOT, 'src/data/agent.db')}"

    # --- Scheduler ---
    SCAN_INTERVAL_SECONDS: int = 3600

    # --- The Graph ---
    THEGRAPH_PROJECT_QUERY_URL: Optional[str] = None

    # --- Development ---
    DEV_MODE_MOCK_API: bool = False

    # --- AI Agent ---
    MODEL_PATH: str = os.path.join(PROJECT_ROOT, "models/llm/qwen3-4b-q8_0.gguf")
    N_GPU_LAYERS: int = 0
    
    # --- Blockchain ---
    CHAIN: str = "eth"

    # --- Notifications ---
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None

    class Config:
        env_file = os.path.join(PROJECT_ROOT, ".env")

# --- 3. Instancia ---
settings = Settings()

# --- 4. Verificación ---
if not settings.THEGRAPH_PROJECT_QUERY_URL and not settings.DEV_MODE_MOCK_API:
    logger.error("¡ERROR CRÍTICO! Se requiere THEGRAPH_PROJECT_QUERY_URL en el archivo .env.")
else:
    logger.info("Configuración de The Graph cargada exitosamente.")