import logging
import asyncio
from datetime import datetime, time
from typing import List

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
        now = datetime.now()
        
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
            
            # Получаем случайную асану
            daily_asana = self.data_service.get_random_asana()
            if not daily_asana:
                logger.error("No asanas found for daily asana")
                return
            
            # Получаем контент
            content, image_path = self.data_service.get_asana_content(daily_asana.name)
            if not content:
                content = f"🧘 **{daily_asana.name}**\n\nОписание временно недоступно."
            
            # Форматируем текст
            asana_text = self._format_daily_asana_text(daily_asana, content, fresh_user)
            keyboard = self._create_daily_asana_keyboard(daily_asana.name, fresh_user)
            
            await self._send_asana_message(fresh_user.telegram_id, asana_text, image_path, keyboard)
            
            # Обновляем дату последней отправки
            db_service.update_last_daily_asana_date(fresh_user.telegram_id)
            
        except Exception as e:
            logger.error(f"Error sending daily asana to user {user_id}: {e}")
    
    def _format_daily_asana_text(self, asana, content: str, user) -> str:
        """Форматирует текст асаны дня с премиум-подсказками"""
        difficulty_text = "⭐" * asana.difficulty
        
        text = (
            f"🧘‍♂️ **Асана дня**\n\n"
            f"**{asana.name}**\n"
            f"Сложность: {difficulty_text}\n\n"
        )
        
        # Добавляем описание если есть
        if content:
            # Обрезаем если слишком длинное
            if len(content) > 500:
                content = content[:500] + "..."
            text += content + "\n\n"
        
        # Премиум-подсказки в зависимости от сложности
        if asana.difficulty >= 4 and not user.is_premium:
            text += (
                "💡 **Это сложная асана!**\n"
                "В премиум-версии есть:\n"
                "• 📹 Видео с подготовительными упражнениями\n"
                "• 🔄 Облегченные вариации\n"
                "• ⚠️ Безопасные альтернативы\n\n"
                "Хотите освоить эту асану безопасно?"
            )
        elif asana.difficulty >= 3 and not user.is_premium:
            text += (
                "💡 **Хотите глубже изучить эту асану?**\n"
                "В премиум-версии есть:\n"
                "• 📹 Детальная видео-отстройка\n"
                "• 🏗️ Анатомические схемы\n"
                "• ❌ Разбор типичных ошибок\n\n"
            )
        
        text += "Хорошей практики! 🙏"
        
        return text
    
    def _create_daily_asana_keyboard(self, asana_name, user):
        """Создает клавиатуру для асаны дня"""
        from aiogram.types import InlineKeyboardMarkup
        
        buttons = []
        
        # Основная кнопка - начать практику
        practice_text = "🕐 Начать практику (5 мин)"
        # Используем короткий ID вместо полного имени асаны
        buttons.append([{"text": practice_text, "callback_data": f"daily_practice_{user.id}"}])
        
        # Премиум-предложения для сложных асан (упрощенно, без объекта asana)
        buttons.append([
            {"text": "📹 Видео-отстройка (премиум)", "callback_data": "premium_upgrade_video"}
        ])
        
        # Кнопки управления
        buttons.append([
            {"text": "⏰ Изменить время", "callback_data": "daily_asana_settings"},
            {"text": "🔕 Отключить уведомления", "callback_data": "daily_asana_disable"}
        ])
        
        return {"inline_keyboard": buttons}
    
    async def _send_asana_message(self, user_id: int, text: str, image_path: str, keyboard):
        """Отправить сообщение с асаной"""
        try:
            if image_path:
                from aiogram.types import FSInputFile
                import os
                
                abs_image_path = os.path.abspath(image_path)
                if os.path.exists(abs_image_path):
                    input_file = FSInputFile(abs_image_path)
                    await self.bot.send_photo(
                        chat_id=user_id,
                        photo=input_file,
                        caption=text,
                        reply_markup=keyboard
                    )
                    return
            
            # Если нет фото, отправляем текст
            await self.bot.send_message(
                chat_id=user_id,
                text=text,
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error sending asana message: {e}")
            # Пробуем отправить просто текст
            try:
                await self.bot.send_message(
                    chat_id=user_id,
                    text=text,
                    reply_markup=keyboard
                )
            except Exception as e2:
                logger.error(f"Error sending fallback message: {e2}")
