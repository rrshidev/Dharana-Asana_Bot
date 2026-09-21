from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ReadySequence(Base):
    """Модель для готовых комплексов"""
    __tablename__ = 'ready_sequences'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)  # Название комплекса
    description = Column(Text, nullable=False)  # Описание
    video_path = Column(String(500))  # Путь к видео файлу
    video_url = Column(String(500))   # URL видео (если есть)
    thumbnail_path = Column(String(500))  # Путь к превью
    duration = Column(Integer, default=30)  # Длительность в минутах
    difficulty_level = Column(Integer, default=1)  # 1-3 уровень сложности
    focus_areas = Column(String(500))  # Зоны воздействия (строка)
    category = Column(String(100))  # Категория (утро/вечер/энергия и т.д.)
    instructor_name = Column(String(255), default="Йога инструктор")
    is_premium = Column(Boolean, default=True)  # Премиум или бесплатный
    is_active = Column(Boolean, default=True)  # Активен ли комплекс
    views_count = Column(Integer, default=0)  # Счетчик просмотров
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ReadySequence(id={self.id}, name='{self.name}', premium={self.is_premium})>"
    
    def to_dict(self):
        """Конвертирует модель в словарь"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'video_path': self.video_path,
            'video_url': self.video_url,
            'thumbnail_path': self.thumbnail_path,
            'duration': self.duration,
            'difficulty_level': self.difficulty_level,
            'focus_areas': self.focus_areas,
            'category': self.category,
            'instructor_name': self.instructor_name,
            'is_premium': self.is_premium,
            'is_active': self.is_active,
            'views_count': self.views_count,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
