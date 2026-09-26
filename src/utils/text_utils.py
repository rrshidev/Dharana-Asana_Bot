import logging

from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)


async def send_markdown_safe(bot, chat_id: int, text: str, **kwargs):
    """Отправить текст в режиме Markdown.

    Если Telegram не может разобрать сущности разметки (например, из-за
    висящей звёздочки/подчёркивания в данных), повторяет отправку без
    parse_mode — чтобы пользователь получил текст, а не ошибку.
    """
    try:
        return await bot.send_message(chat_id, text, parse_mode="Markdown", **kwargs)
    except TelegramBadRequest as e:
        raw = getattr(e, "message", "") or str(e)
        if "can't parse entities" in raw.lower():
            logger.warning("Markdown parse failed, resending plain text; error: %s", e)
            kwargs.pop("parse_mode", None)
            return await bot.send_message(chat_id, text, **kwargs)
        raise