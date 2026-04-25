#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram import types

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
        
        # Регистрация обработчиков сразу в конструкторе
        self._register_handlers()
    
    def _register_handlers(self):
        """Регистрирует все обработчики"""
        logger.info("Starting handler registration...")
        
        # Команды
        self.dp.message(Command('start'))(self.command_handlers.start_command)
        self.dp.message(Command('help'))(self.command_handlers.help_command)
        self.dp.message(Command('what'))(self.command_handlers.what_command)
        self.dp.message(Command('info'))(self.command_handlers.info_command)
        self.dp.message(Command('about_us'))(self.command_handlers.about_us_command)
        logger.info("Commands registered")
        
        # Callback запросы
        self.dp.callback_query(F.data == 'catalog')(self.callback_handlers.catalog_callback)
        self.dp.callback_query(F.data == 'basics')(self.callback_handlers.basics_callback)
        self.dp.callback_query(F.data == 'steps')(self.callback_handlers.steps_callback)
        self.dp.callback_query(F.data == 'random_asana')(self.callback_handlers.random_asana_callback)
        self.dp.callback_query(F.data == 'about')(self.callback_handlers.about_callback)
        self.dp.callback_query(F.data == 'filter_menu')(self.callback_handlers.filter_menu_callback)
        self.dp.callback_query(F.data == 'filter_difficulty_menu')(self.callback_handlers.filter_difficulty_menu_callback)
        self.dp.callback_query(F.data == 'filter_effect_menu')(self.callback_handlers.filter_effect_menu_callback)
        self.dp.callback_query(F.data == 'filter_reset_all')(self.callback_handlers.filter_reset_all_callback)
        self.dp.callback_query(F.data == 'daily_asana')(self.callback_handlers.daily_asana_callback)
        self.dp.callback_query(F.data == 'main_menu')(self.callback_handlers.main_menu_callback)
        logger.info("Basic callbacks registered")
        self.dp.callback_query(F.data == 'back')(self.callback_handlers.back_callback)
        logger.info("Basic callbacks registered")
        
        # Таймер
        self.dp.callback_query(F.data == 'timer_main')(self.callback_handlers.timer_handlers.timer_main_callback)
        self.dp.callback_query(F.data == 'timer_meditation')(self.callback_handlers.timer_handlers.meditation_callback)
        self.dp.callback_query(F.data == 'timer_asana')(self.callback_handlers.timer_handlers.asana_callback)
        self.dp.callback_query(F.data == 'timer_pranayama')(self.callback_handlers.timer_handlers.pranayama_callback)
        self.dp.callback_query(F.data == 'timer_back')(self.callback_handlers.timer_handlers.timer_back_callback)
        self.dp.callback_query(F.data == 'timer_exit')(self.callback_handlers.timer_handlers.timer_exit_callback)
        
        # Асаны - регистрируем ПОСЛЕ отладочного обработчика
        logger.info("Registering asana config handlers...")
        self.dp.callback_query(F.data == 'asana_config')(self.callback_handlers.timer_handlers.asana_config_callback)
        self.dp.callback_query(F.data == 'asana_config_work')(self.callback_handlers.timer_handlers.asana_config_work_callback)
        self.dp.callback_query(F.data == 'asana_config_rest')(self.callback_handlers.timer_handlers.asana_config_rest_callback)
        self.dp.callback_query(F.data == 'asana_config_cycles')(self.callback_handlers.timer_handlers.asana_config_cycles_callback)
        self.dp.callback_query(F.data == 'asana_start')(self.callback_handlers.timer_handlers.asana_start_callback)
        logger.info("Asana config handlers registered")
        
        # Пранаяма
        self.dp.callback_query(F.data == 'pranayama_config')(self.callback_handlers.timer_handlers.pranayama_config_callback)
        self.dp.callback_query(F.data == 'pranayama_exercises')(self.callback_handlers.timer_handlers.pranayama_exercises_callback)
        self.dp.callback_query(F.data == 'pranayama_exercise_time')(self.callback_handlers.timer_handlers.pranayama_exercise_time_callback)
        self.dp.callback_query(F.data == 'pranayama_rest_time')(self.callback_handlers.timer_handlers.pranayama_rest_time_callback)
        self.dp.callback_query(F.data == 'pranayama_start')(self.callback_handlers.timer_handlers.pranayama_start_callback)
        
        for exercises in [1, 2, 3, 4, 5, 6, 7, 8]:
            self.dp.callback_query(F.data == f'pranayama_exercises_{exercises}')(self.callback_handlers.timer_handlers.pranayama_exercises_select_callback)
        
        for time in [10, 15, 20, 30, 45, 60, 90, 120]:
            self.dp.callback_query(F.data == f'pranayama_exercise_time_{time}')(self.callback_handlers.timer_handlers.pranayama_exercise_time_select_callback)
        
        for time in [5, 10, 15, 20, 30, 45, 60]:
            self.dp.callback_query(F.data == f'pranayama_rest_time_{time}')(self.callback_handlers.timer_handlers.pranayama_rest_time_select_callback)
        
        # Медитация
        for minutes in [1, 5, 10, 15, 20, 30, 45, 60]:
            self.dp.callback_query(F.data == f'meditation_{minutes}')(self.callback_handlers.timer_handlers.meditation_start_callback)
        
        self.dp.callback_query(F.data == 'meditation_custom')(self.callback_handlers.timer_handlers.meditation_custom_callback)
        
        for duration in [30, 45, 60, 90, 120, 180]:
            self.dp.callback_query(F.data == f'asana_work_{duration}')(self.callback_handlers.timer_handlers.asana_work_callback)
        
        for duration in [10, 15, 20, 30, 45, 60]:
            self.dp.callback_query(F.data == f'asana_rest_{duration}')(self.callback_handlers.timer_handlers.asana_rest_callback)
        
        for cycles in [3, 5, 7, 10, 15, 20]:
            self.dp.callback_query(F.data == f'asana_cycles_{cycles}')(self.callback_handlers.timer_handlers.asana_cycles_callback)
        
        # Управление таймером
        self.dp.callback_query(F.data.startswith('timer_'))(self.callback_handlers.timer_handlers.timer_control_callback)
        
        # Фильтры асан
        self.dp.callback_query(F.data.startswith('filter_difficulty_'))(self.callback_handlers.filter_handlers.filter_difficulty_callback)
        self.dp.callback_query(F.data.startswith('filter_effect_'))(self.callback_handlers.filter_handlers.filter_effect_callback)
        self.dp.callback_query(F.data.startswith('fa_'))(self.callback_handlers.filter_handlers.filtered_asana_callback)
        
        # Динамические callback запросы
        data = self.callback_handlers.data_service.load_data()
        
        # Категории асан
        for i, category_name in enumerate(data.categories.keys()):
            self.dp.callback_query(F.data == f'category_{i}')(self.callback_handlers.category_callback)
        
        # Асаны - глобальная регистрация
        data = self.callback_handlers.data_service.load_data()
        global_asana_index = 0
        for category in data.categories.values():
            for i, asana in enumerate(category.asanas):
                self.dp.callback_query(F.data == f'asana_{global_asana_index}')(self.callback_handlers.asana_callback)
                global_asana_index += 1
        
        # Основы йоги
        for i, basic in enumerate(data.basics):
            self.dp.callback_query(F.data == f'basic_{i}')(self.callback_handlers.basic_item_callback)
        
        # Ступени йоги
        for i, step in enumerate(data.steps):
            self.dp.callback_query(F.data == f'step_{i}')(self.callback_handlers.step_item_callback)
        
        # Обработчик ручного ввода времени медитации - ставим ПЕРВЫМ
        self.dp.message()(self.callback_handlers.timer_handlers.handle_meditation_time_input)
        
        # Текстовые сообщения
        self.dp.message()(self.message_handlers.text_message)
        
        # Универсальный отладочный обработчик - ставим ПОСЛЕ всех остальных
        logger.info("Registering debug callback handler...")
        # self.dp.callback_query()(self.debug_callback)  # Временно отключаем
        logger.info("Debug callback handler registered")
        logger.info("Handler registration completed!")
    
    async def start(self):
        """Запускает бота"""
        logger.info("Starting YogaBot...")
        
        # Запускаем фоновую задачу обновления таймеров
        asyncio.create_task(self.callback_handlers.timer_handlers.start_timer_update_loop())
        
        await self.dp.start_polling(self.bot, skip_updates=True)

    async def debug_callback(self, callback_query: types.CallbackQuery):
        """Отладочный обработчик для всех остальных callback'ов"""
        logger.info(f"DEBUG: Received callback: {callback_query.data}")
        await self.bot.answer_callback_query(callback_query.id)
        await self.bot.send_message(
            callback_query.from_user.id,
            f"DEBUG: Получен callback: {callback_query.data}\nЭтот callback не обработан."
        )


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
