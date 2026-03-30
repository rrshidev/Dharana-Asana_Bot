from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import datetime, timedelta
import enum


class TimerType(enum.Enum):
    MEDITATION = "meditation"
    ASANA = "asana"
    PRANAYAMA = "pranayama"


class TimerStatus(enum.Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"


class TimerPhase(enum.Enum):
    WORK = "work"
    REST = "rest"
    COMPLETE = "complete"


@dataclass
class TimerSession:
    """Сессия таймера"""
    user_id: int
    timer_type: TimerType
    status: TimerStatus = TimerStatus.STOPPED
    duration: int = 0  # общая длительность в секундах (только для медитации)
    elapsed: int = 0   # прошедшее время в секундах
    current_phase: TimerPhase = TimerPhase.WORK
    start_time: Optional[datetime] = None
    pause_time: Optional[datetime] = None
    total_elapsed: int = 0  # общее время с учетом пауз

    # Только для асан/пранаямы
    work_duration: int = 0      # время работы в секундах
    rest_duration: int = 0      # время отдыха в секундах
    cycles: int = 1            # количество циклов
    current_cycle: int = 1      # текущий цикл

    # Только для пранаямы
    exercises: int = 3         # количество упражнений
    current_exercise: int = 1   # текущее упражнение
    exercise_duration: int = 30  # время каждого упражнения в секундах

    def get_remaining_time(self) -> int:
        """Получить оставшееся время"""
        if self.timer_type == TimerType.MEDITATION:
            return max(0, self.duration - self.elapsed)
        else:
            # Для асан/пранаямы считаем по текущему циклу
            if self.current_phase == TimerPhase.WORK:
                return max(0, self.work_duration - self.elapsed)
            else:
                return max(0, self.rest_duration - self.elapsed)
    
    def get_progress_percentage(self) -> int:
        """Получить процент выполнения"""
        if self.timer_type == TimerType.MEDITATION:
            return min(100, (self.elapsed / self.duration) * 100) if self.duration > 0 else 0
        else:
            # Для асан/пранаямы считаем прогресс текущего цикла
            current_duration = self.work_duration if self.current_phase == TimerPhase.WORK else self.rest_duration
            return min(100, (self.elapsed / current_duration) * 100) if current_duration > 0 else 0
    
    def get_progress_bar(self) -> str:
        """Получить визуальный прогресс-бар"""
        percentage = self.get_progress_percentage()
        filled = int(percentage / 5)  # 20 символов = 100%
        bar = "█" * filled + "░" * (20 - filled)
        return f"[{bar}] {percentage:.0f}%"


@dataclass
class PranayamaConfig:
    """Конфигурация таймера пранаямы"""
    exercises: int = 3           # количество упражнений
    exercise_duration: int = 30   # время каждого упражнения в секундах
    rest_duration: int = 20       # время отдыха между упражнениями


@dataclass
class TimerConfig:
    """Конфигурация таймера для асан/пранаямы"""
    work_duration: int = 60    # по умолчанию 60 секунд работы
    rest_duration: int = 20    # по умолчанию 20 секунд отдыха
    cycles: int = 5            # по умолчанию 5 циклов


# Хранилище активных сессий
active_sessions: Dict[int, TimerSession] = {}

# Хранилище ID сообщений таймера для редактирования
timer_messages: Dict[int, int] = {}  # user_id -> message_id
