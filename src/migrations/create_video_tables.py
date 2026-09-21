"""
Миграция для создания таблиц видео
"""

import logging
from sqlalchemy import text

from src.services.database_service import db_service

logger = logging.getLogger(__name__)

def create_video_tables():
    """Создает таблицы для видео"""
    
    # Таблица asana_videos
    create_videos_sql = """
    CREATE TABLE IF NOT EXISTS asana_videos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asana_name VARCHAR(200) NOT NULL,
        video_path VARCHAR(500) NOT NULL,
        video_url VARCHAR(500),
        thumbnail_path VARCHAR(500),
        duration INTEGER,
        file_size INTEGER,
        resolution VARCHAR(20),
        format VARCHAR(10),
        description TEXT,
        instructor_name VARCHAR(100),
        difficulty_level INTEGER,
        focus_points VARCHAR(500),
        is_premium BOOLEAN DEFAULT 1,
        is_active BOOLEAN DEFAULT 1,
        views_count INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Таблица video_processing_queue
    create_queue_sql = """
    CREATE TABLE IF NOT EXISTS video_processing_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_path VARCHAR(500) NOT NULL,
        status VARCHAR(20) DEFAULT 'pending',
        asana_name VARCHAR(200),
        needs_thumbnail BOOLEAN DEFAULT 1,
        needs_compression BOOLEAN DEFAULT 0,
        target_resolution VARCHAR(20) DEFAULT '1280x720',
        processed_path VARCHAR(500),
        thumbnail_path VARCHAR(500),
        error_message TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        processed_at DATETIME
    );
    """
    
    # Создаем индексы
    create_indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_asana_videos_asana_name ON asana_videos(asana_name);",
        "CREATE INDEX IF NOT EXISTS idx_asana_videos_is_premium ON asana_videos(is_premium);",
        "CREATE INDEX IF NOT EXISTS idx_asana_videos_is_active ON asana_videos(is_active);",
        "CREATE INDEX IF NOT EXISTS idx_asana_videos_views_count ON asana_videos(views_count);",
        "CREATE INDEX IF NOT EXISTS idx_video_queue_status ON video_processing_queue(status);"
    ]
    
    try:
        session = db_service.get_session()
        
        # Создаем таблицы
        session.execute(text(create_videos_sql))
        session.execute(text(create_queue_sql))
        
        # Создаем индексы
        for index_sql in create_indexes_sql:
            session.execute(text(index_sql))
        
        session.commit()
        logger.info("✅ Таблицы видео успешно созданы")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при создании таблиц видео: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def run_migration():
    """Запускает миграцию"""
    logger.info("🔄 Запуск миграции: создание таблиц видео")
    
    success = create_video_tables()
    
    if success:
        logger.info("✅ Миграция видео успешно завершена")
    else:
        logger.error("❌ Миграция видео завершилась с ошибкой")
    
    return success

if __name__ == "__main__":
    run_migration()
