# src/modules/calculations.py
import math

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