#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.data.asana_effects import ASANA_EFFECTS

# Проверяем эффекты
effect_counts = {}
for asana, effects in ASANA_EFFECTS.items():
    for effect in effects:
        if effect not in effect_counts:
            effect_counts[effect] = []
        effect_counts[effect].append(asana)

print("Эффекты и количество асан:")
for effect, asanas in effect_counts.items():
    print(f"  {effect}: {len(asanas)} асан")
    if len(asanas) <= 5:
        for asana in asanas[:3]:
            print(f"    - {asana}")
