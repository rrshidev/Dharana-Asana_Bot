import os
import json

# Получаем все асаны из каталога
asanas = []
catalog_dir = 'bot_data/catalog'

if os.path.exists(catalog_dir):
    for category in os.listdir(catalog_dir):
        category_path = os.path.join(catalog_dir, category)
        if os.path.isdir(category_path):
            for asana_file in os.listdir(category_path):
                if asana_file.endswith('.json'):
                    asana_path = os.path.join(category_path, asana_file)
                    with open(asana_path, 'r', encoding='utf-8') as f:
                        asana_data = json.load(f)
                        asanas.append({
                            'name': asana_data['name'],
                            'category': category,
                            'file': asana_file
                        })

print(f'Всего асан в каталоге: {len(asanas)}')
print('Первые 10 асан:')
for i, asana in enumerate(asanas[:10]):
    print(f'{i+1}. {asana["name"]} ({asana["category"]})')

print('\nВсе категории:')
categories = set(asana['category'] for asana in asanas)
for category in sorted(categories):
    count = len([a for a in asanas if a['category'] == category])
    print(f'- {category}: {count} асан')

# Сохраняем список для дальнейшего использования
with open('all_asanas.json', 'w', encoding='utf-8') as f:
    json.dump(asanas, f, ensure_ascii=False, indent=2)

print(f'\nСписок всех асан сохранен в all_asanas.json')
