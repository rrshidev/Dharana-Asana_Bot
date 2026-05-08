from aiogram import types, Bot, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging

from src.models.sequence_models import SequenceParams, SequenceDifficulty, SequenceDuration, SequenceFocus
from src.services.sequence_generator import SequenceGenerator
from src.services.sequence_practice_service import SequencePracticeService
from src.services.data_service import DataService
from src.services.subscription_service import SubscriptionService
from src.utils.keyboard_service import KeyboardService

logger = logging.getLogger(__name__)

class SequenceHandlers:
    def __init__(self, bot: Bot, data_service: DataService, subscription_service: SubscriptionService):
        self.bot = bot
        self.data_service = data_service
        self.subscription_service = subscription_service
        self.sequence_generator = SequenceGenerator(data_service)
        self.practice_service = SequencePracticeService(data_service)
        self.keyboard_service = KeyboardService()
        
        # Хранилище параметров пользователей
        self.user_sequences = {}

    async def sequence_menu_callback(self, callback_query: types.CallbackQuery):
        """Главное меню генератора последовательностей"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        
        text = (
            "🏋️‍♂️ **Генератор практики 'Зал'**\n\n"
            "Создайте персональную последовательность асан под ваши цели!\n\n"
            "Выберите параметры для генерации:"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎯 Сложность", callback_data="sequence_difficulty")],
            [InlineKeyboardButton(text="⏱️ Длительность", callback_data="sequence_duration")],
            [InlineKeyboardButton(text="🎪 Фокус практики", callback_data="sequence_focus")],
            [InlineKeyboardButton(text="🚀 Сгенерировать", callback_data="sequence_generate")],
            [InlineKeyboardButton(text="🔙 В главное меню", callback_data="main_menu")]
        ])
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            reply_markup=keyboard
        )
    
    async def sequence_difficulty_callback(self, callback_query: types.CallbackQuery):
        """Выбор сложности"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        
        # Получаем текущие параметры пользователя или создаем новые
        if user_id not in self.user_sequences:
            self.user_sequences[user_id] = {
                'difficulty': SequenceDifficulty.BEGINNER,
                'duration': SequenceDuration.MEDIUM,
                'focus': SequenceFocus.BACK
            }
        
        text = (
            "🎯 **Выберите сложность практики:**\n\n"
            "⭐ **Начинающий** - базовые асаны, плавные переходы\n"
            "⭐⭐ **Средний** - разнообразные асаны, умеренная нагрузка\n"
            "⭐⭐⭐ **Продвинутый** - сложные асаны, интенсивная практика"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⭐ Начинающий", callback_data="sequence_set_difficulty_beginner")],
            [InlineKeyboardButton(text="⭐⭐ Средний", callback_data="sequence_set_difficulty_intermediate")],
            [InlineKeyboardButton(text="⭐⭐⭐ Продвинутый", callback_data="sequence_set_difficulty_advanced")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="sequence_menu")]
        ])
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            reply_markup=keyboard
        )
    
    async def sequence_set_difficulty_callback(self, callback_query: types.CallbackQuery):
        """Установка сложности"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        
        difficulty_map = {
            'beginner': SequenceDifficulty.BEGINNER,
            'intermediate': SequenceDifficulty.INTERMEDIATE,
            'advanced': SequenceDifficulty.ADVANCED
        }
        
        difficulty_str = callback_query.data.split('_')[-1]
        self.user_sequences[user_id]['difficulty'] = difficulty_map[difficulty_str]
        
        difficulty_names = {
            'beginner': '⭐ Начинающий',
            'intermediate': '⭐⭐ Средний', 
            'advanced': '⭐⭐⭐ Продвинутый'
        }
        
        text = f"✅ Сложность установлена: {difficulty_names[difficulty_str]}\n\nВыберите следующий параметр:"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏱️ Длительность", callback_data="sequence_duration")],
            [InlineKeyboardButton(text="🎪 Фокус практики", callback_data="sequence_focus")],
            [InlineKeyboardButton(text="🚀 Сгенерировать", callback_data="sequence_generate")],
            [InlineKeyboardButton(text="🔙 В меню генератора", callback_data="sequence_menu")]
        ])
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            reply_markup=keyboard
        )
    
    async def sequence_duration_callback(self, callback_query: types.CallbackQuery):
        """Выбор длительности"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        
        if user_id not in self.user_sequences:
            self.user_sequences[user_id] = {
                'difficulty': SequenceDifficulty.BEGINNER,
                'duration': SequenceDuration.MEDIUM,
                'focus': SequenceFocus.BACK
            }
        
        text = (
            "⏱️ **Выберите длительность практики:**\n\n"
            "🕐 **15 минут** - быстрая практика, утро/перерыв\n"
            "🕕 **30 минут** - стандартная практика, хороший баланс\n"
            "🕐 **60 минут** - полная практика, глубокое погружение"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🕐 15 минут", callback_data="sequence_set_duration_15")],
            [InlineKeyboardButton(text="🕕 30 минут", callback_data="sequence_set_duration_30")],
            [InlineKeyboardButton(text="🕐 60 минут", callback_data="sequence_set_duration_60")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="sequence_menu")]
        ])
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            reply_markup=keyboard
        )
    
    async def sequence_set_duration_callback(self, callback_query: types.CallbackQuery):
        """Установка длительности"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        
        duration_map = {
            '15': SequenceDuration.SHORT,
            '30': SequenceDuration.MEDIUM,
            '60': SequenceDuration.LONG
        }
        
        duration_str = callback_query.data.split('_')[-1]
        self.user_sequences[user_id]['duration'] = duration_map[duration_str]
        
        duration_names = {
            '15': '🕐 15 минут',
            '30': '🕕 30 минут',
            '60': '🕐 60 минут'
        }
        
        text = f"✅ Длительность установлена: {duration_names[duration_str]}\n\nВыберите следующий параметр:"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎯 Сложность", callback_data="sequence_difficulty")],
            [InlineKeyboardButton(text="🎪 Фокус практики", callback_data="sequence_focus")],
            [InlineKeyboardButton(text="🚀 Сгенерировать", callback_data="sequence_generate")],
            [InlineKeyboardButton(text="🔙 В меню генератора", callback_data="sequence_menu")]
        ])
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            reply_markup=keyboard
        )
    
    async def sequence_focus_callback(self, callback_query: types.CallbackQuery):
        """Выбор фокуса практики"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        
        if user_id not in self.user_sequences:
            self.user_sequences[user_id] = {
                'difficulty': SequenceDifficulty.BEGINNER,
                'duration': SequenceDuration.MEDIUM,
                'focus': SequenceFocus.BACK
            }
        
        text = (
            "🎪 **Выберите фокус практики:**\n\n"
            "🦴 **Спина** - укрепление спины, снятие болей\n"
            "🦵 **Ноги** - сила ног, гибкость, баланс\n"
            "⚖️ **Баланс** - концентрация, устойчивость\n"
            "🧘 **Гибкость** - растяжка, подвижность суставов\n"
            "⚡ **Энергия** - бодрость, сила, динамика"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🦴 Спина", callback_data="sequence_set_focus_back")],
            [InlineKeyboardButton(text="🦵 Ноги", callback_data="sequence_set_focus_legs")],
            [InlineKeyboardButton(text="⚖️ Баланс", callback_data="sequence_set_focus_balance")],
            [InlineKeyboardButton(text="🧘 Гибкость", callback_data="sequence_set_focus_flexibility")],
            [InlineKeyboardButton(text="⚡ Энергия", callback_data="sequence_set_focus_energy")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="sequence_menu")]
        ])
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            reply_markup=keyboard
        )
    
    async def sequence_set_focus_callback(self, callback_query: types.CallbackQuery):
        """Установка фокуса"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        
        focus_map = {
            'back': SequenceFocus.BACK,
            'legs': SequenceFocus.LEGS,
            'balance': SequenceFocus.BALANCE,
            'flexibility': SequenceFocus.FLEXIBILITY,
            'energy': SequenceFocus.ENERGY
        }
        
        focus_str = callback_query.data.split('_')[-1]
        self.user_sequences[user_id]['focus'] = focus_map[focus_str]
        
        focus_names = {
            'back': '🦴 Спина',
            'legs': '🦵 Ноги',
            'balance': '⚖️ Баланс',
            'flexibility': '🧘 Гибкость',
            'energy': '⚡ Энергия'
        }
        
        text = f"✅ Фокус установлен: {focus_names[focus_str]}\n\nВыберите следующий параметр:"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎯 Сложность", callback_data="sequence_difficulty")],
            [InlineKeyboardButton(text="⏱️ Длительность", callback_data="sequence_duration")],
            [InlineKeyboardButton(text="🚀 Сгенерировать", callback_data="sequence_generate")],
            [InlineKeyboardButton(text="🔙 В меню генератора", callback_data="sequence_menu")]
        ])
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            reply_markup=keyboard
        )
    
    async def sequence_generate_callback(self, callback_query: types.CallbackQuery):
        """Генерация последовательности"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        
        # Проверяем, есть ли параметры
        if user_id not in self.user_sequences:
            await self.sequence_menu_callback(callback_query)
            return
        
        # Проверяем лимиты генераций
        can_generate, message = self.subscription_service.can_generate_sequence(user_id)
        if not can_generate:
            # Показываем сообщение с предложением подписки
            subscription_info = self.subscription_service.get_subscription_info(user_id)
            
            text = (
                f"{message}\n\n"
                f"🎯 **Премиум-доступ дает:**\n"
                f"• 🔄 Безлимитные генерации\n"
                f"• 🎥 Видео-отстройка асан\n"
                f"• 📊 Детальная статистика\n"
                f"• 🎵 Аудио-медитации\n\n"
                f"Хотите разблокировать все функции?"
            )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🚀 Попробовать 7 дней бесплатно", callback_data="subscription_trial")],
                [InlineKeyboardButton(text="💳 Тарифы", callback_data="subscription_plans")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="sequence_menu")]
            ])
            
            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=callback_query.message.message_id,
                text=text,
                reply_markup=keyboard
            )
            return
        
        params_data = self.user_sequences[user_id]
        params = SequenceParams(
            difficulty=params_data['difficulty'],
            duration=params_data['duration'],
            focus=params_data['focus']
        )
        
        # Используем генерацию (считаем лимит для бесплатных пользователей)
        generation_used = self.subscription_service.use_generation(user_id)
        if not generation_used[0]:
            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=callback_query.message.message_id,
                text=generation_used[1]
            )
            return
        
        # Генерируем последовательность
        try:
            sequence = self.sequence_generator.generate_sequence(params)
            
            # Сохраняем последовательность для пользователя
            self.user_sequences[user_id]['current_sequence'] = sequence
            
            # Формируем текст с описанием
            difficulty_names = {
                'beginner': '⭐ Начинающий',
                'intermediate': '⭐⭐ Средний',
                'advanced': '⭐⭐⭐ Продвинутый'
            }
            
            focus_names = {
                'back': '🦴 Спина',
                'legs': '🦵 Ноги',
                'balance': '⚖️ Баланс',
                'flexibility': '🧘 Гибкость',
                'energy': '⚡ Энергия'
            }
            
            # Добавляем информацию о статусе подписки
            subscription_info = self.subscription_service.get_subscription_info(user_id)
            status_info = f"\n💎 {subscription_info['status']}"
            
            text = (
                f"🎉 **Ваша последовательность готова!**\n\n"
                f"🎯 **Сложность:** {difficulty_names[params.difficulty.value]}\n"
                f"⏱️ **Длительность:** {params.duration.value} минут\n"
                f"🎪 **Фокус:** {focus_names[params.focus.value]}\n"
                f"🔥 **Калории:** ~{sequence.estimated_calories} ккал\n"
                f"📋 **Асан в последовательности:** {len(sequence.items)}{status_info}\n\n"
                f"Готовы начать практику?"
            )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="▶️ Начать практику", callback_data="sequence_start")],
                [InlineKeyboardButton(text="📋 Посмотреть последовательность", callback_data="sequence_show")],
                [InlineKeyboardButton(text="🔄 Перегенерировать", callback_data="sequence_generate")],
                [InlineKeyboardButton(text="🔙 В меню генератора", callback_data="sequence_menu")]
            ])
            
            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=callback_query.message.message_id,
                text=text,
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error generating sequence for user {user_id}: {e}")
            await self.bot.send_message(
                user_id,
                "❌ Произошла ошибка при генерации последовательности. Попробуйте еще раз."
            )
    
    async def sequence_show_callback(self, callback_query: types.CallbackQuery):
        """Показать последовательность"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        
        if user_id not in self.user_sequences or 'current_sequence' not in self.user_sequences[user_id]:
            await self.sequence_menu_callback(callback_query)
            return
        
        sequence = self.user_sequences[user_id]['current_sequence']
        
        text = "📋 **Ваша последовательность:**\n\n"
        
        for i, item in enumerate(sequence.items, 1):
            if item.is_rest:
                text += f"📍 {i}. *{item.asana_name}* - {item.duration_seconds}с\n"
            else:
                text += f"🧘 {i}. **{item.asana_name}** - {item.duration_seconds}с\n"
                text += f"   _{item.description}_\n\n"
        
        # Добавляем информацию о последовательности
        text += f"\n📊 **Итого:** {len(sequence.items)} позиций, {sequence.total_duration.total_seconds()//60} минут"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Начать практику", callback_data="sequence_start")],
            [InlineKeyboardButton(text="🔄 Перегенерировать", callback_data="sequence_generate")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="sequence_menu")]
        ])
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def sequence_start_callback(self, callback_query: types.CallbackQuery):
        """Начать практику с последовательностью"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        
        if user_id not in self.user_sequences or 'current_sequence' not in self.user_sequences[user_id]:
            await self.sequence_menu_callback(callback_query)
            return
        
        sequence = self.user_sequences[user_id]['current_sequence']
        
        # Запускаем последовательную практику
        if self.practice_service.start_sequence(user_id, sequence):
            # Отправляем первую асану
            await self._send_first_asana(user_id, callback_query.message.message_id)
        else:
            await self.bot.send_message(
                user_id,
                "❌ Не удалось запустить практику. Попробуйте еще раз."
            )
    
    async def _send_first_asana(self, user_id: int, message_id: int):
        """Отправляет первую асану последовательности"""
        current_asana = self.practice_service.get_current_asana(user_id)
        if not current_asana:
            return
        
        progress = self.practice_service.get_progress(user_id)
        
        if current_asana.is_rest:
            text = f"🧘 **Отдых**\n\n{current_asana.description}\n\n⏱️ {current_asana.duration_seconds} секунд\n\n📊 Прогресс: {progress['current']}/{progress['total']} ({progress['progress_percent']:.0f}%)"
        else:
            text = (
                f"🧘 **{current_asana.asana_name}**\n\n"
                f"{current_asana.description}\n\n"
                f"⏱️ {current_asana.duration_seconds} секунд\n"
                f"📊 Прогресс: {progress['current']}/{progress['total']} ({progress['progress_percent']:.0f}%)"
            )
        
        # Создаем клавиатуру для практики с кнопкой таймера
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏰ Запустить таймер", callback_data="timer_asana")],
            [InlineKeyboardButton(text="⏭️ Следующая асана", callback_data="sequence_skip")],
            [InlineKeyboardButton(text="🛑 Завершить практику", callback_data="sequence_stop")],
            [InlineKeyboardButton(text=f"📊 {progress.get('current', 0)}/{progress.get('total', 0)}", callback_data="sequence_progress")]
        ])
        
        # Добавляем изображение если есть
        if current_asana.image_path:
            try:
                with open(current_asana.image_path, 'rb') as photo:
                    await self.bot.edit_message_media(
                        chat_id=user_id,
                        message_id=message_id,
                        media=types.InputMediaPhoto(
                            media=photo,
                            caption=text
                        ),
                        reply_markup=keyboard
                    )
            except Exception as e:
                logger.error(f"Error sending image for asana {current_asana.asana_name}: {e}")
                # Если не удалось отправить изображение, отправляем текст
                await self.bot.edit_message_text(
                    chat_id=user_id,
                    message_id=message_id,
                    text=text,
                    reply_markup=keyboard
                )
        else:
            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=text,
                reply_markup=keyboard
            )
    
    async def sequence_pause_callback(self, callback_query: types.CallbackQuery):
        """Поставить практику на паузу"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        
        await self.practice_service.pause_sequence(user_id, self.bot, callback_query.message.message_id)
    
    async def sequence_resume_callback(self, callback_query: types.CallbackQuery):
        """Возобновить практику"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        
        await self.practice_service.resume_sequence(user_id, self.bot, callback_query.message.message_id)
    
    async def sequence_skip_callback(self, callback_query: types.CallbackQuery):
        """Пропустить текущую асану"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        
        if self.practice_service.move_to_next_asana(user_id):
            await self._send_next_asana(user_id, self.bot, callback_query.message.message_id)
        else:
            await self._send_sequence_complete(user_id, self.bot, callback_query.message.message_id)
    
    async def _send_next_asana(self, user_id: int, bot, message_id: int):
        """Отправляет следующую асану"""
        current_asana = self.practice_service.get_current_asana(user_id)
        if not current_asana:
            return
        
        progress = self.practice_service.get_progress(user_id)
        
        if current_asana.is_rest:
            text = f"🧘 **Отдых**\n\n{current_asana.description}\n\n⏱️ {current_asana.duration_seconds} секунд\n\n📊 Прогресс: {progress['current']}/{progress['total']} ({progress['progress_percent']:.0f}%)"
        else:
            text = (
                f"🧘 **{current_asana.asana_name}**\n\n"
                f"{current_asana.description}\n\n"
                f"⏱️ {current_asana.duration_seconds} секунд\n"
                f"📊 Прогресс: {progress['current']}/{progress['total']} ({progress['progress_percent']:.0f}%)"
            )
        
        # Создаем клавиатуру для практики с кнопкой таймера
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏰ Запустить таймер", callback_data="timer_asana")],
            [InlineKeyboardButton(text="⏭️ Следующая асана", callback_data="sequence_skip")],
            [InlineKeyboardButton(text="🛑 Завершить практику", callback_data="sequence_stop")],
            [InlineKeyboardButton(text=f"📊 {progress.get('current', 0)}/{progress.get('total', 0)}", callback_data="sequence_progress")]
        ])
        
        # Добавляем изображение если есть
        if current_asana.image_path:
            try:
                with open(current_asana.image_path, 'rb') as photo:
                    await bot.edit_message_media(
                        chat_id=user_id,
                        message_id=message_id,
                        media=types.InputMediaPhoto(
                            media=photo,
                            caption=text
                        ),
                        reply_markup=keyboard
                    )
            except Exception as e:
                logger.error(f"Error sending image for asana {current_asana.asana_name}: {e}")
                # Если не удалось отправить изображение, отправляем текст
                await bot.edit_message_text(
                    chat_id=user_id,
                    message_id=message_id,
                    text=text,
                    reply_markup=keyboard
                )
        else:
            await bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=text,
                reply_markup=keyboard
            )
    
    async def _send_sequence_complete(self, user_id: int, bot, message_id: int):
        """Отправляет сообщение о завершении последовательности"""
        sequence = self.practice_service.active_sequences.get(user_id)
        if not sequence:
            return
        
        text = (
            f"🎉 **Практика завершена!**\n\n"
            f"📊 **Статистика:**\n"
            f"• Выполнено асан: {len(sequence.items)}\n"
            f"• Общее время: {sequence.total_duration.total_seconds() // 60} минут\n"
            f"• Потрачено калорий: ~{sequence.estimated_calories} ккал\n\n"
            f"Отличная работа! Хотите начать новую практику?"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Новая практика", callback_data="sequence_menu")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
        
        await bot.edit_message_text(
            chat_id=user_id,
            message_id=message_id,
            text=text,
            reply_markup=keyboard
        )
        
        # Останавливаем последовательность
        self.practice_service.stop_sequence(user_id)
    
    async def sequence_stop_callback(self, callback_query: types.CallbackQuery):
        """Завершить практику"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        
        self.practice_service.stop_sequence(user_id)
        
        text = (
            "🛑 **Практика завершена**\n\n"
            "Вы можете начать новую практику или вернуться в главное меню."
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Новая практика", callback_data="sequence_menu")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            reply_markup=keyboard
        )
    
    async def sequence_progress_callback(self, callback_query: types.CallbackQuery):
        """Показать прогресс практики"""
        await self.bot.answer_callback_query(callback_query.id)
        user_id = callback_query.from_user.id
        
        progress = self.practice_service.get_progress(user_id)
        if not progress:
            return
        
        sequence = self.practice_service.active_sequences.get(user_id)
        if not sequence:
            return
        
        text = (
            f"📊 **Прогресс практики**\n\n"
            f"🎯 **Параметры:**\n"
            f"• Сложность: {sequence.params.difficulty.value}\n"
            f"• Длительность: {sequence.params.duration.value} минут\n"
            f"• Фокус: {sequence.params.focus.value}\n\n"
            f"📈 **Выполнение:**\n"
            f"• Асаны: {progress['current']}/{progress['total']}\n"
            f"• Прогресс: {progress['progress_percent']:.0f}%\n"
            f"• Общее время: {sequence.total_duration.total_seconds() // 60} минут\n"
            f"• Калории: ~{sequence.estimated_calories} ккал"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад к практике", callback_data="sequence_resume")]
        ])
        
        await self.bot.edit_message_text(
            chat_id=user_id,
            message_id=callback_query.message.message_id,
            text=text,
            reply_markup=keyboard
        )
