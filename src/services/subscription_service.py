import logging
import os
import time
from datetime import datetime, date
from typing import Optional, List, Dict, Tuple

import httpx

from src.models.subscription_models import UserSubscription, SubscriptionType, SubscriptionPlan
from src.services.database_service import DatabaseService

logger = logging.getLogger(__name__)

API_URL = os.getenv("API_URL", "http://dharana-api:8000")
BOT_ADMIN_KEY = os.getenv("BOT_ADMIN_KEY", "")

# Кэш статуса подписки из API (источник правды по премиуму/триалу)
_API_CACHE_TTL = 60  # секунд

class SubscriptionService:
    """Сервис для управления подписками пользователей"""
    
    def __init__(self, database_service: DatabaseService):
        self.db = database_service
        self._api_cache: Dict[int, Tuple[float, dict]] = {}

    def clear_api_cache(self, telegram_id: int = None):
        """Сбрасывает кэш статуса из API (после выдачи/снятия премиума)"""
        if telegram_id is None:
            self._api_cache.clear()
        else:
            self._api_cache.pop(telegram_id, None)

    async def _api_subscription(self, telegram_id: int) -> Optional[dict]:
        """Статус подписки из API. None, если API недоступен."""
        now = time.monotonic()
        cached = self._api_cache.get(telegram_id)
        if cached and now - cached[0] < _API_CACHE_TTL:
            return cached[1]

        info = None
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(
                    f"{API_URL}/api/v1/admin-bot/subscription",
                    params={"telegram_id": telegram_id},
                    headers={"X-Bot-Key": BOT_ADMIN_KEY},
                )
                if resp.status_code == 200:
                    info = resp.json()
        except Exception as e:
            logger.warning(f"API subscription check failed for {telegram_id}: {e}")

        if info is not None:
            self._api_cache[telegram_id] = (now, info)
        return info
    
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
    
    async def can_generate_sequence(self, telegram_id: int) -> Tuple[bool, str]:
        """Проверяет может ли пользователь генерировать последовательность"""
        api = await self._api_subscription(telegram_id)
        if api and api.get("is_active"):
            return True, "✅ Премиум-доступ: безлимитные генерации"
        
        subscription = self.get_user_subscription(telegram_id)
        
        if subscription.is_subscription_active():
            return True, "✅ Премиум-доступ: безлимитные генерации"
        
        if subscription.is_trial_active():
            return True, "🎯 Пробный период: безлимитные генерации"
        
        if subscription.can_generate_sequence():
            return True, "🆓 Бесплатная генерация: 1 в день"
        
        return False, "❌ Лимит исчерпан. Для безлимитных генераций нужна подписка"
    
    async def use_generation(self, telegram_id: int) -> Tuple[bool, str]:
        """Использует генерацию последовательности"""
        can_generate, message = await self.can_generate_sequence(telegram_id)
        
        if not can_generate:
            return False, message
        
        api = await self._api_subscription(telegram_id)
        subscription = self.get_user_subscription(telegram_id)
        
        # Для премиум-пользователей из API не считаем лимиты
        if api and api.get("is_active"):
            return True, "✅ Генерация успешна"
        
        # Для премиум-пользователей локально не считаем лимиты
        if subscription.is_subscription_active() or subscription.is_trial_active():
            return True, "✅ Генерация успешна"
        
        # Для бесплатных пользователей считаем лимиты
        if subscription.increment_daily_generations():
            self.update_subscription(subscription)
            return True, "✅ Генерация успешна"
        
        return False, "❌ Лимит генераций на сегодня исчерпан"
    
    async def get_subscription_info(self, telegram_id: int) -> dict:
        """Получает информацию о подписке пользователя"""
        api = await self._api_subscription(telegram_id)
        subscription = self.get_user_subscription(telegram_id)
        
        is_active = False
        is_trial = False
        status = "🆓 Бесплатная версия"
        days_left = 0
        subscription_type = subscription.subscription_type
        
        if api is not None:
            is_active = bool(api.get("is_active"))
            is_trial = bool(api.get("is_trial"))
            subscription_type = api.get("subscription_type") or subscription_type
            
            if is_active:
                status = "🎯 Пробный период" if is_trial else "⭐ Премиум"
                end_iso = api.get("subscription_end")
                if end_iso:
                    try:
                        end_dt = datetime.fromisoformat(end_iso)
                        days_left = max(0, (end_dt - datetime.utcnow()).days)
                    except Exception:
                        days_left = 0
        else:
            is_active = subscription.has_premium_access()
            is_trial = subscription.is_trial_active()
            
            if is_active:
                if subscription.subscription_type == SubscriptionType.TRIAL.value:
                    status = "🎯 Пробный период"
                    days_left = (subscription.trial_end - datetime.utcnow()).days if subscription.trial_end else 0
                else:
                    status = "⭐ Премиум"
                    days_left = (subscription.subscription_end - datetime.utcnow()).days if subscription.subscription_end else 0
        
        can_generate, gen_message = await self.can_generate_sequence(telegram_id)
        
        return {
            'status': status,
            'is_active': is_active,
            'is_trial': is_trial,
            'days_left': max(0, days_left),
            'subscription_type': subscription_type,
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
