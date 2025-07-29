# src/modules/calculations.py
import math
from datetime import datetime, timezone

def calculate_impermanent_loss_simplified(
    initial_price_ratio: float, 
    current_price_ratio: float
) -> float:
    """
    Calcula la pérdida impermanente porcentual usando la fórmula simplificada.
    IL = (2 * sqrt(price_ratio) / (1 + price_ratio)) - 1
    donde price_ratio = current_price / initial_price.
    """
    if initial_price_ratio == 0:
        return 0.0
        
    price_ratio = current_price_ratio / initial_price_ratio
    
    if price_ratio < 0: # Evitar errores de dominio matemático
        return 0.0

    il = (2 * math.sqrt(price_ratio)) / (1 + price_ratio) - 1
    
    return il * 100 # Devolver como porcentaje (será un número negativo o cero)

def calculate_unclaimed_fees_usd(
    uncollected_fees_token0: float,
    uncollected_fees_token1: float,
    price_token0_usd: float,
    price_token1_usd: float
) -> float:
    """Calcula el valor total en USD de las comisiones no reclamadas."""
    fees0_usd = uncollected_fees_token0 * price_token0_usd
    fees1_usd = uncollected_fees_token1 * price_token1_usd
    return fees0_usd + fees1_usd

def calculate_real_apr(
    fees_usd: float,
    total_liquidity_usd: float,
    creation_timestamp: int,
    il_percent: float
) -> float:
    """Calcula una estimación del APR real (Fee APR + IL)."""
    if total_liquidity_usd == 0:
        return 0.0

    # Calcular la antigüedad de la posición en días
    current_timestamp = int(datetime.now(timezone.utc).timestamp())
    age_seconds = current_timestamp - creation_timestamp
    if age_seconds <= 0:
        return 0.0 # Evitar división por cero
    age_days = age_seconds / (60 * 60 * 24)

    # Calcular Fee APR
    fees_per_day = fees_usd / age_days
    annualized_fees = fees_per_day * 365
    fee_apr = (annualized_fees / total_liquidity_usd) * 100

    # El IL ya es un porcentaje, pero representa la pérdida total.
    # Para compararlo con el APR, debemos anualizarlo también.
    il_annualized = (il_percent / age_days) * 365
    
    real_apr = fee_apr + il_annualized
    return real_apr