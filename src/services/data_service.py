import os
import logging
import random
from os import listdir
from os.path import exists, join, isfile
from typing import List, Dict, Optional

from src.models.data_models import AsanaData, CategoryData, BotData

logger = logging.getLogger(__name__)


class DataService:
    """Сервис для работы с данными бота"""
    
    def __init__(self):
        self.catalog_dir = "bot_data/catalog"
        self.basics_dir = "bot_data/basics"
        self.steps_dir = "bot_data/steps"
        
        # Кэширование данных и маппинги
        self._cached_data = None
        self._category_mapping = {}  # ID -> category_name
        self._asana_mapping = {}      # ID -> asana_name
        self._basic_mapping = {}       # ID -> basic_name
        self._step_mapping = {}        # ID -> step_name
        
        # Описания категорий
        self.asana_descriptions = {
            'sit_lie+': ['Асаны сидя и лёжа', 'Список асан сидя и лёжа'],
            'stay+': ['Асаны стоя', 'Список асан стоя'],
            'hand+': ['Балансы на руках', 'Список балансов на руках'],
            'coup+': ['Перевёрнутые асаны', 'Список перевернутых асан'],
            'sag+': ['Прогибы', 'Список асан с прогибами'],
            'power+': ['Силовые асаны', 'Список силовых асан'],
        }
        
        self._bot_data: Optional[BotData] = None
    
    def load_data(self) -> BotData:
        """Загружает все данные из файлов"""
        if self._bot_data is None:
            self._bot_data = BotData(
                categories=self._load_categories(),
                basics=self._load_basics(),
                steps=self._load_steps(),
                asana_descriptions=self.asana_descriptions
            )
        return self._bot_data
    
    def _load_categories(self) -> Dict[str, CategoryData]:
        """Загружает категории асан"""
        categories = {}
        
        if not exists(self.catalog_dir):
            logger.error(f"Directory {self.catalog_dir} not found")
            return categories
        
        asana_types = [item for item in os.listdir(self.catalog_dir) if not isfile(join(self.catalog_dir, item))]
        
        for asana_type in asana_types:
            if asana_type in self.asana_descriptions:
                asanas = self._load_asanas_for_category(asana_type)
                categories[asana_type] = CategoryData(
                    name=asana_type,
                    display_name=self.asana_descriptions[asana_type][0],
                    description=self.asana_descriptions[asana_type][1],
                    asanas=asanas
                )
        
        return categories
    
    def _load_asanas_for_category(self, category: str) -> List[str]:
        """Загружает список асан для категории"""
        category_path = join(self.catalog_dir, category)
        if not exists(category_path):
            return []
        
        file_list = [
            os.path.splitext(item)[0] 
            for item in listdir(category_path) 
            if isfile(join(category_path, item))
        ]
        
        # Удаляем дубликаты и сортируем
        return sorted(list(set(file_list)))
    
    def _load_basics(self) -> List[str]:
        """Загружает список основ йоги"""
        if not exists(self.basics_dir):
            return []
        
        basics_files = [item for item in os.listdir(self.basics_dir) if isfile(join(self.basics_dir, item))]
        basics = []
        for basic in basics_files:
            if basic.endswith('.txt'):
                # Убираем номер в начале и расширение
                name = basic[:-4]  # убираем .txt
                # Если начинается с цифр и точки, убираем их
                if name and name[0].isdigit():
                    parts = name.split('.', 1)
                    if len(parts) > 1:
                        name = parts[1].strip()
                basics.append(name)
        return sorted(list(set(basics)))
    
    def _load_steps(self) -> List[str]:
        """Загружает список ступеней йоги"""
        if not exists(self.steps_dir):
            return []
        
        steps_files = [item for item in os.listdir(self.steps_dir) if isfile(join(self.steps_dir, item))]
        steps = []
        for step in steps_files:
            if step.endswith('.txt'):
                # Убираем номер в начале и расширение
                name = step[:-4]  # убираем .txt
                # Если начинается с цифр и точки, убираем их
                if name and name[0].isdigit():
                    parts = name.split('.', 1)
                    if len(parts) > 1:
                        name = parts[1].strip()
                steps.append(name)
        return sorted(list(set(steps)))
    
    def get_asana_data(self, asana_name: str) -> Optional[AsanaData]:
        """Получает данные асаны по имени"""
        data = self.load_data()
        
        for category_name, category in data.categories.items():
            if asana_name in category.asanas:
                txt_path = join(self.catalog_dir, category_name, f"{asana_name}.txt")
                jpg_path = join(self.catalog_dir, category_name, f"{asana_name}.jpg")
                png_path = join(self.catalog_dir, category_name, f"{asana_name}.png")
                
                description = ""
                if exists(txt_path):
                    try:
                        with open(txt_path, 'r', encoding='utf-8') as f:
                            description = f.read()
                    except Exception as e:
                        logger.error(f"Error reading {txt_path}: {e}")
                
                thumbnail_path = png_path if exists(png_path) else None
                
                return AsanaData(
                    name=asana_name,
                    description=description,
                    image_path=jpg_path if exists(jpg_path) else "",
                    thumbnail_path=thumbnail_path,
                    category=category_name
                )
        
        return None
    
    def get_random_asana(self) -> Optional[AsanaData]:
        """Получает случайную асану"""
        import random
        
        data = self.load_data()
        all_asanas = []
        
        for category in data.categories.values():
            all_asanas.extend(category.asanas)
        
        if not all_asanas:
            return None
        
        random_asana_name = random.choice(all_asanas)
        return self.get_asana_data(random_asana_name)
    
    def get_basic_content(self, basic_name: str) -> tuple[str, Optional[str]]:
        """Получает контент для основы йоги"""
        # Добавим логирование для диагностики
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Looking for basic: '{basic_name}'")
        
        # Ищем файл, который заканчивается на basic_name (для поддержки файлов с номерами)
        txt_path = None
        png_path = None
        
        if exists(self.basics_dir):
            # Ищем txt файл
            for item in os.listdir(self.basics_dir):
                if item.endswith('.txt') and item.replace('.txt', '').endswith(basic_name):
                    txt_path = join(self.basics_dir, item)
                    logger.info(f"Found txt: {item}")
                    break
            
            # Ищем png файл с такой же логикой
            for item in os.listdir(self.basics_dir):
                if item.endswith('.png') and item.replace('.png', '').endswith(basic_name):
                    png_path = join(self.basics_dir, item)
                    logger.info(f"Found png: {item}")
                    break
        
        content = ""
        if txt_path and exists(txt_path):
            try:
                with open(txt_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                logger.error(f"Error reading {txt_path}: {e}")
        else:
            logger.warning(f"Txt file not found for: '{basic_name}'")
        
        image_path = png_path if png_path and exists(png_path) else None
        
        return content, image_path
    
    def get_step_content(self, step_name: str) -> str:
        """Получает контент для ступени йоги"""
        # Ищем файл, который заканчивается на step_name (для поддержки файлов с номерами)
        txt_path = None
        
        if exists(self.steps_dir):
            for item in os.listdir(self.steps_dir):
                if item.endswith('.txt') and item.replace('.txt', '').endswith(step_name):
                    txt_path = join(self.steps_dir, item)
                    break
        
        if txt_path and exists(txt_path):
            try:
                with open(txt_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error reading {txt_path}: {e}")
        
        return ""
    
    def get_category_by_id(self, category_id: str) -> Optional[str]:
        """Получает имя категории по ID"""
        data = self.load_data()
        if not self._category_mapping:
            # Строим маппинг категорий
            categories = list(data.categories.keys())
            for i, category in enumerate(categories):
                self._category_mapping[f'category_{i}'] = category
        
        return self._category_mapping.get(category_id)
    
    def get_category_global_start_index(self, category_name: str) -> int:
        """Получает глобальный стартовый индекс для категории"""
        data = self.load_data()
        global_index = 0
        for cat_name, category in data.categories.items():
            if cat_name == category_name:
                return global_index
            global_index += len(category.asanas)
        return 0
    
    def get_asana_by_id(self, asana_id: str) -> Optional[str]:
        """Получает имя асаны по ID"""
        data = self.load_data()
        if not self._asana_mapping:
            # Строим маппинг асан по категориям
            global_asana_index = 0
            for category_name, category in data.categories.items():
                for asana in category.asanas:
                    self._asana_mapping[f'asana_{global_asana_index}'] = asana
                    global_asana_index += 1
        
        return self._asana_mapping.get(asana_id)
    
    def get_basic_by_id(self, basic_id: str) -> Optional[str]:
        """Получает имя основы по ID"""
        data = self.load_data()
        if not self._basic_mapping:
            # Строим маппинг основ
            for i, basic in enumerate(data.basics):
                self._basic_mapping[f'basic_{i}'] = basic
        
        return self._basic_mapping.get(basic_id)
    
    def get_step_by_id(self, step_id: str) -> Optional[str]:
        """Получает имя ступени по ID"""
        data = self.load_data()
        if not self._step_mapping:
            # Строим маппинг ступеней
            for i, step in enumerate(data.steps):
                self._step_mapping[f'step_{i}'] = step
        
        return self._step_mapping.get(step_id)
