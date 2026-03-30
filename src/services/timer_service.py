import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

from src.models.timer_models import (
    TimerSession, TimerType, TimerStatus, TimerPhase, 
    TimerConfig, PranayamaConfig, active_sessions
)

logger = logging.getLogger(__name__)


class TimerService:
    """Сервис для управления таймерами медитации, асан и пранаямы"""
    
    def __init__(self):
        self.active_sessions = active_sessions
    
    def create_meditation_timer(self, user_id: int, duration_minutes: int) -> TimerSession:
        """Создать таймер медитации"""
        session = TimerSession(
            user_id=user_id,
            timer_type=TimerType.MEDITATION,
            duration=duration_minutes * 60,
            start_time=datetime.now()
        )
        self.active_sessions[user_id] = session
        logger.info(f"Created meditation timer for user {user_id}: {duration_minutes} minutes")
        return session
    
    def create_asana_timer(self, user_id: int, config: TimerConfig) -> TimerSession:
        """Создать таймер для асан"""
        session = TimerSession(
            user_id=user_id,
            timer_type=TimerType.ASANA,
            work_duration=config.work_duration,
            rest_duration=config.rest_duration,
            cycles=config.cycles,
            current_cycle=1,
            start_time=datetime.now()
        )
        self.active_sessions[user_id] = session
        logger.info(f"Created asana timer for user {user_id}: {config}")
        return session
    
    def create_pranayama_timer(self, user_id: int, config: PranayamaConfig) -> TimerSession:
        """Создать таймер для пранаямы"""
        session = TimerSession(
            user_id=user_id,
            timer_type=TimerType.PRANAYAMA,
            work_duration=config.exercise_duration,
            rest_duration=config.rest_duration,
            cycles=config.exercises,  # Для пранаямы cycles = exercises
            current_cycle=1,
            exercises=config.exercises,
            current_exercise=1,
            exercise_duration=config.exercise_duration,
            start_time=datetime.now()
        )
        self.active_sessions[user_id] = session
        logger.info(f"Created pranayama timer for user {user_id}: {config}")
        return session
    
    def start_timer(self, user_id: int) -> Optional[TimerSession]:
        """Запустить/продолжить таймер"""
        session = self.active_sessions.get(user_id)
        if not session:
            return None
        
        if session.status == TimerStatus.PAUSED:
            # Возобновляем после паузы - сохраняем прошедшее время
            pause_duration = datetime.now() - session.pause_time
            session.start_time = datetime.now() - timedelta(seconds=session.elapsed)
            session.total_elapsed += int(pause_duration.total_seconds())
            session.status = TimerStatus.RUNNING
            logger.info(f"Resumed timer for user {user_id} - elapsed: {session.elapsed}s")
        elif session.status == TimerStatus.STOPPED:
            # Запускаем заново
            session.elapsed = 0
            session.current_cycle = 1
            session.current_phase = TimerPhase.WORK
            session.start_time = datetime.now()
            session.total_elapsed = 0
            session.status = TimerStatus.RUNNING
            logger.info(f"Started timer for user {user_id}")
        
        return session
    
    def pause_timer(self, user_id: int) -> Optional[TimerSession]:
        """Поставить таймер на паузу"""
        session = self.active_sessions.get(user_id)
        if not session or session.status != TimerStatus.RUNNING:
            return None
        
        session.status = TimerStatus.PAUSED
        session.pause_time = datetime.now()
        logger.info(f"Paused timer for user {user_id}")
        return session
    
    def stop_timer(self, user_id: int) -> Optional[TimerSession]:
        """Остановить таймер"""
        session = self.active_sessions.get(user_id)
        if not session:
            return None
        
        session.status = TimerStatus.STOPPED
        session.elapsed = 0
        session.current_cycle = 1
        session.current_phase = TimerPhase.WORK
        logger.info(f"Stopped timer for user {user_id}")
        return session
    
    def reset_timer(self, user_id: int) -> Optional[TimerSession]:
        """Сбросить таймер"""
        session = self.active_sessions.get(user_id)
        if not session:
            return None
        
        session.elapsed = 0
        session.current_cycle = 1
        session.current_phase = TimerPhase.WORK
        session.start_time = datetime.now()
        session.total_elapsed = 0
        session.status = TimerStatus.RUNNING
        logger.info(f"Reset timer for user {user_id}")
        return session
    
    def update_timer(self, user_id: int) -> Optional[TimerSession]:
        """Обновить состояние таймера (вызывать каждую секунду)"""
        session = self.active_sessions.get(user_id)
        if not session or session.status != TimerStatus.RUNNING:
            return None
        
        now = datetime.now()
        session.elapsed = int((now - session.start_time).total_seconds())
        
        if session.timer_type == TimerType.MEDITATION:
            # Простая медитация - один сеанс
            if session.elapsed >= session.duration:
                session.status = TimerStatus.COMPLETED
                logger.info(f"Meditation completed for user {user_id}")
        else:
            # Асаны/пранаяма - проверяем фазы
            if session.current_phase == TimerPhase.WORK:
                if session.elapsed >= session.work_duration:
                    # Переход к отдыху
                    session.current_phase = TimerPhase.REST
                    session.elapsed = 0
                    session.start_time = now
                    logger.info(f"User {user_id} switched to rest phase, cycle {session.current_cycle}")
            else:  # REST phase
                if session.elapsed >= session.rest_duration:
                    # Увеличиваем цикл ПОСЛЕ отдыха
                    session.current_cycle += 1
                    if session.current_cycle > session.cycles:
                        # Все циклы завершены
                        session.status = TimerStatus.COMPLETED
                        logger.info(f"Asana/Pranayama completed for user {user_id}")
                    else:
                        # Начинаем следующий цикл с упражнения
                        session.current_phase = TimerPhase.WORK
                        session.elapsed = 0
                        session.start_time = now
                        logger.info(f"User {user_id} started cycle {session.current_cycle}")
        
        return session
    
    def get_session(self, user_id: int) -> Optional[TimerSession]:
        """Получить сессию пользователя"""
        return self.active_sessions.get(user_id)
    
    def delete_session(self, user_id: int) -> bool:
        """Удалить сессию пользователя"""
        if user_id in self.active_sessions:
            del self.active_sessions[user_id]
            logger.info(f"Deleted timer session for user {user_id}")
            return True
        return False


# Глобальный экземпляр сервиса
timer_service = TimerService()
