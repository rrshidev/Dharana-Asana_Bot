import logging
import os
from datetime import datetime
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

API_URL = os.getenv("API_URL", "http://dharana-api:8000")
TIMER_BOT_KEY = os.getenv("TIMER_BOT_KEY", "")


class UserService:
    """Запись завершённой практики таймера в общую статистику Dharana.

    Единый источник статистики — dharana-api (та же БД, что у app/web).
    Контракт совпадает с timerasana: POST /api/v1/practice/timer,
    аутентификация по X-Timer-Key. Сбой записи не ломает практику — только логируем.
    """

    def __init__(self, api_url: str = API_URL, timer_bot_key: str = TIMER_BOT_KEY):
        self.api_url = api_url
        self.timer_bot_key = timer_bot_key

    async def record_practice(
        self,
        telegram_id: int,
        practice_type: str,
        total_duration_seconds: int | None = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ) -> bool:
        """Записать завершённую практику таймера: POST /api/v1/practice/timer.

        Не блокирует цикл таймера: при сбое только логируем, ошибка не должна
        прерывать завершение практики.
        """
        if total_duration_seconds is None or total_duration_seconds <= 0:
            return False
        try:
            headers: dict = {}
            if self.timer_bot_key:
                headers["X-Timer-Key"] = self.timer_bot_key
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.api_url}/api/v1/practice/timer",
                    headers=headers,
                    json={
                        "telegram_id": telegram_id,
                        "practice_type": practice_type,
                        "total_duration_seconds": total_duration_seconds,
                        "started_at": started_at.isoformat() if started_at else None,
                        "completed_at": (
                            completed_at.isoformat()
                            if completed_at
                            else datetime.now().isoformat()
                        ),
                    },
                    timeout=10,
                )
            if resp.status_code == 200:
                logger.info(
                    f"Practice recorded for {telegram_id}: {practice_type} "
                    f"{total_duration_seconds}s (id={resp.json().get('id', 'n/a')})"
                )
                return True
            logger.warning(
                f"Record practice failed for {telegram_id}: {resp.status_code} {resp.text}"
            )
        except Exception as e:
            logger.error(f"Error recording practice for {telegram_id}: {e}")
        return False
