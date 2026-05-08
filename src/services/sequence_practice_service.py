import logging
from typing import Dict, List, Optional
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.models.sequence_models import PracticeSequence, SequenceItem
from src.services.timer_service import timer_service, TimerConfig
from src.services.data_service import DataService

logger = logging.getLogger(__name__)

class SequencePracticeService:
    """Сервис для управления последовательными практиками"""
    
    def __init__(self, data_service: DataService):
        self.data_service = data_service
        self.active_sequences: Dict[int, PracticeSequence] = {}  # user_id -> sequence
        self.current_positions: Dict[int, int] = {}  # user_id -> current position
        self.active_timers: Dict[int, str] = {}  # user_id -> timer_id
    
    def start_sequence(self, user_id: int, sequence: PracticeSequence) -> bool:
        """Начинает последовательную практику"""
        try:
            self.active_sequences[user_id] = sequence
            self.current_positions[user_id] = 0
            
            logger.info(f"Started sequence practice for user {user_id}: {len(sequence.items)} items")
            return True
        except Exception as e:
            logger.error(f"Error starting sequence for user {user_id}: {e}")
            return False
    
    def get_current_asana(self, user_id: int) -> Optional[SequenceItem]:
        """Получает текущую асану в последовательности"""
        if user_id not in self.active_sequences:
            return None
        
        sequence = self.active_sequences[user_id]
        position = self.current_positions.get(user_id, 0)
        
        if position >= len(sequence.items):
            return None
        
        return sequence.items[position]
    
    def move_to_next_asana(self, user_id: int) -> bool:
        """Переходит к следующей асане"""
        if user_id not in self.active_sequences:
            return False
        
        sequence = self.active_sequences[user_id]
        current_position = self.current_positions.get(user_id, 0)
        
        if current_position >= len(sequence.items) - 1:
            # Последовательность завершена
            self.stop_sequence(user_id)
            return False
        
        self.current_positions[user_id] = current_position + 1
        return True
    
    def stop_sequence(self, user_id: int):
        """Останавливает последовательную практику"""
        if user_id in self.active_sequences:
            del self.active_sequences[user_id]
        
        if user_id in self.current_positions:
            del self.current_positions[user_id]
        
        if user_id in self.active_timers:
            timer_id = self.active_timers[user_id]
            timer_service.stop_timer(timer_id)
            del self.active_timers[user_id]
        
        logger.info(f"Stopped sequence practice for user {user_id}")
    
    def get_progress(self, user_id: int) -> Dict:
        """Получает прогресс практики"""
        if user_id not in self.active_sequences:
            return {}
        
        sequence = self.active_sequences[user_id]
        current_position = self.current_positions.get(user_id, 0)
        
        return {
            'current': current_position + 1,
            'total': len(sequence.items),
            'progress_percent': ((current_position + 1) / len(sequence.items)) * 100
        }
    
    async def start_timer_for_asana(self, user_id: int, bot, message_id: int) -> bool:
        """Запускает таймер для текущей асаны"""
        current_asana = self.get_current_asana(user_id)
        if not current_asana:
            return False
        
        try:
            # Создаем конфигурацию таймера для текущей асаны
            timer_config = TimerConfig(
                work_duration=current_asana.duration_seconds,
                rest_duration=15 if not current_asana.is_rest else 0,  # 15с отдых между асанами
                cycles=1
            )
            
            # Запускаем таймер
            timer_id = timer_service.create_asana_timer(
                user_id=user_id,
                config=timer_config
            )
            
            self.active_timers[user_id] = timer_id
            timer_service.start_timer(timer_id)
            
            logger.info(f"Started timer for asana '{current_asana.asana_name}' for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting timer for user {user_id}: {e}")
            return False
    
    def _create_sequence_timer_callback(self, user_id: int, bot, message_id: int):
        """Создает callback для таймера последовательности"""
        async def sequence_timer_callback(timer_id: str, state: str, remaining_time: int):
            try:
                if state == 'completed':
                    # Таймер завершен, переходим к следующей асане
                    if self.move_to_next_asana(user_id):
                        # Есть следующая асана
                        await self._send_next_asana(user_id, bot, message_id)
                    else:
                        # Последовательность завершена
                        await self._send_sequence_complete(user_id, bot, message_id)
                elif state == 'stopped':
                    # Таймер остановлен
                    await self._send_sequence_paused(user_id, bot, message_id)
                    
            except Exception as e:
                logger.error(f"Error in sequence timer callback for user {user_id}: {e}")
        
        return sequence_timer_callback
    
    async def _send_next_asana(self, user_id: int, bot, message_id: int):
        """Отправляет следующую асану"""
        current_asana = self.get_current_asana(user_id)
        if not current_asana:
            return
        
        progress = self.get_progress(user_id)
        
        if current_asana.is_rest:
            text = f"🧘 **Отдых**\n\n{current_asana.description}\n\n⏱️ {current_asana.duration_seconds} секунд"
        else:
            text = (
                f"🧘 **{current_asana.asana_name}**\n\n"
                f"{current_asana.description}\n\n"
                f"⏱️ {current_asana.duration_seconds} секунд\n"
                f"📊 Прогресс: {progress['current']}/{progress['total']} ({progress['progress_percent']:.0f}%)"
            )
        
        # Добавляем изображение если есть
        if current_asana.image_path:
            try:
                with open(current_asana.image_path, 'rb') as photo:
                    keyboard = self._create_practice_keyboard(user_id)
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
                keyboard = self._create_practice_keyboard(user_id)
                await bot.edit_message_text(
                    chat_id=user_id,
                    message_id=message_id,
                    text=text,
                    reply_markup=keyboard
                )
        else:
            keyboard = self._create_practice_keyboard(user_id)
            await bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=text,
                reply_markup=keyboard
            )
        
        # Автоматически запускаем таймер для следующей асаны
        await self.start_timer_for_asana(user_id, bot, message_id)
    
    async def _send_sequence_complete(self, user_id: int, bot, message_id: int):
        """Отправляет сообщение о завершении последовательности"""
        sequence = self.active_sequences.get(user_id)
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
        self.stop_sequence(user_id)
    
    async def _send_sequence_paused(self, user_id: int, bot, message_id: int):
        """Отправляет сообщение о паузе"""
        current_asana = self.get_current_asana(user_id)
        if not current_asana:
            return
        
        text = (
            f"⏸️ **Практика на паузе**\n\n"
            f"Текущая асана: **{current_asana.asana_name}**\n\n"
            f"Хотите продолжить?"
        )
        
        keyboard = self._create_practice_keyboard(user_id)
        
        await bot.edit_message_text(
            chat_id=user_id,
            message_id=message_id,
            text=text,
            reply_markup=keyboard
        )
    
    def _create_practice_keyboard(self, user_id: int) -> InlineKeyboardMarkup:
        """Создает клавиатуру для практики"""
        progress = self.get_progress(user_id)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏸️ Пауза", callback_data="sequence_pause")],
            [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="sequence_skip")],
            [InlineKeyboardButton(text="🛑 Завершить", callback_data="sequence_stop")],
            [InlineKeyboardButton(text=f"📊 {progress.get('current', 0)}/{progress.get('total', 0)}", callback_data="sequence_progress")]
        ])
        
        return keyboard
    
    async def pause_sequence(self, user_id: int, bot, message_id: int):
        """Ставит последовательность на паузу"""
        if user_id in self.active_timers:
            timer_id = self.active_timers[user_id]
            timer_service.pause_timer(timer_id)
        
        await self._send_sequence_paused(user_id, bot, message_id)
    
    async def resume_sequence(self, user_id: int, bot, message_id: int):
        """Возобновляет последовательность"""
        if user_id in self.active_timers:
            timer_id = self.active_timers[user_id]
            timer_service.resume_timer(timer_id)
        
        await self._send_next_asana(user_id, bot, message_id)
    
    async def skip_current_asana(self, user_id: int, bot, message_id: int):
        """Пропускает текущую асану"""
        if self.move_to_next_asana(user_id):
            await self._send_next_asana(user_id, bot, message_id)
        else:
            await self._send_sequence_complete(user_id, bot, message_id)
