"""
Демо-данные для готовых комплексов
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.database_service import db_service
from src.services.ready_sequence_service import ReadySequenceService

def create_demo_sequences():
    """Создает демо-комплексы"""
    service = ReadySequenceService(db_service)
    
    demo_sequences = [
        {
            "name": "Сурья Намаскар",
            "description": "Классическая последовательность приветствия солнцу. Идеально для утренней практики, помогает разбудить тело, улучшить гибкость позвоночника и зарядиться энергией на весь день. Состоит из 12 поз, выполняемых плавно и синхронно с дыханием.",
            "duration": 15,
            "difficulty_level": 1,
            "focus_areas": "энергия, гибкость, пробуждение",
            "category": "Утро",
            "is_premium": False  # Бесплатный для привлечения
        },
        {
            "name": "Комплекс героев",
            "description": "Интенсивная силовая практика для развития выносливости и силы. Включает warrior poses, балансы и силовые асаны. Отлично подходит для тех, кто хочет укрепить мышцы и развить внутреннюю силу.",
            "duration": 45,
            "difficulty_level": 3,
            "focus_areas": "сила, выносливость, баланс",
            "category": "Сила",
            "is_premium": True
        },
        {
            "name": "Короткий на 5 мин",
            "description": "Быстрая практика для занятых людей. Включает основные растяжки и дыхательные упражнения. Помогает снять напряжение и восстановить энергию за короткое время. Идеально для перерыва в работе.",
            "duration": 5,
            "difficulty_level": 1,
            "focus_areas": "быстрое восстановление, снятие напряжения",
            "category": "Быстрые",
            "is_premium": False  # Бесплатный для привлечения
        },
        {
            "name": "Утренний",
            "description": "Мягкая утренняя практика для плавного пробуждения тела. Включает легкие растяжки, скрутки и дыхательные упражнения. Помогает начать день с гармонией и хорошим настроением.",
            "duration": 20,
            "difficulty_level": 1,
            "focus_areas": "пробуждение, гармония, гибкость",
            "category": "Утро",
            "is_premium": True
        },
        {
            "name": "Вечерний релакс",
            "description": "Спокойная практика для завершения дня. Включает мягкие наклоны, расслабляющие позы и медитацию. Помогает снять стресс, улучшить качество сна и найти внутренний покой.",
            "duration": 25,
            "difficulty_level": 1,
            "focus_areas": "релакс, сон, снятие стресса",
            "category": "Вечер",
            "is_premium": True
        },
        {
            "name": "Для спины",
            "description": "Целевая практика для здоровья позвоночника. Включает асаны на укрепление мышц спины, растяжку и снятие зажимов. Помогает при сидячей работе и профилактике проблем со спиной.",
            "duration": 30,
            "difficulty_level": 2,
            "focus_areas": "спина, осанка, снятие зажимов",
            "category": "Здоровье",
            "is_premium": True
        },
        {
            "name": "Балансы и концентрация",
            "description": "Практика для развития баланса и концентрации внимания. Включает различные позы баланса от простых до сложных. Помогает улучшить координацию и успокоить ум.",
            "duration": 35,
            "difficulty_level": 2,
            "focus_areas": "баланс, концентрация, координация",
            "category": "Балансы",
            "is_premium": True
        },
        {
            "name": "Гибкость тела",
            "description": "Глубокая практика для развития гибкости всего тела. Включает различные растяжки и асаны на раскрытие суставов. Помогает улучшить амплитуду движений и снять мышечные зажимы.",
            "duration": 40,
            "difficulty_level": 2,
            "focus_areas": "гибкость, растяжка, суставы",
            "category": "Гибкость",
            "is_premium": True
        }
    ]
    
    created_count = 0
    for seq_data in demo_sequences:
        if service.add_ready_sequence(**seq_data):
            created_count += 1
            print(f"✅ Создан комплекс: {seq_data['name']}")
        else:
            print(f"❌ Ошибка при создании: {seq_data['name']}")
    
    print(f"\n🎉 Всего создано комплексов: {created_count}/{len(demo_sequences)}")
    return created_count

if __name__ == "__main__":
    print("🎬 Создание демо-комплексов...")
    create_demo_sequences()
