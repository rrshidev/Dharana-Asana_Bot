from sqlalchemy import Column, Integer, String, Time, Boolean, DateTime, Date
from sqlalchemy.ext.declarative import declarative_base
from datetime import date, datetime, time

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    
    # Настройки "Асаны дня"
    daily_asana_enabled = Column(Boolean, default=True)
    daily_asana_time = Column(Time, default=time(9, 0))  # 9:00 по умолчанию
    timezone = Column(String(50), default='UTC')  # Часовой пояс
    last_daily_asana_date = Column(Date, default=None)  # Когда последний раз присылали
    
    # Премиум статус
    is_premium = Column(Boolean, default=False)
    premium_expires_at = Column(DateTime, default=None)
    
    # Статистика
    total_practices = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)  # Дней подряд практикует
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(id={self.telegram_id}, username={self.username}, premium={self.is_premium})>"
    
    def should_receive_daily_asana(self) -> bool:
        """Проверить, нужно ли присылать асану дня сегодня"""
        if not self.daily_asana_enabled:
            return False
        
        today = date.today()
        if self.last_daily_asana_date == today:
            return False  # Уже присылали сегодня
        
        return True
    
    def mark_daily_asana_sent(self):
        """Отметить, что асана дня отправлена"""
        self.last_daily_asana_date = date.today()
        self.updated_at = datetime.utcnow()
