#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path
from src.data.asana_effects import ASANA_EFFECTS

catalog_dir = Path("bot_data/catalog")

print("=== Проверка реальных асан с файлами ===")

# Собираем все асаны с файлами
real_asanas = set()
for category_dir in catalog_dir.iterdir():
    if category_dir.is_dir():
        for file in category_dir.iterdir():
            if file.suffix in ['.txt', '.png', '.jpg', '.jpeg']:
                asana_name = file.stem
                real_asanas.add(asana_name)

print(f"Всего асан с файлами: {len(real_asanas)}")

# Проверяем эффекты для реальных асан
effect_counts = {}
real_effect_asanas = {}

for asana_name in real_asanas:
    if asana_name in ASANA_EFFECTS:
        effects = ASANA_EFFECTS[asana_name]
        for effect in effects:
            if effect not in effect_counts:
                effect_counts[effect] = 0
                real_effect_asanas[effect] = []
            effect_counts[effect] += 1
            real_effect_asanas[effect].append(asana_name)

print("\n=== Эффекты и количество РЕАЛЬНЫХ асан ===")
for effect, count in sorted(effect_counts.items()):
    print(f"  {effect}: {count} асан")

print("\n=== Проблемные эффекты (менее 5 асан) ===")
for effect, count in effect_counts.items():
    if count < 5:
        print(f"  {effect}: {count} асан")
        print(f"    Асаны: {real_effect_asanas[effect][:3]}")

print("\n=== Асаны из ASANA_EFFECTS без файлов ===")
missing_asanas = []
for asana in ASANA_EFFECTS.keys():
    if asana not in real_asanas:
        missing_asanas.append(asana)

print(f"Всего асан без файлов: {len(missing_asanas)}")
for asana in missing_asanas[:10]:
    print(f"  - {asana}")
