import random
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from aiogram import Bot
from aiogram.enums import ParseMode

from src.models.data_models import AsanaData, AsanaDifficulty, AsanaEffect, UserPreferences
from src.services.data_service import DataService
from src.i18n import t
from src.services.database_service import db_service

logger = logging.getLogger(__name__)

_DIFF_TEXT_KEYS = {
    1: 'flt_diff_1',
    2: 'flt_diff_2',
    3: 'flt_diff_3',
    4: 'flt_diff_4',
    5: 'flt_diff_5',
}

_EFFECT_TEXT_KEYS = {
    'back_pain': 'flt_effect_back_pain',
    'calm_mind': 'flt_effect_calm_mind',
    'boost_energy': 'flt_effect_boost_energy',
    'digestion': 'flt_effect_digestion',
    'flexibility': 'flt_effect_flexibility',
    'balance': 'flt_effect_balance',
    'strength': 'flt_effect_strength',
    'stress_relief': 'flt_effect_stress_relief',
}


class FilterService:
    """Сервис для работы с фильтрами и асаной дня"""
    
    def __init__(self, data_service: DataService):
        self.data_service = data_service
        self.daily_asana = {}  # user_id -> (asana_name, date)
    
    def get_difficulty_filter_keyboard(self, current_difficulty: Optional[int] = None, lang: str = 'ru') -> Dict:
        """Получить клавиатуру для фильтра сложности"""
        keyboard = []
        
        for difficulty in range(1, 6):
            stars = AsanaDifficulty.get_stars(difficulty)
            description = t(lang, _DIFF_TEXT_KEYS.get(difficulty, 'flt_diff_unknown'))
            
            if current_difficulty == difficulty:
                text = f"✅ {stars} {description}"
            else:
                text = f"{stars} {description}"
            
            keyboard.append([{
                "text": text,
                "callback_data": f"filter_difficulty_{difficulty}"
            }])
        
        # Добавляем кнопку "Сбросить"
        if current_difficulty:
            keyboard.append([{
                "text": t(lang, 'flt_btn_reset_filter'),
                "callback_data": "filter_difficulty_reset"
            }])
        
        keyboard.append([{
            "text": t(lang, 'btn_back'),
            "callback_data": "filter_menu"
        }])
        
        return {"inline_keyboard": keyboard}
    
    def get_effect_filter_keyboard(self, current_effects: Optional[List[str]] = None, lang: str = 'ru') -> Dict:
        """Получить клавиатуру для фильтра эффектов"""
        keyboard = []
        
        # Основные эффекты для фильтрации
        main_effects = [
            AsanaEffect.BACK_PAIN.value,
            AsanaEffect.CALM_MIND.value,
            AsanaEffect.BOOST_ENERGY.value,
            AsanaEffect.DIGESTION.value,
            AsanaEffect.FLEXIBILITY.value,
            AsanaEffect.BALANCE.value,
            AsanaEffect.STRENGTH.value,
            AsanaEffect.STRESS_RELIEF.value
        ]
        
        for effect in main_effects:
            emoji = AsanaEffect.get_emoji(effect)
            description = t(lang, _EFFECT_TEXT_KEYS.get(effect, 'flt_effect_unknown'))
            
            if current_effects and effect in current_effects:
                text = f"✅ {emoji} {description}"
            else:
                text = f"{emoji} {description}"
            
            keyboard.append([{
                "text": text,
                "callback_data": f"filter_effect_{effect}"
            }])
        
        # Добавляем кнопку "Сбросить"
        if current_effects:
            keyboard.append([{
                "text": t(lang, 'flt_btn_reset_filter'),
                "callback_data": "filter_effect_reset"
            }])
        
        keyboard.append([{
            "text": t(lang, 'btn_back'),
            "callback_data": "filter_menu"
        }])
        
        return {"inline_keyboard": keyboard}
    
    def filter_asanas(self, asanas: List[AsanaData], preferences: UserPreferences) -> List[AsanaData]:
        """Отфильтровать асаны по предпочтениям пользователя"""
        filtered_asanas = asanas.copy()
        
        # Фильтр по сложности
        if preferences.difficulty:
            filtered_asanas = [
                asana for asana in filtered_asanas 
                if asana.difficulty == preferences.difficulty
            ]
        
        # Фильтр по эффектам
        if preferences.effects:
            filtered_asanas = [
                asana for asana in filtered_asanas 
                if asana.effects and all(effect in asana.effects for effect in preferences.effects)
            ]
        
        return filtered_asanas
    
    def get_daily_asana(self, user_id: int) -> Optional[AsanaData]:
        """Получить асану дня для пользователя"""
        today = datetime.now().date()
        
        # Проверяем, есть ли уже асана дня для сегодня
        if user_id in self.daily_asana:
            asana_name, asana_date = self.daily_asana[user_id]
            if asana_date == today:
                # Возвращаем сохраненную асану
                all_asanas = self.data_service.get_all_asanas()
                for asana in all_asanas:
                    if asana.name == asana_name:
                        return asana
        
        # Выбираем новую случайную асану
        all_asanas = self.data_service.get_all_asanas()
        if not all_asanas:
            return None
        
        daily_asana = random.choice(all_asanas)
        self.daily_asana[user_id] = (daily_asana.name, today)
        
        logger.info(f"Generated daily asana '{daily_asana.name}' for user {user_id}")
        return daily_asana
    
    def get_asana_with_premium_hint(self, asana: AsanaData, user_id: int) -> Tuple[str, bool]:
        """Получить описание асаны с подсказкой о платной версии"""
        lang = db_service.get_user_language(user_id)
        description = asana.description
        
        # Проверяем сложность асаны
        needs_premium_hint = asana.difficulty >= AsanaDifficulty.EXPERT.value
        
        # Проверяем противопоказания
        has_contraindications = asana.contraindications and len(asana.contraindications) > 0
        
        # Формируем текст с подсказками
        if needs_premium_hint or has_contraindications:
            premium_hints = []
            
            if needs_premium_hint:
                premium_hints.append(t(lang, 'flt_hint_hard'))
            
            if has_contraindications:
                premium_hints.append(t(lang, 'flt_hint_contraindications'))
            
            if premium_hints:
                description += f"\n\n{' '.join(premium_hints)}\n"
                description += t(lang, 'flt_premium_block_title')
                description += t(lang, 'flt_premium_item_video')
                description += t(lang, 'flt_premium_item_variants')
                description += t(lang, 'flt_premium_item_alt')
                description += t(lang, 'flt_premium_cta')
        
        return description, needs_premium_hint or has_contraindications
    
    def should_show_premium_offer(self, user_id: int, asana_name: str, view_count: int = 3) -> bool:
        """Проверить, нужно ли показать предложение о платной версии"""
        # Если пользователь просмотрел одну и ту же асану несколько раз
        # TODO: В будущем это будет работать с базой данных просмотров
        return view_count >= 3
    
    def get_premium_offer_text(self, asana_name: str, lang: str = 'ru') -> str:
        """Получить текст предложения о платной версии"""
        return (
            t(lang, 'flt_offer_title', name=asana_name) +
            t(lang, 'flt_offer_block_title') +
            t(lang, 'flt_offer_item_variations', name=asana_name) +
            t(lang, 'flt_offer_item_video') +
            t(lang, 'flt_offer_item_mistakes') +
            t(lang, 'flt_offer_item_personal') +
            t(lang, 'flt_offer_cta')
        )


