from aiogram import types, Bot
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import logging

from src.models.sequence_models import SequenceParams, SequenceDifficulty, SequenceDuration, SequenceFocus
from src.models.timer_models import practice_asana_context, timer_messages, sequence_advance_callbacks
from src.services.timer_service import timer_service
from src.utils.timer_ui import TimerUI
from src.services.sequence_generator import SequenceGenerator
from src.services.sequence_practice_service import SequencePracticeService
from src.services.data_service import DataService
from src.services.subscription_service import SubscriptionService
from src.utils.keyboard_service import KeyboardService
from src.i18n import t
from src.services.database_service import db_service

logger = logging.getLogger(__name__)

_DIFF_KEYS = {
    'beginner': 'seq_btn_beginner',
    'intermediate': 'seq_btn_intermediate',
    'advanced': 'seq_btn_advanced',
}

_DUR_KEYS = {
    '15': 'seq_btn_15min',
    '30': 'seq_btn_30min',
    '60': 'seq_btn_60min',
}

_FOCUS_KEYS = {
    'back': 'seq_btn_back_focus',
    'legs': 'seq_btn_legs',
    'balance': 'seq_btn_balance',
    'flexibility': 'seq_btn_flexibility',
    'energy': 'seq_btn_energy',
}

_DUR_LINE_KEYS = {
    '15': 'seq_dur_line_15',
    '30': 'seq_dur_line_30',
    '60': 'seq_dur_line_60',
}


