from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum


class AsanaDifficulty(Enum):
    """Сложность асан"""
    BEGINNER = 1
    INTERMEDIATE = 2  
    ADVANCED = 3
    EXPERT = 4
    MASTER = 5

    @classmethod
    def get_stars(cls, difficulty: int) -> str:
        """Получить звездное представление сложности"""
        return "⭐" * difficulty

    @classmethod
    def get_description(cls, difficulty: int) -> str:
        """Получить описание сложности"""
        descriptions = {
            1: "Начальный",
            2: "Средний", 
            3: "Продвинутый",
            4: "Экспертный",
            5: "Мастерский"
        }
        return descriptions.get(difficulty, "Неизвестно")


class AsanaEffect(Enum):
    """Эффекты от асан"""
    BACK_PAIN = "back_pain"
    CALM_MIND = "calm_mind"
    BOOST_ENERGY = "boost_energy"
    DIGESTION = "digestion"
    FLEXIBILITY = "flexibility"
    BALANCE = "balance"
    STRENGTH = "strength"
    STRESS_RELIEF = "stress_relief"

    @classmethod
    def get_emoji(cls, effect: str) -> str:
        """Получить эмодзи для эффекта"""
        emoji_map = {
            "back_pain": "🦴",
            "calm_mind": "🧘",
            "boost_energy": "⚡",
            "digestion": "🌿",
            "flexibility": "🤸",
            "balance": "⚖️",
            "strength": "💪",
            "stress_relief": "😌"
        }
        return emoji_map.get(effect, "🎯")

    @classmethod
    def get_description(cls, effect: str) -> str:
        """Получить описание эффекта"""
        descriptions = {
            "back_pain": "Снять боль в спине",
            "calm_mind": "Успокоить ум",
            "boost_energy": "Повысить энергию",
            "digestion": "Улучшить пищеварение",
            "flexibility": "Повысить гибкость",
            "balance": "Улучшить баланс",
            "strength": "Укрепить мышцы",
            "stress_relief": "Снять стресс"
        }
        return descriptions.get(effect, "Улучшить самочувствие")


@dataclass
class AsanaData:
    """Расширенная модель для хранения данных об асане"""
    name: str
    description: str
    image_path: str
    thumbnail_path: Optional[str] = None
    category: str = ""
    difficulty: int = AsanaDifficulty.BEGINNER.value
    effects: List[str] = None
    contraindications: List[str] = None
    video_path: Optional[str] = None  # Для будущей платной версии
    anatomy_overlay: Optional[str] = None  # Для будущей платной версии


@dataclass
class UserPreferences:
    """Предпочтения пользователя для фильтров"""
    difficulty: Optional[int] = None
    effects: List[str] = None
    focus_area: Optional[str] = None


@dataclass
class CategoryData:
    """Модель для хранения данных о категории асан"""
    name: str
    display_name: str
    description: str
    asanas: List[str]


@dataclass
class BotData:
    """Модель для хранения всех данных бота"""
    categories: Dict[str, CategoryData]
    basics: List[str]
    steps: List[str]
    asana_descriptions: Dict[str, List[str]]
