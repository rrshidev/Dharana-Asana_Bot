import logging
import os
from datetime import time
from aiogram import types
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.i18n import t, format_duration, format_cycles
from src.services.database_service import db_service
from src.services.data_service import DataService
from src.services.video_service import VideoService
from src.services.daily_asana_scheduler import DailyAsanaScheduler
from src.utils.keyboard_service import KeyboardService

logger = logging.getLogger(__name__)

class DailyAsanaHandlers:
    """Обработчики для асаны дня"""
    
    def __init__(self, bot, data_service: DataService, subscription_service=None):
        self.bot = bot
        self.data_service = data_service
        self.subscription_service = subscription_service
        self.video_service = VideoService(db_service)
        self.keyboard_service = KeyboardService()
        self.scheduler = DailyAsanaScheduler(bot, data_service)
    
    async def _replace_message(
        self,
        message: types.Message,
        text: str,
        reply_markup=None,
        parse_mode=None,
    ):
        """Отредактировать сообщение, поддерживая фото-caption и обычный текст.

        Сообщение «Асаны дня» отправляется как фото с caption, поэтому
        edit_message_text на нём падает — для медиа нужен edit_message_caption.
        """
        is_media = bool(getattr(message, "photo", None)) or bool(getattr(message, "video", None))
        if is_media:
            await self.bot.edit_message_caption(
                chat_id=message.chat.id,
                message_id=message.message_id,
                caption=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
            )
        else:
            await self.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=message.message_id,
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
            )

    @staticmethod
    def _lang(user_id: int) -> str:
        """Язык пользователя ('ru'|'en')."""
        return db_service.get_user_language(user_id)
    
    async def _send_daily_asana_video(self, message, user_id: int, lang: str, subscription_info):
        """Отправить видео «Асаны дня» премиум-юзеру.

        Видео ищется по последней отправленной юзеру «Асане дня».
        Если видео нет — показываем статус подписки с пояснением.
        """
        asana_name = db_service.get_last_daily_asana(user_id)
        if asana_name:
            video = self.video_service.get_video_for_asana(asana_name, is_premium_user=True)
            if video and video['video_path'] and os.path.exists(video['video_path']):
                from aiogram.types import FSInputFile
                try:
                    await self.bot.send_video(user_id, FSInputFile(video['video_path']))
                    return
                except Exception as e:
                    logger.error(f"Error sending daily asana video: {e}")

        # Видео нет (или не отправилось) — пояснение + статус подписки
        if subscription_info['is_trial']:
            status_text = t(lang, 'sub_status_trial_full').format(
                days_left=subscription_info['days_left'])
        else:
            status_text = t(lang, 'sub_status_premium_full').format(
                days_left=subscription_info['days_left'])

        text = (
            f"{t(lang, 'daily_video_no_video', name=asana_name or '')}\n\n"
            f"{status_text}"
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=t(lang, 'btn_back_main'), callback_data="main_menu")]
            ]
        )
        await self._replace_message(message, text, keyboard, ParseMode.MARKDOWN)

    @staticmethod
    def _format_work_rest_short(lang: str, seconds: int) -> str:
        """'30 сек'/'1 мин' (RU) или '30 s'/'1 min' (EN)."""
        if seconds % 60 == 0:
            return f"{seconds // 60} {t(lang, 'daily_min_label')}"
        return f"{seconds} {t(lang, 'daily_sec_label')}"
    
    @staticmethod
    def _localized_cycles(lang: str, cycles: int) -> str:
        """'бесконечно'/'5 циклов' (RU, как раньше) или 'infinite'/'5 cycles' (EN)."""
        if cycles == 0:
            return t(lang, 'daily_infinite_text')
        if lang == 'en':
            return format_cycles(lang, cycles)
        return f"{cycles} циклов"
    
    async def start_scheduler(self):
        """Запустить планировщик"""
        await self.scheduler.start_scheduler()
    
    def stop_scheduler(self):
        """Остановить планировщик"""
        self.scheduler.stop_scheduler()
    
    async def daily_asana_command(self, message: types.Message):
        """Команда /asana_day - показать асану дня с настройкой"""
        user_id = message.from_user.id
        lang = self._lang(user_id)
        
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
            await self._show_first_time_setup(user_id, message)
        else:
            # Не первый раз - показываем настройки асаны дня
            settings_text = (
                f"{t(lang, 'daily_settings_title')}\n\n"
                f"{t(lang, 'daily_current_time', time=fresh_user.daily_asana_time.strftime('%H:%M') if fresh_user.daily_asana_time else '09:00')}\n"
                f"{t(lang, 'daily_time_zone', tz=fresh_user.timezone if fresh_user.timezone else 'UTC')}\n"
                f"{t(lang, 'daily_status', status=t(lang, 'daily_status_on') if fresh_user.daily_asana_enabled else t(lang, 'daily_status_off'))}\n\n"
                f"{t(lang, 'daily_choose_time')}"
            )
            
            keyboard = self._create_time_selection_keyboard(lang)
            
            await message.answer(
                settings_text,
                parse_mode=ParseMode.MARKDOWN,
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
            await self._show_first_time_setup(user_id, callback_query.message)
        else:
            # Не первый раз - показываем настройки через существующий callback
            await self.daily_asana_settings_callback(callback_query)
    
    async def _show_first_time_setup(self, user_id: int, message=None):
        """Показать приветствие и настройку для первого раза"""
        lang = self._lang(user_id)
        
        welcome_text = (
            f"{t(lang, 'daily_welcome_title')}\n\n"
            f"{t(lang, 'daily_welcome_intro')}\n\n"
            f"{t(lang, 'daily_welcome_li1')}\n"
            f"{t(lang, 'daily_welcome_li2')}\n"
            f"{t(lang, 'daily_welcome_li3')}\n"
            f"{t(lang, 'daily_welcome_li4')}\n\n"
            f"{t(lang, 'daily_welcome_choose')}"
        )
        
        keyboard = self._create_welcome_time_keyboard(lang)
        
        if message:
            # Редактируем существующее сообщение (текст или фото-caption)
            await self._replace_message(message, welcome_text, keyboard, ParseMode.MARKDOWN)
        else:
            # Отправляем новое сообщение
            await self.bot.send_message(
                chat_id=user_id,
                text=welcome_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
    
    async def daily_asana_settings_callback(self, callback_query: types.CallbackQuery):
        """Обработчик настроек времени асаны дня"""
        await self.bot.answer_callback_query(callback_query.id)
        
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)
        
        # Получаем текущие настройки (свежие данные)
        user = db_service.get_user(telegram_id=user_id)
        if not user:
            user = db_service.get_or_create_user(telegram_id=user_id)
        
        current_time = user.daily_asana_time.strftime("%H:%M") if user.daily_asana_time else "09:00"
        current_timezone = user.timezone if user.timezone else 'UTC'
        
        settings_text = (
            f"{t(lang, 'daily_settings_title')}\n\n"
            f"{t(lang, 'daily_current_time', time=current_time)}\n"
            f"{t(lang, 'daily_time_zone', tz=current_timezone)}\n"
            f"{t(lang, 'daily_status', status=t(lang, 'daily_status_on') if user.daily_asana_enabled else t(lang, 'daily_status_off'))}\n\n"
            f"{t(lang, 'daily_choose_time')}"
        )
        
        # Создаем клавиатуру с выбором времени
        keyboard = self._create_time_selection_keyboard(lang)
        
        await self._replace_message(callback_query.message, settings_text, keyboard, ParseMode.MARKDOWN)
    
    async def daily_asana_time_callback(self, callback_query: types.CallbackQuery):
        """Обработчик выбора времени"""
        await self.bot.answer_callback_query(callback_query.id)
        
        data = callback_query.data.split('_')
        if len(data) < 4:
            return
        
        hour = int(data[3])
        minute = int(data[4]) if len(data) > 4 else 0
        
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)
        new_time = time(hour=hour, minute=minute)
        
        # Обновляем настройки
        success = db_service.update_daily_asana_settings(
            telegram_id=user_id,
            asana_time=new_time
        )
        
        if success:
            await self._replace_message(
                callback_query.message,
                t(lang, 'daily_time_changed', time=new_time.strftime('%H:%M')),
                self._create_settings_menu_keyboard(lang),
            )
        else:
            await self.bot.answer_callback_query(
                callback_query.id,
                text=t(lang, 'daily_err_save_time'),
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
        lang = self._lang(user_id)
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
                f"{t(lang, 'daily_saved_ok')}\n\n"
                f"{t(lang, 'daily_saved_time', time=new_time.strftime('%H:%M'))}\n"
                f"{t(lang, 'daily_notif_on')}\n\n"
                f"{t(lang, 'daily_first_asana')}"
            )
            
            await self._replace_message(
                callback_query.message,
                confirmation_text,
                None,
                ParseMode.MARKDOWN,
            )
            
            # Отправляем первую асану дня
            user = db_service.get_user(telegram_id=user_id)
            if user:
                await self.scheduler.send_daily_asana_to_user(user)
        else:
            await self.bot.answer_callback_query(
                callback_query.id,
                text=t(lang, 'daily_err_save_time'),
                show_alert=True
            )
    
    async def daily_asana_disable_callback(self, callback_query: types.CallbackQuery):
        """Обработчик отключения уведомлений"""
        await self.bot.answer_callback_query(callback_query.id)
        
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)
        
        # Отключаем уведомления
        success = db_service.update_daily_asana_settings(
            telegram_id=user_id,
            enabled=False
        )
        
        if success:
            await self._replace_message(
                callback_query.message,
                t(lang, 'daily_disabled'),
                self.keyboard_service.create_main_menu(lang),
            )
    
    async def daily_timezone_settings_callback(self, callback_query: types.CallbackQuery):
        """Обработчик настроек часового пояса"""
        await self.bot.answer_callback_query(callback_query.id)
        
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)
        
        # Получаем текущие настройки
        user = db_service.get_user(telegram_id=user_id)
        if not user:
            user = db_service.get_or_create_user(telegram_id=user_id)
        
        current_timezone = user.timezone or 'UTC'
        
        timezone_text = (
            f"{t(lang, 'daily_tz_title')}\n\n"
            f"{t(lang, 'daily_tz_current', tz=current_timezone)}\n\n"
            f"{t(lang, 'daily_tz_choose')}"
        )
        
        # Создаем клавиатуру с популярными часовыми поясами
        keyboard = self._create_timezone_keyboard(lang)
        
        await self._replace_message(callback_query.message, timezone_text, keyboard, ParseMode.MARKDOWN)
    
    async def daily_timezone_select_callback(self, callback_query: types.CallbackQuery):
        """Обработчик выбора часового пояса"""
        await self.bot.answer_callback_query(callback_query.id)
        
        data = callback_query.data.split('_')
        if len(data) < 4:
            return
        
        timezone = data[3]
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)
        
        # Обновляем часовой пояс
        success = db_service.update_daily_asana_settings(
            telegram_id=user_id,
            timezone=timezone
        )
        
        if success:
            await self._replace_message(
                callback_query.message,
                t(lang, 'daily_tz_changed', tz=timezone),
                self._create_settings_menu_keyboard(lang),
            )
        else:
            await self.bot.answer_callback_query(
                callback_query.id,
                text=t(lang, 'daily_err_save_tz'),
                show_alert=True
            )
    
    def _create_timezone_keyboard(self, lang: str = 'ru'):
        """Создать клавиатуру выбора часового пояса"""
        keyboard = []
        
        # Популярные часовые пояса России и СНГ
        timezones = [
            ("UTC+1", "daily_tz_city_utc1"),
            ("UTC+3", "daily_tz_city_utc3"),
            ("UTC+4", "daily_tz_city_utc4"),
            ("UTC+5", "daily_tz_city_utc5"),
            ("UTC+6", "daily_tz_city_utc6"),
            ("UTC+7", "daily_tz_city_utc7"),
            ("UTC+8", "daily_tz_city_utc8"),
            ("UTC+9", "daily_tz_city_utc9"),
            ("UTC+10", "daily_tz_city_utc10"),
            ("UTC+11", "daily_tz_city_utc11"),
            ("UTC+12", "daily_tz_city_utc12"),
        ]
        
        for tz, key in timezones:
            keyboard.append([{
                "text": t(lang, key),
                "callback_data": f"daily_timezone_select_{tz}"
            }])
        
        keyboard.append([{
            "text": t(lang, 'btn_back'),
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
        lang = self._lang(user_id)
        
        # Получаем последнюю асану дня для этого пользователя из БД
        user = db_service.get_user(telegram_id=user_id)
        if not user or not user.last_daily_asana_date:
            logger.error("DEBUG: No user or no last daily asana found")
            await self.bot.send_message(user_id, t(lang, 'daily_err_no_last'))
            return
        
        # Получаем асану для сегодняшней даты (используем тот же метод, что и в планировщике)
        import random
        from datetime import date
        today = date.today()
        # Используем дату как seed, чтобы получить ту же асану, что и в рассылке
        random.seed(today.toordinal())
        asana_data = self.scheduler.data_service.get_random_asana(lang)
        
        if not asana_data:
            logger.error("DEBUG: No asana data found for today")
            await self.bot.send_message(user_id, t(lang, 'daily_err_no_asana'))
            return
        
        asana_name = asana_data.name
        logger.info(f"DEBUG: Using asana name: {asana_name}")
        
        # Показываем меню настройки таймера для асаны
        await self._show_daily_practice_work_menu(user_id, lang=lang)
    
    async def _show_daily_practice_work_menu(self, user_id: int, message_id: int = None, lang: str = 'ru'):
        """Показать меню выбора времени работы практики"""
        import random
        from datetime import date
        today = date.today()
        # Используем дату как seed, чтобы получить ту же асану, что и в рассылке
        random.seed(today.toordinal())
        asana_data = self.scheduler.data_service.get_random_asana(lang)
        
        if not asana_data:
            logger.error("DEBUG: No asana data found for today")
            await self.bot.send_message(user_id, t(lang, 'daily_err_no_asana'))
            return
        
        asana_name = asana_data.name
        
        # Показываем меню настройки таймера для асаны
        practice_text = t(lang, 'daily_practice_work_menu', title=t(lang, 'daily_practice_title', name=asana_name))
        
        # Создаем клавиатуру с вариантами времени
        keyboard = []
        work_times = [30, 60, 120, 180, 300, 600]
        
        for work in work_times:
            keyboard.append([{
                "text": self._format_work_rest_short(lang, work),
                "callback_data": f"daily_practice_work_{user_id}_{work}"
            }])
        
        keyboard.append([{
            "text": t(lang, 'daily_enter_custom'),
            "callback_data": f"daily_practice_custom_{user_id}"
        }])
        
        keyboard.append([{
            "text": t(lang, 'btn_back'),
            "callback_data": "daily_asana"
        }])
        
        if message_id:
            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=practice_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup={"inline_keyboard": keyboard}
            )
        else:
            await self.bot.send_message(
                chat_id=user_id,
                text=practice_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup={"inline_keyboard": keyboard}
            )
    
    async def daily_practice_work_back_callback(self, callback_query: types.CallbackQuery):
        """Возврат из меню отдыха в меню времени работы"""
        await self.bot.answer_callback_query(callback_query.id)
        
        data = callback_query.data.split('_')
        if len(data) < 5:
            return
        
        user_id = int(data[4])
        await self._show_daily_practice_work_menu(
            user_id,
            message_id=callback_query.message.message_id,
            lang=self._lang(callback_query.from_user.id)
        )
    
    async def daily_practice_rest_back_callback(self, callback_query: types.CallbackQuery):
        """Возврат из меню циклов в меню времени отдыха"""
        await self.bot.answer_callback_query(callback_query.id)
        
        data = callback_query.data.split('_')
        if len(data) < 6:
            return
        
        user_id = int(data[4])
        work_time = int(data[5])
        await self._show_daily_practice_rest_menu(
            user_id,
            work_time,
            callback_query.message.message_id,
            lang=self._lang(callback_query.from_user.id)
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
        lang = self._lang(callback_query.from_user.id)
        
        # Получаем асану для сегодняшней даты (используем тот же метод, что и в планировщике)
        import random
        from datetime import date
        today = date.today()
        # Используем дату как seed, чтобы получить ту же асану, что и в рассылке
        random.seed(today.toordinal())
        asana_data = self.scheduler.data_service.get_random_asana(lang)
        
        if not asana_data:
            logger.error("DEBUG: No asana data found for today")
            await self.bot.send_message(user_id, t(lang, 'daily_err_no_asana'))
            return
        
        asana_name = asana_data.name
        
        # Показываем меню выбора времени отдыха
        await self._show_daily_practice_rest_menu(
            user_id,
            work_time,
            callback_query.message.message_id,
            lang=lang
        )
    
    async def _show_daily_practice_rest_menu(self, user_id: int, work_time: int, message_id: int, lang: str = 'ru'):
        """Показать меню выбора времени отдыха практики"""
        import random
        from datetime import date
        today = date.today()
        # Используем дату как seed, чтобы получить ту же асану, что и в рассылке
        random.seed(today.toordinal())
        asana_data = self.scheduler.data_service.get_random_asana(lang)
        
        if not asana_data:
            logger.error("DEBUG: No asana data found for today")
            await self.bot.send_message(user_id, t(lang, 'daily_err_no_asana'))
            return
        
        asana_name = asana_data.name
        
        rest_text = t(lang, 'daily_rest_menu',
                      title=t(lang, 'daily_practice_title', name=asana_name),
                      work=t(lang, 'daily_dur', m=work_time // 60, s=work_time % 60))
        
        keyboard = []
        rest_times = [10, 15, 30, 60, 120]
        
        for rest in rest_times:
            keyboard.append([{
                "text": self._format_work_rest_short(lang, rest),
                "callback_data": f"daily_practice_rest_{user_id}_{work_time}_{rest}"
            }])
        
        keyboard.append([{
            "text": t(lang, 'daily_enter_custom'),
            "callback_data": f"daily_practice_custom_rest_{user_id}_{work_time}"
        }])
        
        keyboard.append([{
            "text": t(lang, 'btn_back'),
            "callback_data": f"daily_practice_work_back_{user_id}"
        }])
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=message_id,
            text=rest_text,
            parse_mode=ParseMode.MARKDOWN,
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
        lang = self._lang(callback_query.from_user.id)
        
        # Получаем асану для сегодняшней даты (используем тот же метод, что и в планировщике)
        import random
        from datetime import date
        today = date.today()
        # Используем дату как seed, чтобы получить ту же асану, что и в рассылке
        random.seed(today.toordinal())
        asana_data = self.scheduler.data_service.get_random_asana(lang)
        
        if not asana_data:
            logger.error("DEBUG: No asana data found for today")
            await self.bot.send_message(user_id, t(lang, 'daily_err_no_asana'))
            return
        
        asana_name = asana_data.name
        
        # Показываем меню выбора количества циклов
        cycles_text = t(lang, 'daily_cycles_menu',
                        title=t(lang, 'daily_practice_title', name=asana_name),
                        work=t(lang, 'daily_dur', m=work_time // 60, s=work_time % 60),
                        rest=t(lang, 'daily_dur', m=rest_time // 60, s=rest_time % 60))
        
        keyboard = []
        cycle_options = [1, 3, 5, 7, 10, 0]
        
        for count in cycle_options:
            label = t(lang, 'daily_infinite') if count == 0 else format_cycles(lang, count)
            keyboard.append([{
                "text": label,
                "callback_data": f"daily_practice_start_{user_id}_{work_time}_{rest_time}_{count}"
            }])
        
        keyboard.append([{
            "text": t(lang, 'btn_back'),
            "callback_data": f"daily_practice_rest_back_{user_id}_{work_time}"
        }])
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=cycles_text,
            parse_mode=ParseMode.MARKDOWN,
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
        lang = self._lang(callback_query.from_user.id)
        
        # Получаем асану для сегодняшней даты (используем тот же метод, что и в планировщике)
        import random
        from datetime import date
        today = date.today()
        # Используем дату как seed, чтобы получить ту же асану, что и в рассылке
        random.seed(today.toordinal())
        asana_data = self.scheduler.data_service.get_random_asana(lang)
        
        if not asana_data:
            logger.error("DEBUG: No asana data found for today")
            await self.bot.send_message(user_id, t(lang, 'daily_err_no_asana'))
            return
        
        asana_name = asana_data.name
        
        # Увеличиваем счетчик практик
        db_service.increment_practice_count(user_id)
        
        # Запускаем таймер через существующий обработчик
        await self._start_asana_timer(user_id, asana_name, work_time, rest_time, cycles, callback_query.message.message_id, lang)
    
    async def _start_asana_timer(self, user_id: int, asana_name: str, work_time: int, rest_time: int, cycles: int, message_id: int, lang: str = 'ru'):
        """Запускает таймер для практики асаны"""
        cycles_text = self._localized_cycles(lang, cycles)
        start_text = (
            f"{t(lang, 'daily_practice_title', name=asana_name)}\n\n"
            f"{t(lang, 'work_setting', value=t(lang, 'daily_dur', m=work_time // 60, s=work_time % 60))}\n"
            f"{t(lang, 'rest_setting', value=t(lang, 'daily_dur', m=rest_time // 60, s=rest_time % 60))}\n"
            f"{t(lang, 'cycles_setting', value=cycles_text)}\n\n"
            f"{t(lang, 'daily_start_body')}"
        )
        
        keyboard = [
            [{"text": t(lang, 'btn_stop'), "callback_data": "timer_stop"}],
            [{"text": t(lang, 'btn_back'), "callback_data": "daily_asana"}]
        ]
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=message_id,
            text=start_text,
            parse_mode=ParseMode.MARKDOWN,
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
            cycles=cycles,
            asana_name=asana_name
        )
        
        # Создаем и запускаем таймер
        session = timer_service.create_asana_timer(user_id, config)
        timer_service.start_timer(user_id)
        
        # Отправляем сообщение с UI таймера
        work_text = format_duration(lang, session.work_duration)
        rest_text = format_duration(lang, session.rest_duration)
        cycles_text = str(session.cycles) if session.cycles else t(lang, 'daily_infinite_text')
        
        message = await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=message_id,
            text=t(lang, 'asana_started_body',
                   title=t(lang, 'daily_timer_started_title', name=asana_name),
                   work=t(lang, 'work_setting', value=work_text),
                   rest=t(lang, 'rest_setting', value=rest_text),
                   cycles=t(lang, 'cycles_setting', value=cycles_text)),
            parse_mode=ParseMode.MARKDOWN,
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
        lang = self._lang(user_id)

        # У пользователя уже есть премиум/триал
        if self.subscription_service:
            subscription_info = await self.subscription_service.get_subscription_info(user_id)
            if subscription_info['is_active']:
                # Если просят ВИДЕО — пробуем прислать видео «Асаны дня» премиум-юзеру.
                if upgrade_type == 'video':
                    await self._send_daily_asana_video(callback_query.message, user_id, lang, subscription_info)
                    return

                # Остальные типы (easy/safe/general): показываем статус, а не оффер покупки
                if subscription_info['is_trial']:
                    text = t(lang, 'sub_status_trial_full').format(
                        days_left=subscription_info['days_left'])
                else:
                    text = t(lang, 'sub_status_premium_full').format(
                        days_left=subscription_info['days_left'])
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text=t(lang, 'btn_back_main'), callback_data="main_menu")]
                    ]
                )
                await self._replace_message(callback_query.message, text, keyboard, ParseMode.MARKDOWN)
                return
        
        # Формируем текст в зависимости от типа апгрейда
        if upgrade_type == 'easy':
            block_text = t(lang, 'daily_prem_up_easy')
            cta = t(lang, 'daily_prem_up_cta_easy')
        elif upgrade_type == 'safe':
            block_text = t(lang, 'daily_prem_up_safe')
            cta = t(lang, 'daily_prem_up_cta_safe')
        elif upgrade_type == 'video':
            block_text = t(lang, 'daily_prem_up_video')
            cta = t(lang, 'daily_prem_up_cta_video')
        else:
            block_text = t(lang, 'daily_prem_up_general')
            cta = t(lang, 'daily_prem_up_cta_general')
        
        text = (
            f"{block_text}\n\n"
            f"{t(lang, 'daily_prem_up_price')}\n\n"
            f"{cta}"
        )
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=t(lang, 'prem_btn_monthly'), callback_data="premium_buy_monthly")],
                [InlineKeyboardButton(text=t(lang, 'prem_btn_yearly'), callback_data="premium_buy_yearly")],
                [InlineKeyboardButton(text=t(lang, 'btn_back_main'), callback_data="main_menu")]
            ]
        )
        
        await self._replace_message(callback_query.message, text, keyboard, ParseMode.MARKDOWN)
    
    def _create_welcome_time_keyboard(self, lang: str = 'ru'):
        """Создать клавиатуру выбора времени для первого раза"""
        keyboard = []
        
        # Популярные времена с описаниями
        popular_times = [
            ("_0600", 6, 0),
            ("_0700", 7, 0),
            ("_0800", 8, 0),
            ("_0900", 9, 0),
            ("_1000", 10, 0),
            ("_1300", 13, 0),
            ("_1800", 18, 0),
            ("_2000", 20, 0),
            ("_2100", 21, 0),
        ]
        
        for key, hour, minute in popular_times:
            keyboard.append([{
                "text": t(lang, f"daily_w_time{key}"),
                "callback_data": f"daily_welcome_time_{hour}_{minute}"
            }])
        
        keyboard.append([{
            "text": t(lang, 'daily_enter_manual'),
            "callback_data": "daily_time_manual_welcome"
        }])
        
        keyboard.append([{
            "text": t(lang, 'daily_set_other_time'),
            "callback_data": "daily_asana_settings"
        }])
        
        keyboard.append([{
            "text": t(lang, 'btn_back_main'),
            "callback_data": "main_menu"
        }])
        
        return {"inline_keyboard": keyboard}
    
    def _create_time_selection_keyboard(self, lang: str = 'ru'):
        """Создать клавиатуру выбора времени"""
        keyboard = []
        
        # Популярные времена
        popular_times = [
            ("_0700", 7, 0),
            ("_0800", 8, 0),
            ("_0900", 9, 0),
            ("_1000", 10, 0),
            ("_1200", 12, 0),
            ("_1800", 18, 0),
            ("_2000", 20, 0),
            ("_2100", 21, 0),
        ]
        
        for key, hour, minute in popular_times:
            keyboard.append([{
                "text": t(lang, f"daily_s_time{key}"),
                "callback_data": f"daily_time_set_{hour}_{minute}"
            }])
        
        keyboard.append([{
            "text": t(lang, 'daily_enter_manual'),
            "callback_data": "daily_time_manual"
        }])
        
        # Добавляем кнопки управления
        keyboard.append([{
            "text": t(lang, 'daily_tz_button'),
            "callback_data": "daily_timezone_settings"
        }])
        
        keyboard.append([{
            "text": t(lang, 'daily_disable_btn'),
            "callback_data": "daily_asana_disable"
        }])
        
        keyboard.append([{
            "text": t(lang, 'btn_back_main'),
            "callback_data": "main_menu"
        }])
        
        return {"inline_keyboard": keyboard}
    
    async def daily_time_manual_callback(self, callback_query: types.CallbackQuery):
        """Обработчик запроса ручного ввода времени"""
        await self.bot.answer_callback_query(callback_query.id)
        
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)
        
        manual_text = t(lang, 'daily_manual_title')
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=t(lang, 'btn_back'), callback_data="daily_asana_settings")]
            ]
        )
        
        await self._replace_message(callback_query.message, manual_text, keyboard, ParseMode.MARKDOWN)
        
        # Устанавливаем состояние ожидания ввода времени
        # Здесь можно использовать FSM, но для простоты используем временное хранилище
        self.waiting_for_time_input = user_id
    
    async def daily_time_manual_welcome_callback(self, callback_query: types.CallbackQuery):
        """Обработчик запроса ручного ввода времени из приветствия"""
        await self.bot.answer_callback_query(callback_query.id)
        
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)
        
        manual_text = t(lang, 'daily_manual_title')
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=t(lang, 'btn_back'), callback_data="daily_asana_settings")]
            ]
        )
        
        await self._replace_message(callback_query.message, manual_text, keyboard, ParseMode.MARKDOWN)
        
        # Устанавливаем состояние ожидания ввода времени
        self.waiting_for_time_input = user_id
    
    async def handle_time_input(self, message: types.Message):
        """Обработчик текстового ввода времени"""
        user_id = message.from_user.id
        lang = self._lang(user_id)
        
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
                    f"{t(lang, 'daily_saved_ok')}\n\n"
                    f"{t(lang, 'daily_saved_time', time=new_time.strftime('%H:%M'))}\n"
                    f"{t(lang, 'daily_notif_on')}\n\n"
                    f"{t(lang, 'daily_saved_confirm_schedule', time=new_time.strftime('%H:%M'))}\n\n"
                    f"{t(lang, 'daily_ask_now')}"
                )
                
                await message.answer(
                    confirmation_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup={"inline_keyboard": [[
                        {"text": t(lang, 'daily_get_now_btn'), "callback_data": "daily_asana_now"},
                        {"text": t(lang, 'btn_back_main'), "callback_data": "main_menu"}
                    ]]}
                )
            else:
                await message.answer(t(lang, 'daily_err_save_time'))
                
        except ValueError as e:
            await message.answer(t(lang, 'daily_time_invalid'))
        finally:
            # Сбрасываем флаг ожидания ввода
            if hasattr(self, 'waiting_for_time_input'):
                delattr(self, 'waiting_for_time_input')
    
    async def daily_asana_now_callback(self, callback_query: types.CallbackQuery):
        """Обработчик получения асаны дня прямо сейчас"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        lang = self._lang(user_id)
        
        # Получаем пользователя и отправляем асану дня
        user = db_service.get_user(telegram_id=user_id)
        if user:
            await self.scheduler.send_daily_asana_to_user(user)
        else:
            await self.bot.send_message(user_id, t(lang, 'daily_err_user_not_found'))
        
        # Сбрасываем состояние ожидания
        if hasattr(self, 'waiting_for_time_input'):
            delattr(self, 'waiting_for_time_input')
    
    def _create_settings_menu_keyboard(self, lang: str = 'ru'):
        """Создать клавиатуру меню настроек"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=t(lang, 'daily_change_time_btn'), callback_data="daily_asana_settings")],
                [InlineKeyboardButton(text=t(lang, 'daily_change_tz_btn'), callback_data="daily_timezone_settings")],
                [InlineKeyboardButton(text=t(lang, 'daily_disable_btn'), callback_data="daily_asana_disable")],
                [InlineKeyboardButton(text=t(lang, 'btn_back_main'), callback_data="main_menu")]
            ]
        )