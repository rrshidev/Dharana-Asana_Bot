from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict

from src.models.data_models import CategoryData, BotData


class KeyboardService:
    """Сервис для создания клавиатур"""
    
    @staticmethod
    def create_main_menu() -> InlineKeyboardMarkup:
        """Создает главное меню"""
        buttons = [
            [InlineKeyboardButton(text='📚 Каталог асан', callback_data='catalog')],
            [InlineKeyboardButton(text='🧘 Основы йоги', callback_data='basics')],
            [InlineKeyboardButton(text='📈 Ступени йоги', callback_data='steps')],
            [InlineKeyboardButton(text='🎲 Случайная асана', callback_data='random_asana')],
            [InlineKeyboardButton(text='ℹ️ О боте', callback_data='about')],
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def create_categories_menu(categories) -> InlineKeyboardMarkup:
        """Создает меню категорий асан"""
        buttons = []
        for category in categories:
            if isinstance(category, dict):
                # Если это словарь (новый формат)
                text = category['display_name']
                callback_data = f'category_{category.get("id", "")}'
            else:
                # Если это CategoryData (старый формат)
                text = category.display_name
                # Находим индекс категории
                all_categories = list(categories) if all(isinstance(c, dict) for c in categories) else categories
                for i, cat in enumerate(all_categories):
                    if cat == category:
                        callback_data = f'category_{i}'
                        break
                else:
                    callback_data = category.name
            
            buttons.append([InlineKeyboardButton(text=text, callback_data=callback_data)])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def create_asanas_menu(asanas: List[str], start_index: int = 0) -> InlineKeyboardMarkup:
        """Создает меню асан"""
        buttons = []
        for i, asana in enumerate(asanas):
            buttons.append([InlineKeyboardButton(text=asana, callback_data=f'asana_{start_index + i}')])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def create_simple_menu(items: List[str], prefix: str = '') -> InlineKeyboardMarkup:
        """Создает простое меню из списка"""
        buttons = []
        for i, item in enumerate(items):
            buttons.append([InlineKeyboardButton(text=item, callback_data=f'{prefix}_{i}')])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def create_back_menu() -> InlineKeyboardMarkup:
        """Создает кнопку назад"""
        button = [InlineKeyboardButton(text='🔙 Назад', callback_data='back')]
        return InlineKeyboardMarkup(inline_keyboard=[button])
    
    @staticmethod
    def create_asana_button(asana_name: str) -> InlineKeyboardMarkup:
        """Создает кнопку для конкретной асаны"""
        return InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=asana_name, callback_data=asana_name)]]
        )
    
    @staticmethod
    def create_back_to_catalog_menu() -> InlineKeyboardMarkup:
        """Создает кнопку возврата в каталог"""
        return InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text='Каталог', callback_data='catalog')]]
        )
