import os
from pathlib import Path

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN", "5837988056:AAF_your_token_here")

# База данных
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot_data/yoga_bot.db")

# Создаем директорию для БД если нет
db_dir = Path("bot_data")
db_dir.mkdir(exist_ok=True)

# Пути к данным
CATALOG_DIR = "bot_data/catalog"
BASICS_DIR = "bot_data/basics"
STEPS_DIR = "bot_data/steps"

# Настройки асаны дня
DEFAULT_DAILY_ASANA_TIME = "09:00"
DEFAULT_TIMEZONE = "UTC"

# Премиум настройки
PREMIUM_MONTHLY_PRICE = 399  # руб
PREMIUM_YEARLY_PRICE = 2990  # руб
