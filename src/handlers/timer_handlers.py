import logging
import asyncio
import re
from aiogram import types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.services.timer_service import timer_service
from src.utils.timer_ui import TimerUI
from src.models.timer_models import TimerType, TimerStatus, TimerPhase, TimerConfig, PranayamaConfig, timer_messages

logger = logging.getLogger(__name__)


class TimerHandlers:
    """Обработчики для таймера медитации, асан и пранаямы"""
    
    def __init__(self, bot, data_service, keyboard_service):
        self.bot = bot
        self.data_service = data_service
        self.keyboard_service = keyboard_service
        self.awaiting_meditation_time = set()  # пользователи, ожидающие ввода времени медитации
        # Импортируем message_handlers для доступа к поиску асан
        from src.handlers.message_handlers import MessageHandlers
        self.message_handlers = MessageHandlers(bot)
    
    # Главное меню таймера
    async def timer_main_callback(self, callback_query: types.CallbackQuery):
        """Главное меню таймера"""
        await self.bot.answer_callback_query(callback_query.id)
        
        # Сохраняем ID сообщения для меню таймера
        timer_messages[callback_query.from_user.id] = callback_query.message.message_id
        
        await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text="🕐 **Таймер для практики**\n\n"
            "Выбери тип практики:\n"
            "🧘 Медитация - простая практика осознанности\n"
            "🧘‍♂️ Асана - практика поз с чередованием работы/отдыха\n"
            "🌬️ Пранаяма - дыхательные упражнения",
            reply_markup=TimerUI.get_main_menu()
        )
    
    # Медитация
    async def meditation_callback(self, callback_query: types.CallbackQuery):
        """Меню медитации"""
        await self.bot.answer_callback_query(callback_query.id)
        
        await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text="🧘 **Медитация**\n\n"
            "Выбери длительность практики:",
            reply_markup=TimerUI.get_meditation_menu()
        )
    
    async def meditation_start_callback(self, callback_query: types.CallbackQuery):
        """Запуск медитации"""
        await self.bot.answer_callback_query(callback_query.id)
        
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
            text=f"🧘 Медитация на {minutes} минут начата!\n\n"
            "Сконцентрируйся на дыхании и будь настоящим моменте. 🙏\n\n"
            "Используй кнопки управления ниже:",
            reply_markup=TimerUI.get_control_keyboard(session)
        )
        
        # Сохраняем ID сообщения для редактирования
        timer_messages[callback_query.from_user.id] = callback_query.message.message_id
    
    async def meditation_custom_callback(self, callback_query: types.CallbackQuery):
        """Запрос ручного ввода времени медитации"""
        await self.bot.answer_callback_query(callback_query.id)
        
        # Добавляем пользователя в список ожидающих ввода
        self.awaiting_meditation_time.add(callback_query.from_user.id)
        
        await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text="⌨️ **Ввод времени медитации**\n\n"
            "Напиши количество минут (от 1 до 120):\n"
            "Например: 7 или 15 или 45\n\n"
            "Используй обычное сообщение, а не кнопку.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="timer_meditation")]
                ]
            )
        )
    
    async def handle_meditation_time_input(self, message: types.Message):
        """Обработка ручного ввода времени медитации"""
        user_id = message.from_user.id
        text = message.text.strip()
        
        # Если это не число, вызываем поиск асан
        if not text.isdigit():
            # Вызываем обработчик текстовых сообщений для поиска асан
            await self.message_handlers.text_message(message)
            return
        
        # Если это число - обрабатываем как таймер медитации
        minutes = int(text)
        if minutes < 1 or minutes > 120:
            await message.reply("⚠️ Время должно быть от 1 до 120 минут. Попробуй еще раз.")
            return
        
        # Проверяем, ожидает ли пользователь ввод
        if user_id not in self.awaiting_meditation_time:
            # Спонтанный запуск медитации из любого места
            # Создаем и запускаем таймер
            session = timer_service.create_meditation_timer(user_id, minutes)
            timer_service.start_timer(user_id)
            
            # Отправляем стартовое сообщение (оно станет таймером)
            timer_message = await message.answer(
                f"🧘 Медитация на {minutes} минут начата!\n\n"
                "Сконцентрируйся на дыхании и будь настоящем моменте. 🙏\n\n"
                "Используй кнопки управления ниже:",
                reply_markup=TimerUI.get_control_keyboard(session)
            )
            
            # Сохраняем ID сообщения для автообновления
            timer_messages[user_id] = timer_message.message_id
            
            # Отправляем отдельное уведомление и удаляем его через 5 секунд
            notification_message = await message.answer(
                f"🔔 **Медитация началась!**\n\n"
                f"Длительность: {minutes} минут\n"
                "Сосредоточься на дыхании... 🧘"
            )
            asyncio.create_task(self.delete_notification_after_delay(user_id, notification_message.message_id, 5))
            return
        
        # Если пользователь в режиме ожидания ввода
        # Убираем из списка ожидающих
        self.awaiting_meditation_time.discard(user_id)
        
        # Создаем и запускаем таймер
        session = timer_service.create_meditation_timer(user_id, minutes)
        timer_service.start_timer(user_id)
        
        # Отправляем стартовое сообщение (оно станет таймером)
        timer_message = await message.answer(
            f"🧘 Медитация на {minutes} минут начата!\n\n"
            "Сконцентрируйся на дыхании и будь настоящем моменте. 🙏\n\n"
            "Используй кнопки управления ниже:",
            reply_markup=TimerUI.get_control_keyboard(session)
        )
        
        # Сохраняем ID сообщения для автообновления
        timer_messages[user_id] = timer_message.message_id
        
        # Отправляем отдельное уведомление и удаляем его через 5 секунд
        notification_message = await message.answer(
            f"🔔 **Медитация началась!**\n\n"
            f"Длительность: {minutes} минут\n"
            "Сосредоточься на дыхании... 🧘"
        )
        asyncio.create_task(self.delete_notification_after_delay(user_id, notification_message.message_id, 5))
    async def asana_callback(self, callback_query: types.CallbackQuery):
        """Меню конфигурации асан"""
        await self.bot.answer_callback_query(callback_query.id)
        
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
        
        work_text = f"{config.work_duration}с" if config.work_duration < 60 else f"{config.work_duration//60}м"
        rest_text = f"{config.rest_duration}с" if config.rest_duration < 60 else f"{config.rest_duration//60}м"
        
        await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=f"🧘‍♂️ **Таймер асан**\n\n"
            f"⏱️ Работа: {work_text}\n"
            f"⏸️ Отдых: {rest_text}\n"
            f"🔄 Циклы: {config.cycles}\n\n"
            "Настрой параметры или начни практику:",
            reply_markup=TimerUI.get_asana_config_menu()
        )
    
    async def asana_config_callback(self, callback_query: types.CallbackQuery):
        """Возврат в меню конфигурации асан"""
        await self.bot.answer_callback_query(callback_query.id)
        await self.asana_callback(callback_query)
    
    async def asana_config_work_callback(self, callback_query: types.CallbackQuery):
        """Открыть меню выбора времени работы"""
        logger.info(f"asana_config_work_callback received: {callback_query.data}")
        await self.bot.answer_callback_query(callback_query.id)
        
        # Получаем текущее значение
        session = timer_service.get_session(callback_query.from_user.id)
        current_duration = session.work_duration if session and session.timer_type == TimerType.ASANA else 60
        
        await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text="⏱️ **Выбери время работы:**",
            reply_markup=TimerUI.get_work_duration_menu(current_duration)
        )
    
    async def asana_config_rest_callback(self, callback_query: types.CallbackQuery):
        """Открыть меню выбора времени отдыха"""
        logger.info(f"asana_config_rest_callback received: {callback_query.data}")
        await self.bot.answer_callback_query(callback_query.id)
        
        # Получаем текущее значение
        session = timer_service.get_session(callback_query.from_user.id)
        current_duration = session.rest_duration if session and session.timer_type == TimerType.ASANA else 20
        
        await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text="⏸️ **Выбери время отдыха:**",
            reply_markup=TimerUI.get_rest_duration_menu(current_duration)
        )
    
    async def asana_config_cycles_callback(self, callback_query: types.CallbackQuery):
        """Открыть меню выбора количества циклов"""
        logger.info(f"asana_config_cycles_callback received: {callback_query.data}")
        await self.bot.answer_callback_query(callback_query.id)
        
        # Получаем текущее значение
        session = timer_service.get_session(callback_query.from_user.id)
        current_cycles = session.cycles if session and session.timer_type == TimerType.ASANA else 5
        
        await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text="🔄 **Выбери количество циклов:**",
            reply_markup=TimerUI.get_cycles_menu(current_cycles)
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
        
        session = timer_service.get_session(callback_query.from_user.id)
        if not session or session.timer_type != TimerType.ASANA:
            config = TimerConfig()
            session = timer_service.create_asana_timer(callback_query.from_user.id, config)
        else:
            timer_service.start_timer(callback_query.from_user.id)
        
        work_text = f"{session.work_duration}с" if session.work_duration < 60 else f"{session.work_duration//60}м"
        rest_text = f"{session.rest_duration}с" if session.rest_duration < 60 else f"{session.rest_duration//60}м"
        
        message = await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=f"🧘‍♂️ **Практика асан начата!**\n\n"
            f"⏱️ Работа: {work_text}\n"
            f"⏸️ Отдых: {rest_text}\n"
            f"🔄 Циклы: {session.cycles}\n\n"
            "Начинаем с первого подхода! 💪",
            reply_markup=TimerUI.get_control_keyboard(session)
        )
        
        # Сохраняем ID сообщения для редактирования
        timer_messages[callback_query.from_user.id] = callback_query.message.message_id
    
    # Пранаяма (аналогично асанам)
    async def pranayama_callback(self, callback_query: types.CallbackQuery):
        """Меню пранаямы"""
        await self.bot.answer_callback_query(callback_query.id)
        
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
        
        exercise_text = f"{exercise_time}с" if exercise_time < 60 else f"{exercise_time//60}м"
        rest_text = f"{rest_time}с" if rest_time < 60 else f"{rest_time//60}м"
        
        await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=f"🌬️ **Пранаяма**\n\n"
            f"📊 Упражнений: {exercises}\n"
            f"⏱️ Время упражнения: {exercise_text}\n"
            f"⏸️ Время отдыха: {rest_text}\n\n"
            "Настрой параметры или начни практику:",
            reply_markup=TimerUI.get_pranayama_menu()
        )
    
    async def pranayama_config_callback(self, callback_query: types.CallbackQuery):
        """Возврат в меню конфигурации пранаямы"""
        await self.bot.answer_callback_query(callback_query.id)
        await self.pranayama_callback(callback_query)
    
    async def pranayama_exercises_callback(self, callback_query: types.CallbackQuery):
        """Открыть меню выбора количества упражнений"""
        await self.bot.answer_callback_query(callback_query.id)
        
        # Получаем текущее значение
        session = timer_service.get_session(callback_query.from_user.id)
        current_exercises = session.exercises if session and session.timer_type == TimerType.PRANAYAMA else 3
        
        await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text="📊 **Выбери количество упражнений:**",
            reply_markup=TimerUI.get_pranayama_exercises_menu(current_exercises)
        )
    
    async def pranayama_exercise_time_callback(self, callback_query: types.CallbackQuery):
        """Открыть меню выбора времени упражнения"""
        await self.bot.answer_callback_query(callback_query.id)
        
        # Получаем текущее значение
        session = timer_service.get_session(callback_query.from_user.id)
        current_time = session.exercise_duration if session and session.timer_type == TimerType.PRANAYAMA else 30
        
        await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text="⏱️ **Выбери время упражнения:**",
            reply_markup=TimerUI.get_pranayama_exercise_time_menu(current_time)
        )
    
    async def pranayama_rest_time_callback(self, callback_query: types.CallbackQuery):
        """Открыть меню выбора времени отдыха"""
        await self.bot.answer_callback_query(callback_query.id)
        
        # Получаем текущее значение
        session = timer_service.get_session(callback_query.from_user.id)
        current_time = session.rest_duration if session and session.timer_type == TimerType.PRANAYAMA else 20
        
        await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text="⏸️ **Выбери время отдыха:**",
            reply_markup=TimerUI.get_pranayama_rest_time_menu(current_time)
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
        
        session = timer_service.get_session(callback_query.from_user.id)
        if not session or session.timer_type != TimerType.PRANAYAMA:
            config = PranayamaConfig()
            session = timer_service.create_pranayama_timer(callback_query.from_user.id, config)
        else:
            timer_service.start_timer(callback_query.from_user.id)
        
        exercise_text = f"{session.exercise_duration}с" if session.exercise_duration < 60 else f"{session.exercise_duration//60}м"
        rest_text = f"{session.rest_duration}с" if session.rest_duration < 60 else f"{session.rest_duration//60}м"
        
        await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=f"🌬️ **Практика пранаямы начата!**\n\n"
            f"📊 Упражнений: {session.exercises}\n"
            f"⏱️ Время упражнения: {exercise_text}\n"
            f"⏸️ Время отдыха: {rest_text}\n\n"
            "Начинаем с первого упражнения! 🧘‍♂️",
            reply_markup=TimerUI.get_control_keyboard(session)
        )
        
        # Сохраняем ID сообщения для редактирования
        timer_messages[callback_query.from_user.id] = callback_query.message.message_id
    
    # Управление таймером
    async def timer_control_callback(self, callback_query: types.CallbackQuery):
        """Общий обработчик управления таймером"""
        await self.bot.answer_callback_query(callback_query.id)
        
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
                    "⏹️ **Таймер остановлен**\n\n"
                    "Практика завершена. Хорошая работа! 🙏\n\n"
                    "Хочешь начать новую практику?",
                    reply_markup=TimerUI.get_main_menu()
                )
        
        elif action == "reset":
            session = timer_service.reset_timer(user_id)
            if session:
                await self.update_timer_message(user_id, session)
        
        elif action == "delete":
            session = timer_service.get_session(user_id)
            if session:
                await self.bot.edit_message_text(
                    chat_id=callback_query.from_user.id,
                    message_id=callback_query.message.message_id,
                    text="🗑️ Таймер удален\n\n"
                    "Хочешь начать новую практику?",
                    reply_markup=self.keyboard_service.create_main_menu()
                )
            timer_service.delete_session(user_id)
    
    async def timer_back_callback(self, callback_query: types.CallbackQuery):
        """Возврат в главное меню таймера"""
        await self.bot.answer_callback_query(callback_query.id)
        
        await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text="🔙 **Возвращаю в главное меню таймера...**",
            reply_markup=TimerUI.get_main_menu()
        )
    
    async def timer_exit_callback(self, callback_query: types.CallbackQuery):
        """Выход из таймера в главное меню бота"""
        await self.bot.answer_callback_query(callback_query.id)
        
        # Удаляем ID сообщения из хранилища таймеров
        if callback_query.from_user.id in timer_messages:
            del timer_messages[callback_query.from_user.id]
        
        await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text="🔙 **Выход из таймера...**",
            reply_markup=self.keyboard_service.create_main_menu()
        )
    
    async def update_timer_message(self, user_id: int, session):
        """Обновляет сообщение таймера"""
        if user_id not in timer_messages:
            return
        
        try:
            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=timer_messages[user_id],
                text=TimerUI.format_timer_message(session),
                reply_markup=TimerUI.get_control_keyboard(session)
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
                        old_phase = session.current_phase
                        old_cycle = session.current_cycle
                        
                        updated_session = timer_service.update_timer(user_id)
                        
                        if updated_session:
                            # Обновляем основное сообщение каждые 5 секунд
                            if updated_session.elapsed % 5 == 0:
                                await self.update_timer_message(user_id, updated_session)
                            
                            # Проверяем завершение
                            if updated_session.status == TimerStatus.COMPLETED:
                                if user_id in timer_messages:
                                    try:
                                        await self.bot.edit_message_text(
                                            chat_id=user_id,
                                            message_id=timer_messages[user_id],
                                            text=TimerUI.format_timer_message(updated_session),
                                            reply_markup=TimerUI.get_main_menu()
                                        )
                                    except:
                                        pass
                                    del timer_messages[user_id]
                                
                                timer_service.delete_session(user_id)
                            
                            # Проверяем смену фазы (для асан) - отправляем временное уведомление
                            elif (updated_session.timer_type in [TimerType.ASANA, TimerType.PRANAYAMA] and
                                  old_phase != updated_session.current_phase):
                                notification_message = await self.bot.send_message(
                                    user_id,
                                    TimerUI.get_phase_notification(updated_session),
                                    reply_markup=TimerUI.get_control_keyboard(updated_session)
                                )
                                # Удаляем уведомление через 5 секунд
                                asyncio.create_task(self.delete_notification_after_delay(user_id, notification_message.message_id, 5))
                
                await asyncio.sleep(1)  # Обновляем каждую секунду
                
            except Exception as e:
                logger.error(f"Error in timer update loop: {e}")
                await asyncio.sleep(5)  # Пауза при ошибке
