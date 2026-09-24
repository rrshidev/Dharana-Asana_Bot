import logging
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, date, time, timedelta, timezone
from typing import Optional, List

from src.config import DATABASE_URL
from src.i18n import normalize_lang
from src.models.user import User, DailyAsanaLog
from src.models.subscription_models import UserSubscription
from src.models.video_models import AsanaVideo
from src.models.ready_sequence_models import ReadySequence

logger = logging.getLogger(__name__)

class DatabaseService:
    """Сервис для работы с базой данных.

    Единая БД с API (в проде PostgreSQL). Схему создаёт API (alembic),
    здесь — только зеркальные модели для чтения/записи тех же таблиц.
    """

    # Если время асаны дня не задано (NULL после миграции) — используем 09:00.
    DEFAULT_DAILY_ASANA_TIME = time(9, 0)

    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=self.engine)
        self._lang_cache = {}  # telegram_id -> 'ru'|'en' (кэш запросов языка)

        # Локальная разработка (SQLite): создаём недостающие таблицы.
        # В проде (PostgreSQL) таблицы уже созданы API — no-op.
        for base in (User.__table__.metadata,
                     UserSubscription.__table__.metadata,
                     AsanaVideo.__table__.metadata,
                     ReadySequence.__table__.metadata,
                     DailyAsanaLog.__table__.metadata):
            base.create_all(bind=self.engine)
        logger.info("Database tables created/verified")
    
    def get_session(self) -> Session:
        """Получить сессию БД"""
        return self.SessionLocal()
    
    def get_user(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по telegram_id (всегда свежие данные)"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            return user
        finally:
            session.close()
    
    def get_or_create_user(self, telegram_id: int, username: str = None, 
                          first_name: str = None, last_name: str = None,
                          language: str = None) -> User:
        """Получить или создать пользователя"""
        lang = normalize_lang(language)
        session = self.get_session()
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            
            if not user:
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    name=first_name,
                    last_name=last_name,
                    language=lang
                )
                session.add(user)
                session.commit()
                logger.info(f"Created new user: {telegram_id}, language={lang}")
            else:
                # Обновляем данные если изменились
                if username and user.username != username:
                    user.username = username
                if first_name and user.name != first_name:
                    user.name = first_name
                if last_name and user.last_name != last_name:
                    user.last_name = last_name
                # Язык задаём ТОЛЬКО при первом контакте (не перезаписываем ручной выбор)
                if not user.language:
                    user.language = lang
                session.commit()
            
            self._lang_cache[telegram_id] = user.language or 'ru'
            return user
            
        except IntegrityError as e:
            session.rollback()
            logger.error(f"Database error creating user {telegram_id}: {e}")
            raise
        finally:
            session.close()
    
    def get_user_language(self, telegram_id: int) -> str:
        """Получить язык пользователя ('ru'|'en'). Кэшируется."""
        cached = self._lang_cache.get(telegram_id)
        if cached:
            return cached
        user = self.get_user(telegram_id)
        lang = normalize_lang(user.language if user else None)
        self._lang_cache[telegram_id] = lang
        return lang
    
    def set_user_language(self, telegram_id: int, language: str) -> bool:
        """Задать язык пользователя. Кэш обновляется сразу."""
        lang = normalize_lang(language)
        session = self.get_session()
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                return False
            user.language = lang
            user.updated_at = datetime.utcnow()
            session.commit()
            self._lang_cache[telegram_id] = lang
            logger.info(f"Language for user {telegram_id} set to {lang}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error setting language for {telegram_id}: {e}")
            return False
        finally:
            session.close()
    
    def is_user_premium(self, telegram_id: int) -> bool:
        """Премиум/триал доступ из ЕДИНОЙ таблицы подписок (общей с API)."""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                return False
            subscription = session.query(UserSubscription).filter(
                UserSubscription.user_id == user.id
            ).first()
            return bool(subscription and subscription.has_premium_access())
        except Exception as e:
            logger.error(f"Error checking premium for {telegram_id}: {e}")
            return False
        finally:
            session.close()

    def update_daily_asana_settings(self, telegram_id: int, enabled: bool = None,
                                    asana_time: time = None, timezone: str = None) -> bool:
        """Обновить настройки асаны дня"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                return False
            
            if enabled is not None:
                user.daily_asana_enabled = enabled
            if asana_time is not None:
                user.daily_asana_time = asana_time
            if timezone is not None:
                user.timezone = timezone
            
            user.updated_at = datetime.utcnow()
            session.commit()
            logger.info(f"Updated daily asana settings for user {telegram_id}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating daily asana settings: {e}")
            return False
        finally:
            session.close()
    
    @staticmethod
    def _parse_timezone_offset(timezone_str: Optional[str]) -> timedelta:
        """Парсить часовой пояс вида 'UTC', 'UTC+3', 'UTC+3:30', 'UTC-5'.

        dharmana_api хранит пояс строкой вида 'UTC+3' (см. daily_asana_handlers).
        Возвращает смещение от UTC.
        """
        if not timezone_str:
            return timedelta(0)
        tz_str = timezone_str.strip().upper()
        for prefix in ("UTC", "GMT"):
            if tz_str.startswith(prefix):
                tz_str = tz_str[len(prefix):].strip()
                break
        if not tz_str:
            return timedelta(0)

        sign = -1 if tz_str.startswith("-") else 1
        tz_str = tz_str.lstrip("+-")
        parts = tz_str.split(":")
        try:
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
        except ValueError:
            return timedelta(0)
        return timedelta(hours=sign * hours, minutes=sign * minutes)

    def get_users_for_daily_asana(self, current_time: datetime) -> List[User]:
        """Получить пользователей, которым нужно прислать асану дня.

        current_time интерпретируется как момент в UTC (сервер бота живёт по UTC).
        Само время daily_asana_time хранится в ЛОКАЛЬНОМ поясе юзера (user.timezone),
        поэтому тут переводим current_time в локальное время пользователя и
        сравниваем уже его. Проверка «уже присылали сегодня» тоже локальная.
        """
        session = self.get_session()
        try:
            if current_time.tzinfo is None:
                utc_now = current_time.replace(tzinfo=timezone.utc)
            else:
                utc_now = current_time.astimezone(timezone.utc)

            # Получаем пользователей с включенными уведомлениями.
            # Только Telegram-пользователи: рассылка уходит в личку бота.
            users = session.query(User).filter(
                User.daily_asana_enabled == True,
                User.telegram_id.isnot(None),
            ).all()
            
            logger.info(f"Found {len(users)} users with enabled notifications")
            
            target_users = []
            for user in users:
                try:
                    offset = self._parse_timezone_offset(user.timezone)
                    local_now = utc_now + offset

                    # Уже присылали сегодня (по локальному времени юзера)
                    if user.last_daily_asana_date == local_now.date():
                        continue

                    # NULL после миграции = не задано → используем дефолт 09:00
                    user_time = user.daily_asana_time or self.DEFAULT_DAILY_ASANA_TIME

                    logger.info(f"User {user.telegram_id}: time={user_time}, local_now={local_now.time()}, tz={user.timezone}")
                    
                    if (user_time.hour == local_now.hour and 
                        user_time.minute == local_now.minute):
                        target_users.append(user)
                        logger.info(f"✅ User {user.telegram_id} matches time!")
                    else:
                        logger.info(f"❌ User {user.telegram_id} time mismatch: {user_time.hour}:{user_time.minute} != {local_now.hour}:{local_now.minute}")
                        
                except Exception as e:
                    logger.error(f"Error checking time for user {user.telegram_id}: {e}")
                    continue
            
            logger.info(f"Found {len(target_users)} users for daily asana at {current_time}")
            return target_users
            
        except Exception as e:
            logger.error(f"Error getting users for daily asana: {e}")
            return []
        finally:
            session.close()
    
    def mark_daily_asana_sent(self, telegram_id: int) -> bool:
        """Отметить, что асана дня отправлена"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                user.mark_daily_asana_sent()
                session.commit()
                return True
            return False
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error marking daily asana sent: {e}")
            return False
        finally:
            session.close()
    
    def update_last_daily_asana_date(self, telegram_id: int) -> bool:
        """Обновить дату последней отправки асаны дня"""
        from datetime import date
        
        session = self.get_session()
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                return False
            
            user.last_daily_asana_date = date.today()
            session.commit()
            logger.info(f"Updated last daily asana date for user {telegram_id}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating last daily asana date for user {telegram_id}: {e}")
            return False
        finally:
            session.close()
    
    def increment_practice_count(self, telegram_id: int) -> bool:
        """Увеличить счетчик практик"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                user.total_practices += 1
                
                # Обновляем streak (дней подряд)
                today = date.today()
                yesterday = date.fromordinal(today.toordinal() - 1)
                
                if user.last_daily_asana_date == yesterday:
                    user.streak_days += 1
                elif user.last_daily_asana_date != today:
                    user.streak_days = 1
                
                session.commit()
                return True
            return False
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error incrementing practice count: {e}")
            return False
        finally:
            session.close()
    
    def save_last_daily_asana(self, telegram_id: int, asana_name: str) -> bool:
        """Сохранить имя последней отправленной «Асаны дня» (для видео-отстройки)."""
        session = self.get_session()
        try:
            log = session.query(DailyAsanaLog).filter(DailyAsanaLog.telegram_id == telegram_id).first()
            if not log:
                log = DailyAsanaLog(telegram_id=telegram_id, asana_name=asana_name)
                session.add(log)
            else:
                log.asana_name = asana_name
                log.sent_at = datetime.utcnow()
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving last daily asana for user {telegram_id}: {e}")
            return False
        finally:
            session.close()
    
    def get_last_daily_asana(self, telegram_id: int) -> Optional[str]:
        """Имя последней отправленной «Асаны дня» или None."""
        session = self.get_session()
        try:
            log = session.query(DailyAsanaLog).filter(DailyAsanaLog.telegram_id == telegram_id).first()
            return log.asana_name if log else None
        except Exception as e:
            logger.error(f"Error reading last daily asana for user {telegram_id}: {e}")
            return None
        finally:
            session.close()

# Глобальный экземпляр для использования во всем приложении
db_service = DatabaseService()
