import logging
from aiogram import types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup
from src.services.data_service import DataService
from src.services.filter_service import FilterService, AsanaDayNotifier
from src.utils.keyboard_service import KeyboardService

logger = logging.getLogger(__name__)


class FilterHandlers:
    """Обработчики для фильтров и асаны дня"""
    
    def __init__(self, bot, data_service: DataService):
        self.bot = bot
        self.data_service = data_service
        self.filter_service = FilterService(data_service)
        self.keyboard_service = KeyboardService()
        self.asana_day_notifier = AsanaDayNotifier(bot, self.filter_service)
        
        # Хранилище предпочтений пользователей (в будущем будет в БД)
        self.user_preferences = {}
    
    async def filter_difficulty_callback(self, callback_query: types.CallbackQuery):
        """Обработчик выбора фильтра сложности"""
        await self.bot.answer_callback_query(callback_query.id)
        
        data = callback_query.data.split('_')
        if len(data) < 3:
            return
        
        action = data[2]
        user_id = callback_query.from_user.id
        
        if action == "reset":
            # Сбрасываем фильтр сложности
            if user_id in self.user_preferences:
                self.user_preferences[user_id].difficulty = None
            
            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=callback_query.message.message_id,
                text="🔄 Фильтр сложности сброшен\n\n"
                       "Теперь показываются все асаны любого уровня сложности.",
                reply_markup=self.keyboard_service.create_main_menu()
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
                        text="😔 Асан с таким уровнем сложности не найдено\n\n"
                               "Попробуйте другой уровень сложности или сбросьте фильтр.",
                        reply_markup=self.filter_service.get_difficulty_filter_keyboard(difficulty)
                    )
                    return
                
                await self.bot.edit_message_text(
                    chat_id=user_id,
                    message_id=callback_query.message.message_id,
                    text=f"✅ Фильтр применен!\n\n"
                           f"Показаны асаны сложности: "
                           f"{'⭐' * difficulty} ({self._get_difficulty_text(difficulty)})\n"
                           f"Найдено асан: {len(filtered_asanas)}\n\n"
                           "Выберите асану из каталога:",
                    reply_markup=self.keyboard_service.create_main_menu()
                )
                
            except ValueError:
                logger.error(f"Invalid difficulty value: {action}")
    
    async def filter_effect_callback(self, callback_query: types.CallbackQuery):
        """Обработчик выбора фильтра эффектов"""
        await self.bot.answer_callback_query(callback_query.id)
        
        data = callback_query.data.split('_')
        if len(data) < 3:
            return
        
        action = data[2]
        user_id = callback_query.from_user.id
        
        if action == "reset":
            # Сбрасываем фильтр эффектов
            if user_id in self.user_preferences:
                self.user_preferences[user_id].effects = None
            
            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=callback_query.message.message_id,
                text="🔄 Фильтр эффектов сброшен\n\n"
                       "Теперь показываются все асаны с любыми эффектами.",
                reply_markup=self.keyboard_service.create_main_menu()
            )
        else:
            # Устанавливаем новый фильтр эффектов
            effect = action
            if user_id not in self.user_preferences:
                from src.models.data_models import UserPreferences
                self.user_preferences[user_id] = UserPreferences()
            
            if not self.user_preferences[user_id].effects:
                self.user_preferences[user_id].effects = []
            
            if effect not in self.user_preferences[user_id].effects:
                self.user_preferences[user_id].effects.append(effect)
            
            # Получаем отфильтрованные асаны
            all_asanas = self.data_service.get_all_asanas()
            filtered_asanas = self.filter_service.filter_asanas(
                all_asanas, self.user_preferences[user_id]
            )
            
            if not filtered_asanas:
                await self.bot.edit_message_text(
                    chat_id=user_id,
                    message_id=callback_query.message.message_id,
                    text="😔 Асан с таким эффектом не найдено\n\n"
                           "Попробуйте другой эффект или сбросьте фильтр.",
                    reply_markup=self.filter_service.get_effect_filter_keyboard([effect])
                )
                return
            
            effect_emoji = self._get_effect_emoji(effect)
            effect_text = self._get_effect_text(effect)
            
            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=callback_query.message.message_id,
                text=f"✅ Фильтр применен!\n\n"
                       f"Показаны асаны с эффектом: {effect_emoji} {effect_text}\n"
                       f"Найдено асан: {len(filtered_asanas)}\n\n"
                       "Выберите асану из каталога:",
                reply_markup=self.keyboard_service.create_main_menu()
            )
    
    async def show_filter_menu_callback(self, callback_query: types.CallbackQuery):
        """Показать меню фильтров"""
        await self.bot.answer_callback_query(callback_query.id)
        
        user_id = callback_query.from_user.id
        
        # Получаем текущие предпочтения
        current_difficulty = None
        current_effects = None
        
        if user_id in self.user_preferences:
            current_difficulty = self.user_preferences[user_id].difficulty
            current_effects = self.user_preferences[user_id].effects
        
        filter_menu_text = (
            "🔍 **Меню фильтров**\n\n"
            "Выберите, какие асаны показывать:\n\n"
            "⭐ **По сложности** - от начального до мастерского уровня\n"
            "🎯 **По эффекту** - для конкретных результатов\n\n"
            "Фильтры помогут найти асаны под ваши цели!"
        )
        
        filter_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    {"text": "⭐ Фильтр по сложности", "callback_data": "filter_difficulty_menu"},
                    {"text": "🎯 Фильтр по эффектам", "callback_data": "filter_effect_menu"}
                ],
                [
                    {"text": "🧘 Асана дня", "callback_data": "daily_asana"},
                    {"text": "🔄 Сбросить все", "callback_data": "filter_reset_all"}
                ],
                [
                    {"text": "🔙 Назад", "callback_data": "catalog"}
                ]
            ]
        )
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=filter_menu_text,
            reply_markup=filter_keyboard
        )
    
    async def show_difficulty_filter_menu(self, callback_query: types.CallbackQuery):
        """Показать меню фильтра сложности"""
        await self.bot.answer_callback_query(callback_query.id)
        
        user_id = callback_query.from_user.id
        current_difficulty = None
        
        if user_id in self.user_preferences:
            current_difficulty = self.user_preferences[user_id].difficulty
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text="⭐ **Выберите сложность асан:**\n\n"
                   "Фильтр покажет только асаны выбранного уровня сложности.",
            reply_markup=self.filter_service.get_difficulty_filter_keyboard(current_difficulty)
        )
    
    async def show_effect_filter_menu(self, callback_query: types.CallbackQuery):
        """Показать меню фильтра эффектов"""
        await self.bot.answer_callback_query(callback_query.id)
        
        user_id = callback_query.from_user.id
        current_effects = None
        
        if user_id in self.user_preferences:
            current_effects = self.user_preferences[user_id].effects
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text="🎯 **Выберите желаемый эффект:**\n\n"
                   "Фильтр покажет асаны, которые помогают достичь выбранного результата.",
            reply_markup=self.filter_service.get_effect_filter_keyboard(current_effects)
        )
    
    async def show_daily_asana(self, callback_query: types.CallbackQuery):
        """Показать асану дня"""
        await self.bot.answer_callback_query(callback_query.id)
        
        user_id = callback_query.from_user.id
        daily_asana = self.filter_service.get_daily_asana(user_id)
        
        if not daily_asana:
            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=callback_query.message.message_id,
                text="😔 Асаны дня временно недоступны\n\n"
                       "Попробуйте выбрать асану из каталога.",
                reply_markup=self.keyboard_service.create_main_menu()
            )
            return
        
        description, has_premium_hint = self.filter_service.get_asana_with_premium_hint(
            daily_asana, user_id
        )
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=f"🧘‍♂️ **Асана дня**\n\n"
                   f"**{daily_asana.name}**\n\n"
                   f"{description}\n\n"
                   f"Сложность: {self._get_difficulty_stars(daily_asana.difficulty)} "
                   f"({self._get_difficulty_text(daily_asana.difficulty)})\n"
                   "⏰ Практикуй сегодня и будь здоров!",
            reply_markup=self.keyboard_service.create_main_menu()
        )
    
    async def reset_all_filters(self, callback_query: types.CallbackQuery):
        """Сбросить все фильтры"""
        await self.bot.answer_callback_query(callback_query.id)
        
        user_id = callback_query.from_user.id
        
        if user_id in self.user_preferences:
            del self.user_preferences[user_id]
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text="🔄 Все фильтры сброшены\n\n"
                   "Теперь показываются все асаны без ограничений.",
            reply_markup=self.keyboard_service.create_main_menu()
        )
    
    def _get_difficulty_stars(self, difficulty: int) -> str:
        """Получить звездное представление сложности"""
        return "⭐" * difficulty
    
    def _get_difficulty_text(self, difficulty: int) -> str:
        """Получить текстовое представление сложности"""
        texts = {
            1: "Начальный",
            2: "Средний",
            3: "Продвинутый",
            4: "Экспертный",
            5: "Мастерский"
        }
        return texts.get(difficulty, "Неизвестно")
    
    def _get_effect_emoji(self, effect: str) -> str:
        """Получить эмодзи для эффекта"""
        from src.models.data_models import AsanaEffect
        return AsanaEffect.get_emoji(effect)
    
    def _get_effect_text(self, effect: str) -> str:
        """Получить текстовое представление эффекта"""
        from src.models.data_models import AsanaEffect
        return AsanaEffect.get_description(effect)
