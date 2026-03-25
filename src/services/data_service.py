import os
import logging
from typing import Dict, List, Optional
from os import listdir
from os.path import join, isfile, exists

from src.models.data_models import AsanaData, CategoryData, BotData

logger = logging.getLogger(__name__)


class DataService:
    """Сервис для работы с данными асан и контента"""
    
    def __init__(self, data_dir: str = "bot_data"):
        self.data_dir = data_dir
        self.catalog_dir = join(data_dir, "catalog")
        self.basics_dir = join(data_dir, "basics")
        self.steps_dir = join(data_dir, "steps")
        
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
        
        asana_types = [item for item in listdir(self.catalog_dir) if not isfile(join(self.catalog_dir, item))]
        
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
        
        basics_files = [item for item in listdir(self.basics_dir) if isfile(join(self.basics_dir, item))]
        basics = [basic[:-4] for basic in basics_files if basic.endswith('.txt')]
        return sorted(list(set(basics)))
    
    def _load_steps(self) -> List[str]:
        """Загружает список ступеней йоги"""
        if not exists(self.steps_dir):
            return []
        
        steps_files = [item for item in listdir(self.steps_dir) if isfile(join(self.steps_dir, item))]
        steps = [step[:-4] for step in steps_files if step.endswith('.txt')]
        return sorted(steps)
    
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
        txt_path = join(self.basics_dir, f"{basic_name}.txt")
        png_path = join(self.basics_dir, f"{basic_name}.png")
        
        content = ""
        if exists(txt_path):
            try:
                with open(txt_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                logger.error(f"Error reading {txt_path}: {e}")
        
        image_path = png_path if exists(png_path) else None
        
        return content, image_path
    
    def get_step_content(self, step_name: str) -> str:
        """Получает контент для ступени йоги"""
        txt_path = join(self.steps_dir, f"{step_name}.txt")
        
        if exists(txt_path):
            try:
                with open(txt_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error reading {txt_path}: {e}")
        
        return ""
