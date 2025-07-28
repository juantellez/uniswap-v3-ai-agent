# src/modules/notifier.py
import logging
import asyncio
from telegram import Bot
from telegram.error import TelegramError
# --- NUEVA IMPORTACIÓN ---
from telegram.helpers import escape_markdown

from core.config import settings
from models.recommendation import Recommendation

logger = logging.getLogger(__name__)

class Notifier:
    # ... (el __init__ y el _send_message_async se mantienen igual) ...
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
        if not self.bot or not self.chat_id: return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        task = loop.create_task(self._send_message_async(message))
        loop.run_until_complete(task)

    async def _send_message_async(self, message: str):
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='MarkdownV2'
            )
            logger.info(f"Notificación enviada a Telegram Chat ID {self.chat_id}.")
        except TelegramError as e:
            logger.error(f"Error al enviar notificación a Telegram: {e}", exc_info=False)

# --- FUNCIÓN DE ESCAPE ELIMINADA ---
# ya no necesitamos nuestra función `escape_markdown_v2`

def format_recommendation_for_telegram(recommendation: Recommendation) -> str:
    metric = recommendation.metric
    position = metric.position
    
    # --- USAMOS LA FUNCIÓN OFICIAL ---
    # Nota: `version=2` es para MarkdownV2
    action = escape_markdown(recommendation.recommendation_action, version=2)
    justification = escape_markdown(recommendation.justification, version=2)
    pool = escape_markdown(f"{position.token0_symbol}/{position.token1_symbol}", version=2)
    status = "En Rango" if metric.is_in_range else "Fuera de Rango"
    status_icon = "✅" if metric.is_in_range else "❌"
    il_percent = metric.impermanent_loss_percent
    il_icon = "🔻" if il_percent < 0 else "📈"

    # Pre-formateamos los números antes de escaparlos
    current_price_str = f'{metric.current_price:.4f}'
    price_lower_str = f'{metric.price_lower:.4f}'
    price_upper_str = f'{metric.price_upper:.4f}'

    message = (
        f"🚨 *Alerta de Posición Uniswap V3* 🚨\n\n"
        f"*Pool:* `{pool}`\n"
        f"*Token ID:* `{position.token_id}`\n\n"
        f"*{status_icon} Estado:* {status}\n"
        f"*Precio Actual:* `${escape_markdown(current_price_str, version=2)}`\n"
        f"*Rango de la Posición:* `${escape_markdown(price_lower_str, version=2)} \\- ${escape_markdown(price_upper_str, version=2)}`\n"
        f"*{il_icon} Pérdida Impermanente \\(IL\\):* `{escape_markdown(f'{il_percent:.2f}', version=2)}%`\n\n"
        f"🤖 *Recomendación de la IA: {action}*\n"
        f"```{justification}```\n\n"
        # La URL en sí no debe ser escapada, pero su texto sí.
        f"[Ver Pool en Uniswap](https://info.uniswap.org/#/pools/{position.pool_address})"
    )
    return message

# Instancia global (se mantiene igual)
notifier = Notifier(token=settings.TELEGRAM_BOT_TOKEN, chat_id=settings.TELEGRAM_CHAT_ID)