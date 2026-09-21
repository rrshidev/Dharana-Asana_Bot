import logging
import os
import httpx
from aiogram import types
from aiogram.enums import ParseMode
from aiogram.filters import Command

from src.i18n import t, lang_from_telegram
from src.services.database_service import db_service
from src.utils.keyboard_service import KeyboardService

logger = logging.getLogger(__name__)

API_URL = os.getenv("API_URL", "http://dharana-api:8000")


class CommandHandlers:
    """Обработчики команд бота"""

    def __init__(self, bot):
        self.bot = bot
        self.keyboard_service = KeyboardService()

    @staticmethod
    def _lang(message: types.Message) -> str:
        """Язык пользователя для данного сообщения."""
        return db_service.get_user_language(message.from_user.id)

    async def start_command(self, message: types.Message):
        """Обработчик команды /start"""
        text = message.text or ""
        payload = text.split(" ", 1)[1] if " " in text else ""
        telegram_id = message.from_user.id
        name = message.from_user.first_name or ""
        username = message.from_user.username or ""
        display_name = name or username or ""
        tg_lang = lang_from_telegram(message.from_user.language_code)

        # Always register/sync user in DB
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{API_URL}/api/v1/auth/telegram/create-code",
                    json={
                        "telegram_id": telegram_id,
                        "name": name,
                        "username": username,
                        "language": tg_lang,
                    },
                    timeout=10,
                )
        except Exception as e:
            logger.error(f"Error registering user: {e}")

        # Локальное зеркало (язык заполняется только при первом контакте)
        try:
            db_service.get_or_create_user(
                telegram_id, username, name, language=tg_lang
            )
        except Exception as e:
            logger.error(f"Error syncing user in bot DB: {e}")

        lang = db_service.get_user_language(telegram_id)

        if payload == "auth":
            # Show the code for app login
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        f"{API_URL}/api/v1/auth/telegram/create-code",
                        json={
                            "telegram_id": telegram_id,
                            "name": name,
                            "username": username,
                            "language": tg_lang,
                        },
                        timeout=10,
                    )
                    if resp.status_code == 200:
                        code = resp.json()["code"]
                        await message.reply(
                            t(lang, 'auth_code_text', code=code),
                            parse_mode=ParseMode.MARKDOWN,
                        )
                        return
                    else:
                        logger.error(f"Failed to create telegram code: {resp.text}")
            except Exception as e:
                logger.error(f"Error creating telegram code: {e}")

            await message.reply(
                t(lang, 'auth_error'),
            )
            return

        greeting = t(lang, 'start_greeting_named', name=display_name) if display_name else t(lang, 'start_greeting')

        welcome_text = f"{greeting}\n\n{t(lang, 'start_welcome')}"

        await message.reply(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=self.keyboard_service.create_start_menu(lang),
        )

    async def help_command(self, message: types.Message):
        """Обработчик команды /help"""
        lang = self._lang(message)
        await message.reply(
            t(lang, 'help_text'),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=self.keyboard_service.create_main_menu(lang),
        )

    async def what_command(self, message: types.Message):
        """Обработчик команды /what"""
        lang = self._lang(message)
        await message.reply(
            t(lang, 'what_text'),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=self.keyboard_service.create_main_menu(lang),
        )

    async def info_command(self, message: types.Message):
        """Обработчик команды /info"""
        lang = self._lang(message)
        await message.reply(
            t(lang, 'info_text'),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=self.keyboard_service.create_main_menu(lang),
        )

    async def about_us_command(self, message: types.Message):
        """Обработчик команды /about_us"""
        lang = self._lang(message)
        await message.reply(
            t(lang, 'about_us_text'),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=self.keyboard_service.create_main_menu(lang),
        )