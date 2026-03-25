#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command

from config import Token
from src.handlers.command_handlers import CommandHandlers
from src.handlers.callback_handlers import CallbackHandlers
from src.handlers.message_handlers import MessageHandlers


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class YogaBot:
    """Основной класс бота"""
    
    def __init__(self, token: str):
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        
        # Инициализация обработчиков
        self.command_handlers = CommandHandlers(self.bot)
        self.callback_handlers = CallbackHandlers(self.bot)
        self.message_handlers = MessageHandlers(self.bot)
        
        # Регистрация обработчиков
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрирует все обработчики"""
        # Команды
        self.dp.message(Command('start'))(self.command_handlers.start_command)
        self.dp.message(Command('help'))(self.command_handlers.help_command)
        self.dp.message(Command('what'))(self.command_handlers.what_command)
        self.dp.message(Command('info'))(self.command_handlers.info_command)
        self.dp.message(Command('about_us'))(self.command_handlers.about_us_command)
        
        # Callback запросы
        self.dp.callback_query(lambda c: c.data == 'catalog')(self.callback_handlers.catalog_callback)
        self.dp.callback_query(lambda c: c.data == 'basics')(self.callback_handlers.basics_callback)
        self.dp.callback_query(lambda c: c.data == 'steps')(self.callback_handlers.steps_callback)
        self.dp.callback_query(lambda c: c.data == 'random_asana')(self.callback_handlers.random_asana_callback)
        
        # Динамические callback запросы
        data_service = self.callback_handlers.data_service
        bot_data = data_service.load_data()
        
        # Категории асан
        for category_name in bot_data.categories.keys():
            self.dp.callback_query(lambda c: c.data == category_name)(self.callback_handlers.category_callback)
        
        # Асаны
        for category in bot_data.categories.values():
            for asana in category.asanas:
                self.dp.callback_query(lambda c: c.data == asana)(self.callback_handlers.asana_callback)
        
        # Основы йоги
        for basic in bot_data.basics:
            self.dp.callback_query(F.data == basic)(self.callback_handlers.basic_item_callback)
        
        # Ступени йоги
        for step in bot_data.steps:
            self.dp.callback_query(F.data == step)(self.callback_handlers.step_item_callback)
        
        # Текстовые сообщения
        self.dp.message()(self.message_handlers.text_message)
    
    async def start(self):
        """Запускает бота"""
        logger.info("Starting YogaBot...")
        await self.dp.start_polling(self.bot, skip_updates=True)


def main():
    """Главная функция"""
    # Проверка наличия токена
    if not Token:
        logger.error("BOT_TOKEN not found in environment variables or .env file")
        sys.exit(1)
    
    # Создание и запуск бота
    bot = YogaBot(Token)
    
    try:
        asyncio.run(bot.start())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
