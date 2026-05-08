import os
import logging
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.services.subscription_service import SubscriptionService
from src.services.ready_sequence_file_service import ReadySequenceFileService
from src.utils.keyboard_service import KeyboardService

logger = logging.getLogger(__name__)

class ReadySequenceHandlers:
    """Обработчики для готовых комплексов"""
    
    def __init__(self, bot, subscription_service: SubscriptionService):
        self.bot = bot
        self.subscription_service = subscription_service
        self.ready_sequence_service = ReadySequenceFileService()
        self.keyboard_service = KeyboardService()
    
    async def show_ready_sequences_menu(self, callback: types.CallbackQuery):
        """Показывает меню готовых комплексов"""
        try:
            sequences = self.ready_sequence_service.get_all_sequences()
            
            if not sequences:
                await self.bot.send_message(
                    callback.from_user.id,
                    "🎬 *Готовые комплексы*\n\n"
                    "Пока нет доступных комплексов. "
                    "Добавьте видео файлы в папку `videos/ready_sequences/`",
                    reply_markup=self.keyboard_service.create_main_menu()
                )
                await callback.answer()
                return
            
            text = "🎬 *Готовые комплексы*\n\n"
            text += "Выберите комплекс из списка ниже:\n\n"
            
            # Добавляем информацию о количестве комплексов
            free_count = len([s for s in sequences if not s['is_premium']])
            premium_count = len([s for s in sequences if s['is_premium']])
            
            text += f"📊 Доступно: {free_count} бесплатных, {premium_count} премиум\n\n"
            
            await self.bot.send_message(
                callback.from_user.id,
                text,
                reply_markup=self.keyboard_service.create_ready_sequences_menu(sequences)
            )
            
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error showing ready sequences menu: {e}")
            await self.bot.send_message(
                callback.from_user.id,
                "Произошла ошибка при загрузке комплексов. Попробуйте позже.",
                reply_markup=self.keyboard_service.create_main_menu()
            )
            await callback.answer()
    
    async def show_ready_sequence(self, callback: types.CallbackQuery):
        """Показывает информацию о готовом комплексе"""
        try:
            sequence_id = int(callback.data.split('_')[-1])
            user_id = callback.from_user.id
            
            # Получаем информацию о комплексе
            sequence = self.ready_sequence_service.get_sequence_by_id(sequence_id)
            
            if not sequence:
                await callback.answer("Комплекс не найден", show_alert=True)
                return
            
            # Проверяем статус подписки
            subscription_info = self.subscription_service.get_subscription_info(user_id)
            is_premium = subscription_info['is_active']
            
            # Формируем текст с информацией о доступности
            status_text = ""
            if sequence['is_premium'] and is_premium:
                status_text = "🎥 **Видео-инструкция доступна**\n\n"
            elif sequence['is_premium'] and not is_premium:
                status_text = "🎥 **Видео-инструкция доступна в премиум-версии**\n\n"
            else:
                status_text = "🎥 **Видео-инструкция доступна**\n\n"
            
            # Формируем полное описание
            full_text = status_text
            full_text += f"🎬 **{sequence['name']}**\n\n"
            full_text += f"⏱️ Длительность: {sequence['duration']} минут\n"
            full_text += f"📊 Сложность: {'⭐' * sequence['difficulty_level']}\n"
            full_text += f"🏷️ Категория: {sequence['category']}\n"
            full_text += f"🎯 Фокус: {sequence['focus_areas']}\n\n"
            full_text += f"📝 **Описание:**\n{sequence['description']}\n\n"
            full_text += f"👨‍🏫 Инструктор: {sequence['instructor_name']}"
            
            await self.bot.send_message(user_id, full_text)
            
            # Обрабатываем видео
            if sequence['video_path'] and os.path.exists(sequence['video_path']):
                if not sequence['is_premium'] or is_premium:
                    # Бесплатный комплекс или премиум пользователь - отправляем видео
                    try:
                        from aiogram.types.input_file import FSInputFile
                        await self.bot.send_video(user_id, FSInputFile(sequence['video_path']))
                    except Exception as e:
                        logger.error(f"Error sending ready sequence video: {e}")
                        await self.bot.send_message(user_id, "Видео временно недоступно")
                else:
                    # Бесплатный пользователь и премиум комплекс - показываем предложение подписки
                    premium_text = (
                        "🎯 **Хотите видео-инструкцию?**\n\n"
                        "В премиум-версии вы получите:\n"
                        "• 🎥 Детальные видео для всех комплексов\n"
                        "• 📊 Анализ техники и исправление ошибок\n"
                        "• 🎵 Аудио-сопровождение практик\n"
                        "• 🔄 Безлимитные генерации комплексов\n\n"
                        "Попробуйте 7 дней бесплатно!"
                    )
                    
                    premium_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🚀 7 дней бесплатно", callback_data="subscription_trial")],
                        [InlineKeyboardButton(text="💳 Узнать о тарифах", callback_data="subscription_plans")]
                    ])
                    
                    await self.bot.send_message(user_id, premium_text, reply_markup=premium_keyboard)
            else:
                # Видео файл не найден
                await self.bot.send_message(user_id, "Видео файл не найден. Проверьте наличие файла в папке.")
            
            # Кнопка возврата
            sequences = self.ready_sequence_service.get_all_sequences()
            await callback.message.reply(
                'Готовые комплексы',
                reply_markup=self.keyboard_service.create_ready_sequences_menu(sequences)
            )
            
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error showing ready sequence: {e}")
            await callback.answer("Произошла ошибка", show_alert=True)
