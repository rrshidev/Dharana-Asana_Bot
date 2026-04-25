#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path

catalog_dir = Path("bot_data/catalog")
category = "coup+"

category_path = catalog_dir / category
print(f"Checking category: {category}")
print(f"Category path: {category_path}")
print(f"Directory exists: {category_path.exists()}")

if category_path.exists():
    files = [item for item in os.listdir(category_path) if not os.path.isdir(os.path.join(category_path, item))]
    print(f"Files in directory: {len(files)}")
    
    asana_files = []
    for item in files:
        if item.endswith(('.txt', '.png', '.jpg', '.jpeg')):
            asana_name = os.path.splitext(item)[0]
            asana_files.append(asana_name)
            print(f"  - {asana_name}")
    
    unique_asanas = sorted(list(set(asana_files)))
    print(f"Unique asanas: {len(unique_asanas)}")
    for asana in unique_asanas:
        print(f"    {asana}")
