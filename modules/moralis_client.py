# modules/moralis_client.py
import requests
import logging
import json
import os
from typing import List, Dict, Any
from core.config import settings

logger = logging.getLogger(__name__)

class MoralisClient:
    def __init__(self, api_key: str, use_mock: bool = False):
        self.api_key = api_key
        self.use_mock = use_mock
        self.base_url = "https://deep-index.moralis.io/api/v2.2"
        self.mock_file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'mock_moralis_response.json')

    def _get_mock_data(self) -> List[Dict[str, Any]]:
        """Carga los datos desde el archivo JSON de mock."""
        logger.warning("MODO MOCK ACTIVADO: Usando datos de 'mock_moralis_response.json' en lugar de la API real.")
        try:
            with open(self.mock_file_path, 'r') as f:
                data = json.load(f)
                return data.get('positions', [])
        except FileNotFoundError:
            logger.error(f"Archivo mock no encontrado en: {self.mock_file_path}")
            return []
        except json.JSONDecodeError:
            logger.error(f"Error al decodificar el archivo JSON mock: {self.mock_file_path}")
            return []

    def get_uniswap_v3_positions(self, wallet_address: str) -> List[Dict[str, Any]]:
        """
        Obtiene las posiciones de liquidez de Uniswap V3 para una wallet.
        Usa datos mock si está configurado.
        """
        if self.use_mock:
            return self._get_mock_data()

        # --- Lógica de la API real (se mantiene igual) ---
        url = f"{self.base_url}/wallets/{wallet_address}/positions"
        # ... resto de la lógica de requests
        # ...
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Se encontraron {len(data.get('positions', []))} posiciones para la wallet {wallet_address}")
            return data.get('positions', [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al contactar la API de Moralis: {e}")
            return []


# Instancia global que usaremos en el resto de la aplicación
moralis_client = MoralisClient(
    api_key=settings.MORALIS_API_KEY, 
    use_mock=settings.DEV_MODE_MOCK_API
)