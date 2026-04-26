import logging
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, date, time
from typing import Optional, List

from src.models.user import User

logger = logging.getLogger(__name__)

# Временная конфигурация БД (позже вынесем в config)
DATABASE_URL = "sqlite:///bot_data/yoga_bot.db"

class DatabaseService:
    """Сервис для работы с базой данных пользователей"""
    
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Создаем таблицы
        User.metadata.create_all(bind=self.engine)
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
                          first_name: str = None, last_name: str = None) -> User:
        """Получить или создать пользователя"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            
            if not user:
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name
                )
                session.add(user)
                session.commit()
                logger.info(f"Created new user: {telegram_id}")
            else:
                # Обновляем данные если изменились
                if username and user.username != username:
                    user.username = username
                if first_name and user.first_name != first_name:
                    user.first_name = first_name
                if last_name and user.last_name != last_name:
                    user.last_name = last_name
                session.commit()
            
            return user
            
        except IntegrityError as e:
            session.rollback()
            logger.error(f"Database error creating user {telegram_id}: {e}")
            raise
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
    
    def get_users_for_daily_asana(self, current_time: datetime) -> List[User]:
        """Получить пользователей, которым нужно прислать асану дня"""
        session = self.get_session()
        try:
            # Получаем пользователей с включенными уведомлениями
            users = session.query(User).filter(
                User.daily_asana_enabled == True,
                (User.last_daily_asana_date != date.today()) | (User.last_daily_asana_date.is_(None))
            ).all()
            
            logger.info(f"Found {len(users)} users with enabled notifications")
            
            # Фильтруем по времени (учитываем часовой пояс)
            target_users = []
            for user in users:
                try:
                    # Здесь нужно будет добавить конвертацию времени с учетом часового пояса
                    # Пока упрощенно - проверяем совпадение часов и минут
                    user_time = user.daily_asana_time
                    
                    if user_time is None:
                        logger.warning(f"❌ User {user.telegram_id} has daily_asana_enabled=True but daily_asana_time is NULL!")
                        continue
                        
                    logger.info(f"User {user.telegram_id}: time={user_time}, current={current_time.time()}")
                    
                    if (user_time.hour == current_time.hour and 
                        user_time.minute == current_time.minute):
                        target_users.append(user)
                        logger.info(f"✅ User {user.telegram_id} matches time!")
                    else:
                        logger.info(f"❌ User {user.telegram_id} time mismatch: {user_time.hour}:{user_time.minute} != {current_time.hour}:{current_time.minute}")
                        
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

# Глобальный экземпляр для использования во всем приложении
db_service = DatabaseService()
