#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тестирование функциональности таймера
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.timer_service import timer_service
from src.models.timer_models import TimerType, TimerConfig

def test_timer_service():
    """Тестирование TimerService"""
    print("🧪 Тестирование TimerService...")
    
    # Тест 1: Создание таймера медитации
    print("\n1. Создание таймера медитации:")
    session = timer_service.create_meditation_timer(12345, 10)  # 10 минут
    assert session.user_id == 12345
    assert session.timer_type == TimerType.MEDITATION
    assert session.duration == 600  # 10 минут * 60 секунд
    assert session.status.value == "stopped"
    print(f"✅ Медитация создана: {session.duration // 60} минут")
    
    # Тест 2: Создание таймера асан
    print("\n2. Создание таймера асан:")
    config = TimerConfig(work_duration=60, rest_duration=20, cycles=5)
    session = timer_service.create_asana_timer(12345, config)
    assert session.timer_type == TimerType.ASANA
    assert session.work_duration == 60
    assert session.rest_duration == 20
    assert session.cycles == 5
    print(f"✅ Таймер асан создана: работа={session.work_duration}с, отдых={session.rest_duration}с, циклов={session.cycles}")
    
    # Тест 3: Запуск таймера
    print("\n3. Запуск таймера:")
    started_session = timer_service.start_timer(12345)
    assert started_session.status.value == "running"
    print(f"✅ Таймер запущен")
    
    # Тест 4: Пауза таймера
    print("\n4. Пауза таймера:")
    paused_session = timer_service.pause_timer(12345)
    assert paused_session.status.value == "paused"
    print(f"✅ Таймер поставлен на паузу")
    
    # Тест 5: Продолжение таймера
    print("\n5. Продолжение таймера:")
    resumed_session = timer_service.start_timer(12345)
    assert resumed_session.status.value == "running"
    print(f"✅ Таймер возобновлен")
    
    # Тест 6: Обновление таймера
    print("\n6. Обновление таймера:")
    import time
    time.sleep(2)  # ждем 2 секунды
    updated_session = timer_service.update_timer(12345)
    assert updated_session.elapsed >= 2
    print(f"✅ Таймер обновлен: прошло {updated_session.elapsed} секунд")
    
    # Тест 7: Прогресс-бар
    print("\n7. Прогресс-бар:")
    progress_bar = session.get_progress_bar()
    percentage = session.get_progress_percentage()
    print(f"✅ Прогресс: {progress_bar} ({percentage:.1f}%)")
    
    # Тест 8: Остановка таймера
    print("\n8. Остановка таймера:")
    stopped_session = timer_service.stop_timer(12345)
    assert stopped_session.status.value == "stopped"
    assert stopped_session.elapsed == 0
    print(f"✅ Таймер остановлен")
    
    # Тест 9: Удаление сессии
    print("\n9. Удаление сессии:")
    deleted = timer_service.delete_session(12345)
    assert deleted == True
    assert 12345 not in timer_service.active_sessions
    print(f"✅ Сессия удалена")
    
    print("\n🎉 Все тесты пройдены успешно!")

def test_timer_ui():
    """Тестирование UI компонентов"""
    print("\n🎨 Тестирование TimerUI...")
    
    from src.utils.timer_ui import TimerUI
    
    # Тест главного меню
    print("\n1. Главное меню:")
    main_menu = TimerUI.get_main_menu()
    assert main_menu.inline_keyboard
    print("✅ Главное меню создано")
    
    # Тест меню медитации
    print("\n2. Меню медитации:")
    meditation_menu = TimerUI.get_meditation_menu()
    assert meditation_menu.inline_keyboard
    print("✅ Меню медитации создано")
    
    print("\n🎉 UI тесты пройдены успешно!")

if __name__ == "__main__":
    try:
        test_timer_service()
        test_timer_ui()
    except Exception as e:
        print(f"❌ Тест провален: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
