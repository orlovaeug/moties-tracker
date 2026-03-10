#!/usr/bin/env python3
"""
embed_moties.py — bakt moties.json in index.html
- Vervangt var INIT=[...] met verse data
- Bumpt de storage key zodat browsers de nieuwe data oppikken
"""
import json, re
from datetime import date

with open('moties.json', 'r', encoding='utf-8') as f:
    fresh = json.load(f)

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Replace INIT array with merged fresh data
new_init = 'var INIT=' + json.dumps(fresh, ensure_ascii=False, separators=(',', ':')) + ';'
html = re.sub(r'var INIT=\[.*?\];', new_init, html, flags=re.DOTALL)

# 2. Bump storage key with today's date so browsers get fresh data
today = date.today().strftime('%Y%m%d')
html = re.sub(r'var SK="motie-v[\w]+"', f'var SK="motie-v{today}"', html)

# 3. Clear NIEUW
html = re.sub(r'var NIEUW=\[.*?\];', 'var NIEUW=[];', html, flags=re.DOTALL)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"✅ {len(fresh)} moties embedded into INIT, SK bumped to motie-v{today}")
