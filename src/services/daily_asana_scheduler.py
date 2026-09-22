import logging
import asyncio
from datetime import datetime, time, timezone
from typing import List

from aiogram.enums import ParseMode

from src.i18n import t
from src.services.database_service import db_service
from src.services.data_service import DataService
from src.handlers.filter_handlers import FilterHandlers

logger = logging.getLogger(__name__)

class DailyAsanaScheduler:
    """Планировщик для ежедневной отправки асан"""
    
    def __init__(self, bot, data_service: DataService):
        self.bot = bot
        self.data_service = data_service
        self.is_running = False
        
    async def start_scheduler(self):
        """Запустить планировщик"""
        if self.is_running:
            return
            
        self.is_running = True
        logger.info("Daily asana scheduler started")
        
        while self.is_running:
            try:
                await self.check_and_send_daily_asanas()
                await asyncio.sleep(60)  # Проверяем каждую минуту
            except Exception as e:
                logger.error(f"Error in scheduler: {e}")
                await asyncio.sleep(60)
    
    def stop_scheduler(self):
        """Остановить планировщик"""
        self.is_running = False
        logger.info("Daily asana scheduler stopped")
    
    async def check_and_send_daily_asanas(self):
        """Проверить и отправить асаны дня"""
        # Сервер живёт по UTC; перевод в локальное время юзеров делает
        # get_users_for_daily_asana (по user.timezone).
        now = datetime.now(timezone.utc)
        
        # Получаем пользователей, которым нужно отправить асану
        users = db_service.get_users_for_daily_asana(now)
        
        if not users:
            logger.info(f"Found 0 users for daily asana at {now}")
            return
        
        logger.info(f"Sending daily asanas to {len(users)} users")
        
        for user in users:
            try:
                await self.send_daily_asana_to_user(user)
            except Exception as e:
                logger.error(f"Error sending daily asana to user {user.telegram_id}: {e}")
    
    async def send_daily_asana_to_user(self, user):
        """Отправить асану дня конкретному пользователю"""
        user_id = user.telegram_id if hasattr(user, 'telegram_id') else user
        fresh_user = None
        try:
            # Получаем свежие данные пользователя
            from src.services.database_service import db_service
            fresh_user = db_service.get_user(telegram_id=user_id)
            if not fresh_user:
                logger.error(f"User {user_id} not found in database")
                return
            
            lang = db_service.get_user_language(user_id)
            
            # Получаем случайную асану
            daily_asana = self.data_service.get_random_asana(lang)
            if not daily_asana:
                logger.error("No asanas found for daily asana")
                return
            
            # Получаем контент (RU — из файла, EN — локализованное описание)
            base_name = daily_asana.base_name or daily_asana.name
            content, image_path = self.data_service.get_asana_content(base_name)
            if lang == 'en' and daily_asana.description:
                content = daily_asana.description
            if not content:
                content = f"🧘 **{daily_asana.name}**\n\n{t(lang, 'daily_desc_unavailable')}"
            
            # Форматируем текст
            asana_text = self._format_daily_asana_text(daily_asana, content, fresh_user, lang)
            keyboard = self._create_daily_asana_keyboard(daily_asana.name, fresh_user, lang)
            
            await self._send_asana_message(fresh_user.telegram_id, asana_text, image_path, keyboard)
            
            # Обновляем дату последней отправки
            db_service.update_last_daily_asana_date(fresh_user.telegram_id)
            
        except Exception as e:
            logger.error(f"Error sending daily asana to user {user_id}: {e}")
    
    def _format_daily_asana_text(self, asana, content: str, user, lang: str = 'ru') -> str:
        """Форматирует текст асаны дня с премиум-подсказками"""
        difficulty_text = "⭐" * asana.difficulty
        
        text = (
            f"{t(lang, 'daily_asana_title')}\n\n"
            f"**{asana.name}**\n"
            f"{t(lang, 'daily_difficulty', stars=difficulty_text)}\n\n"
        )
        
        # Добавляем описание если есть — полное, без обрезки
        if content:
            text += content + "\n\n"
        
        # Премиум-подсказки в зависимости от сложности
        premium_user = db_service.is_user_premium(user.telegram_id)
        if asana.difficulty >= 4 and not premium_user:
            text += (
                f"{t(lang, 'daily_hint_hard')}\n\n"
                f"{t(lang, 'daily_hint_hard_cta')}"
            )
        elif asana.difficulty >= 3 and not premium_user:
            text += t(lang, 'daily_hint_medium') + "\n\n"
        
        text += t(lang, 'daily_good_practice')
        
        return text
    
    def _create_daily_asana_keyboard(self, asana_name, user, lang: str = 'ru'):
        """Создает клавиатуру для асаны дня"""
        from aiogram.types import InlineKeyboardMarkup
        
        buttons = []
        
        # Основная кнопка - начать практику
        practice_text = t(lang, 'daily_start_practice_btn')
        # Используем короткий ID вместо полного имени асаны
        buttons.append([{"text": practice_text, "callback_data": f"daily_practice_{user.id}"}])
        
        # Премиум-предложения для сложных асан (упрощенно, без объекта asana)
        buttons.append([
            {"text": t(lang, 'daily_video_premium_btn'), "callback_data": "premium_upgrade_video"}
        ])
        
        # Кнопки управления
        buttons.append([
            {"text": t(lang, 'daily_change_time_btn'), "callback_data": "daily_asana_settings"},
            {"text": t(lang, 'daily_disable_btn'), "callback_data": "daily_asana_disable"}
        ])
        
        return {"inline_keyboard": buttons}
    
    async def _send_asana_message(self, user_id: int, text: str, image_path: str, keyboard):
        """Отправить сообщение с асаной.

        Лимиты Telegram: caption у фото — 1024 символа, сообщение — 4096.
        """
        try:
            if image_path:
                from aiogram.types import FSInputFile
                import os
                
                abs_image_path = os.path.abspath(image_path)
                if os.path.exists(abs_image_path):
                    input_file = FSInputFile(abs_image_path)
                    if len(text) <= 1024:
                        await self.bot.send_photo(
                            chat_id=user_id,
                            photo=input_file,
                            caption=text,
                            reply_markup=keyboard,
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        # Капшн фото ограничен 1024 → картинку отдельно,
                        # полный текст отдельным сообщением с клавиатурой.
                        await self.bot.send_photo(chat_id=user_id, photo=input_file)
                        await self._send_text_chunks(user_id, text, keyboard)
                    return
            
            # Если нет фото (или текст длинноват) — отправляем текст целиком
            await self._send_text_chunks(user_id, text, keyboard)
            
        except Exception as e:
            logger.error(f"Error sending asana message: {e}")
            # Пробуем отправить просто текст
            try:
                await self._send_text_chunks(user_id, text, keyboard)
            except Exception as e2:
                logger.error(f"Error sending fallback message: {e2}")
    
    async def _send_text_chunks(self, chat_id: int, text: str, keyboard, chunk_size: int = 4000):
        """Отправить длинный текст, разбивая по границам строк (лимит 4096)."""
        lines = text.split("\n")
        chunks = []
        current = ""
        for line in lines:
            # Строка-гигант (редкий случай) — режем жёстко
            if len(line) > chunk_size:
                if current:
                    chunks.append(current)
                    current = ""
                for i in range(0, len(line), chunk_size):
                    chunks.append(line[i:i + chunk_size])
                continue
            if len(current) + len(line) + 1 > chunk_size:
                if current:
                    chunks.append(current)
                current = line
            else:
                current = (current + "\n" if current else "") + line
        if current:
            chunks.append(current)
        
        if not chunks:
            return
        
        for i, chunk in enumerate(chunks):
            await self._safe_send_message(chat_id, chunk, keyboard if i == 0 else None)
    
    async def _safe_send_message(self, chat_id: int, text: str, keyboard):
        """Отправить текст с md-парсингом, при ошибке парсинга — без него."""
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception:
            await self.bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)
