# src/modules/subgraph_client.py
import logging
import requests
from typing import List, Dict, Any, Optional
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from core.config import settings

logger = logging.getLogger(__name__)

class SubgraphClient:
    def __init__(self, chain: str, query_url: str | None):
        if chain != "eth":
            raise NotImplementedError("Este cliente está configurado para una URL específica de Mainnet.")
        if not query_url:
            raise ValueError("Se requiere la URL de query del proyecto de The Graph Studio en el .env (THEGRAPH_PROJECT_QUERY_URL).")

        transport = RequestsHTTPTransport(url=query_url, retries=3, timeout=30)
        self.client = Client(transport=transport, fetch_schema_from_transport=False)
        logger.info(f"SubgraphClient inicializado usando la URL del proyecto de The Graph Studio.")

    def _get_block_from_timestamp_etherscan(self, timestamp: int) -> Optional[int]:
        """Obtiene el número de bloque más cercano a un timestamp usando la API de Etherscan."""
        if not settings.ETHERSCAN_API_KEY:
            logger.error("Se requiere ETHERSCAN_API_KEY en el .env para obtener datos históricos.")
            return None
        
        url = (
            f"https://api.etherscan.io/api?module=block&action=getblocknobytime"
            f"×tamp={timestamp}&closest=before&apikey={settings.ETHERSCAN_API_KEY}"
        )
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "1":
                block_number = int(data["result"])
                logger.info(f"Timestamp {timestamp} corresponde al bloque {block_number} (vía Etherscan).")
                return block_number
            else:
                logger.error(f"Error de la API de Etherscan al buscar bloque: {data.get('message')}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"No se pudo obtener el bloque desde Etherscan: {e}")
            return None

    def get_historical_pool_price(self, pool_id: str, timestamp: int) -> Optional[float]:
        """Obtiene el precio token0/token1 de un pool en un punto específico del pasado."""
        block_number = self._get_block_from_timestamp_etherscan(timestamp)
        if not block_number:
            return None

        query = gql("""
            query($pool_id: String!, $block: Int!) {
                pool(id: $pool_id, block: {number: $block}) {
                    token0Price
                }
            }
        """)
        params = {"pool_id": pool_id, "block": block_number}
        try:
            result = self.client.execute(query, variable_values=params)
            if result and result.get("pool") and result["pool"].get("token0Price"):
                price = float(result["pool"]["token0Price"])
                logger.info(f"Precio histórico para pool {pool_id} en bloque {block_number} fue {price:.4f}")
                return price
            else:
                logger.warning(f"No se encontraron datos de precio para el pool {pool_id} en el bloque {block_number}.")
                return None
        except Exception as e:
            logger.error(f"No se pudo obtener el precio histórico del pool {pool_id}: {e}")
            return None

    def get_positions_for_wallet(self, owner_address: str) -> List[Dict[str, Any]]:
        """
        Obtiene las posiciones activas para una wallet, incluyendo datos
        para el cálculo de fees y APR.
        """
        query = gql("""
            query($owner: String!) {
                bundle(id: "1") {
                    ethPriceUSD
                }
                positions(where: {owner: $owner, liquidity_gt: 0}) {
                    id
                    transaction { timestamp }
                    pool { 
                        id
                        token0 { id, symbol, derivedETH }
                        token1 { id, symbol, derivedETH }
                        token0Price
                    }
                    tickLower { tickIdx, price0 }
                    tickUpper { tickIdx, price0 }
                    
                    # --- CORRECCIÓN DE LOS NOMBRES DE CAMPO ---
                    collectedFeesToken0 
                    collectedFeesToken1
                    
                    depositedToken0
                    depositedToken1
                }
            }
        """)
        params = {"owner": owner_address.lower()}
        
        try:
            result = self.client.execute(query, variable_values=params)
            eth_price_usd = float(result.get("bundle", {}).get("ethPriceUSD", 0))
            positions = result.get('positions', [])
            
            for pos in positions:
                pos["ethPriceUSD"] = eth_price_usd

            logger.info(f"Subgraph query exitosa. Se encontraron {len(positions)} posiciones activas para la wallet {owner_address}")
            return positions
        except Exception as e:
            logger.error(f"Error al consultar el Subgraph: {e}", exc_info=True)
            return []

subgraph_client = SubgraphClient(chain=settings.CHAIN, query_url=settings.THEGRAPH_PROJECT_QUERY_URL)