import logging
import os
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types.input_file import FSInputFile

from src.services.data_service import DataService
from src.utils.keyboard_service import KeyboardService

logger = logging.getLogger(__name__)


class CallbackHandlers:
    """Обработчики callback запросов"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_service = DataService()
        self.keyboard_service = KeyboardService()
    
    async def catalog_callback(self, callback_query: types.CallbackQuery):
        """Обработчик открытия каталога"""
        await self.bot.answer_callback_query(callback_query.id)
        
        data = self.data_service.load_data()
        categories = list(data.categories.values())
        
        keyboard = self.keyboard_service.create_categories_menu(categories)
        await self.bot.send_message(
            callback_query.from_user.id, 
            'Разделы асан:', 
            reply_markup=keyboard
        )
    
    async def category_callback(self, callback_query: types.CallbackQuery):
        """Обработчик открытия категории асан"""
        await self.bot.answer_callback_query(callback_query.id)
        
        # Получаем имя категории по ID
        category_name = self.data_service.get_category_by_id(callback_query.data)
        if not category_name:
            await self.bot.send_message(
                callback_query.from_user.id,
                'Категория не найдена',
                reply_markup=self.keyboard_service.create_main_menu()
            )
            return
        
        data = self.data_service.load_data()
        category = data.categories[category_name]
        
        # Получаем глобальный стартовый индекс для категории
        start_index = self.data_service.get_category_global_start_index(category_name)
        
        await self.bot.send_message(
            callback_query.from_user.id,
            f'{category.description} приведен ниже.\n'
            'Нажми кнопку с искомой асаной\nПолучишь её фото и описание!'
        )
        
        # Отправляем меню асан
        asanas_menu = self.keyboard_service.create_asanas_menu(category.asanas, start_index)
        await self.bot.send_message(
            callback_query.from_user.id,
            'Выбери асану:',
            reply_markup=asanas_menu
        )
    
    async def asana_callback(self, callback_query: types.CallbackQuery):
        """Обработчик выбора асаны"""
        await self.bot.answer_callback_query(callback_query.id)
        
        # Получаем имя асаны по ID
        asana_name = self.data_service.get_asana_by_id(callback_query.data)
        logger.info(f"Callback data: {callback_query.data} -> Asana name: {asana_name}")
        
        if not asana_name:
            await self.bot.send_message(
                callback_query.from_user.id,
                'Асана не найдена',
                reply_markup=self.keyboard_service.create_main_menu()
            )
            return
        
        asana_data = self.data_service.get_asana_data(asana_name)
        
        if not asana_data:
            await self.bot.send_message(
                callback_query.from_user.id,
                'Асана не найдена',
                reply_markup=self.keyboard_service.create_main_menu()
            )
            return
        
        await self._send_asana_full(callback_query.from_user.id, asana_data, callback_query.message)
    
    async def random_asana_callback(self, callback_query: types.CallbackQuery):
        """Обработчик случайной асаны"""
        await self.bot.answer_callback_query(callback_query.id)
        
        asana_data = self.data_service.get_random_asana()
        
        if not asana_data:
            await self.bot.send_message(
                callback_query.from_user.id,
                'Не удалось загрузить асану',
                reply_markup=self.keyboard_service.create_main_menu()
            )
            return
        
        await self._send_asana_full(callback_query.from_user.id, asana_data)
    
    async def basics_callback(self, callback_query: types.CallbackQuery):
        """Обработчик открытия основ йоги"""
        await self.bot.answer_callback_query(callback_query.id)
        
        data = self.data_service.load_data()
        keyboard = self.keyboard_service.create_simple_menu(data.basics, 'basic')
        
        await self.bot.send_message(
            callback_query.from_user.id,
            'Основные понятия и термины йоги:',
            reply_markup=keyboard
        )
    
    async def basic_item_callback(self, callback_query: types.CallbackQuery):
        """Обработчик выбора основы йоги"""
        await self.bot.answer_callback_query(callback_query.id)
        
        # Получаем имя основы по ID
        basic_name = self.data_service.get_basic_by_id(callback_query.data)
        if not basic_name:
            await self.bot.send_message(
                callback_query.from_user.id,
                'Основы не найдены',
                reply_markup=self.keyboard_service.create_main_menu()
            )
            return
        
        content, image_path = self.data_service.get_basic_content(basic_name)
        
        if not content:
            await self.bot.send_message(
                callback_query.from_user.id,
                f'Содержимое не найдено для: {basic_name}',
                reply_markup=self.keyboard_service.create_main_menu()
            )
            return
        
        await self._send_long_text_with_image(
            callback_query.from_user.id,
            content,
            image_path,
            'Раздел йоги:'
        )
    
    async def steps_callback(self, callback_query: types.CallbackQuery):
        """Обработчик открытия ступеней йоги"""
        await self.bot.answer_callback_query(callback_query.id)
        
        data = self.data_service.load_data()
        keyboard = self.keyboard_service.create_simple_menu(data.steps, 'step')
        
        await self.bot.send_message(
            callback_query.from_user.id,
            '8 ступеней йоги:',
            reply_markup=keyboard
        )
    
    async def step_item_callback(self, callback_query: types.CallbackQuery):
        """Обработчик выбора ступени йоги"""
        await self.bot.answer_callback_query(callback_query.id)
        
        # Получаем имя ступени по ID
        step_name = self.data_service.get_step_by_id(callback_query.data)
        if not step_name:
            await self.bot.send_message(
                callback_query.from_user.id,
                'Ступень не найдена',
                reply_markup=self.keyboard_service.create_main_menu()
            )
            return
        
        content = self.data_service.get_step_content(step_name)
        
        if not content:
            await self.bot.send_message(
                callback_query.from_user.id,
                f'Содержимое не найдено для: {step_name}',
                reply_markup=self.keyboard_service.create_main_menu()
            )
            return
        
        await self._send_long_text(
            callback_query.from_user.id,
            content,
            'Ступень йоги:'
        )
    
    async def _send_asana_with_thumbnail(self, user_id: int, asana_name: str, category_name: str):
        """Отправляет асану с миниатюрой"""
        # Находим ID для асаны через маппинг
        asana_id = None
        data = self.data_service.load_data()
        for i, name in enumerate(data.categories[category_name].asanas):
            if name == asana_name:
                asana_id = f'asana_{i}'
                break
        
        if asana_id:
            # Создаем кнопку с ID
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text=asana_name, callback_data=asana_id)]]
            )
        else:
            # Если ID не найден, создаем кнопку без ID
            keyboard = self.keyboard_service.create_asana_button(asana_name)
        
        # Пытаемся отправить миниатюру .png
        png_path = os.path.normpath(
            os.path.join("bot_data", "catalog", category_name, f'{asana_name}.png')
        )
        
        try:
            await self.bot.send_photo(
                user_id,
                FSInputFile(png_path),
                caption=f'Йогическая поза: {asana_name}',
                reply_markup=keyboard
            )
        except FileNotFoundError:
            # Если миниатюра не найдена, отправляем только кнопку
            await self.bot.send_message(
                user_id,
                f'Йогическая поза: {asana_name}',
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error sending thumbnail for {asana_name}: {e}")
            await self.bot.send_message(
                user_id,
                f'Йогическая поза: {asana_name}',
                reply_markup=keyboard
            )
    
    async def _send_asana_full(self, user_id: int, asana_data, message=None):
        """Отправляет полное описание асаны с фото"""
        try:
            await self.bot.send_message(user_id, asana_data.description)
            
            if asana_data.image_path and os.path.exists(asana_data.image_path):
                await self.bot.send_photo(user_id, FSInputFile(asana_data.image_path))
            
            if message:
                await message.reply('Каталог', reply_markup=self.keyboard_service.create_main_menu())
            else:
                await self.bot.send_message(
                    user_id, 
                    text='Каталог', 
                    reply_markup=self.keyboard_service.create_main_menu()
                )
        except Exception as e:
            logger.error(f"Error sending asana {asana_data.name}: {e}")
            await self.bot.send_message(
                user_id,
                f'Ошибка при загрузке асаны: {e}',
                reply_markup=self.keyboard_service.create_main_menu()
            )
    
    async def _send_long_text(self, user_id: int, text: str, title: str):
        """Отправляет длинный текст частями"""
        await self.bot.send_message(user_id, title)
        
        if len(text) > 4096:
            for i in range(0, len(text), 4096):
                await self.bot.send_message(user_id, text[i:i+4096])
        else:
            await self.bot.send_message(user_id, text)
        
        await self.bot.send_message(
            user_id,
            text='Каталог',
            reply_markup=self.keyboard_service.create_main_menu()
        )
    
    async def back_callback(self, callback_query: types.CallbackQuery):
        """Обработчик кнопки назад"""
        await self.bot.answer_callback_query(callback_query.id)
        await self.bot.send_message(
            callback_query.from_user.id,
            'Выберите раздел:',
            reply_markup=self.keyboard_service.create_main_menu()
        )
    
    async def about_callback(self, callback_query: types.CallbackQuery):
        """Обработчик информации о боте"""
        await self.bot.answer_callback_query(callback_query.id)
        await self.bot.send_message(
            callback_query.from_user.id,
            '🧘‍♂️ Йога Асана Бот\n\n'
            'Этот бот поможет тебе изучить асаны йоги, их описание и правильное выполнение.\n\n'
            'Доступные разделы:\n'
            '📚 Каталог асан - полный список поз с фотографиями\n'
            '🧘 Основы йоги - базовые понятия и термины\n'
            '📈 Ступени йоги - 8 уровней практики\n'
            '🎲 Случайная асана - случайная поза для практики\n\n'
            'Создан с любовью к йоге 🙏',
            reply_markup=self.keyboard_service.create_main_menu()
        )
    
    async def _send_long_text_with_image(self, user_id: int, text: str, image_path: str, title: str):
        """Отправляет длинный текст с изображением"""
        await self.bot.send_message(user_id, title)
        
        # Сначала отправляем текст
        if len(text) > 4096:
            for i in range(0, len(text), 4096):
                await self.bot.send_message(user_id, text[i:i+4096])
        else:
            await self.bot.send_message(user_id, text)
        
        # Затем изображение, если есть
        if image_path and os.path.exists(image_path):
            try:
                await self.bot.send_photo(user_id, FSInputFile(image_path))
            except Exception as e:
                logger.error(f"Error sending image: {e}")
        
        await self.bot.send_message(
            user_id,
            text='Каталог',
            reply_markup=self.keyboard_service.create_main_menu()
        )
