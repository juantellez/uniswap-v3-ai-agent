# daemon.py
import time
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from core.config import settings

# --- Configuración de Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def scan_positions_task():
    """
    Tarea principal que se ejecutará periódicamente.
    Por ahora, solo imprime un mensaje.
    """
    logger.info("Iniciando ciclo de escaneo de posiciones...")
    # Aquí irá la lógica para:
    # 1. Obtener wallets activas de la BD.
    # 2. Llamar a Moralis.
    # 3. Calcular métricas.
    # 4. Llamar a Qwen3.
    # 5. Guardar resultados y notificar.
    logger.info("Ciclo de escaneo completado. Esperando la próxima ejecución.")

def main():
    """Punto de entrada principal para el daemon."""
    logger.info("Iniciando el Agente de Monitoreo Uniswap V3...")
    
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        scan_positions_task, 
        'interval', 
        seconds=settings.SCAN_INTERVAL_SECONDS,
        id='scan_job' # ID para poder referenciar el trabajo si es necesario
    )
    
    logger.info(f"Tarea de escaneo programada para ejecutarse cada {settings.SCAN_INTERVAL_SECONDS} segundos.")
    logger.info("Presiona Ctrl+C para detener el servicio.")

    try:
        # Ejecutar la primera tarea inmediatamente al iniciar
        scan_positions_task()
        # Iniciar el scheduler
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Deteniendo el servicio.")
        scheduler.shutdown()

if __name__ == "__main__":
    main()