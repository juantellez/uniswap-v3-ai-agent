# src/modules/subgraph_client.py
import logging
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

    def get_positions_for_wallet(self, owner_address: str) -> List[Dict[str, Any]]:
        # Query mejorada para obtener datos necesarios para IL en el futuro
        query = gql("""
            query($owner: String!) {
                positions(where: {owner: $owner, liquidity_gt: 0}) {
                    id
                    transaction { timestamp }
                    pool { 
                        id
                        token0 { id, symbol }
                        token1 { id, symbol }
                        token0Price
                    }
                    tickLower { tickIdx, price0 }
                    tickUpper { tickIdx, price0 }
                    depositedToken0
                    depositedToken1
                }
            }
        """)
        params = {"owner": owner_address.lower()}
        
        try:
            result = self.client.execute(query, variable_values=params)
            positions = result.get('positions', []) if result else []
            logger.info(f"Subgraph query exitosa. Se encontraron {len(positions)} posiciones activas para la wallet {owner_address}")
            return positions
        except Exception as e:
            logger.error(f"Error al consultar el Subgraph: {e}", exc_info=True)
            return []

subgraph_client = SubgraphClient(chain=settings.CHAIN, query_url=settings.THEGRAPH_PROJECT_QUERY_URL)