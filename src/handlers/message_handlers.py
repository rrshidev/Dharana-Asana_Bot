import logging
from aiogram import types

from src.services.data_service import DataService
from src.utils.keyboard_service import KeyboardService

logger = logging.getLogger(__name__)


class MessageHandlers:
    """Обработчики текстовых сообщений"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_service = DataService()
        self.keyboard_service = KeyboardService()
    
    async def text_message(self, message: types.Message):
        """Обработчик текстовых сообщений"""
        text = message.text.title()
        
        # Проверяем, является ли текст названием асаны
        asana_data = self.data_service.get_asana_data(text)
        
        if asana_data:
            await self._send_asana_data(message, asana_data)
        else:
            await message.answer(
                'Проверь название или воспользуйся каталогом асан!',
                reply_markup=self.keyboard_service.create_main_menu()
            )
    
    async def _send_asana_data(self, message: types.Message, asana_data):
        """Отправляет данные асаны"""
        try:
            await self.bot.send_message(message.from_user.id, asana_data.description)
            
            if asana_data.image_path:
                from aiogram.types.input_file import FSInputFile
                await self.bot.send_photo(message.from_user.id, FSInputFile(asana_data.image_path))
            
            await message.reply('Каталог', reply_markup=self.keyboard_service.create_main_menu())
        except Exception as e:
            logger.error(f"Error sending asana data: {e}")
            await message.reply(
                f'Ошибка при загрузке асаны: {e}',
                reply_markup=self.keyboard_service.create_main_menu()
            )
