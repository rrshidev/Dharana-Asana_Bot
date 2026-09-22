import os
import logging
import random
from os import listdir
from os.path import exists, join, isfile, basename
from typing import List, Dict, Optional

from src.models.data_models import AsanaData, CategoryData, BotData
from src.data.asana_effects import ASANA_EFFECTS, ASANA_DIFFICULTY, ASANA_CONTRAINDICATIONS
from src.i18n import t

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
        
        file_list = []
        for item in listdir(category_path):
            if not isfile(join(category_path, item)):
                continue
            # Локализованные файлы "<имя>.en.txt/.jpg/.png" — контент ТОЙ ЖЕ асаны,
            # а не отдельная асана. Иначе в каталог попадают фейковые имена с ".en",
            # и «Асана дня» присылает английский контент без картинки.
            stem = os.path.splitext(item)[0]
            if stem.lower().endswith('.en'):
                continue
            file_list.append(stem)
        
        # Удаляем дубликаты только в пределах категории и сортируем
        return sorted(list(set(file_list)))
    
    def _load_basics(self) -> List[str]:
        """Загружает список основ йоги"""
        if not exists(self.basics_dir):
            return []
        
        basics_files = [item for item in os.listdir(self.basics_dir) if isfile(join(self.basics_dir, item)) and not item.endswith('.en.txt')]
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
        
        steps_files = [item for item in os.listdir(self.steps_dir) if isfile(join(self.steps_dir, item)) and not item.endswith('.en.txt')]
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
    
    def localized_category_name(self, category_name: str, lang: str = 'ru') -> str:
        """Локализованное название категории."""
        return t(lang, f'cat_name_{category_name}')

    def localized_category_desc(self, category_name: str, lang: str = 'ru') -> str:
        """Локализованное описание категории."""
        return t(lang, f'cat_desc_{category_name}')

    def localized_asana_name(self, asana_name: str, lang: str = 'ru') -> str:
        """Локализованное имя асаны (для EN берём первую строку <имя>.en.txt)."""
        lang = 'en' if str(lang).lower().startswith('en') else 'ru'
        if lang == 'en':
            for category in self.load_data().categories.values():
                if asana_name in category.asanas:
                    en_path = join(self.catalog_dir, category.name, f"{asana_name}.en.txt")
                    if exists(en_path):
                        try:
                            with open(en_path, 'r', encoding='utf-8') as f:
                                first_line = f.readline().strip()
                                if first_line:
                                    return first_line
                        except Exception as e:
                            logger.error(f"Error reading {en_path}: {e}")
                    break
        return asana_name

    def get_asana_data(self, asana_name: str, lang: str = 'ru') -> Optional[AsanaData]:
        """Получает данные асаны по имени (для lang='en' — EN-имена и EN-описание)"""
        data = self.load_data()
        lang = 'en' if str(lang).lower().startswith('en') else 'ru'
        
        for category_name, category in data.categories.items():
            if asana_name in category.asanas:
                txt_path = join(self.catalog_dir, category_name, f"{asana_name}.txt")
                en_txt_path = join(self.catalog_dir, category_name, f"{asana_name}.en.txt")
                jpg_path = join(self.catalog_dir, category_name, f"{asana_name}.jpg")
                png_path = join(self.catalog_dir, category_name, f"{asana_name}.png")
                
                description = ""
                display_name = asana_name
                if lang == 'en' and exists(en_txt_path):
                    try:
                        with open(en_txt_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        lines = content.split('\n', 1)
                        display_name = lines[0].strip() or asana_name
                        description = content
                    except Exception as e:
                        logger.error(f"Error reading {en_txt_path}: {e}")
                elif exists(txt_path):
                    try:
                        with open(txt_path, 'r', encoding='utf-8') as f:
                            description = f.read()
                    except Exception as e:
                        logger.error(f"Error reading {txt_path}: {e}")
                
                if not description and lang == 'en':
                    if exists(txt_path):
                        try:
                            with open(txt_path, 'r', encoding='utf-8') as f:
                                description = f.read()
                        except Exception as e:
                            logger.error(f"Error reading {txt_path}: {e}")
                
                thumbnail_path = png_path if exists(png_path) else None
                
                return AsanaData(
                    name=display_name,
                    base_name=asana_name,
                    description=description,
                    image_path=jpg_path if exists(jpg_path) else "",
                    thumbnail_path=thumbnail_path,
                    category=category_name
                )
        
        return None

    def get_random_asana(self, lang: str = 'ru') -> Optional[AsanaData]:
        """Получает случайную асану"""
        import random

        data = self.load_data()
        all_asanas = []

        for category in data.categories.values():
            all_asanas.extend(category.asanas)

        if not all_asanas:
            return None

        random_asana_name = random.choice(all_asanas)
        return self.get_asana_data(random_asana_name, lang)
    
    def find_asana(self, query: str, lang: str = 'ru') -> Optional[AsanaData]:
        """Поиск асаны: по базовому имени или по локализованному (для EN)."""
        lang = 'en' if str(lang).lower().startswith('en') else 'ru'
        q = query.strip().lower()

        # Сначала по базовому (файловому) имени
        data = self.load_data()
        for category in data.categories.values():
            for asana in category.asanas:
                if asana.lower() == q:
                    return self.get_asana_data(asana, lang)

        # EN: пробуем по локализованному имени
        if lang == 'en':
            for category in data.categories.values():
                for asana in category.asanas:
                    en_name = self.localized_asana_name(asana, 'en').lower()
                    if en_name == q:
                        return self.get_asana_data(asana, 'en')

        return None

    def _parse_base_name(self, fname: str) -> str:
        """Имя файла без расширения и без ведущего числового префикса ('2.НИЯМА.txt' -> 'НИЯМА')."""
        name = fname
        for ext in ('.txt', '.png', '.jpg'):
            if name.endswith(ext):
                name = name[:-len(ext)]
                break
        if name and name[0].isdigit():
            parts = name.split('.', 1)
            if len(parts) > 1:
                return parts[1].strip()
        return name

    def _find_base_file(self, directory: str, name: str, exts: tuple) -> Optional[str]:
        """Находит файл в каталоге, чьё распарсенное имя точно равно name."""
        if not exists(directory):
            return None
        for item in os.listdir(directory):
            if not item.endswith(exts):
                continue
            if item.endswith('.en.txt'):
                continue
            if self._parse_base_name(item) == name:
                return join(directory, item)
        return None

    def _find_txt_file(self, directory: str, name: str) -> Optional[str]:
        return self._find_base_file(directory, name, ('.txt',))

    def localized_basic_name(self, basic_name: str, lang: str = 'ru') -> str:
        """Локализованное имя основы йоги (для EN — первая строка <файл>.en.txt)."""
        lang = 'en' if str(lang).lower().startswith('en') else 'ru'
        if lang != 'en':
            return basic_name
        txt_path = self._find_txt_file(self.basics_dir, basic_name)
        if txt_path:
            en_path = txt_path[:-4] + '.en.txt'
            if exists(en_path):
                try:
                    with open(en_path, 'r', encoding='utf-8') as f:
                        first_line = f.readline().strip()
                        if first_line:
                            return first_line
                except Exception as e:
                    logger.error(f"Error reading {en_path}: {e}")
        return basic_name

    def localized_step_name(self, step_name: str, lang: str = 'ru') -> str:
        """Локализованное имя ступени йоги (для EN — первая строка <файл>.en.txt)."""
        lang = 'en' if str(lang).lower().startswith('en') else 'ru'
        if lang != 'en':
            return step_name
        txt_path = self._find_txt_file(self.steps_dir, step_name)
        if txt_path:
            en_path = txt_path[:-4] + '.en.txt'
            if exists(en_path):
                try:
                    with open(en_path, 'r', encoding='utf-8') as f:
                        first_line = f.readline().strip()
                        if first_line:
                            return first_line
                except Exception as e:
                    logger.error(f"Error reading {en_path}: {e}")
        return step_name

    def get_basic_content(self, basic_name: str, lang: str = 'ru') -> tuple[str, Optional[str]]:
        """Получает контент для основы йоги"""
        # Добавим логирование для диагностики
        logger.info(f"Looking for basic: '{basic_name}'")
        lang = 'en' if str(lang).lower().startswith('en') else 'ru'
        
        txt_path = self._find_txt_file(self.basics_dir, basic_name)
        png_path = self._find_base_file(self.basics_dir, basic_name, ('.png',))
        if png_path:
            logger.info(f"Found png: {basename(png_path)}")
        
        if txt_path is None:
            logger.warning(f"Txt file not found for: '{basic_name}'")
            return "", png_path if png_path and exists(png_path) else None
        
        read_path = txt_path
        if lang == 'en':
            en_path = txt_path[:-4] + '.en.txt'
            if exists(en_path):
                read_path = en_path
        
        content = ""
        try:
            with open(read_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Error reading {read_path}: {e}")
        
        image_path = png_path if png_path and exists(png_path) else None
        
        return content, image_path
    
    def get_asana_content(self, asana_name: str) -> tuple[str, Optional[str]]:
        """Получает контент и изображение для асаны"""
        data = self.load_data()
        
        # Ищем асану во всех категорориях
        for category_name, category in data.categories.items():
            if asana_name in category.asanas:
                category_path = join(self.catalog_dir, category_name)
                logger.info(f"Looking for asana '{asana_name}' in category '{category_name}'")
                
                # Ищем txt файл
                txt_path = None
                png_path = None
                jpg_path = None
                
                try:
                    files = os.listdir(category_path)
                    logger.info(f"Files in category: {files[:10]}...")  # Показываем первые 10 файлов
                    
                    for item in files:
                        item_name = os.path.splitext(item)[0]  # Получаем имя без расширения
                        if item_name == asana_name:
                            if item.endswith('.txt'):
                                txt_path = join(category_path, item)
                                logger.info(f"Found txt: {item}")
                            elif item.endswith('.png'):
                                png_path = join(category_path, item)
                                logger.info(f"Found png: {item}")
                            elif item.endswith('.jpg'):
                                jpg_path = join(category_path, item)
                                logger.info(f"Found jpg: {item}")
                except Exception as e:
                    logger.error(f"Error listing files in {category_path}: {e}")
                
                content = ""
                if txt_path and exists(txt_path):
                    try:
                        with open(txt_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            logger.info(f"Successfully read {len(content)} characters from {txt_path}")
                    except Exception as e:
                        logger.error(f"Error reading {txt_path}: {e}")
                else:
                    logger.warning(f"Txt file not found for: '{asana_name}' (tried: {txt_path})")
                    logger.info(f"Available txt files in {category_path}: {[f for f in files if f.endswith('.txt')]}")
                
                image_path = None
                logger.info(f"Image paths found - JPG: {jpg_path}, PNG: {png_path}")
                
                if jpg_path and exists(jpg_path):
                    image_path = jpg_path
                    logger.info(f"✅ Using JPG image: {jpg_path}")
                elif png_path and exists(png_path):
                    image_path = png_path
                    logger.info(f"⚠️ Using PNG image (no JPG found): {png_path}")
                else:
                    logger.warning(f"❌ No image found for: '{asana_name}'")
                
                return content, image_path
        
        logger.warning(f"Asana '{asana_name}' not found in any category")
        return "", None
    
    def get_step_content(self, step_name: str, lang: str = 'ru') -> str:
        """Получает контент для ступени йоги"""
        lang = 'en' if str(lang).lower().startswith('en') else 'ru'
        txt_path = self._find_txt_file(self.steps_dir, step_name)
        
        if txt_path is None:
            return ""
        
        read_path = txt_path
        if lang == 'en':
            en_path = txt_path[:-4] + '.en.txt'
            if exists(en_path):
                read_path = en_path
        
        try:
            with open(read_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading {read_path}: {e}")
        
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
    
    def get_all_asanas(self) -> List[AsanaData]:
        """Получить все асаны в виде объектов AsanaData с реальными данными"""
        data = self.load_data()
        all_asanas = []
        
        # Собираем все реальные асаны с файлами
        real_asanas = set()
        for category_name, category in data.categories.items():
            for asana_name in category.asanas:
                real_asanas.add(asana_name)
        
        # Добавляем только те асаны из ASANA_EFFECTS, у которых есть файлы
        for asana_name, effects in ASANA_EFFECTS.items():
            if asana_name in real_asanas:
                # Ищем категорию для асаны
                category_name = None
                for cat_name, category in data.categories.items():
                    if asana_name in category.asanas:
                        category_name = cat_name
                        break
                
                # Если категория не найдена, все равно добавляем асану
                if not category_name:
                    category_name = "unknown"
                
                # Создаем объект AsanaData с реальными параметрами
                asana_data = AsanaData(
                    name=asana_name,
                    description="",  # Будет загружено при необходимости
                    image_path="",   # Будет загружено при необходимости
                    category=category_name,
                    difficulty=ASANA_DIFFICULTY.get(asana_name, 1),  # По умолчанию начальный уровень
                    effects=effects,     # Реальные эффекты из ASANA_EFFECTS
                    contraindications=ASANA_CONTRAINDICATIONS.get(asana_name, [])  # Реальные противопоказания
                )
                all_asanas.append(asana_data)
        
        # Отладочная информация
        logger.info(f"Loaded {len(all_asanas)} asanas with files from ASANA_EFFECTS")
        logger.info(f"Sample asana names: {[a.name for a in all_asanas[:5]]}")
        logger.info(f"Real asanas with files: {len(real_asanas)}")
        
        return all_asanas
