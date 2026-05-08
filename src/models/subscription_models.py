from datetime import datetime, date, timedelta
from enum import Enum
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Date, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class SubscriptionType(Enum):
    """Типы подписок"""
    TRIAL = "trial"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    LIFETIME = "lifetime"

class SubscriptionStatus(Enum):
    """Статусы подписок"""
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    TRIAL = "trial"

class UserSubscription(Base):
    """Модель подписки пользователя"""
    __tablename__ = 'user_subscriptions'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    
    # Статус подписки
    is_premium = Column(Boolean, default=False)
    subscription_type = Column(String(20), default=None)  # trial, monthly, yearly
    subscription_status = Column(String(20), default=None)  # active, expired, cancelled
    
    # Даты подписки
    subscription_start = Column(DateTime, default=None)
    subscription_end = Column(DateTime, default=None)
    trial_used = Column(Boolean, default=False)
    trial_start = Column(DateTime, default=None)
    trial_end = Column(DateTime, default=None)
    
    # Лимиты для бесплатной версии
    daily_generations_used = Column(Integer, default=0)  # Использовано генераций за день
    last_generation_date = Column(Date, default=None)  # Дата последней генерации
    
    # Платежная информация
    payment_id = Column(String(100), default=None)  # ID платежа в системе
    payment_provider = Column(String(50), default=None)  # stripe, yookassa, etc.
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserSubscription(telegram_id={self.telegram_id}, is_premium={self.is_premium})>"
    
    def is_subscription_active(self) -> bool:
        """Проверяет активна ли подписка"""
        if not self.is_premium or not self.subscription_end:
            return False
        return datetime.utcnow() < self.subscription_end
    
    def is_trial_active(self) -> bool:
        """Проверяет активен ли триал"""
        if not self.trial_used or not self.trial_end:
            return False
        return datetime.utcnow() < self.trial_end
    
    def can_generate_sequence(self) -> bool:
        """Проверяет может ли пользователь генерировать последовательность"""
        # Если премиум или активный триал - может
        if self.is_subscription_active() or self.is_trial_active():
            return True
        
        # Бесплатный пользователь - 1 генерация в день
        today = date.today()
        if self.last_generation_date == today:
            return self.daily_generations_used < 1
        else:
            return True  # Новый день, можно генерировать
    
    def increment_daily_generations(self) -> bool:
        """Увеличивает счетчик ежедневных генераций"""
        today = date.today()
        
        # Если новый день, сбрасываем счетчик
        if self.last_generation_date != today:
            self.daily_generations_used = 1
            self.last_generation_date = today
            return True
        
        # Если еще не достигли лимита
        if self.daily_generations_used < 1:
            self.daily_generations_used += 1
            return True
        
        return False
    
    def activate_trial(self, days: int = 7):
        """Активирует триал период"""
        self.trial_used = True
        self.trial_start = datetime.utcnow()
        self.trial_end = self.trial_start + timedelta(days=days)
        self.is_premium = True
        self.subscription_type = SubscriptionType.TRIAL.value
        self.subscription_status = SubscriptionStatus.TRIAL.value
        self.subscription_start = self.trial_start
        self.subscription_end = self.trial_end
    
    def activate_subscription(self, subscription_type: SubscriptionType, duration_days: int = None):
        """Активирует подписку"""
        self.is_premium = True
        self.subscription_type = subscription_type.value
        
        if subscription_type == SubscriptionType.MONTHLY:
            duration_days = 30
        elif subscription_type == SubscriptionType.YEARLY:
            duration_days = 365
        elif subscription_type == SubscriptionType.LIFETIME:
            duration_days = 365 * 100  # Условная "пожизненная" подписка
        
        self.subscription_start = datetime.utcnow()
        self.subscription_end = self.subscription_start + timedelta(days=duration_days)
        self.subscription_status = SubscriptionStatus.ACTIVE.value
    
    def deactivate_subscription(self):
        """Деактивирует подписку"""
        self.is_premium = False
        self.subscription_status = SubscriptionStatus.EXPIRED.value

class SubscriptionPlan:
    """Информация о тарифных планах"""
    
    PLANS = {
        'trial': {
            'name': 'Пробный период',
            'duration_days': 7,
            'price': 0,
            'currency': 'RUB',
            'description': '7 дней бесплатного доступа ко всем функциям'
        },
        'monthly': {
            'name': 'Месячная подписка',
            'duration_days': 30,
            'price': 399,
            'currency': 'RUB',
            'description': 'Полный доступ на 30 дней'
        },
        'yearly': {
            'name': 'Годовая подписка',
            'duration_days': 365,
            'price': 2990,
            'currency': 'RUB',
            'description': 'Экономия 1800₽! Полный доступ на год'
        }
    }
    
    @classmethod
    def get_plan(cls, plan_type: str) -> Optional[dict]:
        """Получает информацию о тарифном плане"""
        return cls.PLANS.get(plan_type)
    
    @classmethod
    def get_all_plans(cls) -> dict:
        """Получает все тарифные планы"""
        return cls.PLANS
