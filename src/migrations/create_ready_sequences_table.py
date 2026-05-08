"""
Миграция для создания таблицы готовых комплексов
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.database_service import db_service
from src.models.ready_sequence_models import ReadySequence
import logging

logger = logging.getLogger(__name__)

def create_ready_sequences_table():
    """Создает таблицу готовых комплексов"""
    try:
        engine = db_service.engine
        ReadySequence.metadata.create_all(engine)
        logger.info("Таблица ready_sequences успешно создана")
        return True
    except Exception as e:
        logger.error(f"Ошибка при создании таблицы ready_sequences: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_ready_sequences_table()
