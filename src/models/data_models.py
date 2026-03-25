from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class AsanaData:
    """Модель для хранения данных об асане"""
    name: str
    description: str
    image_path: str
    thumbnail_path: Optional[str] = None
    category: str = ""


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
