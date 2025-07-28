# modules/notifier.py
import logging
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from core.config import settings
from models.recommendation import Recommendation

logger = logging.getLogger(__name__)

class Notifier:
    def __init__(self, token: str | None, chat_id: str | None):
        if token and chat_id:
            self.bot = Bot(token=token)
            self.chat_id = chat_id
            logger.info("El notificador de Telegram está configurado.")
        else:
            self.bot = None
            self.chat_id = None
            logger.warning("El notificador de Telegram no está configurado. No se enviarán alertas.")

    def send_telegram_message(self, message: str):
        """
        Punto de entrada síncrono para enviar un mensaje de forma segura,
        gestionando su propio bucle de eventos de asyncio.
        """
        if not self.bot or not self.chat_id:
            return

        # Esta es la forma segura de ejecutar una corrutina desde código síncrono
        # sin usar asyncio.run() repetidamente.
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:  # 'RuntimeError: There is no current event loop...'
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Crea la tarea y la ejecuta hasta que se complete
        task = loop.create_task(self._send_message_async(message))
        loop.run_until_complete(task)
        # No cerramos el bucle aquí para permitir reutilización si es posible.

    async def _send_message_async(self, message: str):
        """Corrutina que realmente envía el mensaje."""
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='MarkdownV2'
            )
            logger.info(f"Notificación enviada a Telegram Chat ID {self.chat_id}.")
        except TelegramError as e:
            logger.error(f"Error al enviar notificación a Telegram: {e}", exc_info=False)


def escape_markdown_v2(text: str) -> str:
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in str(text))

def format_recommendation_for_telegram(recommendation: Recommendation) -> str:
    metric = recommendation.metric
    position = metric.position
    
    action = escape_markdown_v2(recommendation.recommendation_action)
    justification = escape_markdown_v2(recommendation.justification)
    pool = escape_markdown_v2(f"{position.token0_symbol}/{position.token1_symbol}")
    status = "En Rango" if metric.is_in_range else "Fuera de Rango"
    status_icon = "✅" if metric.is_in_range else "❌"

    message = (
        f"🚨 *Alerta de Posición Uniswap V3* 🚨\n\n"
        f"*Pool:* `{pool}`\n"
        f"*Token ID:* `{position.token_id}`\n\n"
        f"*{status_icon} Estado:* {status}\n"
        f"*Precio Actual:* `${escape_markdown_v2(f'{metric.current_price:.4f}')}`\n"
        f"*Rango de la Posición:* `${escape_markdown_v2(f'{metric.price_lower:.4f}')} \\- ${escape_markdown_v2(f'{metric.price_upper:.4f}')}`\n\n"
        f"🤖 *Recomendación de la IA: {action}*\n"
        f"```{justification}```\n\n"
        f"[Ver Pool en Uniswap](https://info.uniswap.org/#/pools/{position.pool_address})"
    )
    return message


# Instancia global
notifier = Notifier(token=settings.TELEGRAM_BOT_TOKEN, chat_id=settings.TELEGRAM_CHAT_ID)