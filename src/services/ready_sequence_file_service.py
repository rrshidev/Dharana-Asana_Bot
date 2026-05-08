import os
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class ReadySequenceFileService:
    """Сервис для работы с готовыми комплексами на основе файлов"""
    
    def __init__(self):
        self.sequences_dir = "videos/ready_sequences"
        self.premium_dir = os.path.join(self.sequences_dir, "premium")
        self.free_dir = os.path.join(self.sequences_dir, "free")
        
    def get_all_sequences(self) -> List[Dict]:
        """Получает все комплексы из папок premium и free"""
        sequences = []
        
        try:
            # Сканируем папку с бесплатными комплексами
            if os.path.exists(self.free_dir):
                for filename in os.listdir(self.free_dir):
                    if filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                        sequence = self._create_sequence_from_file(filename, self.free_dir, is_premium=False)
                        if sequence:
                            sequences.append(sequence)
                            logger.info(f"Found free sequence: {sequence['name']}")
            
            # Сканируем папку с премиум комплексами
            if os.path.exists(self.premium_dir):
                for filename in os.listdir(self.premium_dir):
                    if filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                        sequence = self._create_sequence_from_file(filename, self.premium_dir, is_premium=True)
                        if sequence:
                            sequences.append(sequence)
                            logger.info(f"Found premium sequence: {sequence['name']}")
            
            # Сортируем по имени
            sequences.sort(key=lambda x: x['name'])
            
        except Exception as e:
            logger.error(f"Error scanning sequences directory: {e}")
        
        return sequences
    
    def _create_sequence_from_file(self, filename: str, directory: str, is_premium: bool) -> Optional[Dict]:
        """Создает информацию о комплексе из файла"""
        try:
            file_path = os.path.join(directory, filename)
            
            # Получаем имя комплекса из имени файла (без расширения)
            sequence_name = os.path.splitext(filename)[0]
            
            # Получаем размер файла
            file_size = os.path.getsize(file_path)
            
            # Пытаемся прочитать описание из .txt файла
            description = self._read_description_from_file(directory, sequence_name)
            
            # Создаем информацию о комплексе
            sequence = {
                'id': hash(f"{sequence_name}_{is_premium}") % 1000000,  # Генерируем уникальный ID
                'name': sequence_name,
                'description': description,
                'video_path': file_path,
                'video_url': None,
                'thumbnail_path': None,
                'duration': self._estimate_duration(sequence_name, file_size),
                'difficulty_level': self._estimate_difficulty(sequence_name),
                'focus_areas': self._extract_focus_areas(sequence_name),
                'category': self._determine_category(sequence_name),
                'instructor_name': 'Йога инструктор',
                'is_premium': is_premium,
                'is_active': True,
                'views_count': 0,
                'created_at': None,
                'updated_at': None
            }
            
            return sequence
            
        except Exception as e:
            logger.error(f"Error creating sequence from file {filename}: {e}")
            return None
    
    def _read_description_from_file(self, directory: str, sequence_name: str) -> str:
        """Читает описание из .txt файла или генерирует автоматически"""
        try:
            # Ищем .txt файл с таким же именем
            txt_path = os.path.join(directory, f"{sequence_name}.txt")
            
            if os.path.exists(txt_path):
                with open(txt_path, 'r', encoding='utf-8') as f:
                    description = f.read().strip()
                    if description:
                        logger.info(f"Loaded description from file: {txt_path}")
                        return description
            
            # Если .txt файл не найден, генерируем описание автоматически
            logger.info(f"Description file not found, generating auto description for: {sequence_name}")
            return self._generate_description(sequence_name)
            
        except Exception as e:
            logger.error(f"Error reading description file for {sequence_name}: {e}")
            return self._generate_description(sequence_name)
    
    def get_sequence_by_name(self, name: str) -> Optional[Dict]:
        """Получает комплекс по названию"""
        sequences = self.get_all_sequences()
        
        for sequence in sequences:
            if sequence['name'].lower() == name.lower():
                return sequence
        
        return None
    
    def get_sequence_by_id(self, sequence_id: int) -> Optional[Dict]:
        """Получает комплекс по ID"""
        sequences = self.get_all_sequences()
        
        for sequence in sequences:
            if sequence['id'] == sequence_id:
                return sequence
        
        return None
    
    def _generate_description(self, sequence_name: str) -> str:
        """Генерирует описание на основе названия"""
        name_lower = sequence_name.lower()
        
        # Базовые описания по ключевым словам
        if 'сурья намаскар' in name_lower:
            return "Классическая последовательность приветствия солнцу. Идеально для утренней практики, помогает разбудить тело и зарядиться энергией на весь день."
        elif 'короткий' in name_lower or '5 мин' in name_lower:
            return "Быстрая практика для занятых людей. Включает основные растяжки и дыхательные упражнения для быстрого восстановления энергии."
        elif 'утренний' in name_lower:
            return "Мягкая утренняя практика для плавного пробуждения тела. Включает легкие растяжки и дыхательные упражнения."
        elif 'вечерний' in name_lower or 'релакс' in name_lower:
            return "Спокойная практика для завершения дня. Включает мягкие наклоны и расслабляющие позы для хорошего сна."
        elif 'герой' in name_lower or 'сила' in name_lower:
            return "Интенсивная силовая практика для развития выносливости и силы. Включает warrior poses и силовые асаны."
        elif 'баланс' in name_lower:
            return "Практика для развития баланса и концентрации внимания. Включает различные позы баланса."
        elif 'гибкость' in name_lower or 'растяжка' in name_lower:
            return "Глубокая практика для развития гибкости всего тела. Включает различные растяжки и асаны на раскрытие суставов."
        else:
            return f"Йога комплекс '{sequence_name}'. Практика для гармоничного развития тела и духа."
    
    def _estimate_duration(self, sequence_name: str, file_size: int) -> int:
        """Оценивает длительность на основе названия и размера файла"""
        name_lower = sequence_name.lower()
        
        # Определяем по ключевым словам
        if '5 мин' in name_lower:
            return 5
        elif 'короткий' in name_lower:
            return 10
        elif 'длинный' in name_lower or 'полный' in name_lower:
            return 60
        
        # Оцениваем по размеру файла (очень приблизительно)
        # ~1MB в минуту для среднего качества
        estimated_minutes = max(5, min(60, file_size // (1024 * 1024)))
        
        return estimated_minutes
    
    def _estimate_difficulty(self, sequence_name: str) -> int:
        """Оценивает сложность на основе названия"""
        name_lower = sequence_name.lower()
        
        if 'начальный' in name_lower or 'базовый' in name_lower or 'основы' in name_lower:
            return 1
        elif 'продвинутый' in name_lower or 'сложный' in name_lower or 'герой' in name_lower:
            return 3
        else:
            return 2  # Средний уровень по умолчанию
    
    def _extract_focus_areas(self, sequence_name: str) -> str:
        """Извлекает зоны воздействия из названия"""
        name_lower = sequence_name.lower()
        
        areas = []
        if 'сурья намаскар' in name_lower or 'энергия' in name_lower:
            areas.append('энергия')
        if 'гибкость' in name_lower or 'растяжка' in name_lower:
            areas.append('гибкость')
        if 'сила' in name_lower or 'герой' in name_lower:
            areas.append('сила')
        if 'баланс' in name_lower:
            areas.append('баланс')
        if 'релакс' in name_lower or 'вечерний' in name_lower:
            areas.append('релакс')
        if 'спина' in name_lower:
            areas.append('спина')
        
        return ', '.join(areas) if areas else 'общее развитие'
    
    def _determine_category(self, sequence_name: str) -> str:
        """Определяет категорию на основе названия"""
        name_lower = sequence_name.lower()
        
        if 'утренний' in name_lower or 'сурья намаскар' in name_lower:
            return 'Утро'
        elif 'вечерний' in name_lower or 'релакс' in name_lower:
            return 'Вечер'
        elif 'короткий' in name_lower or '5 мин' in name_lower:
            return 'Быстрые'
        elif 'сила' in name_lower or 'герой' in name_lower:
            return 'Сила'
        elif 'баланс' in name_lower:
            return 'Балансы'
        elif 'гибкость' in name_lower:
            return 'Гибкость'
        else:
            return 'Общий'
