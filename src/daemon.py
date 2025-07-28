# src/daemon.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

import time
import logging
from apscheduler.schedulers.blocking import BlockingScheduler

from core.config import settings
from core.database import SessionLocal
from modules.subgraph_client import subgraph_client 
from modules.qwen_agent import qwen_agent
from modules.notifier import notifier, format_recommendation_for_telegram
from models import Wallet, Position, PositionMetric, Recommendation
# Importamos la nueva función, aunque no la usemos con datos reales todavía
from modules.calculations import calculate_impermanent_loss_simplified

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def sync_position_from_subgraph(db_session, wallet: Wallet, api_position: dict):
    token_id = int(api_position.get('id'))
    db_position = db_session.query(Position).filter(Position.token_id == token_id).first()

    if not db_position:
        logger.info(f"Posición nueva encontrada (Token ID: {token_id}). Creando en la base de datos.")
        db_position = Position(
            token_id=token_id, wallet_id=wallet.id,
            pool_address=api_position.get('pool', {}).get('id'),
            token0_symbol=api_position.get('pool', {}).get('token0', {}).get('symbol'),
            token1_symbol=api_position.get('pool', {}).get('token1', {}).get('symbol'),
            tick_lower=api_position.get('tickLower', {}).get('tickIdx'),
            tick_upper=api_position.get('tickUpper', {}).get('tickIdx'),
        )
        db_session.add(db_position)
    
    current_price = float(api_position.get('pool', {}).get('token0Price'))
    price_lower = float(api_position.get('tickLower', {}).get('price0'))
    price_upper = float(api_position.get('tickUpper', {}).get('price0'))
    if price_lower > price_upper: price_lower, price_upper = price_upper, price_lower
    
    # --- LÓGICA DE CÁLCULO PROVISIONAL ---
    il_percent = 0.0
    logger.info(f"Cálculo de IL provisional para la posición {token_id}: {il_percent:.2f}%")

    new_metric = PositionMetric(
        position=db_position, current_price=current_price,
        price_lower=price_lower, price_upper=price_upper,
        is_in_range=(price_lower <= current_price <= price_upper),
        impermanent_loss_percent=il_percent
    )
    db_session.add(new_metric)
    
    logger.info(f"Generando recomendación de IA para la posición {db_position.token_id}...")
    ai_result = qwen_agent.generate_recommendation(new_metric)
    new_recommendation = Recommendation(
        metric=new_metric, recommendation_action=ai_result["action"],
        justification=ai_result["justification"], raw_model_output=ai_result["raw_output"]
    )
    db_session.add(new_recommendation)
    logger.info(f"Recomendación de la IA ('{ai_result['action']}') guardada.")
    
    if new_recommendation.recommendation_action != "MAINTAIN":
        message = format_recommendation_for_telegram(new_recommendation)
        notifier.send_telegram_message(message)
    else:
        logger.info(f"Acción 'MAINTAIN'. No se enviará notificación.")

def scan_positions_task():
    logger.info("Iniciando ciclo de escaneo de posiciones...")
    db = SessionLocal()
    try:
        active_wallets = db.query(Wallet).filter(Wallet.is_active == True).all()
        if not active_wallets:
            logger.warning("No hay wallets activas para escanear."); return

        for wallet in active_wallets:
            logger.info(f"Escaneando wallet: {wallet.address} en la cadena {settings.CHAIN}...")
            positions_from_api = subgraph_client.get_positions_for_wallet(wallet.address)
            
            if not positions_from_api:
                logger.info(f"No se encontraron posiciones activas para {wallet.address}."); continue

            for api_pos in positions_from_api:
                sync_position_from_subgraph(db, wallet, api_pos)
            db.commit()
            logger.info(f"Escaneo completado para la wallet: {wallet.address}")

    except Exception as e:
        logger.error(f"Error inesperado en el ciclo de escaneo: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()
    
    logger.info("Ciclo de escaneo finalizado. Esperando la próxima ejecución.")

def main():
    logger.info("Iniciando el Agente de Monitoreo Uniswap V3...")
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(scan_positions_task, 'interval', seconds=settings.SCAN_INTERVAL_SECONDS, id='scan_job')
    logger.info(f"Tarea programada para ejecutarse cada {settings.SCAN_INTERVAL_SECONDS} segundos.")
    logger.info("Presiona Ctrl+C para detener el servicio.")
    try:
        scan_positions_task()
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Deteniendo el servicio."); scheduler.shutdown()

if __name__ == "__main__":
    main()