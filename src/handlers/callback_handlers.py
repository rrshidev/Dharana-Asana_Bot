import logging
import os
from aiogram import types
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types.input_file import FSInputFile

from src.i18n import t
from src.services.data_service import DataService
from src.services.filter_service import FilterService
from src.services.video_service import VideoService
from src.services.subscription_service import SubscriptionService
from src.services.database_service import db_service
from src.handlers.filter_handlers import FilterHandlers
from src.utils.keyboard_service import KeyboardService
from src.utils.text_utils import send_markdown_safe
from src.handlers.timer_handlers import TimerHandlers

logger = logging.getLogger(__name__)


class CallbackHandlers:
    """Обработчики callback запросов"""

    def __init__(self, bot):
        self.bot = bot
        self.data_service = DataService()
        self.filter_service = FilterService(self.data_service)
        self.video_service = VideoService(db_service)
        self.subscription_service = SubscriptionService(db_service)
        self.keyboard_service = KeyboardService()
        self.filter_handlers = FilterHandlers(bot, self.data_service)
        self.timer_handlers = TimerHandlers(bot, self.data_service, self.keyboard_service)
        self.daily_asana_handlers = None  # Установится позже

    @staticmethod
    def _lang(telegram_id: int) -> str:
        """Язык пользователя по telegram_id."""
        return db_service.get_user_language(telegram_id)

    async def catalog_callback(self, callback_query: types.CallbackQuery):
        """Обработчик открытия каталога"""
        await self.bot.answer_callback_query(callback_query.id)

        lang = self._lang(callback_query.from_user.id)
        data = self.data_service.load_data()
        categories = list(data.categories.values())

        items = [
            {
                'display_name': self.data_service.localized_category_name(cat.name, lang),
                'id': i,
            }
            for i, cat in enumerate(categories)
        ]

        keyboard = self.keyboard_service.create_categories_menu(items, lang)
        await self.bot.send_message(
            callback_query.from_user.id,
            t(lang, 'categories_title'),
            reply_markup=keyboard
        )

    async def category_callback(self, callback_query: types.CallbackQuery):
        """Обработчик открытия категории асан"""
        await self.bot.answer_callback_query(callback_query.id)

        lang = self._lang(callback_query.from_user.id)

        # Получаем имя категории по ID
        category_name = self.data_service.get_category_by_id(callback_query.data)
        if not category_name:
            await self.bot.send_message(
                callback_query.from_user.id,
                t(lang, 'category_not_found'),
                reply_markup=self.keyboard_service.create_main_menu(lang)
            )
            return

        data = self.data_service.load_data()
        category = data.categories[category_name]

        # Получаем глобальный стартовый индекс для категории
        start_index = self.data_service.get_category_global_start_index(category_name)

        localized_desc = self.data_service.localized_category_desc(category_name, lang)
        await self.bot.send_message(
            callback_query.from_user.id,
            t(lang, 'category_intro', desc=localized_desc)
        )

        # Отправляем каждую асану с миниатюрой и кнопкой
        global_asana_index = self.data_service.get_category_global_start_index(category_name)
        for i, asana in enumerate(category.asanas):
            await self._send_asana_with_thumbnail(callback_query.from_user.id, asana, category_name, global_asana_index + i, lang)

        # Сообщение с возвратом в каталог
        await self.bot.send_message(
            callback_query.from_user.id,
            t(lang, 'back_to_catalog_prompt'),
            reply_markup=self.keyboard_service.create_back_to_catalog_menu(lang)
        )

    async def asana_callback(self, callback_query: types.CallbackQuery):
        """Обработчик выбора асаны"""
        await self.bot.answer_callback_query(callback_query.id)

        lang = self._lang(callback_query.from_user.id)

        # Получаем имя асаны по ID
        asana_name = self.data_service.get_asana_by_id(callback_query.data)
        logger.info(f"Callback data: {callback_query.data} -> Asana name: {asana_name}")

        if not asana_name:
            await self.bot.send_message(
                callback_query.from_user.id,
                t(lang, 'asana_not_found'),
                reply_markup=self.keyboard_service.create_main_menu(lang)
            )
            return

        asana_data = self.data_service.get_asana_data(asana_name, lang)

        if not asana_data:
            await self.bot.send_message(
                callback_query.from_user.id,
                t(lang, 'asana_not_found'),
                reply_markup=self.keyboard_service.create_main_menu(lang)
            )
            return

        await self._send_asana_full(callback_query.from_user.id, asana_data, callback_query.message, lang)

    async def random_asana_callback(self, callback_query: types.CallbackQuery):
        """Обработчик случайной асаны"""
        await self.bot.answer_callback_query(callback_query.id)

        lang = self._lang(callback_query.from_user.id)

        asana_data = self.data_service.get_random_asana(lang)

        if not asana_data:
            await self.bot.send_message(
                callback_query.from_user.id,
                t(lang, 'asana_load_error'),
                reply_markup=self.keyboard_service.create_main_menu(lang)
            )
            return

        await self._send_asana_full(callback_query.from_user.id, asana_data, None, lang)

    async def basics_callback(self, callback_query: types.CallbackQuery):
        """Обработчик открытия основ йоги"""
        await self.bot.answer_callback_query(callback_query.id)

        lang = self._lang(callback_query.from_user.id)

        data = self.data_service.load_data()
        items = [self.data_service.localized_basic_name(b, lang) for b in data.basics]
        keyboard = self.keyboard_service.create_simple_menu(items, 'basic', lang)
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text=t(lang, 'btn_back_main'), callback_data='main_menu')]
        )

        await self.bot.send_message(
            callback_query.from_user.id,
            t(lang, 'basics_menu_title'),
            reply_markup=keyboard
        )

    async def basic_item_callback(self, callback_query: types.CallbackQuery):
        """Обработчик выбора основы йоги"""
        await self.bot.answer_callback_query(callback_query.id)

        lang = self._lang(callback_query.from_user.id)

        # Получаем имя основы по ID
        basic_name = self.data_service.get_basic_by_id(callback_query.data)
        if not basic_name:
            await self.bot.send_message(
                callback_query.from_user.id,
                t(lang, 'basics_not_found'),
                reply_markup=self.keyboard_service.create_main_menu(lang)
            )
            return

        content, image_path = self.data_service.get_basic_content(basic_name, lang)

        if not content:
            await self.bot.send_message(
                callback_query.from_user.id,
                t(lang, 'basic_not_found', name=basic_name),
                reply_markup=self.keyboard_service.create_main_menu(lang)
            )
            return

        await self._send_long_text_with_image(
            callback_query.from_user.id,
            content,
            image_path,
            t(lang, 'basics_section_title'),
            lang
        )

    async def steps_callback(self, callback_query: types.CallbackQuery):
        """Обработчик открытия ступеней йоги"""
        await self.bot.answer_callback_query(callback_query.id)

        lang = self._lang(callback_query.from_user.id)

        data = self.data_service.load_data()
        items = [self.data_service.localized_step_name(s, lang) for s in data.steps]
        keyboard = self.keyboard_service.create_simple_menu(items, 'step', lang)
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text=t(lang, 'btn_back_main'), callback_data='main_menu')]
        )

        await self.bot.send_message(
            callback_query.from_user.id,
            t(lang, 'steps_menu_title'),
            reply_markup=keyboard
        )

    async def step_item_callback(self, callback_query: types.CallbackQuery):
        """Обработчик выбора ступени йоги"""
        await self.bot.answer_callback_query(callback_query.id)

        lang = self._lang(callback_query.from_user.id)

        # Получаем имя ступени по ID
        step_name = self.data_service.get_step_by_id(callback_query.data)
        if not step_name:
            await self.bot.send_message(
                callback_query.from_user.id,
                t(lang, 'step_not_found'),
                reply_markup=self.keyboard_service.create_main_menu(lang)
            )
            return

        content = self.data_service.get_step_content(step_name, lang)

        if not content:
            await self.bot.send_message(
                callback_query.from_user.id,
                t(lang, 'step_content_not_found', name=step_name),
                reply_markup=self.keyboard_service.create_main_menu(lang)
            )
            return

        await self._send_long_text(
            callback_query.from_user.id,
            content,
            t(lang, 'step_section_title'),
            lang
        )

    async def _send_asana_with_thumbnail(self, user_id: int, asana_name: str, category_name: str, global_asana_index: int, lang: str = 'ru'):
        """Отправляет асану с миниатюрой"""
        display_name = self.data_service.localized_asana_name(asana_name, lang)
        # Создаем кнопку с глобальным индексом
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=display_name, callback_data=f'asana_{global_asana_index}')]]
        )

        # Пытаемся отправить миниатюру .png
        png_path = os.path.normpath(
            os.path.join("bot_data", "catalog", category_name, f'{asana_name}.png')
        )

        caption = t(lang, 'yoga_pose', name=display_name)
        try:
            await self.bot.send_photo(
                user_id,
                FSInputFile(png_path),
                caption=caption,
                reply_markup=keyboard
            )
        except FileNotFoundError:
            # Если миниатюра не найдена, отправляем только кнопку
            await self.bot.send_message(
                user_id,
                caption,
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error sending thumbnail for {asana_name}: {e}")
            await self.bot.send_message(
                user_id,
                caption,
                reply_markup=keyboard
            )

    async def _send_asana_full(self, user_id: int, asana_data, message=None, lang: str = 'ru'):
        """Отправляет полное описание асаны с фото или видео"""
        try:
            # Проверяем статус подписки пользователя
            subscription_info = await self.subscription_service.get_subscription_info(user_id)
            is_premium = subscription_info['is_active']

            # Ищем видео для этой асаны (по каноническому имени)
            video_name = asana_data.base_name or asana_data.name
            video = self.video_service.get_video_for_asana(video_name, is_premium)

            # Отладочная информация
            logger.info(f"Callback User {user_id}: is_premium={is_premium}, video_found={video is not None}")
            if video:
                logger.info(f"Callback Video info: is_premium={video['is_premium']}, video_path={video['video_path']}")

            # Формируем текст с информацией о доступности
            status_text = ""
            if video and video['is_premium'] and is_premium:
                status_text = t(lang, 'video_available') + "\n\n"
            elif video and video['is_premium'] and not is_premium:
                status_text = t(lang, 'video_premium_only') + "\n\n"

            # Отправляем описание
            full_text = status_text + asana_data.description
            await send_markdown_safe(self.bot, user_id, full_text)

            # Отправляем видео или фото
            if video and video['is_premium'] and is_premium:
                # Премиум-пользователь получает видео
                if video['video_path'] and os.path.exists(video['video_path']):
                    try:
                        await self.bot.send_video(user_id, FSInputFile(video['video_path']))
                        logger.info(f"Sent video for asana {asana_data.name} to premium user {user_id}")
                    except Exception as e:
                        logger.error(f"Error sending video: {e}")
                        # Если видео не отправилось, отправляем фото
                        if asana_data.image_path and os.path.exists(asana_data.image_path):
                            await self.bot.send_photo(user_id, FSInputFile(asana_data.image_path))
                else:
                    # Видео файла нет, отправляем фото
                    if asana_data.image_path and os.path.exists(asana_data.image_path):
                        await self.bot.send_photo(user_id, FSInputFile(asana_data.image_path))

            elif video and video['is_premium'] and not is_premium:
                # Бесплатный пользователь видит превью видео и предложение подписки
                logger.info(f"Callback: Showing subscription offer to user {user_id}")

                if asana_data.image_path and os.path.exists(asana_data.image_path):
                    await self.bot.send_photo(user_id, FSInputFile(asana_data.image_path))

                # Добавляем предложение подписки
                premium_text = t(lang, 'premium_offer')

                premium_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=t(lang, 'btn_trial'), callback_data="subscription_trial")],
                    [InlineKeyboardButton(text=t(lang, 'btn_plans'), callback_data="subscription_plans")]
                ])

                await self.bot.send_message(user_id, premium_text, parse_mode=ParseMode.MARKDOWN, reply_markup=premium_keyboard)

            else:
                # Видео нет, отправляем фото как обычно
                logger.info(f"Callback: No video found for asana {asana_data.name}, sending photo only")
                if asana_data.image_path and os.path.exists(asana_data.image_path):
                    await self.bot.send_photo(user_id, FSInputFile(asana_data.image_path))

            # Кнопка возврата
            outro = t(lang, 'catalog_outro')
            if message:
                await message.reply(outro, reply_markup=self.keyboard_service.create_main_menu(lang))
            else:
                await self.bot.send_message(
                    user_id,
                    text=outro,
                    reply_markup=self.keyboard_service.create_main_menu(lang)
                )

        except Exception as e:
            logger.error(f"Error sending asana {asana_data.name}: {e}")
            await self.bot.send_message(
                user_id,
                t(lang, 'asana_error', err=e),
                reply_markup=self.keyboard_service.create_main_menu(lang)
            )

    async def _send_long_text(self, user_id: int, text: str, title: str, lang: str = 'ru'):
        """Отправляет длинный текст частями"""
        await self.bot.send_message(user_id, title)

        if len(text) > 4096:
            for i in range(0, len(text), 4096):
                await self.bot.send_message(user_id, text[i:i+4096])
        else:
            await self.bot.send_message(user_id, text)

        await self.bot.send_message(
            user_id,
            text=t(lang, 'catalog_outro'),
            reply_markup=self.keyboard_service.create_main_menu(lang)
        )

    async def back_callback(self, callback_query: types.CallbackQuery):
        """Обработчик кнопки назад"""
        await self.bot.answer_callback_query(callback_query.id)
        lang = self._lang(callback_query.from_user.id)
        await self.bot.send_message(
            callback_query.from_user.id,
            t(lang, 'choose_section'),
            reply_markup=self.keyboard_service.create_main_menu(lang)
        )

    async def about_callback(self, callback_query: types.CallbackQuery):
        """Обработчик информации о боте"""
        await self.bot.answer_callback_query(callback_query.id)
        lang = self._lang(callback_query.from_user.id)
        await self.bot.send_message(
            callback_query.from_user.id,
            t(lang, 'about_text'),
            reply_markup=self.keyboard_service.create_main_menu(lang)
        )

    async def filter_menu_callback(self, callback_query: types.CallbackQuery):
        """Обработчик меню фильтров"""
        await self.filter_handlers.show_filter_menu_callback(callback_query)

    async def filter_difficulty_menu_callback(self, callback_query: types.CallbackQuery):
        """Обработчик меню фильтра сложности"""
        await self.filter_handlers.show_difficulty_filter_menu(callback_query)

    async def filter_effect_menu_callback(self, callback_query: types.CallbackQuery):
        """Обработчик меню фильтра эффектов"""
        await self.filter_handlers.show_effect_filter_menu(callback_query)

    async def main_menu_callback(self, callback_query: types.CallbackQuery):
        """Обработчик возврата в главное меню"""
        await self.show_main_menu(callback_query.from_user.id, callback_query.message.message_id)

    async def start_screen_callback(self, callback_query: types.CallbackQuery):
        """Обработчик возврата на главный экран (быстрые действия)"""
        await self.show_start_screen(callback_query.from_user.id, callback_query.message.message_id)

    async def show_main_menu(self, user_id: int, message_id: int = None):
        """Показать главное меню (все разделы)"""
        from src.utils.keyboard_service import KeyboardService
        keyboard_service = KeyboardService()

        lang = db_service.get_user_language(user_id)
        main_menu_text = t(lang, 'main_menu_title')

        keyboard = keyboard_service.create_main_menu(lang)

        if message_id:
            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=main_menu_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
        else:
            await self.bot.send_message(
                chat_id=user_id,
                text=main_menu_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )

    async def show_start_screen(self, user_id: int, message_id: int = None):
        """Показать главный экран (быстрые действия)"""
        from src.utils.keyboard_service import KeyboardService
        keyboard_service = KeyboardService()

        lang = db_service.get_user_language(user_id)
        start_screen_text = t(lang, 'start_screen_title')

        keyboard = keyboard_service.create_start_menu(lang)

        if message_id:
            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=start_screen_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
        else:
            await self.bot.send_message(
                chat_id=user_id,
                text=start_screen_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )

    async def language_menu_callback(self, callback_query: types.CallbackQuery):
        """Меню выбора языка"""
        await self.bot.answer_callback_query(callback_query.id)
        lang = self._lang(callback_query.from_user.id)
        await self.bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=t(lang, 'lang_menu_title'),
            reply_markup=self.keyboard_service.create_language_menu(lang),
            parse_mode=ParseMode.MARKDOWN,
        )

    async def language_set_callback(self, callback_query: types.CallbackQuery):
        """Установка языка и возврат в главное меню"""
        telegram_id = callback_query.from_user.id
        new_lang = 'en' if callback_query.data == 'lang_set_en' else 'ru'
        db_service.set_user_language(telegram_id, new_lang)
        lang_name = 'English' if new_lang == 'en' else 'Русский'
        await self.bot.answer_callback_query(
            callback_query.id,
            t(new_lang, 'lang_changed', name=lang_name)
        )
        await self.show_main_menu(telegram_id, callback_query.message.message_id)

    async def filter_effect_callback(self, callback_query: types.CallbackQuery):
        """Обработчик выбора фильтра эффектов"""
        await self.filter_handlers.filter_effect_callback(callback_query)

    async def filter_reset_all_callback(self, callback_query: types.CallbackQuery):
        """Обработчик сброса всех фильтров"""
        await self.filter_handlers.reset_all_filters(callback_query)

    async def daily_asana_callback(self, callback_query: types.CallbackQuery):
        """Обработчик асаны дня из главного меню"""
        await self.daily_asana_handlers.daily_asana_command_from_callback(callback_query)

    async def _send_long_text_with_image(self, user_id: int, text: str, image_path: str, title: str, lang: str = 'ru'):
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
            text=t(lang, 'catalog_outro'),
            reply_markup=self.keyboard_service.create_main_menu(lang)
        )