import logging
from typing import Callable, Awaitable, Any
from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware

from src.services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)

class SubscriptionMiddleware(BaseMiddleware):
    """Middleware для проверки подписки пользователя"""
    
    def __init__(self, subscription_service: SubscriptionService):
        super().__init__()
        self.subscription_service = subscription_service
    
    async def __call__(
        self,
        handler: Callable[[types.TelegramObject], Awaitable[None]],
        event: types.TelegramObject,
        data: dict
    ) -> Any:
        
        # Получаем telegram_id из события
        if hasattr(event, 'from_user'):
            telegram_id = event.from_user.id
        elif hasattr(event, 'chat'):
            telegram_id = event.chat.id
        else:
            # Если не можем получить ID, пропускаем
            return await handler(event, data)
        
        # Получаем информацию о подписке
        subscription_info = self.subscription_service.get_subscription_info(telegram_id)
        
        # Добавляем информацию о подписке в data
        data['subscription'] = subscription_info
        data['is_premium'] = subscription_info['is_active']
        data['can_generate'] = subscription_info['can_generate']
        
        # Логируем для отладки
        logger.debug(f"User {telegram_id}: {subscription_info['status']}")
        
        # Вызываем следующий обработчик
        return await handler(event, data)

class PremiumFeatureMiddleware(BaseMiddleware):
    """Middleware для блокировки премиум-фич"""
    
    def __init__(self, subscription_service: SubscriptionService):
        super().__init__()
        self.subscription_service = subscription_service
    
    async def __call__(
        self,
        handler: Callable[[types.TelegramObject], Awaitable[None]],
        event: types.TelegramObject,
        data: dict
    ) -> Any:
        
        telegram_id = data.get('telegram_id')
        if not telegram_id:
            if hasattr(event, 'from_user'):
                telegram_id = event.from_user.id
            elif hasattr(event, 'chat'):
                telegram_id = event.chat.id
        
        if not telegram_id:
            return await handler(event, data)
        
        # Проверяем доступ к премиум-фиче
        can_access, message = self.subscription_service.can_generate_sequence(telegram_id)
        
        if not can_access:
            # Если нет доступа, отправляем сообщение с предложением подписки
            if isinstance(event, types.CallbackQuery):
                await event.answer(message, show_alert=True)
            elif isinstance(event, types.Message):
                await event.answer(message)
            
            # Не вызываем обработчик
            return None
        
        # Если доступ есть, вызываем обработчик
        return await handler(event, data)
