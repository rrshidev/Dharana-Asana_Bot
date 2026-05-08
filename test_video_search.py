from src.services.database_service import db_service
from src.services.video_service import VideoService
from src.models.video_models import AsanaVideo
from sqlalchemy import func

session = db_service.get_session()
try:
    # Тест поиска без учета регистра
    print('Тест поиска видео:')
    
    # Прямой запрос к базе
    video1 = session.query(AsanaVideo).filter(
        func.lower(AsanaVideo.asana_name) == func.lower('Падмасана'),
        AsanaVideo.is_active == True
    ).first()
    
    print(f'Прямой запрос для Падмасана: {video1.asana_name if video1 else "Не найдено"}')
    
    # Через сервис
    video_service = VideoService(db_service)
    video2 = video_service.get_video_for_asana('Падмасана', False)
    
    print(f'Через сервис для Падмасана: {video2["asana_name"] if video2 else "Не найдено"}')
    
finally:
    session.close()
