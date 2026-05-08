"""
Демо-скрипт для добавления тестовых видео
"""

import logging
from src.services.database_service import db_service
from src.services.video_service import VideoService, POPULAR_ASANAS

logger = logging.getLogger(__name__)

def create_demo_videos():
    """Создает демо-записи видео для популярных асан"""
    
    video_service = VideoService(db_service)
    
    # Демо-видео с реальными названиями асан из каталога
    demo_videos = [
        {
            'asana_name': 'Падмасана',
            'video_path': 'videos/padmasana_demo.mp4',
            'description': 'Медитативная поза. Открытие тазобедренных суставов.',
            'difficulty_level': 4,
            'focus_points': 'открытие таза, медитация, гибкость'
        },
        {
            'asana_name': 'Гомукхасана',
            'video_path': 'videos/gomukhasana_demo.mp4',
            'description': 'Сидячая поза. Растяжка плеч и таза.',
            'difficulty_level': 3,
            'focus_points': 'растяжка плеч, открытие таза, гибкость'
        },
        {
            'asana_name': 'Вирасана',
            'video_path': 'videos/virasana_demo.mp4',
            'description': 'Поза героя. Укрепление ног и улучшение осанки.',
            'difficulty_level': 2,
            'focus_points': 'укрепление ног, осанка, растяжка стоп'
        },
        {
            'asana_name': 'Дандасана',
            'video_path': 'videos/dandasana_demo.mp4',
            'description': 'Поза посоха. Укрепление мышц кора и спины.',
            'difficulty_level': 2,
            'focus_points': 'укрепление кора, осанка, сила спины'
        },
        {
            'asana_name': 'Джану Ширшасана',
            'video_path': 'videos/janu_sirsasana_demo.mp4',
            'description': 'Поза головы на колене. Глубокая растяжка задней поверхности ноги.',
            'difficulty_level': 2,
            'focus_points': 'растяжка ног, гибкость позвоночника, спокойствие'
        },
        {
            'asana_name': 'Пашчимоттанасана',
            'video_path': 'videos/paschimottanasana_demo.mp4',
            'description': 'Наклон вперед сидя. Полная растяжка задней поверхности тела.',
            'difficulty_level': 3,
            'focus_points': 'растяжка спины, гибкость, успокоение ума'
        },
        {
            'asana_name': 'Сукхасана',
            'video_path': 'videos/sukhasana_demo.mp4',
            'description': 'Удобная поза. Идеальна для медитации и начинающих.',
            'difficulty_level': 1,
            'focus_points': 'медитация, удобство, спокойствие'
        },
        {
            'asana_name': 'Ваджрасана',
            'video_path': 'videos/vajrasana_demo.mp4',
            'description': 'Поза алмаза. Улучшение пищеварения и укрепление ног.',
            'difficulty_level': 1,
            'focus_points': 'пищеварение, укрепление ног, медитация'
        },
        {
            'asana_name': 'Маричасана 1',
            'video_path': 'videos/marichasana_demo.mp4',
            'description': 'Поза мудреца Маричи. Скручивание с растяжкой.',
            'difficulty_level': 3,
            'focus_points': 'скручивание позвоночника, гибкость, детокс'
        },
        {
            'asana_name': 'Ардха Навасана',
            'video_path': 'videos/ardha_navasana_demo.mp4',
            'description': 'Половинная лодка. Укрепление мышц живота.',
            'difficulty_level': 3,
            'focus_points': 'укрепление кора, баланс, сила'
        }
    ]
    
    added_count = 0
    for video_data in demo_videos:
        try:
            video_service.add_video(
                asana_name=video_data['asana_name'],
                video_path=video_data['video_path'],
                is_premium=True,  # Все видео премиум
                description=video_data['description'],
                instructor_name="Демо-инструктор",
                difficulty_level=video_data['difficulty_level'],
                focus_points=video_data['focus_points']
            )
            added_count += 1
            logger.info(f"Added demo video: {video_data['asana_name']}")
            
        except Exception as e:
            logger.error(f"Error adding demo video {video_data['asana_name']}: {e}")
    
    logger.info(f"✅ Added {added_count} demo videos")
    return added_count

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_demo_videos()
