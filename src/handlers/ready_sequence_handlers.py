import os
import logging
from aiogram import types
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.services.subscription_service import SubscriptionService
from src.services.ready_sequence_file_service import ReadySequenceFileService
from src.utils.keyboard_service import KeyboardService
from src.utils.text_utils import send_markdown_safe
from src.i18n import t
from src.services.database_service import db_service

logger = logging.getLogger(__name__)

class ReadySequenceHandlers:
    """Обработчики для готовых комплексов"""
    
    def __init__(self, bot, subscription_service: SubscriptionService):
        self.bot = bot
        self.subscription_service = subscription_service
        self.ready_sequence_service = ReadySequenceFileService()
        self.keyboard_service = KeyboardService()

    @staticmethod
    def _lang(user_id: int) -> str:
        return db_service.get_user_language(user_id)
    
    async def show_ready_sequences_menu(self, callback: types.CallbackQuery):
        """Показывает меню готовых комплексов"""
        lang = self._lang(callback.from_user.id)
        try:
            sequences = self.ready_sequence_service.get_all_sequences()
            
            if not sequences:
                await self.bot.send_message(
                    callback.from_user.id,
                    t(lang, 'rs_menu_empty'),
                    reply_markup=self.keyboard_service.create_main_menu(lang)
                )
                await callback.answer()
                return
            
            text = t(lang, 'rs_menu_title')
            
            # Добавляем информацию о количестве комплексов
            free_count = len([s for s in sequences if not s['is_premium']])
            premium_count = len([s for s in sequences if s['is_premium']])
            
            text = text.format(free=free_count, premium=premium_count)
            
            await self.bot.send_message(
                callback.from_user.id,
                text,
                reply_markup=self.keyboard_service.create_ready_sequences_menu(sequences, lang)
            )
            
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error showing ready sequences menu: {e}")
            await self.bot.send_message(
                callback.from_user.id,
                t(lang, 'rs_menu_error'),
                reply_markup=self.keyboard_service.create_main_menu(lang)
            )
            await callback.answer()
    
    async def show_ready_sequence(self, callback: types.CallbackQuery):
        """Показывает информацию о готовом комплексе"""
        lang = self._lang(callback.from_user.id)
        try:
            sequence_id = int(callback.data.split('_')[-1])
            user_id = callback.from_user.id
            
            # Получаем информацию о комплексе
            sequence = self.ready_sequence_service.get_sequence_by_id(sequence_id)
            
            if not sequence:
                await callback.answer(t(lang, 'rs_not_found'), show_alert=True)
                return
            
            # Проверяем статус подписки
            subscription_info = await self.subscription_service.get_subscription_info(user_id)
            is_premium = subscription_info['is_active']
            
            # Краткая информация о доступности (без вымышленных метаданных)
            if sequence['is_premium'] and is_premium:
                status_text = t(lang, 'rs_status_owned')
            elif sequence['is_premium'] and not is_premium:
                status_text = t(lang, 'rs_status_locked')
            else:
                status_text = t(lang, 'rs_status_free')
            
            full_text = t(lang, 'rs_seq_title', name=sequence['name'])
            full_text += status_text
            
            await send_markdown_safe(self.bot, user_id, full_text)
            
            # Обрабатываем видео
            if sequence['video_path'] and os.path.exists(sequence['video_path']):
                if not sequence['is_premium'] or is_premium:
                    # Бесплатный комплекс или премиум пользователь - отправляем видео
                    try:
                        from aiogram.types.input_file import FSInputFile
                        await self.bot.send_video(user_id, FSInputFile(sequence['video_path']))
                    except Exception as e:
                        logger.error(f"Error sending ready sequence video: {e}")
                        await self.bot.send_message(user_id, t(lang, 'rs_video_unavailable'))
                else:
                    # Бесплатный пользователь и премиум комплекс - показываем предложение подписки
                    premium_text = t(lang, 'rs_premium_offer')
                    
                    premium_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text=t(lang, 'sub_btn_trial7'), callback_data="subscription_trial")],
                        [InlineKeyboardButton(text=t(lang, 'rs_btn_plans'), callback_data="subscription_plans")]
                    ])
                    
                    await self.bot.send_message(user_id, premium_text, parse_mode=ParseMode.MARKDOWN, reply_markup=premium_keyboard)
            else:
                # Видео файл не найден
                await self.bot.send_message(
                    user_id,
                    t(lang, 'rs_video_missing'),
                )
            
            # Кнопка возврата
            sequences = self.ready_sequence_service.get_all_sequences()
            await callback.message.reply(
                t(lang, 'rs_menu_back_btn'),
                reply_markup=self.keyboard_service.create_ready_sequences_menu(sequences, lang)
            )
            
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error showing ready sequence: {e}")
            await callback.answer(t(lang, 'rs_error_alert'), show_alert=True)