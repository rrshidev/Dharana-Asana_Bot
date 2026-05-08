from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class AsanaVideo(Base):
    """Модель видео для асан"""
    __tablename__ = 'asana_videos'
    
    id = Column(Integer, primary_key=True)
    asana_name = Column(String(200), nullable=False, index=True)  # Название асаны
    video_path = Column(String(500), nullable=False)  # Путь к видеофайлу
    video_url = Column(String(500))  # URL видео (если храним в облаке)
    thumbnail_path = Column(String(500))  # Путь к превью-изображению
    
    # Метаданные видео
    duration = Column(Integer)  # Длительность в секундах
    file_size = Column(Integer)  # Размер файла в байтах
    resolution = Column(String(20))  # Разрешение (1920x1080)
    format = Column(String(10))  # Формат (mp4, mov, etc.)
    
    # Контентная информация
    description = Column(Text)  # Описание видео
    instructor_name = Column(String(100))  # Имя инструктора
    difficulty_level = Column(Integer)  # Уровень сложности 1-5
    focus_points = Column(String(500))  # Ключевые моменты через запятую
    
    # Статус и доступность
    is_premium = Column(Boolean, default=True)  # Только для премиум
    is_active = Column(Boolean, default=True)  # Активно ли видео
    views_count = Column(Integer, default=0)  # Счетчик просмотров
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<AsanaVideo(asana='{self.asana_name}', premium={self.is_premium})>"

class VideoProcessingQueue(Base):
    """Очередь обработки видео"""
    __tablename__ = 'video_processing_queue'
    
    id = Column(Integer, primary_key=True)
    video_path = Column(String(500), nullable=False)
    status = Column(String(20), default='pending')  # pending, processing, completed, failed
    asana_name = Column(String(200))
    
    # Параметры обработки
    needs_thumbnail = Column(Boolean, default=True)
    needs_compression = Column(Boolean, default=False)  # Нужно ли сжать
    target_resolution = Column(String(20), default='1280x720')
    
    # Результаты обработки
    processed_path = Column(String(500))
    thumbnail_path = Column(String(500))
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    
    def __repr__(self):
        return f"<VideoProcessingQueue(status='{self.status}', asana='{self.asana_name}')>"
