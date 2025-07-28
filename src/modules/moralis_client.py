# src/modules/moralis_client.py
import logging
from typing import List, Dict, Any, Optional
from moralis import evm_api
from core.config import settings

logger = logging.getLogger(__name__)

# Direcciones del contrato NonfungiblePositionManager de Uniswap V3
UNISWAP_V3_CONTRACTS = {
    "eth": "0xC36442b4a4522E871399CD717aDd847Ab11FE88",
    "sepolia": "0x1238536071E1c279A02540BC548F303C23130283",
}

# El ABI mínimo necesario para llamar a la función `positions` del contrato
UNISWAP_V3_ABI = [{
    "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
    "name": "positions",
    "outputs": [
        {"internalType": "uint96", "name": "nonce", "type": "uint96"},
        {"internalType": "address", "name": "operator", "type": "address"},
        {"internalType": "address", "name": "token0", "type": "address"},
        {"internalType": "address", "name": "token1", "type": "address"},
        {"internalType": "uint24", "name": "fee", "type": "uint24"},
        {"internalType": "int24", "name": "tickLower", "type": "int24"},
        {"internalType": "int24", "name": "tickUpper", "type": "int24"},
        {"internalType": "uint128", "name": "liquidity", "type": "uint128"},
        {"internalType": "uint256", "name": "feeGrowthInside0LastX128", "type": "uint256"},
        {"internalType": "uint256", "name": "feeGrowthInside1LastX128", "type": "uint256"},
        {"internalType": "uint128", "name": "tokensOwed0", "type": "uint128"},
        {"internalType": "uint128", "name": "tokensOwed1", "type": "uint128"}
    ],
    "stateMutability": "view",
    "type": "function"
}]

class MoralisClient:
    def __init__(self, api_key: str | None):
        if not api_key:
            logger.warning("No se proporcionó una API Key de Moralis. El cliente solo funcionará en modo mock.")
            self.api_key = ""
        else:
            self.api_key = api_key
            logger.info("MoralisClient inicializado con API Key.")
            
    def _get_pool_details_from_nft_metadata(self, nft: Dict[str, Any]) -> Dict[str, Any]:
        """Extrae la información del pool del campo de metadatos del NFT."""
        metadata = nft.get("normalized_metadata", {})
        attributes = metadata.get("attributes", [])
        
        pool_details = {}
        for attr in attributes:
            trait_type = attr.get("trait_type", "").lower()
            if "token 0" in trait_type:
                pool_details["token0_symbol"] = attr.get("value")
            elif "token 1" in trait_type:
                pool_details["token1_symbol"] = attr.get("value")
        return pool_details

    def get_all_positions_for_wallet(self, wallet_address: str) -> List[Dict[str, Any]]:
        """
        Obtiene todas las posiciones de Uniswap V3 para una wallet usando un proceso de 3 pasos.
        1. Obtiene todos los NFTs de la wallet.
        2. Filtra para encontrar solo los que son posiciones de Uniswap V3.
        3. Para cada posición, llama al contrato para obtener los detalles del rango y el precio.
        """
        logger.info(f"Iniciando proceso de obtención de posiciones para {wallet_address} con Moralis...")
        contract_address = UNISWAP_V3_CONTRACTS.get(settings.CHAIN)
        if not contract_address:
            raise ValueError(f"Dirección de contrato de Uniswap V3 no definida para la cadena: {settings.CHAIN}")

        # --- Paso 1 y 2: Obtener y filtrar NFTs de Uniswap V3 ---
        try:
            params = {"chain": settings.CHAIN, "format": "decimal", "media_items": False, "address": wallet_address}
            nfts_result = evm_api.nft.get_wallet_nfts(api_key=self.api_key, params=params)
            
            uniswap_nfts = [nft for nft in nfts_result.get("result", []) if nft["token_address"].lower() == contract_address.lower()]
            logger.info(f"Se encontraron {len(uniswap_nfts)} NFTs de Uniswap V3.")
        except Exception as e:
            logger.error(f"Error al obtener NFTs de Moralis: {e}", exc_info=True)
            return []

        # --- Paso 3: Obtener detalles de cada posición y precio del pool ---
        all_positions_data = []
        for nft in uniswap_nfts:
            try:
                token_id = nft["token_id"]
                logger.info(f"Procesando Token ID: {token_id}...")

                # Obtener detalles de la posición (ticks)
                params = {
                    "chain": settings.CHAIN,
                    "address": contract_address,
                    "function_name": "positions",
                    "abi": UNISWAP_V3_ABI,
                    "params": {"tokenId": token_id}
                }
                position_details = evm_api.smart_contract.run_contract_function(api_key=self.api_key, params=params)
                
                token0_address = position_details.get("token0")
                if not token0_address:
                    logger.warning(f"No se pudo obtener la dirección de token0 para el Token ID {token_id}. Saltando.")
                    continue
                
                # Obtener el precio actual del pool (usando el precio de token0)
                price_params = {"chain": settings.CHAIN, "address": token0_address}
                price_result = evm_api.token.get_token_price(api_key=self.api_key, params=price_params)
                
                # Combinar todos los datos en el formato que nuestra aplicación espera
                pool_details_from_meta = self._get_pool_details_from_nft_metadata(nft)
                tick_lower = int(position_details["tickLower"])
                tick_upper = int(position_details["tickUpper"])
                
                # Moralis no devuelve el precio del tick, solo el tick. 
                # Calculamos el precio desde el tick. Es una fórmula estándar de Uniswap V3.
                price_lower = 1.0001 ** tick_lower
                price_upper = 1.0001 ** tick_upper

                # Si token0 es WETH/ETH, los precios estarán invertidos (ej. USDC/WETH).
                # La heurística es que si el precio es < 1, probablemente es un par invertido.
                if price_upper < 1 and price_result["usd_price"] > 1:
                     price_lower = 1 / (1.0001 ** tick_upper)
                     price_upper = 1 / (1.0001 ** tick_lower)
                
                formatted_position = {
                    "id": token_id,
                    "pool": {
                        "id": "N/A - Se requiere llamada adicional a 'tokenURI'",
                        "token0": {"symbol": pool_details_from_meta.get("token0_symbol", "TOKEN0")},
                        "token1": {"symbol": pool_details_from_meta.get("token1_symbol", "TOKEN1")},
                        "token0Price": price_result.get("usd_price", 0)
                    },
                    "tickLower": {"tickIdx": str(tick_lower), "price0": price_lower},
                    "tickUpper": {"tickIdx": str(tick_upper), "price0": price_upper}
                }
                all_positions_data.append(formatted_position)

            except Exception as e:
                logger.error(f"Error al procesar el Token ID {nft.get('token_id')}: {e}", exc_info=True)
                continue
        
        logger.info(f"Proceso completado. Se han formateado {len(all_positions_data)} posiciones.")
        return all_positions_data

# Instancia global
moralis_client = MoralisClient(api_key=settings.MORALIS_API_KEY)