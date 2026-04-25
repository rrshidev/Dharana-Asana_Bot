#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.data.asana_effects import ASANA_EFFECTS
from collections import Counter

# Считаем эффекты
effect_counts = Counter()
for asana, effects in ASANA_EFFECTS.items():
    for effect in effects:
        effect_counts[effect] += 1

print('Эффекты в базе данных:')
for effect, count in sorted(effect_counts.items(), key=lambda x: x[1], reverse=True):
    print(f'  {effect}: {count} асан')

print(f'\nВсего асан в базе: {len(ASANA_EFFECTS)}')
