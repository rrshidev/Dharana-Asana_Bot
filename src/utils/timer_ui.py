from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.models.timer_models import TimerSession, TimerType, TimerStatus, TimerPhase


class TimerUI:
    """UI компоненты для таймера"""
    
    @staticmethod
    def get_main_menu() -> InlineKeyboardMarkup:
        """Главное меню таймера"""
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🧘 Медитация", callback_data="timer_meditation"),
                    InlineKeyboardButton(text="🧘‍♂️ Асана", callback_data="timer_asana")
                ],
                [
                    InlineKeyboardButton(text="🌬️ Пранаяма", callback_data="timer_pranayama"),
                    InlineKeyboardButton(text="🔙 Выйти из таймера", callback_data="timer_exit")
                ]
            ]
        )
        return keyboard
    
    @staticmethod
    def get_meditation_menu() -> InlineKeyboardMarkup:
        """Меню выбора времени медитации"""
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="1 минута", callback_data="meditation_1")],
                [InlineKeyboardButton(text="5 минут", callback_data="meditation_5")],
                [InlineKeyboardButton(text="10 минут", callback_data="meditation_10")],
                [InlineKeyboardButton(text="15 минут", callback_data="meditation_15")],
                [InlineKeyboardButton(text="20 минут", callback_data="meditation_20")],
                [InlineKeyboardButton(text="30 минут", callback_data="meditation_30")],
                [InlineKeyboardButton(text="45 минут", callback_data="meditation_45")],
                [InlineKeyboardButton(text="60 минут", callback_data="meditation_60")],
                [InlineKeyboardButton(text="⌨️ Ввести время вручную", callback_data="meditation_custom")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="timer_main")]
            ]
        )
        return keyboard
    
    @staticmethod
    def get_asana_config_menu() -> InlineKeyboardMarkup:
        """Меню конфигурации таймера асан"""
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="⏱️ Время работы", callback_data="asana_config_work"),
                    InlineKeyboardButton(text="⏸️ Время отдыха", callback_data="asana_config_rest")
                ],
                [
                    InlineKeyboardButton(text="🔄 Количество циклов", callback_data="asana_config_cycles"),
                    InlineKeyboardButton(text="▶️ Начать", callback_data="asana_start")
                ],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="timer_main")]
            ]
        )
        return keyboard
    
    @staticmethod
    def get_work_duration_menu(current_duration: int = 60) -> InlineKeyboardMarkup:
        """Меню выбора времени работы"""
        durations = [30, 45, 60, 90, 120, 180]  # 30с, 45с, 1м, 1.5м, 2м, 3м
        
        keyboard = []
        for duration in durations:
            text = f"{duration}с" if duration < 60 else f"{duration//60}м"
            if duration == current_duration:
                text = f"✅ {text}"
            keyboard.append([InlineKeyboardButton(text=text, callback_data=f"asana_work_{duration}")])
        
        keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="asana_config")])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    @staticmethod
    def get_rest_duration_menu(current_duration: int = 20) -> InlineKeyboardMarkup:
        """Меню выбора времени отдыха"""
        durations = [10, 15, 20, 30, 45, 60]  # 10с, 15с, 20с, 30с, 45с, 1м
        
        keyboard = []
        for duration in durations:
            text = f"{duration}с" if duration < 60 else f"{duration//60}м"
            if duration == current_duration:
                text = f"✅ {text}"
            keyboard.append([InlineKeyboardButton(text=text, callback_data=f"asana_rest_{duration}")])
        
        keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="asana_config")])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    @staticmethod
    def get_cycles_menu(current_cycles: int = 5) -> InlineKeyboardMarkup:
        """Меню выбора количества циклов"""
        cycles = [3, 5, 7, 10, 15, 20]
        
        keyboard = []
        for cycle in cycles:
            text = f"{cycle} циклов"
            if cycle == current_cycles:
                text = f"✅ {text}"
            keyboard.append([InlineKeyboardButton(text=text, callback_data=f"asana_cycles_{cycle}")])
        
        keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="asana_config")])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    @staticmethod
    def get_pranayama_menu() -> InlineKeyboardMarkup:
        """Меню конфигурации пранаямы"""
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="📊 Количество упражнений", callback_data="pranayama_exercises"),
                    InlineKeyboardButton(text="⏱️ Время упражнения", callback_data="pranayama_exercise_time")
                ],
                [
                    InlineKeyboardButton(text="⏸️ Время отдыха", callback_data="pranayama_rest_time"),
                    InlineKeyboardButton(text="▶️ Начать", callback_data="pranayama_start")
                ],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="timer_main")]
            ]
        )
        return keyboard
    
    @staticmethod
    def get_pranayama_exercises_menu(current_exercises: int = 3) -> InlineKeyboardMarkup:
        """Меню выбора количества упражнений"""
        exercises = [1, 2, 3, 4, 5, 6, 7, 8]
        
        keyboard = []
        for exercise in exercises:
            text = f"{exercise} упражнени{'е' if exercise == 1 else 'я' if exercise in [2, 3, 4] else 'й'}"
            if exercise == current_exercises:
                text = f"✅ {text}"
            keyboard.append([InlineKeyboardButton(text=text, callback_data=f"pranayama_exercises_{exercise}")])
        
        keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="pranayama_config")])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    @staticmethod
    def get_pranayama_exercise_time_menu(current_time: int = 30) -> InlineKeyboardMarkup:
        """Меню выбора времени упражнения"""
        times = [10, 15, 20, 30, 45, 60, 90, 120]
        
        keyboard = []
        for time in times:
            text = f"{time}с" if time < 60 else f"{time//60}м"
            if time == current_time:
                text = f"✅ {text}"
            keyboard.append([InlineKeyboardButton(text=text, callback_data=f"pranayama_exercise_time_{time}")])
        
        keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="pranayama_config")])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    @staticmethod
    def get_pranayama_rest_time_menu(current_time: int = 20) -> InlineKeyboardMarkup:
        """Меню выбора времени отдыха"""
        times = [5, 10, 15, 20, 30, 45, 60]
        
        keyboard = []
        for time in times:
            text = f"{time}с" if time < 60 else f"{time//60}м"
            if time == current_time:
                text = f"✅ {text}"
            keyboard.append([InlineKeyboardButton(text=text, callback_data=f"pranayama_rest_time_{time}")])
        
        keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="pranayama_config")])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    @staticmethod
    def get_control_keyboard(session: TimerSession) -> InlineKeyboardMarkup:
        """Клавиатура управления таймером"""
        if session.status == TimerStatus.RUNNING:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="⏸️ Пауза", callback_data="timer_pause"),
                        InlineKeyboardButton(text="⏹️ Стоп", callback_data="timer_stop")
                    ],
                    [InlineKeyboardButton(text="🔄 Сброс", callback_data="timer_reset")]
                ]
            )
        elif session.status == TimerStatus.PAUSED:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="▶️ Продолжить", callback_data="timer_start"),
                        InlineKeyboardButton(text="⏹️ Стоп", callback_data="timer_stop")
                    ],
                    [InlineKeyboardButton(text="🔄 Сброс", callback_data="timer_reset")]
                ]
            )
        else:  # STOPPED or COMPLETED
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="▶️ Начать", callback_data="timer_start"),
                        InlineKeyboardButton(text="🗑️ Удалить", callback_data="timer_delete")
                    ],
                    [InlineKeyboardButton(text="🔄 Сброс", callback_data="timer_reset")]
                ]
            )
        return keyboard
    
    @staticmethod
    def format_timer_message(session: TimerSession) -> str:
        """Отформатировать сообщение о состоянии таймера"""
        if session.timer_type == TimerType.MEDITATION:
            return TimerUI._format_meditation_message(session)
        else:
            return TimerUI._format_asana_message(session)
    
    @staticmethod
    def _format_meditation_message(session: TimerSession) -> str:
        """Отформатировать сообщение для медитации"""
        remaining = session.get_remaining_time()
        minutes = remaining // 60
        seconds = remaining % 60
        
        if session.status == TimerStatus.COMPLETED:
            return (
                "🧘 **Медитация завершена!**\n\n"
                "Отличная практика! Надеюсь, ты чувствуешь себя спокойно и гармонично. 🙏\n\n"
                "Хочешь начать новую медитацию?"
            )
        
        status_emoji = "⏸️" if session.status == TimerStatus.PAUSED else "🧘"
        
        return (
            f"{status_emoji} **Медитация**\n\n"
            f"Осталось времени: {minutes:02d}:{seconds:02d}\n"
            f"{session.get_progress_bar()}\n\n"
            f"Прогресс: {session.elapsed // 60}м {session.elapsed % 60}с / {session.duration // 60}м {session.duration % 60}с"
        )
    
    @staticmethod
    def _format_asana_message(session: TimerSession) -> str:
        """Отформатировать сообщение для асан/пранаямы"""
        timer_name = "🧘‍♂️ Асана" if session.timer_type == TimerType.ASANA else "🌬️ Пранаяма"
        
        if session.status == TimerStatus.COMPLETED:
            return (
                f"{timer_name} **практика завершена!**\n\n"
                "Отличная работа! Все циклы выполнены. 💪\n\n"
                "Ты молодец! Хочешь начать новую практику?"
            )
        
        phase_emoji = "💪" if session.current_phase == TimerPhase.WORK else "🛏️"
        phase_name = "Работа" if session.current_phase == TimerPhase.WORK else "Отдых"
        status_emoji = "⏸️" if session.status == TimerStatus.PAUSED else phase_emoji
        
        remaining = session.get_remaining_time()
        minutes = remaining // 60
        seconds = remaining % 60
        
        return (
            f"{status_emoji} **{timer_name}**\n\n"
            f"Фаза: {phase_name}\n"
            f"Осталось: {minutes:02d}:{seconds:02d}\n"
            f"{session.get_progress_bar()}\n\n"
            f"Цикл: {session.current_cycle}/{session.cycles}\n"
            f"Общее время: {session.total_elapsed // 60}м {session.total_elapsed % 60}с"
        )
    
    @staticmethod
    def get_phase_notification(session: TimerSession) -> str:
        """Получить уведомление о смене фазы"""
        if session.current_phase == TimerPhase.REST:
            return (
                "🔔 **Время работы завершено!**\n\n"
                "Отдыхай! Восстанови дыхание и подготовься к следующему подходу. 🛏️\n\n"
                f"Отдых: {session.rest_duration} секунд"
            )
        else:
            return (
                "🔔 **Отдых завершен!**\n\n"
                "Приготовься! Начинаем следующий подход. 💪\n\n"
                f"Работа: {session.work_duration} секунд"
            )
