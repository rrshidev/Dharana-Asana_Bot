#!/usr/bin/env python3
"""
Тестовый скрипт для проверки генератора последовательностей
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.data_service import DataService
from src.services.sequence_generator import SequenceGenerator
from src.models.sequence_models import SequenceParams, SequenceDifficulty, SequenceFocus, SequenceDuration

def test_sequence_generator():
    """Тестируем генератор последовательностей"""
    print("🧪 Тестирование генератора последовательностей...")
    
    # Инициализация сервисов
    data_service = DataService()
    generator = SequenceGenerator(data_service)
    
    # Создаем тестовые параметры
    params = SequenceParams(
        difficulty=SequenceDifficulty.BEGINNER,
        duration=SequenceDuration.SHORT,
        focus=SequenceFocus.LEGS
    )
    
    print(f"📊 Параметры: {params.difficulty.value}, {params.duration.value}мин, {params.focus.value}")
    
    try:
        # Генерируем последовательность
        sequence = generator.generate_sequence(params)
        
        print(f"✅ Последовательность сгенерирована!")
        print(f"📋 Асан в последовательности: {len(sequence.items)}")
        print(f"⏱️ Общая длительность: {sequence.total_duration.total_seconds()} секунд")
        print(f"🔥 Калории: {sequence.estimated_calories}")
        
        if sequence.items:
            print("\n🧘 Первые 3 асаны:")
            for i, item in enumerate(sequence.items[:3]):
                print(f"  {i+1}. {item.asana_name} - {item.duration_seconds}с")
                print(f"     {item.description[:50]}...")
        else:
            print("❌ Асаны не найдены!")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sequence_generator()
