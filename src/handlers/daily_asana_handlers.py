import logging
from datetime import time
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.services.database_service import db_service
from src.services.data_service import DataService
from src.services.daily_asana_scheduler import DailyAsanaScheduler
from src.utils.keyboard_service import KeyboardService

logger = logging.getLogger(__name__)

class DailyAsanaHandlers:
    """Обработчики для асаны дня"""
    
    def __init__(self, bot, data_service: DataService):
        self.bot = bot
        self.data_service = data_service
        self.keyboard_service = KeyboardService()
        self.scheduler = DailyAsanaScheduler(bot, data_service)
    
    async def start_scheduler(self):
        """Запустить планировщик"""
        await self.scheduler.start_scheduler()
    
    def stop_scheduler(self):
        """Остановить планировщик"""
        self.scheduler.stop_scheduler()
    
    async def daily_asana_command(self, message: types.Message):
        """Команда /asana_day - показать асану дня с настройкой"""
        user_id = message.from_user.id
        
        # Регистрируем/обновляем пользователя в БД
        user = db_service.get_or_create_user(
            telegram_id=user_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
        
        # Проверяем, первый ли это раз (получаем свежие данные из БД)
        fresh_user = db_service.get_user(telegram_id=user_id)
        if fresh_user and fresh_user.last_daily_asana_date is None:
            # Первый раз - показываем приветствие и настройку
            await self._show_first_time_setup(user_id, message.message_id)
        else:
            # Не первый раз - показываем настройки асаны дня
            settings_text = (
                f"⏰ **Настройки асаны дня**\n\n"
                f"Текущее время: {fresh_user.daily_asana_time.strftime('%H:%M') if fresh_user.daily_asana_time else '09:00'}\n"
                f"Часовой пояс: {fresh_user.timezone if fresh_user.timezone else 'UTC'}\n"
                f"Статус: {'✅ Включено' if fresh_user.daily_asana_enabled else '❌ Выключено'}\n\n"
                f"Выберите время для получения асаны дня:"
            )
            
            keyboard = self._create_time_selection_keyboard()
            
            await message.answer(
                settings_text,
                reply_markup=keyboard
            )
    
    async def daily_asana_command_from_callback(self, callback_query: types.CallbackQuery):
        """Команда асаны дня из callback (главное меню)"""
        await self.bot.answer_callback_query(callback_query.id)
        
        user_id = callback_query.from_user.id
        
        # Регистрируем/обновляем пользователя в БД
        user = db_service.get_or_create_user(
            telegram_id=user_id,
            username=callback_query.from_user.username,
            first_name=callback_query.from_user.first_name,
            last_name=callback_query.from_user.last_name
        )
        
        # Проверяем, первый ли это раз (получаем свежие данные из БД)
        fresh_user = db_service.get_user(telegram_id=user_id)
        if fresh_user and fresh_user.last_daily_asana_date is None:
            # Первый раз - показываем приветствие и настройку
            await self._show_first_time_setup(user_id, callback_query.message.message_id)
        else:
            # Не первый раз - показываем настройки через существующий callback
            await self.daily_asana_settings_callback(callback_query)
    
    async def _show_first_time_setup(self, user_id: int, message_id: int = None):
        """Показать приветствие и настройку для первого раза"""
        welcome_text = (
            "🌅 **Добро пожаловать в Асану Дня!**\n\n"
            "Это ежедневная практика для вашей йоги:\n\n"
            "✅ **Каждый день** новая асана в удобное время\n"
            "✅ **Автоматические уведомления** - не нужно помнить\n"
            "✅ **Премиум-подсказки** для сложных асан\n"
            "✅ **Статистика прогресса** и мотивация\n\n"
            "🎯 **Выберите время для ежедневной практики:**"
        )
        
        keyboard = self._create_welcome_time_keyboard()
        
        if message_id:
            # Редактируем существующее сообщение
            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=welcome_text,
                reply_markup=keyboard
            )
        else:
            # Отправляем новое сообщение
            await self.bot.send_message(
                chat_id=user_id,
                text=welcome_text,
                reply_markup=keyboard
            )
    
    async def daily_asana_settings_callback(self, callback_query: types.CallbackQuery):
        """Обработчик настроек времени асаны дня"""
        await self.bot.answer_callback_query(callback_query.id)
        
        user_id = callback_query.from_user.id
        
        # Получаем текущие настройки (свежие данные)
        user = db_service.get_user(telegram_id=user_id)
        if not user:
            user = db_service.get_or_create_user(telegram_id=user_id)
        
        current_time = user.daily_asana_time.strftime("%H:%M") if user.daily_asana_time else "09:00"
        current_timezone = user.timezone if user.timezone else 'UTC'
        
        settings_text = (
            f"⏰ **Настройки асаны дня**\n\n"
            f"Текущее время: {current_time}\n"
            f"Часовой пояс: {current_timezone}\n"
            f"Статус: {'✅ Включено' if user.daily_asana_enabled else '❌ Выключено'}\n\n"
            f"Выберите время для получения асаны дня:"
        )
        
        # Создаем клавиатуру с выбором времени
        keyboard = self._create_time_selection_keyboard()
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=settings_text,
            reply_markup=keyboard
        )
    
    async def daily_asana_time_callback(self, callback_query: types.CallbackQuery):
        """Обработчик выбора времени"""
        await self.bot.answer_callback_query(callback_query.id)
        
        data = callback_query.data.split('_')
        if len(data) < 4:
            return
        
        hour = int(data[3])
        minute = int(data[4]) if len(data) > 4 else 0
        
        user_id = callback_query.from_user.id
        new_time = time(hour=hour, minute=minute)
        
        # Обновляем настройки
        success = db_service.update_daily_asana_settings(
            telegram_id=user_id,
            asana_time=new_time
        )
        
        if success:
            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=callback_query.message.message_id,
                text=f"✅ Время изменено на {new_time.strftime('%H:%M')}\n\n"
                       f"Теперь я буду присылать вам асану дня в {new_time.strftime('%H:%M')}!\n\n"
                       f"Хотите настроить что-то еще?",
                reply_markup=self._create_settings_menu_keyboard()
            )
        else:
            await self.bot.answer_callback_query(
                callback_query.id,
                text="Ошибка при сохранении времени",
                show_alert=True
            )
    
    async def daily_welcome_time_callback(self, callback_query: types.CallbackQuery):
        """Обработчик выбора времени из приветствия"""
        await self.bot.answer_callback_query(callback_query.id)
        
        data = callback_query.data.split('_')
        if len(data) < 5:
            return
        
        hour = int(data[3])
        minute = int(data[4]) if len(data) > 4 else 0
        
        user_id = callback_query.from_user.id
        new_time = time(hour=hour, minute=minute)
        
        # Обновляем настройки
        success = db_service.update_daily_asana_settings(
            telegram_id=user_id,
            asana_time=new_time,
            enabled=True  # Включаем уведомления
        )
        
        if success:
            # Показываем подтверждение и первую асану
            confirmation_text = (
                f"✅ **Отлично! Настройки сохранены**\n\n"
                f"⏰ Время: {new_time.strftime('%H:%M')}\n"
                f"📅 Ежедневные уведомления: включены\n\n"
                f"🎯 **Ваша первая асана дня:**"
            )
            
            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=callback_query.message.message_id,
                text=confirmation_text
            )
            
            # Отправляем первую асану дня
            user = db_service.get_user(telegram_id=user_id)
            if user:
                await self.scheduler.send_daily_asana_to_user(user)
        else:
            await self.bot.answer_callback_query(
                callback_query.id,
                text="Ошибка при сохранении времени",
                show_alert=True
            )
    
    async def daily_asana_disable_callback(self, callback_query: types.CallbackQuery):
        """Обработчик отключения уведомлений"""
        await self.bot.answer_callback_query(callback_query.id)
        
        user_id = callback_query.from_user.id
        
        # Отключаем уведомления
        success = db_service.update_daily_asana_settings(
            telegram_id=user_id,
            enabled=False
        )
        
        if success:
            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=callback_query.message.message_id,
                text="❌ Уведомления асаны дня отключены\n\n"
                       "Вы всегда можете включить их снова в настройках.\n\n"
                       "Хотите посмотреть другие функции?",
                reply_markup=self.keyboard_service.create_main_menu()
            )
    
    async def daily_timezone_settings_callback(self, callback_query: types.CallbackQuery):
        """Обработчик настроек часового пояса"""
        await self.bot.answer_callback_query(callback_query.id)
        
        user_id = callback_query.from_user.id
        
        # Получаем текущие настройки
        user = db_service.get_user(telegram_id=user_id)
        if not user:
            user = db_service.get_or_create_user(telegram_id=user_id)
        
        current_timezone = user.timezone or 'UTC'
        
        timezone_text = (
            f"🌍 **Настройки часового пояса**\n\n"
            f"Текущий часовой пояс: {current_timezone}\n\n"
            f"Выберите ваш часовой пояс:"
        )
        
        # Создаем клавиатуру с популярными часовыми поясами
        keyboard = self._create_timezone_keyboard()
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=timezone_text,
            reply_markup=keyboard
        )
    
    async def daily_timezone_select_callback(self, callback_query: types.CallbackQuery):
        """Обработчик выбора часового пояса"""
        await self.bot.answer_callback_query(callback_query.id)
        
        data = callback_query.data.split('_')
        if len(data) < 4:
            return
        
        timezone = data[3]
        user_id = callback_query.from_user.id
        
        # Обновляем часовой пояс
        success = db_service.update_daily_asana_settings(
            telegram_id=user_id,
            timezone=timezone
        )
        
        if success:
            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=callback_query.message.message_id,
                text=f"✅ Часовой пояс изменен на {timezone}\n\n"
                       f"Теперь асаны будут приходить с учетом вашего времени.\n\n"
                       f"Хотите настроить что-то еще?",
                reply_markup=self._create_settings_menu_keyboard()
            )
        else:
            await self.bot.answer_callback_query(
                callback_query.id,
                text="Ошибка при сохранении часового пояса",
                show_alert=True
            )
    
    def _create_timezone_keyboard(self):
        """Создать клавиатуру выбора часового пояса"""
        keyboard = []
        
        # Популярные часовые пояса России и СНГ
        timezones = [
            ("🌍 Калининград (UTC+1)", "UTC+1"),
            ("🌍 Москва (UTC+3)", "UTC+3"),
            ("🌍 Самара (UTC+4)", "UTC+4"),
            ("🌍 Екатеринбург (UTC+5)", "UTC+5"),
            ("🌍 Омск (UTC+6)", "UTC+6"),
            ("🌍 Красноярск (UTC+7)", "UTC+7"),
            ("🌍 Иркутск (UTC+8)", "UTC+8"),
            ("🌍 Якутск (UTC+9)", "UTC+9"),
            ("🌍 Владивосток (UTC+10)", "UTC+10"),
            ("🌍 Магадан (UTC+11)", "UTC+11"),
            ("🌍 Камчатка (UTC+12)", "UTC+12"),
        ]
        
        for text, tz in timezones:
            keyboard.append([{
                "text": text,
                "callback_data": f"daily_timezone_select_{tz}"
            }])
        
        keyboard.append([{
            "text": "🔙 Назад",
            "callback_data": "daily_asana_settings"
        }])
        
        return {"inline_keyboard": keyboard}
    
    async def daily_practice_callback(self, callback_query: types.CallbackQuery):
        """Обработчик начала практики из асаны дня"""
        logger.info(f"DEBUG: daily_practice_callback received: {callback_query.data}")
        await self.bot.answer_callback_query(callback_query.id)
        
        # Проверяем, это базовый callback или custom
        if callback_query.data.startswith('daily_practice_custom_'):
            # Это custom callback - обрабатываем отдельно
            logger.info("DEBUG: This is a custom practice callback")
            # TODO: Реализовать custom обработку
            return
        
        data = callback_query.data.split('_', 2)
        logger.info(f"DEBUG: Split data: {data}")
        
        if len(data) < 3:
            logger.error(f"DEBUG: Not enough data parts: {len(data)}")
            return
        
        # Получаем ID пользователя из callback
        user_id = callback_query.from_user.id
        
        # Получаем последнюю асану дня для этого пользователя из БД
        user = db_service.get_user(telegram_id=user_id)
        if not user or not user.last_daily_asana_date:
            logger.error("DEBUG: No user or no last daily asana found")
            await self.bot.send_message(user_id, "Ошибка: не найдена последняя асана дня")
            return
        
        # Получаем асану для сегодняшней даты (используем тот же метод, что и в планировщике)
        import random
        from datetime import date
        today = date.today()
        # Используем дату как seed, чтобы получить ту же асану, что и в рассылке
        random.seed(today.toordinal())
        asana_data = self.scheduler.data_service.get_random_asana()
        
        if not asana_data:
            logger.error("DEBUG: No asana data found for today")
            await self.bot.send_message(user_id, "Ошибка: не найдена асана для сегодня")
            return
        
        asana_name = asana_data.name
        logger.info(f"DEBUG: Using asana name: {asana_name}")
        
        # Показываем меню настройки таймера для асаны
        practice_text = (
            f"🕐 **Практика: {asana_name}**\n\n"
            f"Настройте таймер для вашей практики:\n\n"
            f"⏱️ **Время выполнения асаны** (в секундах)\n"
            f"⏸️ **Время отдыха** (в секундах)\n"
            f"🔄 **Количество циклов** (0 = бесконечно)\n\n"
            f"Выберите время работы:"
        )
        
        # Создаем клавиатуру с вариантами времени
        keyboard = []
        work_times = [
            ("30 сек", 30), ("1 мин", 60), ("2 мин", 120), 
            ("3 мин", 180), ("5 мин", 300), ("10 мин", 600)
        ]
        
        for text, time in work_times:
            keyboard.append([{
                "text": text,
                "callback_data": f"daily_practice_work_{user_id}_{time}"
            }])
        
        keyboard.append([{
            "text": "⏰ Указать свое время",
            "callback_data": f"daily_practice_custom_{user_id}"
        }])
        
        keyboard.append([{
            "text": "🔙 Назад",
            "callback_data": "daily_asana"
        }])
        
        await self.bot.send_message(
            chat_id=user_id,
            text=practice_text,
            reply_markup={"inline_keyboard": keyboard}
        )
    
    async def daily_practice_work_callback(self, callback_query: types.CallbackQuery):
        """Обработчик выбора времени работы для практики"""
        await self.bot.answer_callback_query(callback_query.id)
        
        data = callback_query.data.split('_')
        if len(data) < 5:
            return
        
        # Получаем параметры из callback
        user_id = int(data[3])
        work_time = int(data[4])
        
        # Получаем асану для сегодняшней даты (используем тот же метод, что и в планировщике)
        import random
        from datetime import date
        today = date.today()
        # Используем дату как seed, чтобы получить ту же асану, что и в рассылке
        random.seed(today.toordinal())
        asana_data = self.scheduler.data_service.get_random_asana()
        
        if not asana_data:
            logger.error("DEBUG: No asana data found for today")
            await self.bot.send_message(user_id, "Ошибка: не найдена асана для сегодня")
            return
        
        asana_name = asana_data.name
        
        # Показываем меню выбора времени отдыха
        rest_text = (
            f"🕐 **Практика: {asana_name}**\n\n"
            f"Время работы: {work_time // 60} мин {work_time % 60} сек\n\n"
            f"Выберите время отдыха:"
        )
        
        keyboard = []
        rest_times = [
            ("10 сек", 10), ("15 сек", 15), ("30 сек", 30), 
            ("1 мин", 60), ("2 мин", 120)
        ]
        
        for text, time in rest_times:
            keyboard.append([{
                "text": text,
                "callback_data": f"daily_practice_rest_{user_id}_{work_time}_{time}"
            }])
        
        keyboard.append([{
            "text": "⏰ Указать свое время",
            "callback_data": f"daily_practice_custom_rest_{user_id}_{work_time}"
        }])
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=rest_text,
            reply_markup={"inline_keyboard": keyboard}
        )
    
    async def daily_practice_rest_callback(self, callback_query: types.CallbackQuery):
        """Обработчик выбора времени отдыха для практики"""
        await self.bot.answer_callback_query(callback_query.id)
        
        data = callback_query.data.split('_')
        if len(data) < 6:
            return
        
        # Получаем параметры из callback
        user_id = int(data[3])
        work_time = int(data[4])
        rest_time = int(data[5])
        
        # Получаем асану для сегодняшней даты (используем тот же метод, что и в планировщике)
        import random
        from datetime import date
        today = date.today()
        # Используем дату как seed, чтобы получить ту же асану, что и в рассылке
        random.seed(today.toordinal())
        asana_data = self.scheduler.data_service.get_random_asana()
        
        if not asana_data:
            logger.error("DEBUG: No asana data found for today")
            await self.bot.send_message(user_id, "Ошибка: не найдена асана для сегодня")
            return
        
        asana_name = asana_data.name
        
        # Показываем меню выбора количества циклов
        cycles_text = (
            f"🕐 **Практика: {asana_name}**\n\n"
            f"Время работы: {work_time // 60} мин {work_time % 60} сек\n"
            f"Время отдыха: {rest_time // 60} мин {rest_time % 60} сек\n\n"
            f"Выберите количество циклов:"
        )
        
        keyboard = []
        cycles = [
            ("1 цикл", 1), ("3 цикла", 3), ("5 циклов", 5), 
            ("7 циклов", 7), ("10 циклов", 10), ("Бесконечно", 0)
        ]
        
        for text, count in cycles:
            keyboard.append([{
                "text": text,
                "callback_data": f"daily_practice_start_{user_id}_{work_time}_{rest_time}_{count}"
            }])
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=cycles_text,
            reply_markup={"inline_keyboard": keyboard}
        )
    
    async def daily_practice_start_callback(self, callback_query: types.CallbackQuery):
        """Обработчик запуска практики асаны"""
        await self.bot.answer_callback_query(callback_query.id)
        
        data = callback_query.data.split('_')
        if len(data) < 7:
            return
        
        # Получаем параметры из callback
        user_id = int(data[3])
        work_time = int(data[4])
        rest_time = int(data[5])
        cycles = int(data[6])
        
        # Получаем асану для сегодняшней даты (используем тот же метод, что и в планировщике)
        import random
        from datetime import date
        today = date.today()
        # Используем дату как seed, чтобы получить ту же асану, что и в рассылке
        random.seed(today.toordinal())
        asana_data = self.scheduler.data_service.get_random_asana()
        
        if not asana_data:
            logger.error("DEBUG: No asana data found for today")
            await self.bot.send_message(user_id, "Ошибка: не найдена асана для сегодня")
            return
        
        asana_name = asana_data.name
        
        # Увеличиваем счетчик практик
        db_service.increment_practice_count(user_id)
        
        # Запускаем таймер через существующий обработчик
        await self._start_asana_timer(user_id, asana_name, work_time, rest_time, cycles, callback_query.message.message_id)
    
    async def _start_asana_timer(self, user_id: int, asana_name: str, work_time: int, rest_time: int, cycles: int, message_id: int):
        """Запускает таймер для практики асаны"""
        cycles_text = "бесконечно" if cycles == 0 else f"{cycles} циклов"
        start_text = (
            f"🕐 **Практика: {asana_name}**\n\n"
            f"⏱️ Работа: {work_time // 60} мин {work_time % 60} сек\n"
            f"⏸️ Отдых: {rest_time // 60} мин {rest_time % 60} сек\n"
            f"🔄 Циклы: {cycles_text}\n\n"
            f"🧘 Начинаем практику! Сосредоточьтесь на дыхании.\n\n"
            f"Первый цикл начался!"
        )
        
        keyboard = [
            [{"text": "⏹️ Стоп", "callback_data": "timer_stop"}],
            [{"text": "🔙 Назад", "callback_data": "daily_asana"}]
        ]
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=message_id,
            text=start_text,
            reply_markup={"inline_keyboard": keyboard}
        )
        
        # Запускаем таймер через существующий сервис с полноценным UI
        from src.services.timer_service import timer_service
        from src.models.timer_models import TimerConfig, timer_messages
        from src.utils.timer_ui import TimerUI
        
        # Создаем конфигурацию таймера
        config = TimerConfig(
            work_duration=work_time,
            rest_duration=rest_time,
            cycles=cycles
        )
        
        # Создаем и запускаем таймер
        session = timer_service.create_asana_timer(user_id, config)
        timer_service.start_timer(user_id)
        
        # Отправляем сообщение с UI таймера
        work_text = f"{session.work_duration}с" if session.work_duration < 60 else f"{session.work_duration//60}м"
        rest_text = f"{session.rest_duration}с" if session.rest_duration < 60 else f"{session.rest_duration//60}м"
        cycles_text = "бесконечно" if session.cycles == 0 else str(session.cycles)
        
        message = await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=message_id,
            text=f"🧘‍♂️ **Практика: {asana_name} начата!**\n\n"
            f"⏱️ Работа: {work_text}\n"
            f"⏸️ Отдых: {rest_text}\n"
            f"🔄 Циклы: {cycles_text}\n\n"
            "Начинаем с первого подхода! 💪",
            reply_markup=TimerUI.get_control_keyboard(session)
        )
        
        # Сохраняем ID сообщения для редактирования таймером
        timer_messages[user_id] = message_id
    
    async def premium_upgrade_callback(self, callback_query: types.CallbackQuery):
        """Обработчики премиум-апгрейдов"""
        await self.bot.answer_callback_query(callback_query.id)
        
        data = callback_query.data.split('_')
        upgrade_type = data[2] if len(data) > 2 else 'general'
        
        user_id = callback_query.from_user.id
        
        # Формируем текст в зависимости от типа апгрейда
        if upgrade_type == 'easy':
            text = (
                "🌟 **Откройте облегченные варианты асан!**\n\n"
                "В премиум-версии вы получите:\n"
                "• 📹 Видео с подготовительными упражнениями\n"
                "• 🔄 3 уровня сложности каждой асаны\n"
                "• 🛡️ Безопасные прогрессии\n\n"
                "💰 **399₽/месяц или 2990₽/год**\n\n"
                "Хотите начать безопасную практику?"
            )
        elif upgrade_type == 'safe':
            text = (
                "🛡️ **Практикуйте безопасно!**\n\n"
                "В премиум-версии:\n"
                "• ⚠️ Индивидуальные противопоказания\n"
                "• 🔄 Безопасные альтернативы сложных асан\n"
                "• 👨‍⚕️ Рекомендации по модификациям\n\n"
                "💰 **399₽/месяц или 2990₽/год**\n\n"
                "Ваше здоровье - это инвестиция!"
            )
        elif upgrade_type == 'video':
            text = (
                "📹 **Детальная видео-отстройка!**\n\n"
                "В премиум-версии:\n"
                "• 🎥 Качественные видео для каждой асаны\n"
                "• 🏗️ Анатомические 3D-схемы\n"
                "• ❌ Разбор типичных ошибок\n\n"
                "💰 **399₽/месяц или 2990₽/год**\n\n"
                "Изучайте асаны профессионально!"
            )
        else:
            text = (
                "🌟 **Откройте все возможности йоги!**\n\n"
                "В премиум-версии:\n"
                "• 📹 Видео-инструкции для всех асан\n"
                "• 🎯 Генератор персональных комплексов\n"
                "• 📊 Статистика и прогресс\n"
                "• 🧘 Готовые программы под цели\n\n"
                "💰 **399₽/месяц или 2990₽/год**\n\n"
                "Начните свой путь в йоге профессионально!"
            )
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💳 Оформить подписку", callback_data="premium_buy_monthly")],
                [InlineKeyboardButton(text="💰 Годовая подписка (экономия 25%)", callback_data="premium_buy_yearly")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
            ]
        )
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            reply_markup=keyboard
        )
    
    def _create_welcome_time_keyboard(self):
        """Создать клавиатуру выбора времени для первого раза"""
        keyboard = []
        
        # Популярные времена с описаниями
        popular_times = [
            ("🌅 Раннее утро (6:00)", 6, 0),
            ("☀️ Утро (7:00)", 7, 0),
            ("🌤️ Завтрак (8:00)", 8, 0),
            ("🌞 Начало дня (9:00)", 9, 0),
            ("🌅 Перед работой (10:00)", 10, 0),
            ("🌤️ Обед (13:00)", 13, 0),
            ("🌆 После работы (18:00)", 18, 0),
            ("🌙 Вечер (20:00)", 20, 0),
            ("🌛 Перед сном (21:00)", 21, 0),
        ]
        
        for text, hour, minute in popular_times:
            keyboard.append([{
                "text": text,
                "callback_data": f"daily_welcome_time_{hour}_{minute}"
            }])
        
        keyboard.append([{
            "text": "⏰ Ввести время вручную",
            "callback_data": "daily_time_manual_welcome"
        }])
        
        keyboard.append([{
            "text": "⏰ Настроить другое время",
            "callback_data": "daily_asana_settings"
        }])
        
        keyboard.append([{
            "text": "🔙 В главное меню",
            "callback_data": "main_menu"
        }])
        
        return {"inline_keyboard": keyboard}
    
    def _create_time_selection_keyboard(self):
        """Создать клавиатуру выбора времени"""
        keyboard = []
        
        # Популярные времена
        popular_times = [
            ("🌅 Утро (7:00)", 7, 0),
            ("☀️ Раннее утро (8:00)", 8, 0),
            ("🌤️ Начало дня (9:00)", 9, 0),
            ("🌞 Перед работой (10:00)", 10, 0),
            ("🌅 Обед (12:00)", 12, 0),
            ("🌤️ После работы (18:00)", 18, 0),
            ("🌆 Вечер (20:00)", 20, 0),
            ("🌙 Перед сном (21:00)", 21, 0),
        ]
        
        for text, hour, minute in popular_times:
            keyboard.append([{
                "text": text,
                "callback_data": f"daily_time_set_{hour}_{minute}"
            }])
        
        keyboard.append([{
            "text": "⏰ Ввести время вручную",
            "callback_data": "daily_time_manual"
        }])
        
        # Добавляем кнопки управления
        keyboard.append([{
            "text": "🌍 Часовой пояс",
            "callback_data": "daily_timezone_settings"
        }])
        
        keyboard.append([{
            "text": "🔕 Отключить уведомления",
            "callback_data": "daily_asana_disable"
        }])
        
        keyboard.append([{
            "text": "🔙 В главное меню",
            "callback_data": "main_menu"
        }])
        
        return {"inline_keyboard": keyboard}
    
    async def daily_time_manual_callback(self, callback_query: types.CallbackQuery):
        """Обработчик запроса ручного ввода времени"""
        await self.bot.answer_callback_query(callback_query.id)
        
        user_id = callback_query.from_user.id
        
        manual_text = (
            "⏰ **Введите время вручную**\n\n"
            "Пожалуйста, введите время в формате ЧЧ:ММ\n"
            "Например: 14:30 или 09:15\n\n"
            "⚠️ Время должно быть в 24-часовом формате"
        )
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="daily_asana_settings")]
            ]
        )
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=manual_text,
            reply_markup=keyboard
        )
        
        # Устанавливаем состояние ожидания ввода времени
        # Здесь можно использовать FSM, но для простоты используем временное хранилище
        self.waiting_for_time_input = user_id
    
    async def daily_time_manual_welcome_callback(self, callback_query: types.CallbackQuery):
        """Обработчик запроса ручного ввода времени из приветствия"""
        await self.bot.answer_callback_query(callback_query.id)
        
        user_id = callback_query.from_user.id
        
        manual_text = (
            "⏰ **Введите время вручную**\n\n"
            "Пожалуйста, введите время в формате ЧЧ:ММ\n"
            "Например: 14:30 или 09:15\n\n"
            "⚠️ Время должно быть в 24-часовом формате"
        )
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="daily_asana_settings")]
            ]
        )
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=manual_text,
            reply_markup=keyboard
        )
        
        # Устанавливаем состояние ожидания ввода времени
        self.waiting_for_time_input = user_id
    
    async def handle_time_input(self, message: types.Message):
        """Обработчик текстового ввода времени"""
        user_id = message.from_user.id
        
        # Проверяем, ожидаем ли мы ввод времени от этого пользователя
        if not hasattr(self, 'waiting_for_time_input') or self.waiting_for_time_input != user_id:
            return
        
        # Парсим время
        time_text = message.text.strip()
        
        try:
            # Проверяем формат ЧЧ:ММ
            if ':' not in time_text:
                raise ValueError("Неверный формат")
            
            hour_str, minute_str = time_text.split(':')
            hour = int(hour_str)
            minute = int(minute_str)
            
            # Проверяем диапазон
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError("Неверное время")
            
            # Сохраняем время
            from datetime import time as time_class
            new_time = time_class(hour=hour, minute=minute)
            
            success = db_service.update_daily_asana_settings(
                telegram_id=user_id,
                asana_time=new_time,
                enabled=True
            )
            
            if success:
                confirmation_text = (
                    f"✅ **Отлично! Настройки сохранены**\n\n"
                    f"⏰ Время: {new_time.strftime('%H:%M')}\n"
                    f"📅 Ежедневные уведомления: включены\n\n"
                    f"🎯 Асана дня будет приходить каждый день в {new_time.strftime('%H:%M')}\n\n"
                    f"Хотите получить асану дня прямо сейчас?"
                )
                
                await message.answer(
                    confirmation_text,
                    reply_markup={"inline_keyboard": [[
                        {"text": "🕐 Получить асану дня", "callback_data": "daily_asana_now"},
                        {"text": "🔙 В главное меню", "callback_data": "main_menu"}
                    ]]}
                )
            else:
                await message.answer("❌ Ошибка при сохранении времени")
                
        except ValueError as e:
            await message.answer(
                f"❌ Неверный формат времени!\n\n"
                f"Пожалуйста, введите время в формате ЧЧ:ММ\n"
                f"Например: 14:30 или 09:15\n"
                f"Часы: 0-23, Минуты: 0-59"
            )
        finally:
            # Сбрасываем флаг ожидания ввода
            if hasattr(self, 'waiting_for_time_input'):
                delattr(self, 'waiting_for_time_input')
    
    async def daily_asana_now_callback(self, callback_query: types.CallbackQuery):
        """Обработчик получения асаны дня прямо сейчас"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        
        # Получаем пользователя и отправляем асану дня
        user = db_service.get_user(telegram_id=user_id)
        if user:
            await self.scheduler.send_daily_asana_to_user(user)
        else:
            await self.bot.send_message(user_id, "❌ Ошибка: пользователь не найден")
        
        # Сбрасываем состояние ожидания
        if hasattr(self, 'waiting_for_time_input'):
            delattr(self, 'waiting_for_time_input')
    
    def _create_settings_menu_keyboard(self):
        """Создать клавиатуру меню настроек"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⏰ Изменить время", callback_data="daily_asana_settings")],
                [InlineKeyboardButton(text="🌍 Изменить часовой пояс", callback_data="daily_timezone_settings")],
                [InlineKeyboardButton(text="🔕 Отключить уведомления", callback_data="daily_asana_disable")],
                [InlineKeyboardButton(text="🔙 В главное меню", callback_data="main_menu")]
            ]
        )
