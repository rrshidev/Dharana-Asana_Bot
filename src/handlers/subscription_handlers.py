from aiogram import types, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging

from src.services.subscription_service import SubscriptionService
from src.models.subscription_models import SubscriptionPlan
from src.utils.keyboard_service import KeyboardService

logger = logging.getLogger(__name__)

class SubscriptionHandlers:
    def __init__(self, bot: Bot, subscription_service: SubscriptionService):
        self.bot = bot
        self.subscription_service = subscription_service
        self.keyboard_service = KeyboardService()
    
    async def subscription_plans_callback(self, callback_query: types.CallbackQuery):
        """Показывает тарифные планы"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        
        subscription_info = self.subscription_service.get_subscription_info(user_id)
        
        text = (
            f"💎 **Премиум-доступ к Йога Энциклопедии**\n\n"
            f"Текущий статус: {subscription_info['status']}\n\n"
            f"🎯 **Что вы получаете:**\n"
            f"• 🔄 Безлимитные генерации последовательностей\n"
            f"• 🎥 Видео-отстройка для 50+ асан\n"
            f"• 📊 Детальная статистика практики\n"
            f"• 🎵 Аудио-медитации и голосовое управление\n"
            f"• 📝 Персональные комплексы под задачи\n"
            f"• 🚀 Приоритетная поддержка\n\n"
            f"💳 **Выберите тариф:**"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚀 7 дней бесплатно", callback_data="subscription_trial")],
            [InlineKeyboardButton(text="📅 1 месяц - 399₽", callback_data="subscription_monthly")],
            [InlineKeyboardButton(text="📆 1 год - 2990₽", callback_data="subscription_yearly")],
            [InlineKeyboardButton(text="❓ Подробнее о функциях", callback_data="subscription_features")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
        ])
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            reply_markup=keyboard
        )
    
    async def subscription_trial_callback(self, callback_query: types.CallbackQuery):
        """Активирует пробный период"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        
        # Проверяем, не использовал ли пользователь триал
        subscription = self.subscription_service.get_user_subscription(user_id)
        
        if subscription.trial_used:
            text = (
                "❌ **Пробный период уже использован**\n\n"
                "Вы уже активировали 7-дневный пробный период.\n"
                "Для доступа ко всем функциям выберите платный тариф:\n\n"
                "💳 **Доступные тарифы:**\n"
                "• 📅 1 месяц - 399₽\n"
                "• 📆 1 год - 2990₽ (экономия 1800₽)"
            )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📅 1 месяц - 399₽", callback_data="subscription_monthly")],
                [InlineKeyboardButton(text="📆 1 год - 2990₽", callback_data="subscription_yearly")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="subscription_plans")]
            ])
        else:
            # Активируем триал
            success = self.subscription_service.activate_trial(user_id)
            
            if success:
                text = (
                    "🎉 **Пробный период активирован!**\n\n"
                    "✅ Вам доступен 7-дневный премиум-доступ:\n"
                    "• 🔄 Безлимитные генерации последовательностей\n"
                    "• 🎥 Видео-отстройка асан\n"
                    "• 📊 Детальная статистика\n"
                    "• 🎵 Аудио-медитации\n\n"
                    "Наслаждайтесь всеми функциями бота!"
                )
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🏋️‍♂️ Генератор практики", callback_data="sequence_menu")],
                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
                ])
            else:
                text = "❌ Ошибка при активации пробного периода. Попробуйте позже."
                keyboard = self.keyboard_service.create_back_to_main_menu()
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            reply_markup=keyboard
        )
    
    async def subscription_features_callback(self, callback_query: types.CallbackQuery):
        """Показывает подробности о функциях"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        
        text = (
            "💎 **Премиум-функции Йога Энциклопедии**\n\n"
            "🔄 **Генератор практики 'Зал'**\n"
            "• Безлимитные генерации последовательностей\n"
            "• Персональные комплексы под ваши цели\n"
            "• Интеграция с таймером\n\n"
            "🎥 **Видео-отстройка**\n"
            "• 50+ видео с детальной инструкцией\n"
            "• Акцент на правильную технику\n"
            "• Анатомические пояснения\n\n"
            "📊 **Статистика и прогресс**\n"
            "• Отслеживание ваших практик\n"
            "• Любимые асаны и комплексы\n"
            "• Ежедневные достижения\n\n"
            "🎵 **Аудио-сопровождение**\n"
            "• Голосовые инструкции для практик\n"
            "• Фоновая музыка для медитаций\n"
            "• Звуковые таймеры\n\n"
            "🚀 **Эксклюзивный контент**\n"
            "• Готовые программы под задачи\n"
            "• Челленджи и марафоны\n"
            "• Приоритетная поддержка"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Попробовать 7 дней бесплатно", callback_data="subscription_trial")],
            [InlineKeyboardButton(text="💳 Тарифы", callback_data="subscription_plans")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
        ])
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            reply_markup=keyboard
        )
    
    async def subscription_monthly_callback(self, callback_query: types.CallbackQuery):
        """Обработка покупки месячной подписки"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        
        # Временно показываем заглушку - пока нет платежной системы
        text = (
            "💳 **Покупка подписки**\n\n"
            "📅 **Месячная подписка - 399₽**\n\n"
            "⚠️ Платежная система в процессе подключения.\n"
            "Скоро вы сможете оформить подписку прямо в боте!\n\n"
            "Временный вариант:\n"
            "Напишите @admin для активации подписки"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="subscription_plans")]
        ])
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            reply_markup=keyboard
        )
    
    async def subscription_yearly_callback(self, callback_query: types.CallbackQuery):
        """Обработка покупки годовой подписки"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        
        # Временно показываем заглушку - пока нет платежной системы
        text = (
            "💳 **Покупка подписки**\n\n"
            "📆 **Годовая подписка - 2990₽**\n"
            "💰 Экономия 1800₽ по сравнению с месячной!\n\n"
            "⚠️ Платежная система в процессе подключения.\n"
            "Скоро вы сможете оформить подписку прямо в боте!\n\n"
            "Временный вариант:\n"
            "Напишите @admin для активации подписки"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="subscription_plans")]
        ])
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            reply_markup=keyboard
        )
    
    async def subscription_status_callback(self, callback_query: types.CallbackQuery):
        """Показывает статус подписки пользователя"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        
        subscription_info = self.subscription_service.get_subscription_info(user_id)
        
        if subscription_info['is_active']:
            if subscription_info['is_trial']:
                days_left = subscription_info['days_left']
                text = (
                    f"🎯 **Статус: Пробный период**\n\n"
                    f"📅 Осталось дней: {days_left}\n"
                    f"✅ Все функции доступны\n\n"
                    f"После окончания пробного периода\n"
                    f"вы сможете оформить подписку"
                )
            else:
                days_left = subscription_info['days_left']
                text = (
                    f"⭐ **Статус: Премиум**\n\n"
                    f"📅 Осталось дней: {days_left}\n"
                    f"✅ Все функции доступны\n\n"
                    f"Спасибо за поддержку проекта!"
                )
        else:
            text = (
                f"🆓 **Статус: Бесплатная версия**\n\n"
                f"📋 Доступно:\n"
                f"• Энциклопедия асан (фото)\n"
                f"• Простой таймер\n"
                f"• 1 генерация последовательности в день\n\n"
                f"💎 Для премиум-функций оформите подписку"
            )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Тарифы", callback_data="subscription_plans")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
        ])
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            reply_markup=keyboard
        )
