"""
Background tasks that run periodically.
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import select

from database import AsyncSessionLocal, Device
from config import settings
from services.telegram import notify_device_offline

logger = logging.getLogger(__name__)

# Track which devices we already notified as offline to avoid spam
_notified_offline: set = set()

async def check_offline_devices():
    """
    Runs every 60 seconds.
    Marks devices as offline if no heartbeat received within threshold.
    Sends Telegram notification once per offline transition.
    """
    while True:
        await asyncio.sleep(60)
        try:
            async with AsyncSessionLocal() as db:
                threshold = datetime.now(timezone.utc) - timedelta(seconds=settings.OFFLINE_THRESHOLD_SECONDS)
                result = await db.execute(select(Device))
                devices = result.scalars().all()

                for device in devices:
                    last_seen = device.last_seen.replace(tzinfo=timezone.utc) if device.last_seen.tzinfo is None else device.last_seen
                    is_offline = last_seen < threshold

                    if is_offline and device.status != "offline":
                        device.status = "offline"
                        await db.commit()

                        # Notify only once per offline transition
                        if device.id not in _notified_offline:
                            _notified_offline.add(device.id)
                            await notify_device_offline(device.name, device.id, device.telegram_chat_id)
                            logger.info(f"Device {device.id} went offline, notification sent")

                    elif not is_offline and device.id in _notified_offline:
                        # Device is back online, reset notification flag
                        _notified_offline.discard(device.id)
                        logger.info(f"Device {device.id} is back online")

        except Exception as e:
            logger.error(f"Error in offline check task: {e}")
