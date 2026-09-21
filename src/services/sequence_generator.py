import random
import logging
from typing import List, Dict
from datetime import timedelta

from src.models.sequence_models import (
    SequenceParams, SequenceItem, PracticeSequence,
    SequenceDifficulty, SequenceFocus, SequenceDuration
)
from src.services.data_service import DataService

logger = logging.getLogger(__name__)

class SequenceGenerator:
    """Генератор последовательностей асан для практики"""
    
    def __init__(self, data_service: DataService):
        self.data_service = data_service
        self.asanas_by_category = {}
        self.asanas_by_difficulty = {1: [], 2: [], 3: [], 4: [], 5: []}
        self.asanas_by_effect = {}
        self._load_asana_database()
    
    def _load_asana_database(self):
        """Загружает базу асан для генерации"""
        self.asanas_by_category = {}
        self.asanas_by_difficulty = {1: [], 2: [], 3: [], 4: [], 5: []}
        self.asanas_by_effect = {}
        
        data = self.data_service.load_data()
        
        logger.info(f"Loading data from {len(data.categories)} categories")
        
        for category_name, category in data.categories.items():
            self.asanas_by_category[category_name] = category.asanas
            logger.info(f"Category {category_name}: {len(category.asanas)} asanas")
            
            for asana in category.asanas:
                # Группируем по сложности
                if hasattr(asana, 'difficulty') and asana.difficulty:
                    try:
                        difficulty_num = int(asana.difficulty) if isinstance(asana.difficulty, str) else asana.difficulty
                        if 1 <= difficulty_num <= 5:
                            self.asanas_by_difficulty[difficulty_num].append(asana)
                    except (ValueError, TypeError):
                        # Если сложность не может быть конвертирована в число, пропускаем
                        continue
                
                # Группируем по эффектам
                if hasattr(asana, 'effects') and asana.effects:
                    try:
                        # Если effects - это строка, разделяем ее
                        effects_list = asana.effects.split(',') if isinstance(asana.effects, str) else asana.effects
                        for effect in effects_list:
                            effect = effect.strip()  # Убираем пробелы
                            if effect not in self.asanas_by_effect:
                                self.asanas_by_effect[effect] = []
                            self.asanas_by_effect[effect].append(asana)
                    except (ValueError, TypeError, AttributeError):
                        continue
        
        total_asanas = sum(len(asanas) for asanas in self.asanas_by_category.values())
        logger.info(f"Loaded {total_asanas} asanas for sequence generation")
        
        # Логируем распределение по сложности
        for diff, asanas in self.asanas_by_difficulty.items():
            logger.info(f"Difficulty {diff}: {len(asanas)} asanas")
    
    def generate_sequence(self, params: SequenceParams) -> PracticeSequence:
        """Генерирует последовательность асан по параметрам"""
        logger.info(f"Generating sequence: {params.difficulty.value}, {params.duration.value}min, {params.focus.value}")
        
        # Проверяем, загружены ли данные
        if not self.asanas_by_category:
            logger.warning("No asanas loaded, forcing reload")
            self._load_asana_database()
        
        # Определяем общую длительность в секундах
        total_seconds = params.duration.value * 60
        
        # Распределяем время: разминка 10%, основная часть 75%, заминка 15%
        warmup_time = int(total_seconds * 0.1)
        main_time = int(total_seconds * 0.75)
        cooldown_time = total_seconds - warmup_time - main_time
        
        items = []
        
        # 1. Разминка
        warmup_asanas = self._get_warmup_asanas(params.difficulty, warmup_time)
        items.extend(warmup_asanas)
        
        # 2. Основная часть по фокусу
        main_asanas = self._get_main_asanas(params.difficulty, params.focus, main_time)
        items.extend(main_asanas)
        
        # 3. Заминка
        cooldown_asanas = self._get_cooldown_asanas(params.difficulty, cooldown_time)
        items.extend(cooldown_asanas)
        
        # Рассчитываем общие параметры
        actual_duration = sum(item.duration_seconds for item in items)
        estimated_calories = self._estimate_calories(params, actual_duration)
        
        sequence = PracticeSequence(
            params=params,
            items=items,
            total_duration=timedelta(seconds=actual_duration),
            estimated_calories=estimated_calories
        )
        
        logger.info(f"Generated sequence with {len(items)} items, {actual_duration}s total")
        return sequence
    
    def _get_warmup_asanas(self, difficulty: SequenceDifficulty, total_time: int) -> List[SequenceItem]:
        """Генерирует разминку"""
        asanas = []
        time_per_asana = min(60, total_time // 3)  # 60 секунд на асану максимум
        
        # Простые асаны на разогрев
        warmup_categories = ['coup+', 'sit_lie+']  # стоячие и сидячие/лежачие
        available_asanas = []
        
        logger.info(f"Looking for warmup asanas in categories: {warmup_categories}")
        
        for category in warmup_categories:
            if category in self.asanas_by_category:
                logger.info(f"Found {len(self.asanas_by_category[category])} asanas in category {category}")
                for asana in self.asanas_by_category[category]:
                    # Если у асаны нет сложности или она некорректная, все равно добавляем для начинающих
                    if not hasattr(asana, 'difficulty') or not asana.difficulty:
                        if difficulty == SequenceDifficulty.BEGINNER:
                            available_asanas.append(asana)
                        continue
                    
                    try:
                        difficulty_num = int(asana.difficulty) if isinstance(asana.difficulty, str) else asana.difficulty
                        if difficulty_num <= self._difficulty_to_number(difficulty):
                            available_asanas.append(asana)
                    except (ValueError, TypeError):
                        # Если сложность не может быть конвертирована, добавляем для начинающих
                        if difficulty == SequenceDifficulty.BEGINNER:
                            available_asanas.append(asana)
                        continue
            else:
                logger.warning(f"Category {category} not found")
        
        logger.info(f"Found {len(available_asanas)} suitable warmup asanas")
        
        # Выбираем случайные асаны на разминку
        num_asanas = min(3, total_time // time_per_asana)
        if available_asanas:
            selected_asanas = random.sample(available_asanas, min(num_asanas, len(available_asanas)))
        else:
            # Если нет подходящих асан, создаем заглушку
            selected_asanas = []
        
        for asana in selected_asanas:
            # Проверяем тип асаны и получаем имя
            if isinstance(asana, str):
                asana_name = asana
                asana_category = "unknown"
                asana_description = "Описание асаны"
            else:
                asana_name = getattr(asana, 'name', 'Unknown Asana')
                asana_category = getattr(asana, 'category', 'unknown')
                asana_description = getattr(asana, 'description', 'Описание асаны')[:100] + "..." if hasattr(asana, 'description') and len(getattr(asana, 'description', '')) > 100 else getattr(asana, 'description', 'Описание асаны')
            
            asanas.append(SequenceItem(
                asana_name=asana_name,
                asana_category=asana_category,
                duration_seconds=time_per_asana,
                description=asana_description,
                image_path=self._get_image_path(asana) if not isinstance(asana, str) else None
            ))
        
        return asanas
    
    def _get_main_asanas(self, difficulty: SequenceDifficulty, focus: SequenceFocus, total_time: int) -> List[SequenceItem]:
        """Генерирует основную часть практики по фокусу"""
        asanas = []
        time_per_asana = min(90, total_time // 4)  # 90 секунд на асану максимум
        
        # Маппинг фокусов на категории и эффекты
        focus_mapping = {
            SequenceFocus.BACK: ['sag+', 'coup+'],  # прогибы и стоячие
            SequenceFocus.LEGS: ['coup+', 'sit_lie+'],  # стоячие и сидячие/лежачие
            SequenceFocus.BALANCE: ['stay+'],  # балансы
            SequenceFocus.FLEXIBILITY: ['sit_lie+', 'sag+'],  # сидячие/лежачие и прогибы
            SequenceFocus.ENERGY: ['coup+', 'power+']  # стоячие и силовые
        }
        
        target_categories = focus_mapping.get(focus, ['coup+', 'sit_lie+'])  # по умолчанию стоячие и сидячие/лежачие
        available_asanas = []
        
        for category in target_categories:
            if category in self.asanas_by_category:
                logger.info(f"Checking category {category} for focus {focus.value}")
                for asana in self.asanas_by_category[category]:
                    # Если у асаны нет сложности или она некорректная, добавляем для начинающих
                    if not hasattr(asana, 'difficulty') or not asana.difficulty:
                        if difficulty == SequenceDifficulty.BEGINNER:
                            available_asanas.append(asana)
                        continue
                    
                    try:
                        difficulty_num = int(asana.difficulty) if isinstance(asana.difficulty, str) else asana.difficulty
                        if difficulty_num <= self._difficulty_to_number(difficulty):
                            available_asanas.append(asana)
                            logger.info(f"Added asana {getattr(asana, 'name', 'Unknown')} with difficulty {difficulty_num}")
                    except (ValueError, TypeError):
                        # Если сложность не может быть конвертирована, добавляем для начинающих
                        if difficulty == SequenceDifficulty.BEGINNER:
                            available_asanas.append(asana)
                        continue
        
        # Добавляем отдых между асанами
        num_asanas = min(5, total_time // (time_per_asana + 15))  # +15с на отдых
        
        logger.info(f"Found {len(available_asanas)} suitable asanas for main sequence")
        
        if not available_asanas:
            logger.warning(f"No suitable asanas found for focus {focus.value}, using fallback")
            # Используем все асаны из доступных категорий как запасной вариант
            for category in ['coup+', 'sit_lie+']:  # базовые категории
                if category in self.asanas_by_category:
                    for asana in self.asanas_by_category[category]:
                        available_asanas.append(asana)
        
        selected_asanas = random.sample(available_asanas, min(num_asanas, len(available_asanas)))
        
        for i, asana in enumerate(selected_asanas):
            # Проверяем тип асаны и получаем имя
            if isinstance(asana, str):
                asana_name = asana
                asana_category = "unknown"
                asana_description = "Описание асаны"
            else:
                asana_name = getattr(asana, 'name', 'Unknown Asana')
                asana_category = getattr(asana, 'category', 'unknown')
                asana_description = getattr(asana, 'description', 'Описание асаны')[:100] + "..." if hasattr(asana, 'description') and len(getattr(asana, 'description', '')) > 100 else getattr(asana, 'description', 'Описание асаны')
            
            asanas.append(SequenceItem(
                asana_name=asana_name,
                asana_category=asana_category,
                duration_seconds=time_per_asana,
                description=asana_description,
                image_path=self._get_image_path(asana) if not isinstance(asana, str) else None
            ))
            
            # Добавляем отдых после каждой асаны, кроме последней
            if i < len(selected_asanas) - 1:
                asanas.append(SequenceItem(
                    asana_name="Отдых",
                    asana_category="rest",
                    duration_seconds=15,
                    description="Отдых между асанами",
                    is_rest=True
                ))
        
        return asanas
    
    def _get_cooldown_asanas(self, difficulty: SequenceDifficulty, total_time: int) -> List[SequenceItem]:
        """Генерирует заминку"""
        asanas = []
        time_per_asana = min(60, total_time // 2)
        
        # Асаны на расслабление
        cooldown_categories = ['sit_lie+', 'sag+']  # сидячие/лежачие и прогибы
        available_asanas = []
        
        for category in cooldown_categories:
            if category in self.asanas_by_category:
                for asana in self.asanas_by_category[category]:
                    if hasattr(asana, 'difficulty') and asana.difficulty:
                        try:
                            difficulty_num = int(asana.difficulty) if isinstance(asana.difficulty, str) else asana.difficulty
                            if difficulty_num <= self._difficulty_to_number(difficulty):
                                available_asanas.append(asana)
                        except (ValueError, TypeError):
                            continue
        
        num_asanas = min(2, total_time // time_per_asana)
        selected_asanas = random.sample(available_asanas, min(num_asanas, len(available_asanas)))
        
        for asana in selected_asanas:
            # Проверяем тип асаны и получаем имя
            if isinstance(asana, str):
                asana_name = asana
                asana_category = "unknown"
                asana_description = "Описание асаны"
            else:
                asana_name = getattr(asana, 'name', 'Unknown Asana')
                asana_category = getattr(asana, 'category', 'unknown')
                asana_description = getattr(asana, 'description', 'Описание асаны')[:100] + "..." if hasattr(asana, 'description') and len(getattr(asana, 'description', '')) > 100 else getattr(asana, 'description', 'Описание асаны')
            
            asanas.append(SequenceItem(
                asana_name=asana_name,
                asana_category=asana_category,
                duration_seconds=time_per_asana,
                description=asana_description,
                image_path=self._get_image_path(asana) if not isinstance(asana, str) else None
            ))
        
        return asanas
    
    def _difficulty_to_number(self, difficulty: SequenceDifficulty) -> int:
        """Конвертирует Enum сложности в число"""
        mapping = {
            SequenceDifficulty.BEGINNER: 2,
            SequenceDifficulty.INTERMEDIATE: 3,
            SequenceDifficulty.ADVANCED: 4
        }
        return mapping.get(difficulty, 3)
    
    def _get_image_path(self, asana) -> str:
        """Получает путь к изображению асаны"""
        # Если асана - это строка, возвращаем None
        if isinstance(asana, str):
            return None
        
        # Используем существующую логику из data_service
        try:
            category = getattr(asana, 'category', 'unknown')
            name = getattr(asana, 'name', 'unknown')
            return self.data_service._get_image_path(category, name)
        except Exception as e:
            logger.error(f"Error getting image path for asana {asana}: {e}")
            return None
    
    def _estimate_calories(self, params: SequenceParams, duration_seconds: int) -> int:
        """Оценивает расход калорий"""
        # Базовые метаболические эквиваленты (MET)
        met_by_difficulty = {
            SequenceDifficulty.BEGINNER: 2.5,
            SequenceDifficulty.INTERMEDIATE: 3.0,
            SequenceDifficulty.ADVANCED: 3.5
        }
        
        met = met_by_difficulty.get(params.difficulty, 3.0)
        # Предполагаемый вес 70 кг
        calories_per_minute = met * 70 / 60
        total_calories = int(calories_per_minute * (duration_seconds / 60))
        
        return total_calories
