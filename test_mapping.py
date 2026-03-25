#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тест для проверки маппинга ID → имена в data_service
"""

from src.services.data_service import DataService

def test_mapping():
    """Тестируем работу маппинга"""
    ds = DataService()
    data = ds.load_data()
    
    print("=== Тестирование маппинга ===")
    print(f"Всего категорий: {len(data.categories)}")
    print(f"Всего основ: {len(data.basics)}")
    print(f"Всего ступеней: {len(data.steps)}")
    print()
    
    # Тест категорий
    print("=== Категории ===")
    for i, category_name in enumerate(data.categories.keys()):
        category_id = f'category_{i}'
        retrieved = ds.get_category_by_id(category_id)
        print(f"ID: {category_id} -> Имя: {category_name} -> Получено: {retrieved}")
        assert retrieved == category_name, f"Ошибка маппинга категории: {category_id}"
    print()
    
    # Тест основ
    print("=== Основы йоги ===")
    for i, basic_name in enumerate(data.basics):
        basic_id = f'basic_{i}'
        retrieved = ds.get_basic_by_id(basic_id)
        print(f"ID: {basic_id} -> Имя: {basic_name} -> Получено: {retrieved}")
        assert retrieved == basic_name, f"Ошибка маппинга основы: {basic_id}"
    print()
    
    # Тест ступеней
    print("=== Ступени йоги ===")
    for i, step_name in enumerate(data.steps):
        step_id = f'step_{i}'
        retrieved = ds.get_step_by_id(step_id)
        print(f"ID: {step_id} -> Имя: {step_name} -> Получено: {retrieved}")
        assert retrieved == step_name, f"Ошибка маппинга ступени: {step_id}"
    print()
    
    # Тест асан (для первой категории)
    print("=== Асаны (первая категория) ===")
    first_category = list(data.categories.values())[0]
    for i, asana_name in enumerate(first_category.asanas[:5]):  # Только первые 5 для краткости
        asana_id = f'asana_{i}'
        retrieved = ds.get_asana_by_id(asana_id)
        print(f"ID: {asana_id} -> Имя: {asana_name} -> Получено: {retrieved}")
        assert retrieved == asana_name, f"Ошибка маппинга асаны: {asana_id}"
    
    print("\n✅ Все тесты пройдены!")

if __name__ == '__main__':
    test_mapping()
