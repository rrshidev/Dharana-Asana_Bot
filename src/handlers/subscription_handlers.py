from aiogram import types, Bot
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging

from src.services.subscription_service import SubscriptionService
from src.models.subscription_models import SubscriptionPlan
from src.utils.keyboard_service import KeyboardService
from src.i18n import t
from src.services.database_service import db_service

logger = logging.getLogger(__name__)

class SubscriptionHandlers:
    def __init__(self, bot: Bot, subscription_service: SubscriptionService):
        self.bot = bot
        self.subscription_service = subscription_service
        self.keyboard_service = KeyboardService()

    @staticmethod
    def _lang(user_id: int) -> str:
        """Язык пользователя ('ru'|'en')."""
        return db_service.get_user_language(user_id)

    async def subscription_plans_callback(self, callback_query: types.CallbackQuery):
        """Показывает тарифные планы"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)

        subscription_info = await self.subscription_service.get_subscription_info(user_id)

        text = (
            f"{t(lang, 'sub_plans_title')}\n\n"
            f"{t(lang, 'sub_plans_status', status=subscription_info['status'])}\n\n"
            f"{t(lang, 'sub_plans_benefits')}\n\n"
            f"{t(lang, 'sub_plans_choose')}"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, 'sub_btn_trial7'), callback_data="subscription_trial")],
            [InlineKeyboardButton(text=t(lang, 'sub_btn_pay'), callback_data="pay_now")],
            [InlineKeyboardButton(text=t(lang, 'sub_btn_features'), callback_data="subscription_features")],
            [InlineKeyboardButton(text=t(lang, 'btn_back'), callback_data="main_menu")]
        ])

        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )

    async def subscription_trial_callback(self, callback_query: types.CallbackQuery):
        """Активирует пробный период"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)

        # Проверяем, не использовал ли пользователь триал
        subscription = self.subscription_service.get_user_subscription(user_id)

        if subscription.trial_used:
            text = t(lang, 'sub_trial_used')

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=t(lang, 'sub_btn_month'), callback_data="subscription_monthly")],
                [InlineKeyboardButton(text=t(lang, 'sub_btn_year'), callback_data="subscription_yearly")],
                [InlineKeyboardButton(text=t(lang, 'btn_back'), callback_data="subscription_plans")]
            ])
        else:
            # Активируем триал
            success = self.subscription_service.activate_trial(user_id)

            if success:
                text = t(lang, 'sub_trial_ok')

                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=t(lang, 'sub_btn_generator'), callback_data="sequence_menu")],
                    [InlineKeyboardButton(text=t(lang, 'btn_home'), callback_data="main_menu")]
                ])
            else:
                text = t(lang, 'sub_trial_error')
                keyboard = self.keyboard_service.create_back_to_main_menu()

        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )

    async def subscription_features_callback(self, callback_query: types.CallbackQuery):
        """Показывает подробности о функциях"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)

        text = t(lang, 'sub_features_full')

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, 'seq_btn_trial'), callback_data="subscription_trial")],
            [InlineKeyboardButton(text=t(lang, 'seq_btn_plans'), callback_data="subscription_plans")],
            [InlineKeyboardButton(text=t(lang, 'btn_back'), callback_data="main_menu")]
        ])

        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )

    async def subscription_monthly_callback(self, callback_query: types.CallbackQuery):
        """Обработка покупки месячной подписки"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)

        # Временно показываем реквизиты и просим прислать чек (мок-оплата)
        text = t(lang, 'sub_monthly_buy')

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, 'sub_btn_pay'), callback_data="pay_now")],
            [InlineKeyboardButton(text=t(lang, 'btn_back'), callback_data="subscription_plans")]
        ])

        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )

    async def subscription_yearly_callback(self, callback_query: types.CallbackQuery):
        """Обработка покупки годовой подписки"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)

        text = t(lang, 'sub_yearly_buy')

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, 'sub_btn_pay'), callback_data="pay_now")],
            [InlineKeyboardButton(text=t(lang, 'btn_back'), callback_data="subscription_plans")]
        ])

        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )

    async def subscription_status_callback(self, callback_query: types.CallbackQuery):
        """Показывает статус подписки пользователя"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)

        subscription_info = await self.subscription_service.get_subscription_info(user_id)

        if subscription_info['is_active']:
            if subscription_info['is_trial']:
                days_left = subscription_info['days_left']
                text = t(lang, 'sub_status_trial_full', days_left=days_left)
            else:
                days_left = subscription_info['days_left']
                text = t(lang, 'sub_status_premium_full', days_left=days_left)
        else:
            text = t(lang, 'sub_status_free_full')

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, 'seq_btn_plans'), callback_data="subscription_plans")],
            [InlineKeyboardButton(text=t(lang, 'btn_back'), callback_data="main_menu")]
        ])

        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )