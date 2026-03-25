import logging
import os
from aiogram import types
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
        """Обработчик выбора категории асан"""
        await self.bot.answer_callback_query(callback_query.id)
        
        data = self.data_service.load_data()
        category_name = callback_query.data
        
        if category_name not in data.categories:
            await self.bot.send_message(
                callback_query.from_user.id,
                'Категория не найдена',
                reply_markup=self.keyboard_service.create_main_menu()
            )
            return
        
        category = data.categories[category_name]
        await self.bot.send_message(
            callback_query.from_user.id,
            f'{category.description} приведен ниже.\n'
            'Нажми кнопку с искомой асаной\nПолучишь её фото и описание!'
        )
        
        # Отправляем каждую асану с миниатюрой и кнопкой
        for asana in category.asanas:
            await self._send_asana_with_thumbnail(callback_query.from_user.id, asana, category_name)
    
    async def asana_callback(self, callback_query: types.CallbackQuery):
        """Обработчик выбора асаны"""
        await self.bot.answer_callback_query(callback_query.id)
        
        asana_data = self.data_service.get_asana_data(callback_query.data)
        
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
        keyboard = self.keyboard_service.create_simple_menu(data.basics)
        
        await self.bot.send_message(
            callback_query.from_user.id,
            'Основные понятия и термины йоги:',
            reply_markup=keyboard
        )
    
    async def basic_item_callback(self, callback_query: types.CallbackQuery):
        """Обработчик выбора основы йоги"""
        await self.bot.answer_callback_query(callback_query.id)
        
        content, image_path = self.data_service.get_basic_content(callback_query.data)
        
        if not content:
            await self.bot.send_message(
                callback_query.from_user.id,
                'Содержимое не найдено',
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
        keyboard = self.keyboard_service.create_simple_menu(data.steps)
        
        await self.bot.send_message(
            callback_query.from_user.id,
            '8 ступеней йоги:',
            reply_markup=keyboard
        )
    
    async def step_item_callback(self, callback_query: types.CallbackQuery):
        """Обработчик выбора ступени йоги"""
        await self.bot.answer_callback_query(callback_query.id)
        
        content = self.data_service.get_step_content(callback_query.data)
        
        if not content:
            await self.bot.send_message(
                callback_query.from_user.id,
                'Содержимое не найдено',
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
