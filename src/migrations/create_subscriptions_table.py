"""
Миграция для создания таблицы подписок пользователей
"""

import logging
from sqlalchemy import text

from src.services.database_service import db_service

logger = logging.getLogger(__name__)

def create_subscriptions_table():
    """Создает таблицу user_subscriptions"""
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS user_subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE NOT NULL,
        is_premium BOOLEAN DEFAULT 0,
        subscription_type VARCHAR(20) DEFAULT NULL,
        subscription_status VARCHAR(20) DEFAULT NULL,
        subscription_start DATETIME DEFAULT NULL,
        subscription_end DATETIME DEFAULT NULL,
        trial_used BOOLEAN DEFAULT 0,
        trial_start DATETIME DEFAULT NULL,
        trial_end DATETIME DEFAULT NULL,
        daily_generations_used INTEGER DEFAULT 0,
        last_generation_date DATE DEFAULT NULL,
        payment_id VARCHAR(100) DEFAULT NULL,
        payment_provider VARCHAR(50) DEFAULT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Создаем индексы для оптимизации
    create_indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_user_subscriptions_telegram_id ON user_subscriptions(telegram_id);",
        "CREATE INDEX IF NOT EXISTS idx_user_subscriptions_is_premium ON user_subscriptions(is_premium);",
        "CREATE INDEX IF NOT EXISTS idx_user_subscriptions_last_generation_date ON user_subscriptions(last_generation_date);"
    ]
    
    try:
        session = db_service.get_session()
        
        # Создаем таблицу
        session.execute(text(create_table_sql))
        
        # Создаем индексы
        for index_sql in create_indexes_sql:
            session.execute(text(index_sql))
        
        session.commit()
        logger.info("✅ Таблица user_subscriptions успешно создана")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при создании таблицы user_subscriptions: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def run_migration():
    """Запускает миграцию"""
    logger.info("🔄 Запуск миграции: создание таблицы подписок")
    
    success = create_subscriptions_table()
    
    if success:
        logger.info("✅ Миграция успешно завершена")
    else:
        logger.error("❌ Миграция завершилась с ошибкой")
    
    return success

if __name__ == "__main__":
    run_migration()
