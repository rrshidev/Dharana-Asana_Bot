from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.i18n import t, format_duration, format_mm_ss, format_progress, t_minutes, t_exercises
from src.models.timer_models import TimerSession, TimerType, TimerStatus, TimerPhase


class TimerUI:
    """UI компоненты для таймера"""

    @staticmethod
    def get_main_menu(lang: str = 'ru') -> InlineKeyboardMarkup:
        """Главное меню таймера"""
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text=t(lang, 'btn_meditation'), callback_data="timer_meditation"),
                    InlineKeyboardButton(text=t(lang, 'btn_asana'), callback_data="timer_asana")
                ],
                [
                    InlineKeyboardButton(text=t(lang, 'btn_pranayama'), callback_data="timer_pranayama"),
                    InlineKeyboardButton(text=t(lang, 'btn_timer_exit'), callback_data="timer_exit")
                ]
            ]
        )
        return keyboard

    @staticmethod
    def get_meditation_menu(lang: str = 'ru') -> InlineKeyboardMarkup:
        """Меню выбора времени медитации"""
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=t_minutes(lang, 1), callback_data="meditation_1")],
                [InlineKeyboardButton(text=t_minutes(lang, 5), callback_data="meditation_5")],
                [InlineKeyboardButton(text=t_minutes(lang, 10), callback_data="meditation_10")],
                [InlineKeyboardButton(text=t_minutes(lang, 15), callback_data="meditation_15")],
                [InlineKeyboardButton(text=t_minutes(lang, 20), callback_data="meditation_20")],
                [InlineKeyboardButton(text=t_minutes(lang, 30), callback_data="meditation_30")],
                [InlineKeyboardButton(text=t_minutes(lang, 45), callback_data="meditation_45")],
                [InlineKeyboardButton(text=t_minutes(lang, 60), callback_data="meditation_60")],
                [InlineKeyboardButton(text=t(lang, 'btn_custom'), callback_data="meditation_custom")],
                [InlineKeyboardButton(text=t(lang, 'btn_back'), callback_data="timer_main")]
            ]
        )
        return keyboard

    @staticmethod
    def get_asana_config_menu(lang: str = 'ru') -> InlineKeyboardMarkup:
        """Меню конфигурации таймера асан"""
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text=t(lang, 'btn_work_time'), callback_data="asana_config_work"),
                    InlineKeyboardButton(text=t(lang, 'btn_rest_time'), callback_data="asana_config_rest")
                ],
                [
                    InlineKeyboardButton(text=t(lang, 'btn_cycles'), callback_data="asana_config_cycles"),
                    InlineKeyboardButton(text=t(lang, 'btn_start'), callback_data="asana_start")
                ],
                [InlineKeyboardButton(text=t(lang, 'btn_back'), callback_data="timer_main")]
            ]
        )
        return keyboard

    @staticmethod
    def get_work_duration_menu(current_duration: int = 60, lang: str = 'ru') -> InlineKeyboardMarkup:
        """Меню выбора времени работы"""
        durations = [30, 45, 60, 90, 120, 180]  # 30с, 45с, 1м, 1.5м, 2м, 3м

        keyboard = []
        for duration in durations:
            text = format_duration(lang, duration)
            if duration == current_duration:
                text = f"✅ {text}"
            keyboard.append([InlineKeyboardButton(text=text, callback_data=f"asana_work_{duration}")])

        keyboard.append([InlineKeyboardButton(text=t(lang, 'btn_back'), callback_data="asana_config")])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_rest_duration_menu(current_duration: int = 20, lang: str = 'ru') -> InlineKeyboardMarkup:
        """Меню выбора времени отдыха"""
        durations = [10, 15, 20, 30, 45, 60]  # 10с, 15с, 20с, 30с, 45с, 1м

        keyboard = []
        for duration in durations:
            text = format_duration(lang, duration)
            if duration == current_duration:
                text = f"✅ {text}"
            keyboard.append([InlineKeyboardButton(text=text, callback_data=f"asana_rest_{duration}")])

        keyboard.append([InlineKeyboardButton(text=t(lang, 'btn_back'), callback_data="asana_config")])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_cycles_menu(current_cycles: int = 5, lang: str = 'ru') -> InlineKeyboardMarkup:
        """Меню выбора количества циклов"""
        cycles = [3, 5, 7, 10, 15, 20]

        keyboard = []
        for cycle in cycles:
            text = t(lang, 'cycles_count', n=cycle)
            if cycle == current_cycles:
                text = f"✅ {text}"
            keyboard.append([InlineKeyboardButton(text=text, callback_data=f"asana_cycles_{cycle}")])

        keyboard.append([InlineKeyboardButton(text=t(lang, 'btn_back'), callback_data="asana_config")])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_pranayama_menu(lang: str = 'ru') -> InlineKeyboardMarkup:
        """Меню конфигурации пранаямы"""
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text=t(lang, 'btn_exercises'), callback_data="pranayama_exercises"),
                    InlineKeyboardButton(text=t(lang, 'btn_exercise_time'), callback_data="pranayama_exercise_time")
                ],
                [
                    InlineKeyboardButton(text=t(lang, 'btn_rest_time'), callback_data="pranayama_rest_time"),
                    InlineKeyboardButton(text=t(lang, 'btn_start'), callback_data="pranayama_start")
                ],
                [InlineKeyboardButton(text=t(lang, 'btn_back'), callback_data="timer_main")]
            ]
        )
        return keyboard

    @staticmethod
    def get_pranayama_exercises_menu(current_exercises: int = 3, lang: str = 'ru') -> InlineKeyboardMarkup:
        """Меню выбора количества упражнений"""
        exercises = [1, 2, 3, 4, 5, 6, 7, 8]

        keyboard = []
        for exercise in exercises:
            text = t_exercises(lang, exercise)
            if exercise == current_exercises:
                text = f"✅ {text}"
            keyboard.append([InlineKeyboardButton(text=text, callback_data=f"pranayama_exercises_{exercise}")])

        keyboard.append([InlineKeyboardButton(text=t(lang, 'btn_back'), callback_data="pranayama_config")])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_pranayama_exercise_time_menu(current_time: int = 30, lang: str = 'ru') -> InlineKeyboardMarkup:
        """Меню выбора времени упражнения"""
        times = [10, 15, 20, 30, 45, 60, 90, 120]

        keyboard = []
        for time in times:
            text = format_duration(lang, time)
            if time == current_time:
                text = f"✅ {text}"
            keyboard.append([InlineKeyboardButton(text=text, callback_data=f"pranayama_exercise_time_{time}")])

        keyboard.append([InlineKeyboardButton(text=t(lang, 'btn_back'), callback_data="pranayama_config")])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_pranayama_rest_time_menu(current_time: int = 20, lang: str = 'ru') -> InlineKeyboardMarkup:
        """Меню выбора времени отдыха"""
        times = [5, 10, 15, 20, 30, 45, 60]

        keyboard = []
        for time in times:
            text = format_duration(lang, time)
            if time == current_time:
                text = f"✅ {text}"
            keyboard.append([InlineKeyboardButton(text=text, callback_data=f"pranayama_rest_time_{time}")])

        keyboard.append([InlineKeyboardButton(text=t(lang, 'btn_back'), callback_data="pranayama_config")])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_control_keyboard(session: TimerSession, lang: str = 'ru') -> InlineKeyboardMarkup:
        """Клавиатура управления таймером"""
        if session.status == TimerStatus.RUNNING:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text=t(lang, 'btn_pause'), callback_data="timer_pause"),
                        InlineKeyboardButton(text=t(lang, 'btn_stop'), callback_data="timer_stop")
                    ],
                    [InlineKeyboardButton(text=t(lang, 'btn_reset'), callback_data="timer_reset")]
                ]
            )
        elif session.status == TimerStatus.PAUSED:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text=t(lang, 'btn_resume'), callback_data="timer_start"),
                        InlineKeyboardButton(text=t(lang, 'btn_stop'), callback_data="timer_stop")
                    ],
                    [InlineKeyboardButton(text=t(lang, 'btn_reset'), callback_data="timer_reset")]
                ]
            )
        else:  # STOPPED or COMPLETED
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text=t(lang, 'btn_timer_start'), callback_data="timer_start"),
                        InlineKeyboardButton(text=t(lang, 'btn_delete'), callback_data="timer_delete")
                    ],
                    [InlineKeyboardButton(text=t(lang, 'btn_reset'), callback_data="timer_reset")]
                ]
            )
        return keyboard

    @staticmethod
    def format_timer_message(session: TimerSession, lang: str = 'ru') -> str:
        """Отформатировать сообщение о состоянии таймера"""
        if session.timer_type == TimerType.MEDITATION:
            return TimerUI._format_meditation_message(session, lang)
        else:
            return TimerUI._format_asana_message(session, lang)

    @staticmethod
    def _format_meditation_message(session: TimerSession, lang: str = 'ru') -> str:
        """Отформатировать сообщение для медитации"""
        remaining = session.get_remaining_time()

        if session.status == TimerStatus.COMPLETED:
            return t(lang, 'meditation_completed')

        status_emoji = "⏸️" if session.status == TimerStatus.PAUSED else "🧘"

        return t(
            lang, 'meditation_status',
            emoji=status_emoji,
            remaining=format_mm_ss(lang, remaining),
            bar=session.get_progress_bar(),
            progress=format_progress(lang, session.elapsed, session.duration)
        )

    @staticmethod
    def _format_asana_message(session: TimerSession, lang: str = 'ru') -> str:
        """Отформатировать сообщение для асан/пранаямы"""
        if session.asana_name and session.timer_type == TimerType.ASANA:
            timer_name = f"🧘 **{session.asana_name}**"
        elif session.timer_type == TimerType.ASANA:
            timer_name = t(lang, 'timer_asana_name')
        else:
            timer_name = t(lang, 'timer_pranayama_name')

        if session.status == TimerStatus.COMPLETED:
            return t(lang, 'asana_completed', timer_name=timer_name)

        phase_emoji = "🛏️"
        phase_name = t(lang, 'phase_rest')
        if not session.is_rest:
            phase_emoji = "💪" if session.current_phase == TimerPhase.WORK else "🛏️"
            phase_name = t(lang, 'phase_work') if session.current_phase == TimerPhase.WORK else t(lang, 'phase_rest')
        status_emoji = "⏸️" if session.status == TimerStatus.PAUSED else phase_emoji

        remaining = session.get_remaining_time()

        return t(
            lang, 'asana_status',
            emoji=status_emoji,
            timer_name=timer_name,
            phase=phase_name,
            remaining=format_mm_ss(lang, remaining),
            bar=session.get_progress_bar(),
            cycle=session.current_cycle,
            cycles=session.cycles,
            total=format_duration(lang, session.total_elapsed)
        )

    @staticmethod
    def get_phase_notification(session: TimerSession, lang: str = 'ru') -> str:
        """Получить уведомление о смене фазы"""
        if session.current_phase == TimerPhase.REST:
            return t(lang, 'work_finish_notif', seconds=session.rest_duration)
        else:
            return t(lang, 'rest_finish_notif', seconds=session.work_duration)