import os
import logging
from typing import Optional, List
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.models.video_models import AsanaVideo, VideoProcessingQueue
from src.services.database_service import DatabaseService

logger = logging.getLogger(__name__)

class VideoService:
    """Сервис для работы с видео асан"""
    
    def __init__(self, database_service: DatabaseService):
        self.db = database_service
        self.videos_dir = Path("videos")
        self.thumbnails_dir = Path("videos/thumbnails")
        
        # Создаем папки если их нет
        self.videos_dir.mkdir(exist_ok=True)
        self.thumbnails_dir.mkdir(exist_ok=True)
    
    def add_video(self, asana_name: str, video_path: str, is_premium: bool = True,
                  description: str = None, instructor_name: str = None,
                  difficulty_level: int = 1, focus_points: str = None) -> AsanaVideo:
        """Добавляет видео для асаны"""
        session = self.db.get_session()
        try:
            video = AsanaVideo(
                asana_name=asana_name,
                video_path=video_path,
                is_premium=is_premium,
                description=description,
                instructor_name=instructor_name,
                difficulty_level=difficulty_level,
                focus_points=focus_points
            )
            
            session.add(video)
            session.commit()
            logger.info(f"Added video for asana: {asana_name}")
            return video
            
        except Exception as e:
            logger.error(f"Error adding video: {e}")
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_video_for_asana(self, asana_name: str, is_premium_user: bool = False) -> Optional[dict]:
        """Получает видео для асаны с учетом премиум-статуса"""
        session = self.db.get_session()
        try:
            # Ищем видео без учета регистра
            logger.info(f"Searching for video: '{asana_name}', is_premium_user={is_premium_user}")
            video = session.query(AsanaVideo).filter(
                func.lower(AsanaVideo.asana_name) == func.lower(asana_name),
                AsanaVideo.is_active == True
            ).first()
            
            if not video:
                logger.info(f"No video found for '{asana_name}'")
                return None
            
            logger.info(f"Found video: {video.asana_name}, is_premium={video.is_premium}")
            
            # Увеличиваем счетчик просмотров
            video.views_count += 1
            session.commit()
            
            # НЕ проверяем премиум-статус здесь - возвращаем видео всегда
            # Проверка будет в UI слое для показа правильного контента
            logger.info(f"Returning video for '{asana_name}' (premium check will be in UI)")
            
            # Возвращаем словарь вместо объекта ORM
            return {
                'id': video.id,
                'asana_name': video.asana_name,
                'video_path': video.video_path,
                'video_url': video.video_url,
                'thumbnail_path': video.thumbnail_path,
                'duration': video.duration,
                'file_size': video.file_size,
                'resolution': video.resolution,
                'format': video.format,
                'description': video.description,
                'instructor_name': video.instructor_name,
                'difficulty_level': video.difficulty_level,
                'focus_points': video.focus_points,
                'is_premium': video.is_premium,
                'is_active': video.is_active,
                'views_count': video.views_count,
                'created_at': video.created_at,
                'updated_at': video.updated_at
            }
            
        except Exception as e:
            logger.error(f"Error getting video for asana {asana_name}: {e}")
            return None
        finally:
            session.close()
    
    def get_all_videos(self, is_premium_user: bool = False, limit: int = 50) -> List[AsanaVideo]:
        """Получает все доступные видео"""
        session = self.db.get_session()
        try:
            query = session.query(AsanaVideo).filter(AsanaVideo.is_active == True)
            
            # Если пользователь не премиум, фильтруем премиум-видео
            if not is_premium_user:
                query = query.filter(AsanaVideo.is_premium == False)
            
            videos = query.order_by(AsanaVideo.views_count.desc()).limit(limit).all()
            return videos
            
        except Exception as e:
            logger.error(f"Error getting all videos: {e}")
            return []
        finally:
            session.close()
    
    def get_popular_videos(self, is_premium_user: bool = False, limit: int = 10) -> List[AsanaVideo]:
        """Получает популярные видео"""
        session = self.db.get_session()
        try:
            query = session.query(AsanaVideo).filter(AsanaVideo.is_active == True)
            
            if not is_premium_user:
                query = query.filter(AsanaVideo.is_premium == False)
            
            videos = query.order_by(AsanaVideo.views_count.desc()).limit(limit).all()
            return videos
            
        except Exception as e:
            logger.error(f"Error getting popular videos: {e}")
            return []
        finally:
            session.close()
    
    def update_video(self, video_id: int, **kwargs) -> bool:
        """Обновляет информацию о видео"""
        session = self.db.get_session()
        try:
            video = session.query(AsanaVideo).filter(AsanaVideo.id == video_id).first()
            if not video:
                return False
            
            for key, value in kwargs.items():
                if hasattr(video, key):
                    setattr(video, key, value)
            
            session.commit()
            logger.info(f"Updated video {video_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating video {video_id}: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def delete_video(self, video_id: int) -> bool:
        """Удаляет видео"""
        session = self.db.get_session()
        try:
            video = session.query(AsanaVideo).filter(AsanaVideo.id == video_id).first()
            if not video:
                return False
            
            # Удаляем файлы
            if video.video_path and os.path.exists(video.video_path):
                os.remove(video.video_path)
            
            if video.thumbnail_path and os.path.exists(video.thumbnail_path):
                os.remove(video.thumbnail_path)
            
            session.delete(video)
            session.commit()
            logger.info(f"Deleted video {video_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting video {video_id}: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_video_stats(self) -> dict:
        """Получает статистику видео"""
        session = self.db.get_session()
        try:
            total_videos = session.query(AsanaVideo).filter(AsanaVideo.is_active == True).count()
            premium_videos = session.query(AsanaVideo).filter(
                AsanaVideo.is_active == True,
                AsanaVideo.is_premium == True
            ).count()
            free_videos = total_videos - premium_videos
            
            total_views = session.query(AsanaVideo).filter(AsanaVideo.is_active == True).with_entities(
                func.sum(AsanaVideo.views_count)
            ).scalar() or 0
            
            return {
                'total_videos': total_videos,
                'premium_videos': premium_videos,
                'free_videos': free_videos,
                'total_views': total_views
            }
            
        except Exception as e:
            logger.error(f"Error getting video stats: {e}")
            return {}
        finally:
            session.close()
    
    def search_videos(self, query: str, is_premium_user: bool = False) -> List[AsanaVideo]:
        """Поиск видео по названию асаны"""
        session = self.db.get_session()
        try:
            db_query = session.query(AsanaVideo).filter(
                AsanaVideo.asana_name.ilike(f"%{query}%"),
                AsanaVideo.is_active == True
            )
            
            if not is_premium_user:
                db_query = db_query.filter(AsanaVideo.is_premium == False)
            
            videos = db_query.order_by(AsanaVideo.views_count.desc()).all()
            return videos
            
        except Exception as e:
            logger.error(f"Error searching videos: {e}")
            return []
        finally:
            session.close()

# Список популярных асан для видео
POPULAR_ASANAS = [
    "Тадасана (Поза горы)",
    "Адхо Мукха Шванасана (Собака мордой вниз)",
    "Врикшасана (Дерево)",
    "Падмасана (Лотос)",
    "Вирабхадрасана I (Воин 1)",
    "Бхуджангасана (Кобра)",
    "Гомухасана (Коза)",
    "Капотасана (Голубь)",
    "Уттхита Тадасана (Звезда)",
    "Сурья Намаскар (Приветствие солнцу)",
    "Баласана (Поза ребенка)",
    "Уттанасана (Наклон вперед)",
    "Триконасана (Треугольник)",
    "Арда Чандрасана (Полумесяц)",
    "Шавасана (Поза трупа)"
]
