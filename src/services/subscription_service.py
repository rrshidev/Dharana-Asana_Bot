import logging
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy.orm import Session

from src.models.subscription_models import UserSubscription, SubscriptionType, SubscriptionPlan
from src.services.database_service import DatabaseService

logger = logging.getLogger(__name__)

class SubscriptionService:
    """Сервис для управления подписками пользователей"""
    
    def __init__(self, database_service: DatabaseService):
        self.db = database_service
    
    def get_user_subscription(self, telegram_id: int) -> UserSubscription:
        """Получает или создает подписку пользователя"""
        session = self.db.get_session()
        try:
            subscription = session.query(UserSubscription).filter(
                UserSubscription.telegram_id == telegram_id
            ).first()
            
            if not subscription:
                subscription = UserSubscription(telegram_id=telegram_id)
                session.add(subscription)
                session.commit()
                logger.info(f"Created new subscription for user {telegram_id}")
            
            return subscription
        except Exception as e:
            logger.error(f"Error getting user subscription: {e}")
            session.rollback()
            raise
        finally:
            session.close()
    
    def update_subscription(self, subscription: UserSubscription):
        """Обновляет подписку в базе"""
        session = self.db.get_session()
        try:
            session.merge(subscription)
            session.commit()
            logger.info(f"Updated subscription for user {subscription.telegram_id}")
        except Exception as e:
            logger.error(f"Error updating subscription: {e}")
            session.rollback()
            raise
        finally:
            session.close()
    
    def activate_trial(self, telegram_id: int, days: int = 7) -> bool:
        """Активирует триал период для пользователя"""
        subscription = self.get_user_subscription(telegram_id)
        
        if subscription.trial_used:
            logger.warning(f"User {telegram_id} already used trial")
            return False
        
        subscription.activate_trial(days)
        self.update_subscription(subscription)
        
        logger.info(f"Activated trial for user {telegram_id}")
        return True
    
    def activate_subscription(self, telegram_id: int, subscription_type: SubscriptionType, 
                           payment_id: str = None, payment_provider: str = None) -> bool:
        """Активирует подписку для пользователя"""
        subscription = self.get_user_subscription(telegram_id)
        
        subscription.activate_subscription(subscription_type)
        
        if payment_id:
            subscription.payment_id = payment_id
        if payment_provider:
            subscription.payment_provider = payment_provider
        
        self.update_subscription(subscription)
        
        logger.info(f"Activated {subscription_type.value} subscription for user {telegram_id}")
        return True
    
    def deactivate_subscription(self, telegram_id: int) -> bool:
        """Деактивирует подписку пользователя"""
        subscription = self.get_user_subscription(telegram_id)
        subscription.deactivate_subscription()
        self.update_subscription(subscription)
        
        logger.info(f"Deactivated subscription for user {telegram_id}")
        return True
    
    def can_generate_sequence(self, telegram_id: int) -> tuple[bool, str]:
        """Проверяет может ли пользователь генерировать последовательность"""
        subscription = self.get_user_subscription(telegram_id)
        
        if subscription.is_subscription_active():
            return True, "✅ Премиум-доступ: безлимитные генерации"
        
        if subscription.is_trial_active():
            return True, "🎯 Пробный период: безлимитные генерации"
        
        if subscription.can_generate_sequence():
            return True, "🆓 Бесплатная генерация: 1 в день"
        
        return False, "❌ Лимит исчерпан. Для безлимитных генераций нужна подписка"
    
    def use_generation(self, telegram_id: int) -> tuple[bool, str]:
        """Использует генерацию последовательности"""
        subscription = self.get_user_subscription(telegram_id)
        
        can_generate, message = self.can_generate_sequence(telegram_id)
        
        if not can_generate:
            return False, message
        
        # Для премиум-пользователей не считаем лимиты
        if subscription.is_subscription_active() or subscription.is_trial_active():
            return True, "✅ Генерация успешна"
        
        # Для бесплатных пользователей считаем лимиты
        if subscription.increment_daily_generations():
            self.update_subscription(subscription)
            return True, "✅ Генерация успешна"
        
        return False, "❌ Лимит генераций на сегодня исчерпан"
    
    def get_subscription_info(self, telegram_id: int) -> dict:
        """Получает информацию о подписке пользователя"""
        subscription = self.get_user_subscription(telegram_id)
        
        is_active = subscription.is_subscription_active()
        is_trial = subscription.is_trial_active()
        
        if is_active:
            if subscription.subscription_type == SubscriptionType.TRIAL.value:
                status = "🎯 Пробный период"
                days_left = (subscription.trial_end - datetime.utcnow()).days if subscription.trial_end else 0
            else:
                status = "⭐ Премиум"
                days_left = (subscription.subscription_end - datetime.utcnow()).days if subscription.subscription_end else 0
        else:
            status = "🆓 Бесплатная версия"
            days_left = 0
        
        # Информация о лимитах генераций
        can_generate, gen_message = self.can_generate_sequence(telegram_id)
        
        return {
            'status': status,
            'is_active': is_active,
            'is_trial': is_trial,
            'days_left': max(0, days_left),
            'subscription_type': subscription.subscription_type,
            'can_generate': can_generate,
            'generation_message': gen_message,
            'daily_generations_used': subscription.daily_generations_used,
            'last_generation_date': subscription.last_generation_date
        }
    
    def check_expired_subscriptions(self) -> List[int]:
        """Проверяет истекшие подписки и деактивирует их"""
        session = self.db.get_session()
        expired_users = []
        
        try:
            expired_subscriptions = session.query(UserSubscription).filter(
                UserSubscription.is_premium == True,
                UserSubscription.subscription_end < datetime.utcnow()
            ).all()
            
            for subscription in expired_subscriptions:
                subscription.is_premium = False
                subscription.subscription_status = 'expired'
                expired_users.append(subscription.telegram_id)
                logger.info(f"Deactivated expired subscription for user {subscription.telegram_id}")
            
            session.commit()
            return expired_users
            
        except Exception as e:
            logger.error(f"Error checking expired subscriptions: {e}")
            session.rollback()
            return []
        finally:
            session.close()
    
    def get_subscription_stats(self) -> dict:
        """Получает статистику подписок"""
        session = self.db.get_session()
        try:
            total_users = session.query(UserSubscription).count()
            premium_users = session.query(UserSubscription).filter(
                UserSubscription.is_premium == True
            ).count()
            trial_users = session.query(UserSubscription).filter(
                UserSubscription.subscription_type == SubscriptionType.TRIAL.value,
                UserSubscription.is_premium == True
            ).count()
            
            return {
                'total_users': total_users,
                'premium_users': premium_users,
                'trial_users': trial_users,
                'free_users': total_users - premium_users,
                'conversion_rate': (premium_users / total_users * 100) if total_users > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting subscription stats: {e}")
            return {}
        finally:
            session.close()
