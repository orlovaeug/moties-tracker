#!/usr/bin/env python3
"""
embed_moties.py — bakt moties.json in index.html
Zodat GitHub Pages nooit een aparte fetch nodig heeft.
"""
import json, re

with open('moties.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

new_data = json.dumps(data, ensure_ascii=False, separators=(',', ':'))

# Replace INIT array with fresh data from moties.json
# Keep existing INIT as fallback seed — merge new on top
html = re.sub(
    r'var NIEUW=\[\];',
    'var NIEUW=' + new_data + ';',
    html
)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'✅ {len(data)} moties embedded into index.html via NIEUW array')
