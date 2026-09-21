import os
import logging
from typing import List, Optional, Dict
from sqlalchemy import func
from src.services.database_service import db_service
from src.models.ready_sequence_models import ReadySequence

logger = logging.getLogger(__name__)

class ReadySequenceService:
    """Сервис для работы с готовыми комплексами"""
    
    def __init__(self, database_service):
        self.db = database_service
    
    def add_ready_sequence(self, name: str, description: str, video_path: str = None,
                          duration: int = 30, difficulty_level: int = 1, 
                          focus_areas: str = "", category: str = "Общий",
                          instructor_name: str = "Йога инструктор", 
                          is_premium: bool = True) -> bool:
        """Добавляет новый готовый комплекс"""
        session = self.db.get_session()
        try:
            sequence = ReadySequence(
                name=name,
                description=description,
                video_path=video_path or f"videos/ready_sequences/{name}.mp4",
                duration=duration,
                difficulty_level=difficulty_level,
                focus_areas=focus_areas,
                category=category,
                instructor_name=instructor_name,
                is_premium=is_premium,
                is_active=True
            )
            
            session.add(sequence)
            session.commit()
            logger.info(f"Added ready sequence: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding ready sequence {name}: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_all_active_sequences(self) -> List[Dict]:
        """Получает все активные комплексы"""
        session = self.db.get_session()
        try:
            sequences = session.query(ReadySequence).filter(
                ReadySequence.is_active == True
            ).order_by(ReadySequence.name).all()
            
            return [sequence.to_dict() for sequence in sequences]
            
        except Exception as e:
            logger.error(f"Error getting ready sequences: {e}")
            return []
        finally:
            session.close()
    
    def get_sequence_by_name(self, name: str, is_premium_user: bool = False) -> Optional[Dict]:
        """Получает комплекс по названию"""
        session = self.db.get_session()
        try:
            # Ищем без учета регистра
            sequence = session.query(ReadySequence).filter(
                func.lower(ReadySequence.name) == func.lower(name),
                ReadySequence.is_active == True
            ).first()
            
            if not sequence:
                return None
            
            # Увеличиваем счетчик просмотров
            sequence.views_count += 1
            session.commit()
            
            # Возвращаем комплекс (проверка премиум будет в UI)
            return sequence.to_dict()
            
        except Exception as e:
            logger.error(f"Error getting ready sequence {name}: {e}")
            return None
        finally:
            session.close()
    
    def get_sequences_by_category(self, category: str) -> List[Dict]:
        """Получает комплексы по категории"""
        session = self.db.get_session()
        try:
            sequences = session.query(ReadySequence).filter(
                func.lower(ReadySequence.category) == func.lower(category),
                ReadySequence.is_active == True
            ).order_by(ReadySequence.name).all()
            
            return [sequence.to_dict() for sequence in sequences]
            
        except Exception as e:
            logger.error(f"Error getting sequences by category {category}: {e}")
            return []
        finally:
            session.close()
    
    def get_categories(self) -> List[str]:
        """Получает все категории"""
        session = self.db.get_session()
        try:
            categories = session.query(ReadySequence.category).filter(
                ReadySequence.is_active == True
            ).distinct().all()
            
            return [cat[0] for cat in categories if cat[0]]
            
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
        finally:
            session.close()
    
    def update_sequence(self, sequence_id: int, **kwargs) -> bool:
        """Обновляет комплекс"""
        session = self.db.get_session()
        try:
            sequence = session.query(ReadySequence).filter(
                ReadySequence.id == sequence_id
            ).first()
            
            if not sequence:
                return False
            
            for key, value in kwargs.items():
                if hasattr(sequence, key):
                    setattr(sequence, key, value)
            
            session.commit()
            logger.info(f"Updated ready sequence {sequence_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating ready sequence {sequence_id}: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def deactivate_sequence(self, sequence_id: int) -> bool:
        """Деактивирует комплекс"""
        return self.update_sequence(sequence_id, is_active=False)
