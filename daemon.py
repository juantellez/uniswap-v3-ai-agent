# daemon.py
import sys
import os
import time
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from core.config import settings
from core.database import SessionLocal
from modules.moralis_client import moralis_client

# Modelos
from models.wallet import Wallet
from models.position import Position
from models.metric import PositionMetric
from modules.qwen_agent import qwen_agent
from models.recommendation import Recommendation
from modules.notifier import notifier, format_recommendation_for_telegram

# --- Configuración de Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def sync_position_from_api(db_session, wallet: Wallet, api_position: dict):
    """Sincroniza una posición individual desde la API a la BD."""
    token_id = int(api_position.get('token_id'))
    
    # 1. Busca si la posición ya existe
    db_position = db_session.query(Position).filter(Position.token_id == token_id).first()

    if not db_position:
        # 2. Si no existe, la crea
        logger.info(f"Posición nueva encontrada (Token ID: {token_id}). Creando en la base de datos.")
        db_position = Position(
            token_id=token_id,
            wallet_id=wallet.id,
            pool_address=api_position.get('pool', {}).get('address'),
            token0_symbol=api_position.get('token0', {}).get('symbol'),
            token1_symbol=api_position.get('token1', {}).get('symbol'),
            tick_lower=api_position.get('tick_lower'),
            tick_upper=api_position.get('tick_upper'),
        )
        db_session.add(db_position)
        # No es necesario hacer commit aquí, flush() más tarde es suficiente
    
    # 3. Crea una nueva entrada de métricas
    current_price = float(api_position.get('pool', {}).get('token0_price'))
    price_lower = float(api_position.get('price_lower'))
    price_upper = float(api_position.get('price_upper'))

    new_metric = PositionMetric(
        position=db_position, # Asignamos el objeto Position completo
        current_price=current_price,
        price_lower=price_lower,
        price_upper=price_upper,
        is_in_range=(price_lower <= current_price <= price_upper)
    )
    db_session.add(new_metric)
    
    # 4. Generar y guardar recomendación de la IA
    logger.info(f"Generando recomendación de IA para la posición {db_position.token_id}...")
    ai_result = qwen_agent.generate_recommendation(new_metric)
    
    new_recommendation = Recommendation(
        metric=new_metric,
        recommendation_action=ai_result["action"],
        justification=ai_result["justification"],
        raw_model_output=ai_result["raw_output"]
    )
    db_session.add(new_recommendation)
    logger.info(f"Recomendación de la IA ('{ai_result['action']}') guardada.")
    
    # 5. Enviar notificación si es relevante
    if new_recommendation.recommendation_action != "MAINTAIN":
        # Ahora new_recommendation tiene acceso a .metric y .metric.position
        message = format_recommendation_for_telegram(new_recommendation)
        notifier.send_telegram_message(message)
    else:
        logger.info(f"Acción 'MAINTAIN' para la posición {db_position.token_id}. No se enviará notificación.")


def scan_positions_task():
    """Tarea principal que se ejecutará periódicamente."""
    logger.info("Iniciando ciclo de escaneo de posiciones...")
    db = SessionLocal()
    try:
        # 1. Obtener wallets activas de la BD
        active_wallets = db.query(Wallet).filter(Wallet.is_active == True).all()
        if not active_wallets:
            logger.warning("No hay wallets activas en la base de datos para escanear. Agrega una wallet para comenzar.")
            return

        for wallet in active_wallets:
            logger.info(f"Escaneando wallet: {wallet.address}")
            # 2. Llamar a Moralis para obtener posiciones
            positions_from_api = moralis_client.get_uniswap_v3_positions(wallet.address)
            
            for api_pos in positions_from_api:
                sync_position_from_api(db, wallet, api_pos)

            db.commit() # Commit final de la sesión para esta wallet
            logger.info(f"Escaneo completado para la wallet: {wallet.address}")

    except Exception as e:
        logger.error(f"Ocurrió un error inesperado durante el ciclo de escaneo: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()
    
    logger.info("Ciclo de escaneo finalizado. Esperando la próxima ejecución.")


def main():
    logger.info("Iniciando el Agente de Monitoreo Uniswap V3...")
    
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        scan_positions_task, 
        'interval', 
        seconds=settings.SCAN_INTERVAL_SECONDS,
        id='scan_job'
    )
    
    logger.info(f"Tarea de escaneo programada para ejecutarse cada {settings.SCAN_INTERVAL_SECONDS} segundos.")
    logger.info("Presiona Ctrl+C para detener el servicio.")

    try:
        scan_positions_task()
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Deteniendo el servicio.")
        scheduler.shutdown()

if __name__ == "__main__":
    main()