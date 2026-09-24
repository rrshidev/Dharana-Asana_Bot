import logging
import asyncio
import re
from datetime import datetime
from aiogram import types, F
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.i18n import t, format_duration
from src.services.timer_service import timer_service
from src.services.database_service import db_service
from src.services.user_service import UserService
from src.utils.timer_ui import TimerUI
from src.models.timer_models import TimerType, TimerStatus, TimerPhase, TimerConfig, PranayamaConfig, timer_messages, practice_asana_context, sequence_advance_callbacks

logger = logging.getLogger(__name__)


class TimerHandlers:
    """Обработчики для таймера медитации, асан и пранаямы"""

    def __init__(self, bot, data_service, keyboard_service, user_service=None):
        self.bot = bot
        self.data_service = data_service
        self.keyboard_service = keyboard_service
        self.user_service = user_service or UserService()  # запись практики в общую статистику
        self.awaiting_meditation_time = set()  # пользователи, ожидающие ввода времени медитации
        # Импортируем message_handlers для доступа к поиску асан
        from src.handlers.message_handlers import MessageHandlers
        self.message_handlers = MessageHandlers(bot)

    @staticmethod
    def _lang(user_id: int) -> str:
        return db_service.get_user_language(user_id)

    # Главное меню таймера
    async def timer_main_callback(self, callback_query: types.CallbackQuery):
        """Главное меню таймера"""
        await self.bot.answer_callback_query(callback_query.id)

        lang = self._lang(callback_query.from_user.id)

        # Сохраняем ID сообщения для меню таймера
        timer_messages[callback_query.from_user.id] = callback_query.message.message_id

        await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=t(lang, 'timer_main_title'),
            reply_markup=TimerUI.get_main_menu(lang),
            parse_mode=ParseMode.MARKDOWN
        )

    # Медитация
    async def meditation_callback(self, callback_query: types.CallbackQuery):
        """Меню медитации"""
        await self.bot.answer_callback_query(callback_query.id)

        lang = self._lang(callback_query.from_user.id)

        await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=t(lang, 'meditation_title'),
            reply_markup=TimerUI.get_meditation_menu(lang),
            parse_mode=ParseMode.MARKDOWN
        )

    async def meditation_start_callback(self, callback_query: types.CallbackQuery):
        """Запуск медитации"""
        await self.bot.answer_callback_query(callback_query.id)

        lang = self._lang(callback_query.from_user.id)

        # Парсим callback_data: meditation_5, meditation_10, etc.
        parts = callback_query.data.split('_')
        if len(parts) < 2:
            return

        try:
            minutes = int(parts[1])
        except ValueError:
            return

        session = timer_service.create_meditation_timer(callback_query.from_user.id, minutes)
        timer_service.start_timer(callback_query.from_user.id)

        await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=t(lang, 'meditation_started', minutes=minutes),
            reply_markup=TimerUI.get_control_keyboard(session, lang)
        )

        # Сохраняем ID сообщения для редактирования
        timer_messages[callback_query.from_user.id] = callback_query.message.message_id

    async def meditation_custom_callback(self, callback_query: types.CallbackQuery):
        """Запрос ручного ввода времени медитации"""
        await self.bot.answer_callback_query(callback_query.id)

        lang = self._lang(callback_query.from_user.id)

        # Добавляем пользователя в список ожидающих ввода
        self.awaiting_meditation_time.add(callback_query.from_user.id)

        await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=t(lang, 'meditation_custom_title'),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=t(lang, 'btn_back'), callback_data="timer_meditation")]
                ]
            ),
            parse_mode=ParseMode.MARKDOWN
        )

    async def handle_meditation_time_input(self, message: types.Message):
        """Обработка ручного ввода времени медитации"""
        user_id = message.from_user.id
        text = message.text.strip()
        lang = self._lang(user_id)

        # Если это не число, вызываем поиск асан
        if not text.isdigit():
            # Вызываем обработчик текстовых сообщений для поиска асан
            await self.message_handlers.text_message(message)
            return

        # Если это число - обрабатываем как таймер медитации
        minutes = int(text)
        if minutes < 1 or minutes > 120:
            await message.reply(t(lang, 'meditation_invalid'))
            return

        # Проверяем, ожидает ли пользователь ввод
        if user_id not in self.awaiting_meditation_time:
            # Спонтанный запуск медитации из любого места
            # Создаем и запускаем таймер
            session = timer_service.create_meditation_timer(user_id, minutes)
            timer_service.start_timer(user_id)

            # Отправляем стартовое сообщение (оно станет таймером)
            timer_message = await message.answer(
                t(lang, 'meditation_started', minutes=minutes),
                reply_markup=TimerUI.get_control_keyboard(session, lang)
            )

            # Сохраняем ID сообщения для автообновления
            timer_messages[user_id] = timer_message.message_id

            # Отправляем отдельное уведомление и удаляем его через 2 секунды
            notification_message = await message.answer(
                t(lang, 'meditation_started_notif', minutes=minutes),
                parse_mode=ParseMode.MARKDOWN
            )
            asyncio.create_task(self.delete_notification_after_delay(user_id, notification_message.message_id, 2))
            return

        # Если пользователь в режиме ожидания ввода
        # Убираем из списка ожидающих
        self.awaiting_meditation_time.discard(user_id)

        # Создаем и запускаем таймер
        session = timer_service.create_meditation_timer(user_id, minutes)
        timer_service.start_timer(user_id)

        # Отправляем стартовое сообщение (оно станет таймером)
        timer_message = await message.answer(
            t(lang, 'meditation_started', minutes=minutes),
            reply_markup=TimerUI.get_control_keyboard(session, lang)
        )

        # Сохраняем ID сообщения для автообновления
        timer_messages[user_id] = timer_message.message_id

        # Отправляем отдельное уведомление и удаляем его через 2 секунды
        notification_message = await message.answer(
            t(lang, 'meditation_started_notif', minutes=minutes),
            parse_mode=ParseMode.MARKDOWN
        )
        asyncio.create_task(self.delete_notification_after_delay(user_id, notification_message.message_id, 2))

    async def asana_callback(self, callback_query: types.CallbackQuery):
        """Меню конфигурации асан"""
        await self.bot.answer_callback_query(callback_query.id)

        lang = self._lang(callback_query.from_user.id)

        # Получаем или создаем конфигурацию для пользователя
        session = timer_service.get_session(callback_query.from_user.id)
        if session and session.timer_type == TimerType.ASANA:
            config = TimerConfig(
                work_duration=session.work_duration,
                rest_duration=session.rest_duration,
                cycles=session.cycles
            )
        else:
            config = TimerConfig()  # значения по умолчанию

        work_text = format_duration(lang, config.work_duration)
        rest_text = format_duration(lang, config.rest_duration)

        # Показываем имя текущей асаны (если таймер запущен из последовательности)
        context_name = practice_asana_context.get(callback_query.from_user.id)
        title = t(lang, 'asana_timer_title_named', name=context_name) if context_name else t(lang, 'asana_timer_title')

        await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=t(
                lang, 'asana_config_body',
                title=title,
                work=t(lang, 'work_setting', value=work_text),
                rest=t(lang, 'rest_setting', value=rest_text),
                cycles=t(lang, 'cycles_setting', value=config.cycles),
            ),
            reply_markup=TimerUI.get_asana_config_menu(lang),
            parse_mode=ParseMode.MARKDOWN
        )

    async def asana_config_callback(self, callback_query: types.CallbackQuery):
        """Возврат в меню конфигурации асан"""
        await self.bot.answer_callback_query(callback_query.id)
        await self.asana_callback(callback_query)

    async def asana_config_work_callback(self, callback_query: types.CallbackQuery):
        """Открыть меню выбора времени работы"""
        logger.info(f"asana_config_work_callback received: {callback_query.data}")
        await self.bot.answer_callback_query(callback_query.id)

        lang = self._lang(callback_query.from_user.id)

        # Получаем текущее значение
        session = timer_service.get_session(callback_query.from_user.id)
        current_duration = session.work_duration if session and session.timer_type == TimerType.ASANA else 60

        await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=t(lang, 'select_work'),
            reply_markup=TimerUI.get_work_duration_menu(current_duration, lang),
            parse_mode=ParseMode.MARKDOWN
        )

    async def asana_config_rest_callback(self, callback_query: types.CallbackQuery):
        """Открыть меню выбора времени отдыха"""
        logger.info(f"asana_config_rest_callback received: {callback_query.data}")
        await self.bot.answer_callback_query(callback_query.id)

        lang = self._lang(callback_query.from_user.id)

        # Получаем текущее значение
        session = timer_service.get_session(callback_query.from_user.id)
        current_duration = session.rest_duration if session and session.timer_type == TimerType.ASANA else 20

        await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=t(lang, 'select_rest'),
            reply_markup=TimerUI.get_rest_duration_menu(current_duration, lang),
            parse_mode=ParseMode.MARKDOWN
        )

    async def asana_config_cycles_callback(self, callback_query: types.CallbackQuery):
        """Открыть меню выбора количества циклов"""
        logger.info(f"asana_config_cycles_callback received: {callback_query.data}")
        await self.bot.answer_callback_query(callback_query.id)

        lang = self._lang(callback_query.from_user.id)

        # Получаем текущее значение
        session = timer_service.get_session(callback_query.from_user.id)
        current_cycles = session.cycles if session and session.timer_type == TimerType.ASANA else 5

        await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=t(lang, 'select_cycles'),
            reply_markup=TimerUI.get_cycles_menu(current_cycles, lang),
            parse_mode=ParseMode.MARKDOWN
        )

    async def asana_work_callback(self, callback_query: types.CallbackQuery):
        """Выбор времени работы"""
        await self.bot.answer_callback_query(callback_query.id)

        # Парсим callback_data: asana_work_60, asana_work_30, etc.
        parts = callback_query.data.split('_')
        if len(parts) < 3:
            return

        try:
            duration = int(parts[2])
        except ValueError:
            return

        # Обновляем сессию или создаем новую
        session = timer_service.get_session(callback_query.from_user.id)
        if session and session.timer_type == TimerType.ASANA:
            session.work_duration = duration
        else:
            config = TimerConfig(work_duration=duration)
            timer_service.create_asana_timer(callback_query.from_user.id, config)

        await self.asana_callback(callback_query)

    async def asana_rest_callback(self, callback_query: types.CallbackQuery):
        """Выбор времени отдыха"""
        await self.bot.answer_callback_query(callback_query.id)

        # Парсим callback_data: asana_rest_20, asana_rest_30, etc.
        parts = callback_query.data.split('_')
        if len(parts) < 3:
            return

        try:
            duration = int(parts[2])
        except ValueError:
            return

        # Обновляем сессию
        session = timer_service.get_session(callback_query.from_user.id)
        if session and session.timer_type == TimerType.ASANA:
            session.rest_duration = duration
        else:
            config = TimerConfig(rest_duration=duration)
            timer_service.create_asana_timer(callback_query.from_user.id, config)

        await self.asana_callback(callback_query)

    async def asana_cycles_callback(self, callback_query: types.CallbackQuery):
        """Выбор количества циклов"""
        await self.bot.answer_callback_query(callback_query.id)

        # Парсим callback_data: asana_cycles_5, asana_cycles_10, etc.
        parts = callback_query.data.split('_')
        if len(parts) < 3:
            return

        try:
            cycles = int(parts[2])
        except ValueError:
            return

        # Обновляем сессию
        session = timer_service.get_session(callback_query.from_user.id)
        if session and session.timer_type == TimerType.ASANA:
            session.cycles = cycles
        else:
            config = TimerConfig(cycles=cycles)
            timer_service.create_asana_timer(callback_query.from_user.id, config)

        await self.asana_callback(callback_query)

    async def asana_start_callback(self, callback_query: types.CallbackQuery):
        """Запуск таймера асан"""
        await self.bot.answer_callback_query(callback_query.id)

        lang = self._lang(callback_query.from_user.id)

        user_id = callback_query.from_user.id
        context_name = practice_asana_context.pop(user_id, None)

        session = timer_service.get_session(user_id)
        if not session or session.timer_type != TimerType.ASANA:
            config = TimerConfig(asana_name=context_name)
            session = timer_service.create_asana_timer(user_id, config)
        else:
            # Таймер запускается из последовательности — всегда обновляем имя текущей асаны
            if context_name:
                session.asana_name = context_name
            session = timer_service.start_timer(user_id)

        work_text = format_duration(lang, session.work_duration)
        rest_text = format_duration(lang, session.rest_duration)
        start_title = t(lang, 'asana_started_title', name=session.asana_name) if session.asana_name else t(lang, 'asana_started_generic')

        message = await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=t(
                lang, 'asana_started_body',
                title=start_title,
                work=t(lang, 'work_setting', value=work_text),
                rest=t(lang, 'rest_setting', value=rest_text),
                cycles=t(lang, 'cycles_setting', value=session.cycles),
            ),
            reply_markup=TimerUI.get_control_keyboard(session, lang),
            parse_mode=ParseMode.MARKDOWN
        )

        # Сохраняем ID сообщения для редактирования
        timer_messages[callback_query.from_user.id] = callback_query.message.message_id

    # Пранаяма (аналогично асанам)
    async def pranayama_callback(self, callback_query: types.CallbackQuery):
        """Меню пранаямы"""
        await self.bot.answer_callback_query(callback_query.id)

        lang = self._lang(callback_query.from_user.id)

        # Получаем или создаем конфигурацию для пользователя
        session = timer_service.get_session(callback_query.from_user.id)
        if session and session.timer_type == TimerType.PRANAYAMA:
            exercises = session.exercises
            exercise_time = session.exercise_duration
            rest_time = session.rest_duration
        else:
            exercises = 3
            exercise_time = 30
            rest_time = 20

        exercise_text = format_duration(lang, exercise_time)
        rest_text = format_duration(lang, rest_time)

        await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=t(
                lang, 'pranayama_config_body',
                title=t(lang, 'pranayama_title'),
                exercises=exercises,
                exercise_time=exercise_text,
                rest_time=rest_text,
            ),
            reply_markup=TimerUI.get_pranayama_menu(lang),
            parse_mode=ParseMode.MARKDOWN
        )

    async def pranayama_config_callback(self, callback_query: types.CallbackQuery):
        """Возврат в меню конфигурации пранаямы"""
        await self.bot.answer_callback_query(callback_query.id)
        await self.pranayama_callback(callback_query)

    async def pranayama_exercises_callback(self, callback_query: types.CallbackQuery):
        """Открыть меню выбора количества упражнений"""
        await self.bot.answer_callback_query(callback_query.id)

        lang = self._lang(callback_query.from_user.id)

        # Получаем текущее значение
        session = timer_service.get_session(callback_query.from_user.id)
        current_exercises = session.exercises if session and session.timer_type == TimerType.PRANAYAMA else 3

        await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=t(lang, 'select_exercises'),
            reply_markup=TimerUI.get_pranayama_exercises_menu(current_exercises, lang),
            parse_mode=ParseMode.MARKDOWN
        )

    async def pranayama_exercise_time_callback(self, callback_query: types.CallbackQuery):
        """Открыть меню выбора времени упражнения"""
        await self.bot.answer_callback_query(callback_query.id)

        lang = self._lang(callback_query.from_user.id)

        # Получаем текущее значение
        session = timer_service.get_session(callback_query.from_user.id)
        current_time = session.exercise_duration if session and session.timer_type == TimerType.PRANAYAMA else 30

        await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=t(lang, 'select_exercise_time'),
            reply_markup=TimerUI.get_pranayama_exercise_time_menu(current_time, lang),
            parse_mode=ParseMode.MARKDOWN
        )

    async def pranayama_rest_time_callback(self, callback_query: types.CallbackQuery):
        """Открыть меню выбора времени отдыха"""
        await self.bot.answer_callback_query(callback_query.id)

        lang = self._lang(callback_query.from_user.id)

        # Получаем текущее значение
        session = timer_service.get_session(callback_query.from_user.id)
        current_time = session.rest_duration if session and session.timer_type == TimerType.PRANAYAMA else 20

        await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=t(lang, 'select_rest_time'),
            reply_markup=TimerUI.get_pranayama_rest_time_menu(current_time, lang),
            parse_mode=ParseMode.MARKDOWN
        )

    async def pranayama_exercises_select_callback(self, callback_query: types.CallbackQuery):
        """Выбор количества упражнений"""
        await self.bot.answer_callback_query(callback_query.id)

        # Парсим callback_data: pranayama_exercises_3, pranayama_exercises_5, etc.
        parts = callback_query.data.split('_')
        if len(parts) < 3:
            return

        try:
            exercises = int(parts[2])
        except ValueError:
            return

        # Обновляем сессию или создаем новую
        session = timer_service.get_session(callback_query.from_user.id)
        if session and session.timer_type == TimerType.PRANAYAMA:
            session.exercises = exercises
            session.cycles = exercises  # Для пранаямы cycles = exercises
        else:
            config = PranayamaConfig(exercises=exercises)
            session = timer_service.create_pranayama_timer(callback_query.from_user.id, config)

        await self.pranayama_callback(callback_query)

    async def pranayama_exercise_time_select_callback(self, callback_query: types.CallbackQuery):
        """Выбор времени упражнения"""
        logger.info(f"pranayama_exercise_time_select_callback received: {callback_query.data}")
        await self.bot.answer_callback_query(callback_query.id)

        # Парсим callback_data: pranayama_exercise_time_30, pranayama_exercise_time_45, etc.
        parts = callback_query.data.split('_')
        if len(parts) < 4:
            logger.error(f"Invalid callback_data format: {callback_query.data}")
            return

        try:
            duration = int(parts[3])  # Исправляем индекс - время в parts[3]
        except ValueError:
            logger.error(f"Cannot parse duration from: {callback_query.data}")
            return

        logger.info(f"Parsed exercise duration: {duration} seconds")

        # Обновляем сессию
        session = timer_service.get_session(callback_query.from_user.id)
        if session and session.timer_type == TimerType.PRANAYAMA:
            session.exercise_duration = duration
            session.work_duration = duration  # Для пранаямы work_duration = exercise_duration
            logger.info(f"Updated pranayama session: exercise_duration={duration}")
        else:
            config = PranayamaConfig(exercise_duration=duration)
            session = timer_service.create_pranayama_timer(callback_query.from_user.id, config)
            logger.info(f"Created new pranayama session with exercise_duration={duration}")

        await self.pranayama_callback(callback_query)

    async def pranayama_rest_time_select_callback(self, callback_query: types.CallbackQuery):
        """Выбор времени отдыха"""
        logger.info(f"pranayama_rest_time_select_callback received: {callback_query.data}")
        await self.bot.answer_callback_query(callback_query.id)

        # Парсим callback_data: pranayama_rest_time_20, pranayama_rest_time_30, etc.
        parts = callback_query.data.split('_')
        if len(parts) < 4:
            logger.error(f"Invalid callback_data format: {callback_query.data}")
            return

        try:
            duration = int(parts[3])  # Исправляем индекс - время в parts[3]
        except ValueError:
            logger.error(f"Cannot parse duration from: {callback_query.data}")
            return

        logger.info(f"Parsed rest duration: {duration} seconds")

        # Обновляем сессию
        session = timer_service.get_session(callback_query.from_user.id)
        if session and session.timer_type == TimerType.PRANAYAMA:
            session.rest_duration = duration
            logger.info(f"Updated pranayama session: rest_duration={duration}")
        else:
            config = PranayamaConfig(rest_duration=duration)
            session = timer_service.create_pranayama_timer(callback_query.from_user.id, config)
            logger.info(f"Created new pranayama session with rest_duration={duration}")

        await self.pranayama_callback(callback_query)

    async def pranayama_start_callback(self, callback_query: types.CallbackQuery):
        """Запуск таймера пранаямы"""
        await self.bot.answer_callback_query(callback_query.id)

        lang = self._lang(callback_query.from_user.id)

        session = timer_service.get_session(callback_query.from_user.id)
        if not session or session.timer_type != TimerType.PRANAYAMA:
            config = PranayamaConfig()
            session = timer_service.create_pranayama_timer(callback_query.from_user.id, config)
        else:
            timer_service.start_timer(callback_query.from_user.id)

        exercise_text = format_duration(lang, session.exercise_duration)
        rest_text = format_duration(lang, session.rest_duration)

        await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=t(
                lang, 'pranayama_started_body',
                exercises=session.exercises,
                exercise_time=exercise_text,
                rest_time=rest_text,
            ),
            reply_markup=TimerUI.get_control_keyboard(session, lang),
            parse_mode=ParseMode.MARKDOWN
        )

        # Сохраняем ID сообщения для редактирования
        timer_messages[callback_query.from_user.id] = callback_query.message.message_id

    # Управление таймером
    async def timer_control_callback(self, callback_query: types.CallbackQuery):
        """Общий обработчик управления таймером"""
        await self.bot.answer_callback_query(callback_query.id)

        lang = self._lang(callback_query.from_user.id)

        action = callback_query.data.split('_')[1]  # pause, stop, start, reset, delete
        user_id = callback_query.from_user.id

        if action == "start":
            session = timer_service.start_timer(user_id)
            if session:
                await self.update_timer_message(user_id, session)

        elif action == "pause":
            session = timer_service.pause_timer(user_id)
            if session:
                await self.update_timer_message(user_id, session)

        elif action == "stop":
            session = timer_service.stop_timer(user_id)
            if session:
                practice_asana_context.pop(user_id, None)
                # Удаляем сообщение таймера
                if user_id in timer_messages:
                    try:
                        await self.bot.delete_message(
                            chat_id=user_id,
                            message_id=timer_messages[user_id]
                        )
                    except:
                        pass
                    del timer_messages[user_id]

                await self.bot.send_message(
                    user_id,
                    t(lang, 'timer_stopped'),
                    reply_markup=TimerUI.get_main_menu(lang),
                    parse_mode=ParseMode.MARKDOWN
                )

        elif action == "reset":
            session = timer_service.reset_timer(user_id)
            if session:
                await self.update_timer_message(user_id, session)

        elif action == "delete":
            session = timer_service.get_session(user_id)
            if session:
                practice_asana_context.pop(user_id, None)
                await self.bot.edit_message_text(
                    chat_id=callback_query.from_user.id,
                    message_id=callback_query.message.message_id,
                    text=t(lang, 'timer_deleted'),
                    reply_markup=self.keyboard_service.create_main_menu(lang)
                )
            timer_service.delete_session(user_id)

    async def timer_back_callback(self, callback_query: types.CallbackQuery):
        """Возврат в главное меню таймера"""
        await self.bot.answer_callback_query(callback_query.id)

        lang = self._lang(callback_query.from_user.id)

        await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=t(lang, 'timer_back_text'),
            reply_markup=TimerUI.get_main_menu(lang),
            parse_mode=ParseMode.MARKDOWN
        )

    async def timer_exit_callback(self, callback_query: types.CallbackQuery):
        """Выход из таймера в главное меню бота"""
        await self.bot.answer_callback_query(callback_query.id)

        lang = self._lang(callback_query.from_user.id)

        # Удаляем ID сообщения из хранилища таймеров
        if callback_query.from_user.id in timer_messages:
            del timer_messages[callback_query.from_user.id]

        await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=t(lang, 'timer_exit_text'),
            reply_markup=self.keyboard_service.create_main_menu(lang),
            parse_mode=ParseMode.MARKDOWN
        )

    async def update_timer_message(self, user_id: int, session):
        """Обновляет сообщение таймера"""
        if user_id not in timer_messages:
            return

        lang = self._lang(user_id)

        try:
            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=timer_messages[user_id],
                text=TimerUI.format_timer_message(session, lang),
                reply_markup=TimerUI.get_control_keyboard(session, lang),
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Error updating timer message: {e}")

    async def delete_notification_after_delay(self, user_id: int, message_id: int, delay_seconds: int):
        """Удаляет уведомление через указанное время"""
        await asyncio.sleep(delay_seconds)
        try:
            await self.bot.delete_message(
                chat_id=user_id,
                message_id=message_id
            )
            logger.info(f"Deleted notification message {message_id} for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to delete notification message {message_id}: {e}")

    # Фоновая задача обновления таймеров
    async def start_timer_update_loop(self):
        """Запустить фоновый цикл обновления таймеров"""
        while True:
            try:
                # Обновляем все активные сессии
                for user_id, session in list(timer_service.active_sessions.items()):
                    if session.status == TimerStatus.RUNNING:
                        lang = self._lang(user_id)
                        old_phase = session.current_phase
                        old_cycle = session.current_cycle

                        updated_session = timer_service.update_timer(user_id)

                        if updated_session:
                            # Обновляем основное сообщение каждые 5 секунд
                            if updated_session.elapsed % 5 == 0:
                                await self.update_timer_message(user_id, updated_session)

                            # Проверяем завершение
                            if updated_session.status == TimerStatus.COMPLETED:
                                practice_asana_context.pop(user_id, None)
                                timer_message_id = timer_messages.get(user_id)
                                timer_service.delete_session(user_id)

                                # Записываем завершённую практику в общую статистику Dharana
                                # (контракт как у timersana: POST /api/v1/practice/timer).
                                # Сбой записи не должен ломать завершение практики.
                                try:
                                    if updated_session.timer_type == TimerType.MEDITATION:
                                        practice_seconds = max(
                                            updated_session.total_elapsed,
                                            updated_session.elapsed,
                                        )
                                    else:
                                        # Для асан/пранаямы elapsed сбрасывается на каждой
                                        # фазе, а total_elapsed растёт только при паузе — итог
                                        # равен суммарному времени работы: циклы × work.
                                        practice_seconds = updated_session.cycles * updated_session.work_duration
                                    await self.user_service.record_practice(
                                        telegram_id=user_id,
                                        practice_type=updated_session.timer_type.value,
                                        total_duration_seconds=practice_seconds,
                                        cycles=updated_session.cycles,
                                        started_at=updated_session.start_time,
                                        completed_at=datetime.now(),
                                    )
                                except Exception as e:
                                    logger.error(f"Ошибка записи практики для {user_id}: {e}")

                                # Автопереход к следующей асане последовательности
                                advance_cb = sequence_advance_callbacks.get(user_id)
                                if advance_cb:
                                    try:
                                        await advance_cb(user_id, timer_message_id)
                                        continue
                                    except Exception as e:
                                        logger.error(f"Error advancing sequence for user {user_id}: {e}")

                                # Звуковое уведомление о завершении практики
                                try:
                                    complete_notification = await self.bot.send_message(
                                        user_id,
                                        t(lang, 'practice_completed_notif'),
                                        parse_mode=ParseMode.MARKDOWN
                                    )
                                    asyncio.create_task(
                                        self.delete_notification_after_delay(user_id, complete_notification.message_id, 2)
                                    )
                                except Exception as e:
                                    logger.error(f"Error sending completion notification: {e}")

                                if user_id in timer_messages:
                                    try:
                                        await self.bot.edit_message_text(
                                            chat_id=user_id,
                                            message_id=timer_messages[user_id],
                                            text=TimerUI.format_timer_message(updated_session, lang),
                                            reply_markup=TimerUI.get_main_menu(lang),
                                            parse_mode=ParseMode.MARKDOWN
                                        )
                                    except:
                                        pass
                                    del timer_messages[user_id]

                            # Проверяем смену фазы (для асан) - отправляем временное уведомление
                            elif (updated_session.timer_type in [TimerType.ASANA, TimerType.PRANAYAMA] and
                                  old_phase != updated_session.current_phase and
                                  updated_session.rest_duration > 0):
                                notification_message = await self.bot.send_message(
                                    user_id,
                                    TimerUI.get_phase_notification(updated_session, lang),
                                    reply_markup=TimerUI.get_control_keyboard(updated_session, lang),
                                    parse_mode=ParseMode.MARKDOWN
                                )
                                # Удаляем уведомление через 2 секунды
                                asyncio.create_task(self.delete_notification_after_delay(user_id, notification_message.message_id, 2))

                await asyncio.sleep(1)  # Обновляем каждую секунду

            except Exception as e:
                logger.error(f"Error in timer update loop: {e}")
                await asyncio.sleep(5)  # Пауза при ошибке