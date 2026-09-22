import logging
import os
from typing import List
from aiogram import types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from src.services.data_service import DataService
from src.services.filter_service import FilterService, AsanaDayNotifier
from src.utils.keyboard_service import KeyboardService
from src.models.data_models import AsanaData, UserPreferences
from src.data.asana_effects import ASANA_EFFECTS, ASANA_DIFFICULTY, ASANA_CONTRAINDICATIONS
from src.i18n import t
from src.services.database_service import db_service

logger = logging.getLogger(__name__)

_DIFF_TEXT_KEYS = {
    1: 'flt_diff_1',
    2: 'flt_diff_2',
    3: 'flt_diff_3',
    4: 'flt_diff_4',
    5: 'flt_diff_5',
}

_EFFECT_TEXT_KEYS = {
    'back_pain': 'flt_effect_back_pain',
    'calm_mind': 'flt_effect_calm_mind',
    'boost_energy': 'flt_effect_boost_energy',
    'digestion': 'flt_effect_digestion',
    'flexibility': 'flt_effect_flexibility',
    'balance': 'flt_effect_balance',
    'strength': 'flt_effect_strength',
    'stress_relief': 'flt_effect_stress_relief',
}


class FilterHandlers:
    """Обработчики для фильтров и асаны дня"""
    
    def __init__(self, bot, data_service: DataService):
        self.bot = bot
        self.data_service = data_service
        self.filter_service = FilterService(data_service)
        self.keyboard_service = KeyboardService()
        
        # Для отслеживания изменений в фильтрах
        self._last_filtered_count = None
        self.asana_day_notifier = AsanaDayNotifier(bot, self.filter_service)
        
        # Хранилище предпочтений пользователей (в будущем будет в БД)
        self.user_preferences = {}

    @staticmethod
    def _lang(user_id: int) -> str:
        """Язык пользователя ('ru'|'en')."""
        return db_service.get_user_language(user_id)
    
    async def filter_difficulty_callback(self, callback_query: types.CallbackQuery):
        """Обработчик выбора фильтра сложности"""
        await self.bot.answer_callback_query(callback_query.id)
        
        data = callback_query.data.split('_')
        if len(data) < 3:
            return
        
        action = data[2]
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)
        
        if action == "reset":
            # Сбрасываем фильтр сложности
            if user_id in self.user_preferences:
                self.user_preferences[user_id].difficulty = None
            
            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=callback_query.message.message_id,
                text=t(lang, 'flt_difficulty_reset'),
                reply_markup=self.keyboard_service.create_main_menu(lang)
            )
        else:
            # Устанавливаем новый фильтр сложности
            try:
                difficulty = int(action)
                if user_id not in self.user_preferences:
                    from src.models.data_models import UserPreferences
                    self.user_preferences[user_id] = UserPreferences()
                
                self.user_preferences[user_id].difficulty = difficulty
                
                # Получаем отфильтрованные асаны
                all_asanas = self.data_service.get_all_asanas()
                filtered_asanas = self.filter_service.filter_asanas(
                    all_asanas, self.user_preferences[user_id]
                )
                
                if not filtered_asanas:
                    await self.bot.edit_message_text(
                        chat_id=user_id,
                        message_id=callback_query.message.message_id,
                        text=t(lang, 'flt_diff_not_found'),
                        reply_markup=self.filter_service.get_difficulty_filter_keyboard(difficulty, lang)
                    )
                    return
                
                await self.bot.edit_message_text(
                    chat_id=user_id,
                    message_id=callback_query.message.message_id,
                    text=t(lang, 'flt_diff_applied',
                           stars='⭐' * difficulty,
                           difficulty=self._get_difficulty_text(lang, difficulty),
                           count=len(filtered_asanas)),
                    reply_markup=self._create_filtered_asanas_keyboard(filtered_asanas, lang)
                )
                
            except ValueError:
                logger.error(f"Invalid difficulty value: {action}")
    
    async def filter_effect_callback(self, callback_query: types.CallbackQuery):
        """Обработчик выбора фильтра эффектов"""
        await self.bot.answer_callback_query(callback_query.id)
        
        # Отладочный лог
        logger.info(f"Filter effect callback received: {callback_query.data}")
        
        data = callback_query.data.split('_')
        logger.info(f"Callback data split: {data}")
        
        if len(data) < 3:
            logger.error(f"Invalid callback data format: {callback_query.data}")
            return
        
        action = '_'.join(data[2:])  # Объединяем все части после 'filter_effect'
        logger.info(f"Action extracted: {action}")
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)
        
        logger.info(f"User ID: {user_id}")
        logger.info(f"Checking if action is 'reset': {action == 'reset'}")
        
        if action == "reset":
            logger.info("Processing reset action")
            # Сбрасываем фильтр эффектов
            if user_id in self.user_preferences:
                self.user_preferences[user_id].effects = None
            
            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=callback_query.message.message_id,
                text=t(lang, 'flt_effect_reset'),
                reply_markup=self.keyboard_service.create_main_menu(lang)
            )
            return
        
        logger.info("Processing filter effect action")
        # Устанавливаем новый фильтр эффектов
        effect = action
        logger.info(f"Effect variable set to: {effect}")
        
        if user_id not in self.user_preferences:
            logger.info("Creating new UserPreferences for user")
            from src.models.data_models import UserPreferences
            self.user_preferences[user_id] = UserPreferences()
        
        logger.info(f"User preferences exists: {user_id in self.user_preferences}")
        
        if not self.user_preferences[user_id].effects:
            logger.info("Initializing empty effects list")
            self.user_preferences[user_id].effects = []
        
        logger.info(f"Current effects before adding: {self.user_preferences[user_id].effects}")
        
        # Получаем текущие эффекты пользователя
        current_effects = self.user_preferences[user_id].effects or []
        logger.info(f"Current effects for check: {current_effects}")
        
        # Получаем данные эффекта
        logger.info("Getting effect emoji and text")
        effect_emoji = self._get_effect_emoji(effect)
        effect_text = self._get_effect_text(lang, effect)
        logger.info(f"Effect emoji: {effect_emoji}, text: {effect_text}")
        
        # Если эффект уже выбран, просто показываем уведомление
        if effect in current_effects:
            logger.info(f"Effect {effect} already selected, showing notification")
            await self.bot.answer_callback_query(
                callback_query.id,
                text=t(lang, 'flt_effect_selected', effect=effect_text),
                show_alert=True
            )
            return
        
        logger.info(f"Effect {effect} not selected before, adding to preferences")
        # Добавляем новый эффект
        if effect not in self.user_preferences[user_id].effects:
            logger.info(f"Adding effect {effect} to user preferences")
            self.user_preferences[user_id].effects.append(effect)
        
        logger.info("Effect not selected before, proceeding to load asanas")
        
        # Получаем отфильтрованные асаны
        all_asanas = self.data_service.get_all_asanas()
        logger.info(f"Total asanas loaded: {len(all_asanas)}")
        logger.info(f"User preferences: {self.user_preferences[user_id]}")
        
        filtered_asanas = self.filter_service.filter_asanas(
            all_asanas, self.user_preferences[user_id]
        )
        logger.info(f"Filtered asanas count: {len(filtered_asanas)}")
        logger.info(f"Looking for effect: {effect}")
        
        if not filtered_asanas:
            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=callback_query.message.message_id,
                text=t(lang, 'flt_effect_not_found'),
                reply_markup=self.filter_service.get_effect_filter_keyboard([effect], lang)
            )
            return
        
        # Формируем уникальный текст с количеством асан
        filter_text = t(lang, 'flt_effect_applied',
                        effect=f"{effect_emoji} {effect_text}",
                        count=len(filtered_asanas))
        
        # Проверяем, изменилось ли количество асан
        if hasattr(self, '_last_filtered_count') and self._last_filtered_count == len(filtered_asanas):
            # Если количество не изменилось, просто показываем клавиатуру
            await self.bot.edit_message_reply_markup(
                chat_id=user_id,
                message_id=callback_query.message.message_id,
                reply_markup=self._create_filtered_asanas_keyboard(filtered_asanas, lang)
            )
        else:
            # Если количество изменилось, редактируем текст
            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=callback_query.message.message_id,
                text=filter_text,
                reply_markup=self._create_filtered_asanas_keyboard(filtered_asanas, lang)
            )
            self._last_filtered_count = len(filtered_asanas)
    
    async def show_filter_menu_callback(self, callback_query: types.CallbackQuery):
        """Показать меню фильтров"""
        await self.bot.answer_callback_query(callback_query.id)
        
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)
        
        # Получаем текущие предпочтения
        current_difficulty = None
        current_effects = None
        
        if user_id in self.user_preferences:
            current_difficulty = self.user_preferences[user_id].difficulty
            current_effects = self.user_preferences[user_id].effects
        
        filter_menu_text = t(lang, 'flt_menu_title')
        
        filter_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    {"text": t(lang, 'flt_btn_difficulty'), "callback_data": "filter_difficulty_menu"},
                    {"text": t(lang, 'flt_btn_effect'), "callback_data": "filter_effect_menu"}
                ],
                [
                    {"text": t(lang, 'flt_btn_daily'), "callback_data": "daily_asana"},
                    {"text": t(lang, 'flt_btn_reset_all'), "callback_data": "filter_reset_all"}
                ],
                [
                    {"text": t(lang, 'btn_back_main'), "callback_data": "main_menu"}
                ]
            ]
        )
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=filter_menu_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=filter_keyboard
        )
    
    async def show_difficulty_filter_menu(self, callback_query: types.CallbackQuery):
        """Показать меню фильтра сложности"""
        await self.bot.answer_callback_query(callback_query.id)
        
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)
        current_difficulty = None
        
        if user_id in self.user_preferences:
            current_difficulty = self.user_preferences[user_id].difficulty
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=t(lang, 'flt_difficulty_menu_title'),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=self.filter_service.get_difficulty_filter_keyboard(current_difficulty, lang)
        )
    
    async def show_effect_filter_menu(self, callback_query: types.CallbackQuery):
        """Показать меню фильтра эффектов"""
        await self.bot.answer_callback_query(callback_query.id)
        
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)
        current_effects = None
        
        if user_id in self.user_preferences:
            current_effects = self.user_preferences[user_id].effects
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=t(lang, 'flt_effect_menu_title'),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=self.filter_service.get_effect_filter_keyboard(current_effects, lang)
        )
    
    async def show_daily_asana(self, callback_query: types.CallbackQuery):
        """Показать асану дня"""
        await self.bot.answer_callback_query(callback_query.id)
        
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)
        
        # Получаем случайную асану через data_service
        daily_asana_data = self.data_service.get_random_asana()
        
        if not daily_asana_data:
            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=callback_query.message.message_id,
                text=t(lang, 'flt_daily_unavailable'),
                reply_markup=self.keyboard_service.create_main_menu(lang)
            )
            return
        
        # Получаем описание и фото из data_service
        content, image_path = self.data_service.get_asana_content(daily_asana_data.name)
        
        # Добавляем premium-подсказки
        description, has_premium_hint = self.filter_service.get_asana_with_premium_hint(
            daily_asana_data, user_id
        )
        
        # Если есть контент из файла, используем его
        if content:
            description = content
        
        # Формируем текст
        asana_text = (
            f"{t(lang, 'daily_asana_title')}\n\n"
            f"**{daily_asana_data.name}**\n\n"
            f"{description}\n\n"
            f"{t(lang, 'flt_difficulty_full', stars=self._get_difficulty_stars(daily_asana_data.difficulty), difficulty=self._get_difficulty_text(lang, daily_asana_data.difficulty))}\n"
            f"{t(lang, 'flt_practice_today')}"
        )
        
        # Отправляем с фото или без
        try:
            if image_path and os.path.exists(image_path):
                await self.bot.send_photo(
                    chat_id=user_id,
                    photo=image_path,
                    caption=asana_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=self.keyboard_service.create_main_menu(lang)
                )
            else:
                await self.bot.send_message(
                    chat_id=user_id,
                    text=asana_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=self.keyboard_service.create_main_menu(lang)
                )
        except Exception as e:
            logger.error(f"Error sending daily asana: {e}")
            await self.bot.send_message(
                chat_id=user_id,
                text=asana_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=self.keyboard_service.create_main_menu(lang)
            )
    
    async def reset_all_filters(self, callback_query: types.CallbackQuery):
        """Сбросить все фильтры"""
        await self.bot.answer_callback_query(callback_query.id)
        
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)
        
        if user_id in self.user_preferences:
            del self.user_preferences[user_id]
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=t(lang, 'flt_reset_all'),
            reply_markup=self.keyboard_service.create_main_menu(lang)
        )
    
    async def filtered_asana_callback(self, callback_query: types.CallbackQuery):
        """Обработчик выбора отфильтрованной асаны"""
        await self.bot.answer_callback_query(callback_query.id)
        
        data = callback_query.data.split('_')
        if len(data) < 2:
            return
        
        try:
            # Получаем индекс асаны из callback_data
            asana_index = int(data[1])
            
            # Получаем асану из кэша
            if not hasattr(self, 'filtered_asanas_cache') or asana_index >= len(self.filtered_asanas_cache):
                await self.bot.send_message(
                    chat_id=callback_query.from_user.id,
                    text=t(self._lang(callback_query.from_user.id), 'flt_err_not_found'),
                    reply_markup=self.keyboard_service.create_main_menu(self._lang(callback_query.from_user.id))
                )
                return
            
            asana = self.filtered_asanas_cache[asana_index]
            asana_name = asana.name
            user_id = callback_query.from_user.id
            lang = self._lang(user_id)
            
            # Получаем данные асаны
            asana_data = self.data_service.get_asana_data(asana_name)
            if not asana_data:
                await self.bot.send_message(
                    chat_id=user_id,
                    text=t(lang, 'flt_err_asana_missing', name=asana_name),
                    reply_markup=self.keyboard_service.create_main_menu(lang)
                )
                return
            
            # Получаем контент и изображение
            content, image_path = self.data_service.get_asana_content(asana_name)
            
            # Формируем текст
            asana_text = f"**{asana_name}**\n\n"
            if content:
                # Обрезаем описание до 800 символов (оставляем место для сложности)
                max_content_length = 800
                if len(content) > max_content_length:
                    content = content[:max_content_length] + t(lang, 'flt_truncated')
                asana_text += content
            
            asana_text += f"\n\n{t(lang, 'daily_difficulty', stars=self._get_difficulty_stars(ASANA_DIFFICULTY.get(asana_name, 1)))}"
            
            # Проверяем общую длину (Telegram лимит - 1024 символа)
            if len(asana_text) > 1024:
                asana_text = asana_text[:1020] + "..."
            
            # Отправляем с фото или без
            try:
                if image_path and os.path.exists(image_path):
                    # Конвертируем в абсолютный путь для Telegram
                    abs_image_path = os.path.abspath(image_path)
                    logger.info(f"Sending photo with absolute path: {abs_image_path}")
                    
                    # Создаем FSInputFile для отправки фото
                    input_file = FSInputFile(abs_image_path)
                    await self.bot.send_photo(
                        chat_id=user_id,
                        photo=input_file,
                        caption=asana_text,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=self.keyboard_service.create_back_to_filters_menu(lang)
                    )
                else:
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=asana_text,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=self.keyboard_service.create_back_to_filters_menu(lang)
                    )
            except Exception as e:
                logger.error(f"Error sending filtered asana: {e}")
                await self.bot.send_message(
                    chat_id=user_id,
                    text=asana_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=self.keyboard_service.create_back_to_filters_menu(lang)
                )
                
        except (ValueError, IndexError) as e:
            logger.error(f"Error parsing filtered_asana callback: {e}")
            await self.bot.send_message(
                chat_id=callback_query.from_user.id,
                text=t(self._lang(callback_query.from_user.id), 'flt_err_bad_data'),
                reply_markup=self.keyboard_service.create_main_menu(self._lang(callback_query.from_user.id))
            )
    
    def _get_difficulty_stars(self, difficulty: int) -> str:
        """Получить звездное представление сложности"""
        return "⭐" * difficulty
    
    def _get_difficulty_text(self, lang: str, difficulty: int) -> str:
        """Получить текстовое представление сложности"""
        return t(lang, _DIFF_TEXT_KEYS.get(difficulty, 'flt_diff_unknown'))
    
    def _get_effect_emoji(self, effect: str) -> str:
        """Получить эмодзи для эффекта"""
        from src.models.data_models import AsanaEffect
        return AsanaEffect.get_emoji(effect)
    
    def _get_effect_text(self, lang: str, effect: str) -> str:
        """Получить текстовое представление эффекта"""
        return t(lang, _EFFECT_TEXT_KEYS.get(effect, 'flt_effect_unknown'))
    
    def _create_filtered_asanas_keyboard(self, filtered_asanas: List[AsanaData], lang: str = 'ru') -> InlineKeyboardMarkup:
        """Создать клавиатуру с отфильтрованными асанами"""
        from aiogram.types import InlineKeyboardButton
        
        keyboard = []
        for i, asana in enumerate(filtered_asanas[:10]):  # Ограничим до 10 асан для удобства
            # Используем индекс вместо названия для короткого callback_data
            keyboard.append([InlineKeyboardButton(
                text=asana.name,
                callback_data=f"fa_{i}"  # fa = filtered_asana, i = индекс
            )])
        
        # Сохраняем отфильтрованные асаны для доступа по индексу
        self.filtered_asanas_cache = filtered_asanas
        
        # Добавляем навигацию
        keyboard.append([InlineKeyboardButton(text=t(lang, 'btn_back'), callback_data="filter_menu")])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)