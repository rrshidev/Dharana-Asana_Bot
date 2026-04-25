#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path

catalog_dir = Path("bot_data/catalog")
empty_asanas = []

for category_dir in catalog_dir.iterdir():
    if category_dir.is_dir():
        for file_path in category_dir.glob("*.txt"):
            if file_path.stat().st_size == 0:
                asana_name = file_path.stem
                empty_asanas.append(f"{asana_name} (в категории {category_dir.name})")

print("Асаны с пустыми описаниями:")
for asana in empty_asanas:
    print(f"  - {asana}")

print(f"\nВсего асан с пустыми описаниями: {len(empty_asanas)}")