class AsanaDayNotifier:
    """Сервис для уведомлений об асане дня"""
    
    def __init__(self, bot: Bot, filter_service: FilterService):
        self.bot = bot
        self.filter_service = filter_service
        self.notified_users = set()  # Пользователи, которых уже уведомили сегодня
    
    async def send_daily_asana(self, user_id: int):
        """Отправить асану дня пользователю"""
        if user_id in self.notified_users:
            return  # Уже уведомляли сегодня
        
        daily_asana = self.filter_service.get_daily_asana(user_id)
        if not daily_asana:
            return
        
        description, has_premium_hint = self.filter_service.get_asana_with_premium_hint(
            daily_asana, user_id
        )
        
        lang = db_service.get_user_language(user_id)
        
        try:
            await self.bot.send_photo(
                chat_id=user_id,
                photo=daily_asana.image_path,
                caption=f"{t(lang, 'daily_asana_title')}\n\n"
                       f"**{daily_asana.name}**\n\n"
                       f"{description}\n\n"
                       f"{t(lang, 'flt_difficulty_full', stars=AsanaDifficulty.get_stars(daily_asana.difficulty), difficulty=t(lang, _DIFF_TEXT_KEYS.get(daily_asana.difficulty, 'flt_diff_unknown')))}\n"
                       f"{t(lang, 'flt_practice_today')}",
                reply_markup={
                    "inline_keyboard": [[
                        {"text": t(lang, 'flt_btn_all_asanas'), "callback_data": "catalog"},
                        {"text": t(lang, 'flt_btn_another_asana'), "callback_data": "random_asana"}
                    ]]
                },
                parse_mode=ParseMode.MARKDOWN
            )
            
            self.notified_users.add(user_id)
            logger.info(f"Sent daily asana to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending daily asana to user {user_id}: {e}")
    
    def reset_daily_notifications(self):
        """Сбросить ежедневные уведомления"""
        self.notified_users.clear()
        logger.info("Reset daily notifications")