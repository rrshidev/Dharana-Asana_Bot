from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict

from src.i18n import t
from src.models.data_models import CategoryData, BotData


class KeyboardService:
    """Сервис для создания клавиатур (локализуемо через lang)."""

    @staticmethod
    def create_start_menu(lang: str = 'ru') -> InlineKeyboardMarkup:
        """Создает стартовое меню (быстрые действия после /start)"""
        buttons = [
            [InlineKeyboardButton(text=t(lang, 'btn_home'), callback_data='main_menu')],
            [InlineKeyboardButton(text=t(lang, 'btn_timer'), callback_data='timer_main')],
            [InlineKeyboardButton(text=t(lang, 'btn_random_asana'), callback_data='random_asana')],
            [InlineKeyboardButton(text=t(lang, 'btn_premium'), callback_data='subscription_plans')],
            [InlineKeyboardButton(text=t(lang, 'btn_language'), callback_data='lang_menu')],
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def create_main_menu(lang: str = 'ru') -> InlineKeyboardMarkup:
        """Создает главное меню бота (всё, кроме быстрых действий)"""
        buttons = [
            [InlineKeyboardButton(text=t(lang, 'btn_timer'), callback_data='timer_main')],
            [InlineKeyboardButton(text=t(lang, 'btn_catalog'), callback_data='catalog')],
            [InlineKeyboardButton(text=t(lang, 'btn_ready_sequences'), callback_data='ready_sequences')],
            [InlineKeyboardButton(text=t(lang, 'btn_basics'), callback_data='basics')],
            [InlineKeyboardButton(text=t(lang, 'btn_steps'), callback_data='steps')],
            [InlineKeyboardButton(text=t(lang, 'btn_daily_asana'), callback_data='daily_asana')],
            [InlineKeyboardButton(text=t(lang, 'btn_generator'), callback_data='sequence_menu')],
            [InlineKeyboardButton(text=t(lang, 'btn_filters'), callback_data='filter_menu')],
            [InlineKeyboardButton(text=t(lang, 'btn_start_screen'), callback_data='start_screen')],
            [InlineKeyboardButton(text=t(lang, 'btn_about'), callback_data='about')],
            [InlineKeyboardButton(text=t(lang, 'btn_language'), callback_data='lang_menu')],
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def create_language_menu(lang: str = 'ru') -> InlineKeyboardMarkup:
        """Меню выбора языка бота"""
        buttons = [
            [InlineKeyboardButton(text=t(lang, 'lang_ru'), callback_data='lang_set_ru')],
            [InlineKeyboardButton(text=t(lang, 'lang_en'), callback_data='lang_set_en')],
            [InlineKeyboardButton(text=t(lang, 'btn_back'), callback_data='main_menu')],
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def create_ready_sequences_menu(sequences, lang: str = 'ru') -> InlineKeyboardMarkup:
        """Создает меню готовых комплексов"""
        buttons = []
        for sequence in sequences:
            text = sequence['name']
            callback_data = f'ready_sequence_{sequence["id"]}'
            buttons.append([InlineKeyboardButton(text=text, callback_data=callback_data)])

        # Добавляем кнопку возврата
        buttons.append([InlineKeyboardButton(text=t(lang, 'btn_back'), callback_data='main_menu')])
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def create_categories_menu(categories, lang: str = 'ru') -> InlineKeyboardMarkup:
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

        # Кнопка возврата в главное меню
        buttons.append([InlineKeyboardButton(text=t(lang, 'btn_back_main'), callback_data='main_menu')])
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def create_asanas_menu(asanas: List[str], start_index: int = 0, lang: str = 'ru') -> InlineKeyboardMarkup:
        """Создает меню асан"""
        buttons = []
        for i, asana in enumerate(asanas):
            buttons.append([InlineKeyboardButton(text=asana, callback_data=f'asana_{start_index + i}')])
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def create_simple_menu(items: List[str], prefix: str = '', lang: str = 'ru') -> InlineKeyboardMarkup:
        """Создает простое меню из списка"""
        buttons = []
        for i, item in enumerate(items):
            buttons.append([InlineKeyboardButton(text=item, callback_data=f'{prefix}_{i}')])
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @staticmethod
    def create_back_menu(lang: str = 'ru') -> InlineKeyboardMarkup:
        """Создает кнопку назад"""
        button = [InlineKeyboardButton(text=t(lang, 'btn_back'), callback_data='back')]
        return InlineKeyboardMarkup(inline_keyboard=[button])

    @staticmethod
    def create_asana_button(asana_name: str, lang: str = 'ru') -> InlineKeyboardMarkup:
        """Создает кнопку для конкретной асаны"""
        return InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=asana_name, callback_data=asana_name)]]
        )

    @staticmethod
    def create_back_to_catalog_menu(lang: str = 'ru') -> InlineKeyboardMarkup:
        """Создает кнопку возврата в каталог"""
        return InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=t(lang, 'btn_back_catalog'), callback_data='catalog')]]
        )

    @staticmethod
    def create_back_to_filters_menu(lang: str = 'ru') -> InlineKeyboardMarkup:
        """Создает кнопку возврата к фильтрам"""
        return InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=t(lang, 'btn_back_filters'), callback_data='filter_menu')]]
        )

    @staticmethod
    def create_back_to_main_menu(lang: str = 'ru') -> InlineKeyboardMarkup:
        """Создает кнопку возврата в главное меню"""
        return InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=t(lang, 'btn_back_main'), callback_data='main_menu')]]
        )