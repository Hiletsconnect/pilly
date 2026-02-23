import httpx
import logging
from config import settings

logger = logging.getLogger(__name__)

async def send_telegram(chat_id: str, message: str) -> bool:
    """Send a Telegram message to a specific chat_id."""
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        logger.warning("Telegram bot token not configured")
        return False

    target_chat = chat_id or settings.TELEGRAM_CHAT_ID
    if not target_chat:
        logger.warning("No Telegram chat_id provided or configured")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": target_chat,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                logger.info(f"Telegram message sent to {target_chat}")
                return True
            else:
                logger.error(f"Telegram error {resp.status_code}: {resp.text}")
                return False
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return False

async def notify_alarm(device_name: str, device_id: str, compartment: int,
                       scheduled_time: str, chat_id: str = "") -> bool:
    msg = (
        f"💊 <b>¡Hora de tomar la pastilla!</b>\n\n"
        f"📦 Dispositivo: <b>{device_name}</b>\n"
        f"🗂 Compartimento: <b>{compartment + 1}</b>\n"
        f"🕐 Horario: <b>{scheduled_time}</b>\n\n"
        f"<i>ID: {device_id}</i>"
    )
    return await send_telegram(chat_id, msg)

async def notify_dose_missed(device_name: str, device_id: str, compartment: int,
                              scheduled_time: str, chat_id: str = "") -> bool:
    msg = (
        f"⚠️ <b>Dosis NO tomada</b>\n\n"
        f"📦 Dispositivo: <b>{device_name}</b>\n"
        f"🗂 Compartimento: <b>{compartment + 1}</b>\n"
        f"🕐 Horario programado: <b>{scheduled_time}</b>\n\n"
        f"El pastillero no registró confirmación de toma.\n"
        f"<i>ID: {device_id}</i>"
    )
    return await send_telegram(chat_id, msg)

async def notify_device_offline(device_name: str, device_id: str, chat_id: str = "") -> bool:
    msg = (
        f"🔴 <b>Dispositivo desconectado</b>\n\n"
        f"📦 <b>{device_name}</b> perdió conexión con el servidor.\n"
        f"Las alarmas locales siguen funcionando.\n\n"
        f"<i>ID: {device_id}</i>"
    )
    return await send_telegram(chat_id, msg)

async def notify_reboot(device_name: str, device_id: str, chat_id: str = "") -> bool:
    msg = (
        f"🔁 <b>Reinicio remoto enviado</b>\n\n"
        f"📦 El dispositivo <b>{device_name}</b> fue reiniciado remotamente.\n\n"
        f"<i>ID: {device_id}</i>"
    )
    return await send_telegram(chat_id, msg)
    