class SequenceHandlers:
    def __init__(self, bot: Bot, data_service: DataService, subscription_service: SubscriptionService):
        self.bot = bot
        self.data_service = data_service
        self.subscription_service = subscription_service
        self.sequence_generator = SequenceGenerator(data_service)
        self.practice_service = SequencePracticeService(data_service)
        self.keyboard_service = KeyboardService()
        
        # Хранилище параметров пользователей
        self.user_sequences = {}

    @staticmethod
    def _lang(user_id: int) -> str:
        """Язык пользователя ('ru'|'en')."""
        return db_service.get_user_language(user_id)

    @staticmethod
    def _diff_name(lang: str, value: str) -> str:
        """Локализованное название сложности по raw-значению ('beginner'|...)."""
        return t(lang, _DIFF_KEYS[value])

    @staticmethod
    def _focus_name(lang: str, value: str) -> str:
        """Локализованное название фокуса по raw-значению ('back'|...)."""
        return t(lang, _FOCUS_KEYS[value])

    async def _send_phase_notification(self, user_id: int, text: str, delay: int = 2):
        """Отправляет временное уведомление со звуком и удаляет его через несколько секунд"""
        try:
            notification_message = await self.bot.send_message(
                user_id,
                text,
                parse_mode=ParseMode.MARKDOWN
            )
            asyncio.create_task(self._delete_notification_after_delay(user_id, notification_message.message_id, delay))
        except Exception as e:
            logger.error(f"Error sending phase notification for user {user_id}: {e}")

    async def _delete_notification_after_delay(self, user_id: int, message_id: int, delay: int):
        await asyncio.sleep(delay)
        try:
            await self.bot.delete_message(chat_id=user_id, message_id=message_id)
        except Exception as e:
            logger.error(f"Error deleting notification {message_id}: {e}")

    async def sequence_menu_callback(self, callback_query: types.CallbackQuery):
        """Главное меню генератора последовательностей"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)

        text = t(lang, 'seq_menu_title')

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, 'seq_btn_difficulty'), callback_data="sequence_difficulty")],
            [InlineKeyboardButton(text=t(lang, 'seq_btn_duration'), callback_data="sequence_duration")],
            [InlineKeyboardButton(text=t(lang, 'seq_btn_focus'), callback_data="sequence_focus")],
            [InlineKeyboardButton(text=t(lang, 'seq_btn_generate'), callback_data="sequence_generate")],
            [InlineKeyboardButton(text=t(lang, 'btn_back_main'), callback_data="main_menu")]
        ])

        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )

    async def sequence_difficulty_callback(self, callback_query: types.CallbackQuery):
        """Выбор сложности"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)

        # Получаем текущие параметры пользователя или создаем новые
        if user_id not in self.user_sequences:
            self.user_sequences[user_id] = {
                'difficulty': SequenceDifficulty.BEGINNER,
                'duration': SequenceDuration.MEDIUM,
                'focus': SequenceFocus.BACK
            }

        text = (
            f"{t(lang, 'seq_diff_title')}\n\n"
            f"{t(lang, 'seq_diff_line_beginner')}\n"
            f"{t(lang, 'seq_diff_line_intermediate')}\n"
            f"{t(lang, 'seq_diff_line_advanced')}"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, 'seq_btn_beginner'), callback_data="sequence_set_difficulty_beginner")],
            [InlineKeyboardButton(text=t(lang, 'seq_btn_intermediate'), callback_data="sequence_set_difficulty_intermediate")],
            [InlineKeyboardButton(text=t(lang, 'seq_btn_advanced'), callback_data="sequence_set_difficulty_advanced")],
            [InlineKeyboardButton(text=t(lang, 'btn_back'), callback_data="sequence_menu")]
        ])

        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )

    async def sequence_set_difficulty_callback(self, callback_query: types.CallbackQuery):
        """Установка сложности"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)

        difficulty_map = {
            'beginner': SequenceDifficulty.BEGINNER,
            'intermediate': SequenceDifficulty.INTERMEDIATE,
            'advanced': SequenceDifficulty.ADVANCED
        }

        difficulty_str = callback_query.data.split('_')[-1]
        self.user_sequences[user_id]['difficulty'] = difficulty_map[difficulty_str]

        text = t(lang, 'seq_set_difficulty_ok', name=self._diff_name(lang, difficulty_str))

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, 'seq_btn_duration'), callback_data="sequence_duration")],
            [InlineKeyboardButton(text=t(lang, 'seq_btn_focus'), callback_data="sequence_focus")],
            [InlineKeyboardButton(text=t(lang, 'seq_btn_generate'), callback_data="sequence_generate")],
            [InlineKeyboardButton(text=t(lang, 'seq_btn_back_to_menu'), callback_data="sequence_menu")]
        ])

        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )

    async def sequence_duration_callback(self, callback_query: types.CallbackQuery):
        """Выбор длительности"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)

        if user_id not in self.user_sequences:
            self.user_sequences[user_id] = {
                'difficulty': SequenceDifficulty.BEGINNER,
                'duration': SequenceDuration.MEDIUM,
                'focus': SequenceFocus.BACK
            }

        text = (
            f"{t(lang, 'seq_dur_title')}\n\n"
            f"{t(lang, 'seq_dur_line_15')}\n"
            f"{t(lang, 'seq_dur_line_30')}\n"
            f"{t(lang, 'seq_dur_line_60')}"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, 'seq_btn_15min'), callback_data="sequence_set_duration_15")],
            [InlineKeyboardButton(text=t(lang, 'seq_btn_30min'), callback_data="sequence_set_duration_30")],
            [InlineKeyboardButton(text=t(lang, 'seq_btn_60min'), callback_data="sequence_set_duration_60")],
            [InlineKeyboardButton(text=t(lang, 'btn_back'), callback_data="sequence_menu")]
        ])

        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )

    async def sequence_set_duration_callback(self, callback_query: types.CallbackQuery):
        """Установка длительности"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)

        duration_map = {
            '15': SequenceDuration.SHORT,
            '30': SequenceDuration.MEDIUM,
            '60': SequenceDuration.LONG
        }

        duration_str = callback_query.data.split('_')[-1]
        self.user_sequences[user_id]['duration'] = duration_map[duration_str]

        text = t(lang, 'seq_set_duration_ok', name=t(lang, _DUR_KEYS[duration_str]))

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, 'seq_btn_difficulty'), callback_data="sequence_difficulty")],
            [InlineKeyboardButton(text=t(lang, 'seq_btn_focus'), callback_data="sequence_focus")],
            [InlineKeyboardButton(text=t(lang, 'seq_btn_generate'), callback_data="sequence_generate")],
            [InlineKeyboardButton(text=t(lang, 'seq_btn_back_to_menu'), callback_data="sequence_menu")]
        ])

        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )

    async def sequence_focus_callback(self, callback_query: types.CallbackQuery):
        """Выбор фокуса практики"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)

        if user_id not in self.user_sequences:
            self.user_sequences[user_id] = {
                'difficulty': SequenceDifficulty.BEGINNER,
                'duration': SequenceDuration.MEDIUM,
                'focus': SequenceFocus.BACK
            }

        text = (
            f"{t(lang, 'seq_focus_title')}\n\n"
            f"{t(lang, 'seq_focus_line_back')}\n"
            f"{t(lang, 'seq_focus_line_legs')}\n"
            f"{t(lang, 'seq_focus_line_balance')}\n"
            f"{t(lang, 'seq_focus_line_flexibility')}\n"
            f"{t(lang, 'seq_focus_line_energy')}"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, 'seq_btn_back_focus'), callback_data="sequence_set_focus_back")],
            [InlineKeyboardButton(text=t(lang, 'seq_btn_legs'), callback_data="sequence_set_focus_legs")],
            [InlineKeyboardButton(text=t(lang, 'seq_btn_balance'), callback_data="sequence_set_focus_balance")],
            [InlineKeyboardButton(text=t(lang, 'seq_btn_flexibility'), callback_data="sequence_set_focus_flexibility")],
            [InlineKeyboardButton(text=t(lang, 'seq_btn_energy'), callback_data="sequence_set_focus_energy")],
            [InlineKeyboardButton(text=t(lang, 'btn_back'), callback_data="sequence_menu")]
        ])

        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )

    async def sequence_set_focus_callback(self, callback_query: types.CallbackQuery):
        """Установка фокуса"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)

        focus_map = {
            'back': SequenceFocus.BACK,
            'legs': SequenceFocus.LEGS,
            'balance': SequenceFocus.BALANCE,
            'flexibility': SequenceFocus.FLEXIBILITY,
            'energy': SequenceFocus.ENERGY
        }

        focus_str = callback_query.data.split('_')[-1]
        self.user_sequences[user_id]['focus'] = focus_map[focus_str]

        text = t(lang, 'seq_set_focus_ok', name=self._focus_name(lang, focus_str))

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, 'seq_btn_difficulty'), callback_data="sequence_difficulty")],
            [InlineKeyboardButton(text=t(lang, 'seq_btn_duration'), callback_data="sequence_duration")],
            [InlineKeyboardButton(text=t(lang, 'seq_btn_generate'), callback_data="sequence_generate")],
            [InlineKeyboardButton(text=t(lang, 'seq_btn_back_to_menu'), callback_data="sequence_menu")]
        ])

        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )

    async def sequence_generate_callback(self, callback_query: types.CallbackQuery):
        """Генерация последовательности"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)

        # Проверяем, есть ли параметры
        if user_id not in self.user_sequences:
            await self.sequence_menu_callback(callback_query)
            return

        # Проверяем лимиты генераций
        can_generate, message = await self.subscription_service.can_generate_sequence(user_id)
        if not can_generate:
            # Показываем сообщение с предложением подписки
            subscription_info = await self.subscription_service.get_subscription_info(user_id)

            text = (
                f"{message}\n\n"
                f"{t(lang, 'seq_premium_title_block')}"
            )

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=t(lang, 'seq_btn_trial'), callback_data="subscription_trial")],
                [InlineKeyboardButton(text=t(lang, 'seq_btn_plans'), callback_data="subscription_plans")],
                [InlineKeyboardButton(text=t(lang, 'btn_back'), callback_data="sequence_menu")]
            ])

            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=callback_query.message.message_id,
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
            return

        params_data = self.user_sequences[user_id]
        params = SequenceParams(
            difficulty=params_data['difficulty'],
            duration=params_data['duration'],
            focus=params_data['focus']
        )

        # Используем генерацию (считаем лимит для бесплатных пользователей)
        generation_used = await self.subscription_service.use_generation(user_id)
        if not generation_used[0]:
            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=callback_query.message.message_id,
                text=generation_used[1]
            )
            return

        # Генерируем последовательность
        try:
            sequence = self.sequence_generator.generate_sequence(params)

            # Сохраняем последовательность для пользователя
            self.user_sequences[user_id]['current_sequence'] = sequence

            # Добавляем информацию о статусе подписки
            subscription_info = await self.subscription_service.get_subscription_info(user_id)
            status_info = f"\n💎 {subscription_info['status']}"

            # Компактный список асан практики
            asana_lines = []
            for i, item in enumerate(sequence.items, 1):
                if item.is_rest:
                    asana_lines.append(t(lang, 'seq_item_rest', n=i, name=t(lang, 'seq_rest_short'), sec=item.duration_seconds))
                else:
                    asana_lines.append(t(lang, 'seq_item_asana', n=i, name=item.asana_name, sec=item.duration_seconds))
            asana_list_text = "\n".join(asana_lines)

            text = (
                f"{t(lang, 'seq_ready_title')}\n\n"
                f"{t(lang, 'seq_diff_value_line', name=self._diff_name(lang, params.difficulty.value))}\n"
                f"{t(lang, 'seq_dur_value_line', mins=params.duration.value)}\n"
                f"{t(lang, 'seq_focus_value_line', name=self._focus_name(lang, params.focus.value))}\n"
                f"{t(lang, 'seq_calories_line', kcal=sequence.estimated_calories)}\n\n"
                f"{t(lang, 'seq_practice_list_title', count=len(sequence.items))}\n"
                f"{asana_list_text}{status_info}\n\n"
                f"{t(lang, 'seq_ready_prompt')}"
            )

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=t(lang, 'seq_btn_start_practice'), callback_data="sequence_start")],
                [InlineKeyboardButton(text=t(lang, 'seq_btn_show_seq'), callback_data="sequence_show")],
                [InlineKeyboardButton(text=t(lang, 'seq_btn_regenerate'), callback_data="sequence_generate")],
                [InlineKeyboardButton(text=t(lang, 'seq_btn_back_to_menu'), callback_data="sequence_menu")]
            ])

            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=callback_query.message.message_id,
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )

        except Exception as e:
            logger.error(f"Error generating sequence for user {user_id}: {e}")
            await self.bot.send_message(
                user_id,
                t(lang, 'seq_gen_error')
            )

    async def sequence_show_callback(self, callback_query: types.CallbackQuery):
        """Показать последовательность"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)

        if user_id not in self.user_sequences or 'current_sequence' not in self.user_sequences[user_id]:
            await self.sequence_menu_callback(callback_query)
            return

        sequence = self.user_sequences[user_id]['current_sequence']

        text = t(lang, 'seq_show_title') + "\n\n"

        for i, item in enumerate(sequence.items, 1):
            if item.is_rest:
                text += t(lang, 'seq_show_item_rest', n=i, name=item.asana_name, sec=item.duration_seconds)
            else:
                text += t(lang, 'seq_show_item_asana', n=i, name=item.asana_name, sec=item.duration_seconds)
                text += f"   _{item.description}_\n\n"

        # Добавляем информацию о последовательности
        text += t(lang, 'seq_show_total', count=len(sequence.items), mins=sequence.total_duration.total_seconds() // 60)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, 'seq_btn_start_practice'), callback_data="sequence_start")],
            [InlineKeyboardButton(text=t(lang, 'seq_btn_regenerate'), callback_data="sequence_generate")],
            [InlineKeyboardButton(text=t(lang, 'btn_back'), callback_data="sequence_menu")]
        ])

        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )

    async def sequence_start_callback(self, callback_query: types.CallbackQuery):
        """Начать практику с последовательностью"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)

        if user_id not in self.user_sequences or 'current_sequence' not in self.user_sequences[user_id]:
            await self.sequence_menu_callback(callback_query)
            return

        sequence = self.user_sequences[user_id]['current_sequence']

        # Сбрасываем предыдущую незавершённую практику
        if user_id in self.practice_service.active_sequences:
            self.practice_service.stop_sequence(user_id)
        sequence_advance_callbacks.pop(user_id, None)

        # Запускаем последовательную практику
        if self.practice_service.start_sequence(user_id, sequence):
            # Автопереход между асанами при завершении таймера
            sequence_advance_callbacks[user_id] = self._advance_sequence
            # Отправляем первую асану
            await self._send_first_asana(user_id, callback_query.message.message_id)
        else:
            await self.bot.send_message(
                user_id,
                t(lang, 'seq_start_error')
            )

    async def _send_first_asana(self, user_id: int, message_id: int):
        """Отправляет первую асану последовательности"""
        lang = self._lang(user_id)
        current_asana = self.practice_service.get_current_asana(user_id)
        if not current_asana:
            return

        # Запоминаем имя текущей асаны для таймера
        practice_asana_context[user_id] = current_asana.asana_name

        progress = self.practice_service.get_progress(user_id)

        pct = f"{progress['progress_percent']:.0f}"
        if current_asana.is_rest:
            text = (
                f"{t(lang, 'seq_rest_title')}\n\n"
                f"{current_asana.description}\n\n"
                f"{t(lang, 'seq_sec_word', sec=current_asana.duration_seconds)}\n\n"
                f"{t(lang, 'seq_progress_inline', cur=progress['current'], total=progress['total'], pct=pct)}"
            )
        else:
            text = (
                f"{t(lang, 'seq_asana_title_named', name=current_asana.asana_name)}\n\n"
                f"{current_asana.description}\n\n"
                f"{t(lang, 'seq_sec_word', sec=current_asana.duration_seconds)}\n"
                f"{t(lang, 'seq_progress_inline', cur=progress['current'], total=progress['total'], pct=pct)}"
            )

        # Создаем клавиатуру для практики с кнопкой таймера
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, 'seq_btn_start_timer'), callback_data="timer_asana")],
            [InlineKeyboardButton(text=t(lang, 'seq_btn_next_asana'), callback_data="sequence_skip")],
            [InlineKeyboardButton(text=t(lang, 'seq_btn_finish'), callback_data="sequence_stop")],
            [InlineKeyboardButton(text=f"📊 {progress.get('current', 0)}/{progress.get('total', 0)}", callback_data="sequence_progress")]
        ])

        # Добавляем изображение если есть
        if current_asana.image_path:
            try:
                with open(current_asana.image_path, 'rb') as photo:
                    await self.bot.edit_message_media(
                        chat_id=user_id,
                        message_id=message_id,
                        media=types.InputMediaPhoto(
                            media=photo,
                            caption=text
                        ),
                        reply_markup=keyboard
                    )
            except Exception as e:
                logger.error(f"Error sending image for asana {current_asana.asana_name}: {e}")
                # Если не удалось отправить изображение, отправляем текст
                await self.bot.edit_message_text(
                    chat_id=user_id,
                    message_id=message_id,
                    text=text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=keyboard
                )
        else:
            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )

        # Автозапуск таймера первой асаны — практика идёт цепочкой таймеров
        await self._auto_start_asana_timer(user_id, message_id)

    async def _auto_start_asana_timer(self, user_id: int, message_id: int):
        """Автоматически запускает таймер текущей асаны и выводит отсчёт в её сообщение"""
        try:
            started = await self.practice_service.start_timer_for_asana(user_id, self.bot, message_id)
            if started:
                timer_messages[user_id] = message_id
                session = timer_service.get_session(user_id)
                if session:
                    await self.bot.edit_message_text(
                        chat_id=user_id,
                        message_id=message_id,
                        text=TimerUI.format_timer_message(session),
                        reply_markup=TimerUI.get_control_keyboard(session),
                        parse_mode=ParseMode.MARKDOWN
                    )
        except Exception as e:
            logger.error(f"Error auto-starting timer for user {user_id}: {e}")

    async def _advance_sequence(self, user_id: int, message_id: int | None):
        """Переход к следующей асане при завершении таймера текущей"""
        if user_id not in self.practice_service.active_sequences:
            sequence_advance_callbacks.pop(user_id, None)
            return
        if message_id is None:
            message_id = timer_messages.get(user_id)
        if self.practice_service.move_to_next_asana(user_id):
            sequence_advance_callbacks[user_id] = self._advance_sequence
            if message_id:
                await self._send_next_asana(user_id, self.bot, message_id)
        else:
            sequence_advance_callbacks.pop(user_id, None)
            if message_id:
                await self._send_sequence_complete(user_id, self.bot, message_id)

    async def sequence_pause_callback(self, callback_query: types.CallbackQuery):
        """Поставить практику на паузу"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id

        await self.practice_service.pause_sequence(user_id, self.bot, callback_query.message.message_id)

    async def sequence_resume_callback(self, callback_query: types.CallbackQuery):
        """Возобновить практику"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id

        await self.practice_service.resume_sequence(user_id, self.bot, callback_query.message.message_id)

    async def sequence_skip_callback(self, callback_query: types.CallbackQuery):
        """Пропустить текущую асану"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id

        if self.practice_service.move_to_next_asana(user_id):
            await self._send_next_asana(user_id, self.bot, callback_query.message.message_id)
        else:
            await self._send_sequence_complete(user_id, self.bot, callback_query.message.message_id)

    async def _send_next_asana(self, user_id: int, bot, message_id: int):
        """Отправляет следующую асану"""
        lang = self._lang(user_id)
        current_asana = self.practice_service.get_current_asana(user_id)
        if not current_asana:
            return

        # Запоминаем имя текущей асаны для таймера
        practice_asana_context[user_id] = current_asana.asana_name

        # Звуковое уведомление о смене фазы
        phase_name = t(lang, 'seq_phase_rest') if current_asana.is_rest else current_asana.asana_name
        await self._send_phase_notification(user_id, t(lang, 'seq_phase_notif', name=phase_name))

        progress = self.practice_service.get_progress(user_id)

        pct = f"{progress['progress_percent']:.0f}"
        if current_asana.is_rest:
            text = (
                f"{t(lang, 'seq_rest_title')}\n\n"
                f"{current_asana.description}\n\n"
                f"{t(lang, 'seq_sec_word', sec=current_asana.duration_seconds)}\n\n"
                f"{t(lang, 'seq_progress_inline', cur=progress['current'], total=progress['total'], pct=pct)}"
            )
        else:
            text = (
                f"{t(lang, 'seq_asana_title_named', name=current_asana.asana_name)}\n\n"
                f"{current_asana.description}\n\n"
                f"{t(lang, 'seq_sec_word', sec=current_asana.duration_seconds)}\n"
                f"{t(lang, 'seq_progress_inline', cur=progress['current'], total=progress['total'], pct=pct)}"
            )

        # Создаем клавиатуру для практики с кнопкой таймера
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, 'seq_btn_start_timer'), callback_data="timer_asana")],
            [InlineKeyboardButton(text=t(lang, 'seq_btn_next_asana'), callback_data="sequence_skip")],
            [InlineKeyboardButton(text=t(lang, 'seq_btn_finish'), callback_data="sequence_stop")],
            [InlineKeyboardButton(text=f"📊 {progress.get('current', 0)}/{progress.get('total', 0)}", callback_data="sequence_progress")]
        ])

        # Добавляем изображение если есть
        if current_asana.image_path:
            try:
                with open(current_asana.image_path, 'rb') as photo:
                    await bot.edit_message_media(
                        chat_id=user_id,
                        message_id=message_id,
                        media=types.InputMediaPhoto(
                            media=photo,
                            caption=text
                        ),
                        reply_markup=keyboard
                    )
            except Exception as e:
                logger.error(f"Error sending image for asana {current_asana.asana_name}: {e}")
                # Если не удалось отправить изображение, отправляем текст
                await bot.edit_message_text(
                    chat_id=user_id,
                    message_id=message_id,
                    text=text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=keyboard
                )
        else:
            await bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )

        # Автозапуск таймера следующей асаны
        await self._auto_start_asana_timer(user_id, message_id)

    async def _send_sequence_complete(self, user_id: int, bot, message_id: int):
        """Отправляет сообщение о завершении последовательности"""
        lang = self._lang(user_id)
        sequence = self.practice_service.active_sequences.get(user_id)
        if not sequence:
            return

        await self._send_phase_notification(user_id, t(lang, 'seq_done_notif'))

        text = (
            f"{t(lang, 'seq_complete_title')}\n\n"
            f"{t(lang, 'seq_complete_stats')}\n"
            f"{t(lang, 'seq_complete_done', count=len(sequence.items))}\n"
            f"{t(lang, 'seq_complete_time', mins=sequence.total_duration.total_seconds() // 60)}\n"
            f"{t(lang, 'seq_complete_kcal', kcal=sequence.estimated_calories)}\n\n"
            f"{t(lang, 'seq_complete_prompt')}"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, 'seq_btn_new_practice'), callback_data="sequence_menu")],
            [InlineKeyboardButton(text=t(lang, 'btn_home'), callback_data="main_menu")]
        ])

        await bot.edit_message_text(
            chat_id=user_id,
            message_id=message_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )

        # Останавливаем последовательность
        sequence_advance_callbacks.pop(user_id, None)
        self.practice_service.stop_sequence(user_id)

    async def sequence_stop_callback(self, callback_query: types.CallbackQuery):
        """Завершить практику"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)

        sequence_advance_callbacks.pop(user_id, None)
        self.practice_service.stop_sequence(user_id)

        text = (
            f"{t(lang, 'seq_stopped_title')}\n\n"
            f"{t(lang, 'seq_stopped_text')}"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, 'seq_btn_new_practice'), callback_data="sequence_menu")],
            [InlineKeyboardButton(text=t(lang, 'btn_home'), callback_data="main_menu")]
        ])

        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )

    async def sequence_progress_callback(self, callback_query: types.CallbackQuery):
        """Показать прогресс практики"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)

        progress = self.practice_service.get_progress(user_id)
        if not progress:
            return

        sequence = self.practice_service.active_sequences.get(user_id)
        if not sequence:
            return

        pct = f"{progress['progress_percent']:.0f}"

        text = (
            f"{t(lang, 'seq_progress_title')}\n\n"
            f"{t(lang, 'seq_progress_params_title')}\n"
            f"{t(lang, 'seq_progress_diff', value=sequence.params.difficulty.value)}\n"
            f"{t(lang, 'seq_progress_dur', value=sequence.params.duration.value)}\n"
            f"{t(lang, 'seq_progress_focus', value=sequence.params.focus.value)}\n\n"
            f"{t(lang, 'seq_progress_exec_title')}\n"
            f"{t(lang, 'seq_progress_asanas', cur=progress['current'], total=progress['total'])}\n"
            f"{t(lang, 'seq_progress_pct', pct=pct)}\n"
            f"{t(lang, 'seq_progress_time', mins=sequence.total_duration.total_seconds() // 60)}\n"
            f"{t(lang, 'seq_progress_kcal', kcal=sequence.estimated_calories)}"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, 'seq_btn_back_to_practice'), callback_data="sequence_resume")]
        ])

        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )