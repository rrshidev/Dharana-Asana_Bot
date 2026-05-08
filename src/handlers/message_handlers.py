import logging
import os
from aiogram import types

from src.services.data_service import DataService
from src.services.video_service import VideoService
from src.services.subscription_service import SubscriptionService
from src.services.database_service import db_service
from src.utils.keyboard_service import KeyboardService

logger = logging.getLogger(__name__)


class MessageHandlers:
    """Обработчики текстовых сообщений"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_service = DataService()
        self.video_service = VideoService(db_service)
        self.subscription_service = SubscriptionService(db_service)
        self.keyboard_service = KeyboardService()
    
    async def text_message(self, message: types.Message):
        """Обработчик текстовых сообщений"""
        text = message.text.title()
        
        # Проверяем, является ли текст названием асаны
        asana_data = self.data_service.get_asana_data(text)
        
        if asana_data:
            await self._send_asana_data(message, asana_data)
        else:
            await message.answer(
                'Проверь название или воспользуйся каталогом асан!',
                reply_markup=self.keyboard_service.create_main_menu()
            )
    
    async def _send_asana_data(self, message: types.Message, asana_data):
        """Отправляет данные асаны с видео или фото"""
        try:
            # Проверяем статус подписки пользователя
            subscription_info = self.subscription_service.get_subscription_info(message.from_user.id)
            is_premium = subscription_info['is_active']
            
            # Ищем видео для этой асаны
            video = self.video_service.get_video_for_asana(asana_data.name, is_premium)
            
            # Отладочная информация
            logger.info(f"User {message.from_user.id}: is_premium={is_premium}, video_found={video is not None}")
            if video:
                logger.info(f"Video info: is_premium={video['is_premium']}, video_path={video['video_path']}")
            
            # Формируем текст с информацией о доступности
            status_text = ""
            if video and video['is_premium'] and is_premium:
                status_text = "🎥 **Видео-инструкция доступна**\n\n"
            elif video and video['is_premium'] and not is_premium:
                status_text = "🎥 **Видео-инструкция доступна в премиум-версии**\n\n"
            
            # Отправляем описание
            full_text = status_text + asana_data.description
            await self.bot.send_message(message.from_user.id, full_text)
            
            # Отправляем видео или фото
            if video and video['is_premium'] and is_premium:
                # Премиум-пользователь получает видео
                if video['video_path'] and os.path.exists(video['video_path']):
                    try:
                        from aiogram.types.input_file import FSInputFile
                        await self.bot.send_video(message.from_user.id, FSInputFile(video['video_path']))
                        logger.info(f"Sent video for asana {asana_data.name} to premium user {message.from_user.id}")
                    except Exception as e:
                        logger.error(f"Error sending video: {e}")
                        # Если видео не отправилось, отправляем фото
                        if asana_data.image_path:
                            from aiogram.types.input_file import FSInputFile
                            await self.bot.send_photo(message.from_user.id, FSInputFile(asana_data.image_path))
                else:
                    # Видео файла нет, отправляем фото
                    if asana_data.image_path:
                        from aiogram.types.input_file import FSInputFile
                        await self.bot.send_photo(message.from_user.id, FSInputFile(asana_data.image_path))
                        
            elif video and video['is_premium'] and not is_premium:
                # Бесплатный пользователь видит превью видео и предложение подписки
                logger.info(f"Showing subscription offer to user {message.from_user.id}")
                
                if asana_data.image_path:
                    from aiogram.types.input_file import FSInputFile
                    await self.bot.send_photo(message.from_user.id, FSInputFile(asana_data.image_path))
                
                # Добавляем предложение подписки
                premium_text = (
                    "🎯 **Хотите видео-инструкцию?**\n\n"
                    "В премиум-версии вы получите:\n"
                    "• 🎥 Детальные видео для 50+ асан\n"
                    "• 📊 Анализ техники и исправление ошибок\n"
                    "• 🎵 Аудио-сопровождение практик\n"
                    "• 🔄 Безлимитные генерации комплексов\n\n"
                    "Попробуйте 7 дней бесплатно!"
                )
                
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                premium_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🚀 7 дней бесплатно", callback_data="subscription_trial")],
                    [InlineKeyboardButton(text="💳 Узнать о тарифах", callback_data="subscription_plans")]
                ])
                
                await self.bot.send_message(message.from_user.id, premium_text, reply_markup=premium_keyboard)
                
            else:
                # Видео нет, отправляем фото как обычно
                logger.info(f"No video found for asana {asana_data.name}, sending photo only")
                if asana_data.image_path:
                    from aiogram.types.input_file import FSInputFile
                    await self.bot.send_photo(message.from_user.id, FSInputFile(asana_data.image_path))
            
            # Кнопка возврата
            await message.reply('Каталог', reply_markup=self.keyboard_service.create_main_menu())
                
        except Exception as e:
            logger.error(f"Error sending asana {asana_data.name}: {e}")
            await message.answer(
                f'Ошибка при загрузке асаны: {e}',
                reply_markup=self.keyboard_service.create_main_menu()
            )
