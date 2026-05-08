import sys
import os
sys.path.append('src')

from src.services.database_service import db_service
from src.services.ready_sequence_service import ReadySequenceService

def create_demo_sequences():
    service = ReadySequenceService(db_service)
    
    demo_sequences = [
        {
            'name': 'Сурья Намаскар',
            'description': 'Классическая последовательность приветствия солнцу. Идеально для утренней практики, помогает разбудить тело, улучшить гибкость позвоночника и зарядиться энергией на весь день.',
            'duration': 15,
            'difficulty_level': 1,
            'focus_areas': 'энергия, гибкость, пробуждение',
            'category': 'Утро',
            'is_premium': False
        },
        {
            'name': 'Комплекс героев',
            'description': 'Интенсивная силовая практика для развития выносливости и силы. Включает warrior poses, балансы и силовые асаны.',
            'duration': 45,
            'difficulty_level': 3,
            'focus_areas': 'сила, выносливость, баланс',
            'category': 'Сила',
            'is_premium': True
        },
        {
            'name': 'Короткий на 5 мин',
            'description': 'Быстрая практика для занятых людей. Включает основные растяжки и дыхательные упражнения.',
            'duration': 5,
            'difficulty_level': 1,
            'focus_areas': 'быстрое восстановление, снятие напряжения',
            'category': 'Быстрые',
            'is_premium': False
        },
        {
            'name': 'Утренний',
            'description': 'Мягкая утренняя практика для плавного пробуждения тела. Включает легкие растяжки, скрутки и дыхательные упражнения.',
            'duration': 20,
            'difficulty_level': 1,
            'focus_areas': 'пробуждение, гармония, гибкость',
            'category': 'Утро',
            'is_premium': True
        },
        {
            'name': 'Вечерний релакс',
            'description': 'Спокойная практика для завершения дня. Включает мягкие наклоны, расслабляющие позы и медитацию.',
            'duration': 25,
            'difficulty_level': 1,
            'focus_areas': 'релакс, сон, снятие стресса',
            'category': 'Вечер',
            'is_premium': True
        }
    ]
    
    created_count = 0
    for seq_data in demo_sequences:
        if service.add_ready_sequence(**seq_data):
            created_count += 1
            print(f'Создан комплекс: {seq_data["name"]}')
        else:
            print(f'Ошибка при создании: {seq_data["name"]}')
    
    print(f'Всего создано комплексов: {created_count}/{len(demo_sequences)}')
    return created_count

if __name__ == "__main__":
    create_demo_sequences()
