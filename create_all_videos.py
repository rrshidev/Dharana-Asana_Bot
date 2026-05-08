import os
import sys
sys.path.append('src')

from src.data.asana_effects import ASANA_EFFECTS, ASANA_DIFFICULTY
from src.services.database_service import db_service
from src.models.video_models import AsanaVideo
from sqlalchemy import func

def create_videos_for_all_asanas():
    """Создает записи видео для всех асан из ASANA_EFFECTS"""
    
    session = db_service.get_session()
    try:
        # Получаем все существующие видео
        existing_videos = {video.asana_name for video in session.query(AsanaVideo).all()}
        print(f"Существующих видео в базе: {len(existing_videos)}")
        
        # Создаем видео для всех асан
        created_count = 0
        for asana_name in ASANA_EFFECTS.keys():
            if asana_name not in existing_videos:
                # Конвертируем список эффектов в строку
                effects_str = ", ".join(ASANA_EFFECTS.get(asana_name, []))
                
                # Создаем видео запись
                video = AsanaVideo(
                    asana_name=asana_name,
                    video_path=f"videos/{asana_name}.mp4",
                    video_url=None,
                    thumbnail_path=None,
                    duration=300,  # 5 минут по умолчанию
                    file_size=50000000,  # 50MB по умолчанию
                    resolution="1920x1080",
                    format="mp4",
                    description=f"Видео-инструкция для асаны {asana_name}",
                    instructor_name="Йога инструктор",
                    difficulty_level=ASANA_DIFFICULTY.get(asana_name, 1),
                    focus_points=effects_str,
                    is_premium=True,  # Все видео премиум
                    is_active=True
                )
                
                session.add(video)
                created_count += 1
                print(f"Создано видео для: {asana_name}")
        
        session.commit()
        print(f"Всего создано видео: {created_count}")
        
        # Показываем статистику
        total_videos = session.query(AsanaVideo).count()
        print(f"Всего видео в базе: {total_videos}")
        
    except Exception as e:
        print(f"Ошибка: {e}")
        session.rollback()
    finally:
        session.close()

def update_video_filenames_to_russian():
    """Обновляет пути к видео файлам на русские названия"""
    
    session = db_service.get_session()
    try:
        videos = session.query(AsanaVideo).all()
        
        for video in videos:
            # Используем русское название асаны как имя файла
            old_path = video.video_path
            new_path = f"videos/{video.asana_name}.mp4"
            
            if old_path != new_path:
                video.video_path = new_path
                print(f"Обновлен путь: {old_path} -> {new_path}")
        
        session.commit()
        print("Все пути к видео файлам обновлены на русские названия")
        
    except Exception as e:
        print(f"Ошибка: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    print("Создание видео для всех асан...")
    create_videos_for_all_asanas()
    
    print("\nОбновление путей к видео файлам...")
    update_video_filenames_to_russian()
    
    print("\nГотово! Теперь можно добавлять видео файлы с русскими названиями.")
