#!/usr/bin/env python3
"""
embed_moties.py — bakt moties.json en agenda.json in index.html
"""
import json, re, os
from datetime import date

with open('moties.json', 'r', encoding='utf-8') as f:
    fresh = json.load(f)

# Load agenda if available
agenda = []
if os.path.exists('agenda.json'):
    with open('agenda.json', 'r', encoding='utf-8') as f:
        agenda = json.load(f)

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Replace INIT array
new_init = 'var INIT=' + json.dumps(fresh, ensure_ascii=False, separators=(',', ':')) + ';'
html = re.sub(r'var INIT=\[.*?\];', new_init, html, flags=re.DOTALL)

# 2. Replace AGENDA array (or insert after INIT if not present)
new_agenda = 'var AGENDA=' + json.dumps(agenda, ensure_ascii=False, separators=(',', ':')) + ';'
if re.search(r'var AGENDA=\[.*?\];', html, flags=re.DOTALL):
    html = re.sub(r'var AGENDA=\[.*?\];', new_agenda, html, flags=re.DOTALL)
else:
    html = html.replace('var INIT=', new_agenda + '\nvar INIT=', 1)

# 3. Bump storage key
today = date.today().strftime('%Y%m%d')
html = re.sub(r'var SK="motie-v[\w]+"', f'var SK="motie-v{today}"', html)

# 4. Clear NIEUW
html = re.sub(r'var NIEUW=\[.*?\];', 'var NIEUW=[];', html, flags=re.DOTALL)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"✅ {len(fresh)} moties embedded, {len(agenda)} agenda-items, SK bumped to motie-v{today}")
