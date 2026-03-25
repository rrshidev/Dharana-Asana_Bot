from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.models.data_models import CategoryData, BotData


class KeyboardService:
    """Сервис для создания клавиатур"""
    
    @staticmethod
    def create_main_menu() -> InlineKeyboardMarkup:
        """Создает главное меню"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text='!Каталог асан!', callback_data='catalog')],
                [InlineKeyboardButton(text='Основы йоги', callback_data='basics')],
                [InlineKeyboardButton(text='8 ступеней йоги', callback_data='steps')],
                [InlineKeyboardButton(text='Асана дня, согласно карме', callback_data='random_asana')]
            ]
        )
    
    @staticmethod
    def create_categories_menu(categories: List[CategoryData]) -> InlineKeyboardMarkup:
        """Создает меню категорий асан"""
        buttons = []
        for category in categories:
            buttons.append([InlineKeyboardButton(
                text=category.display_name, 
                callback_data=category.name
            )])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def create_asanas_menu(asanas: List[str]) -> InlineKeyboardMarkup:
        """Создает меню асан"""
        buttons = []
        for asana in asanas:
            buttons.append([InlineKeyboardButton(text=asana, callback_data=asana)])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def create_simple_menu(items: List[str]) -> InlineKeyboardMarkup:
        """Создает простое меню из списка"""
        buttons = []
        for item in items:
            buttons.append([InlineKeyboardButton(text=item, callback_data=item)])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def create_asana_button(asana_name: str) -> InlineKeyboardMarkup:
        """Создает кнопку для конкретной асаны"""
        return InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=asana_name, callback_data=asana_name)]]
        )
    
    @staticmethod
    def create_back_menu() -> InlineKeyboardMarkup:
        """Создает кнопку возврата в каталог"""
        return InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text='Каталог', callback_data='catalog')]]
        )
