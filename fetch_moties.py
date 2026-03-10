#!/usr/bin/env python3
"""
fetch_moties.py — haalt moties op via Tweede Kamer Open Data API
https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0
"""
import json, re, time, hashlib
from datetime import date
import urllib.request, urllib.parse

DATA_FILE  = 'moties.json'
TODAY      = date.today().isoformat()
START_DATE = '2026-02-23'

TK_BASE = 'https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0'

HEADERS = {
    'User-Agent': 'MotieTracker/1.0',
    'Accept': 'application/json',
}

THEMA_KEYWORDS = {
    "Defensie": ["defensie","militair","navo","leger","oekra","wapen","krijgsmacht","bewapening"],
    "Bestaanszekerheid": ["aow","pensioen","uitkering","armoede","minimumloon","bijstand","zzp","ww-duur"],
    "Klimaat & Energie": ["klimaat","energie","windmolen","kerncentrale","co2","netcongestie","groene"],
    "Wonen & Bouwen": ["woning","huur","hypotheek","bouwen","nieuwbouw","woningmarkt","huurder"],
    "Zorg": ["zorg","eigen risico","ggz","ziekenhuis","verpleging","mantelzorg","huisarts"],
    "Asiel & Migratie": ["asiel","migratie","vluchteling","ind","spreidingswet","verblijf","inburgering"],
    "Onderwijs & Wetenschap": ["onderwijs","school","leraar","student","universiteit","mbo","kinderopvang"],
    "Landbouw & Natuur": ["landbouw","boer","stikstof","natuur","natura","veehouderij","mest"],
    "Financien": ["belasting","begroting","box 3","btw","financien","rijksbegroting","staatsschuld"],
    "Buitenlandse Zaken & Europa": ["europa","oekra","buitenland","sanctie","diplomatie","navo"],
    "Democratie & Rechtsstaat": ["democratie","grondwet","rechtsstaat","referendum","verkiezing"],
    "Economie & Ondernemen": ["economie","ondernemen","mkb","innovatie","bedrijf","concurrentie"],
    "Bereikbaarheid & Mobiliteit": ["mobiliteit","trein","openbaar vervoer","fiets","schiphol","lelystad"],
    "Digitalisering & AI": ["digitaal","algoritme","cyber","software","kunstmatige intelligentie"],
    "Veiligheid & Justitie": ["politie","criminaliteit","justitie","gevangenis","drugs","terrorisme"],
    "Sociale Cohesie": ["cultuur","integratie","discriminatie","racisme","lhbti","emancipatie"],
    "Overheid & Bestuur": ["overheid","gemeente","provincie","bestuur","ambtenaar","uitvoering"],
}

PARTIJEN = ["PVV","VVD","NSC","BBB","D66","GL-PvdA","CDA","SP","PvdD","CU","SGP","Volt","DENK","FvD","JA21","50PLUS","Gr.Markuszower"]

def detect_thema(text):
    text = text.lower()
    best, best_score = "Overig", 0
    for thema, kws in THEMA_KEYWORDS.items():
        score = sum(1 for k in kws if k in text)
        if score > best_score:
            best, best_score = thema, score
    return best

def detect_indiener(text):
    for p in PARTIJEN:
        if p in text:
            return p
    return "Onbekend"

def make_id(val):
    return 'tk' + hashlib.md5(str(val).encode()).hexdigest()[:10]

def api_get(endpoint, params):
    url = TK_BASE + endpoint + '?' + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f'  ⚠️  {e}')
        return None

def main():
    print(f'🏛️  Moties ophalen — {TODAY}')

    # Load existing
    try:
        with open(DATA_FILE, encoding='utf-8') as f:
            existing = json.load(f)
    except FileNotFoundError:
        existing = []
    
    existing_ids = {x['id'] for x in existing}
    print(f'   Bestaande moties: {len(existing)}')

    new_items = []

    # ── Kamerstukken: Moties ──────────────────────────────────────────────
    print('   Fetching Kamerstuk (Motie)...')
    data = api_get('/Kamerstuk', {
        '$filter': f"Soort eq 'Motie' and GewijzigdOp gt {START_DATE}T00:00:00Z",
        '$orderby': 'GewijzigdOp desc',
        '$top': '100',
        '$select': 'Id,Nummer,Titel,Ondertitel,Datum,Soort,GewijzigdOp',
    })
    
    if data and 'value' in data:
        items = data['value']
        print(f'   ✓ {len(items)} kamerstukken gevonden')
        for item in items:
            raw_date = (item.get('Datum') or item.get('GewijzigdOp') or '')[:10]
            if raw_date < START_DATE:
                continue
            titel = (item.get('Titel') or item.get('Ondertitel') or item.get('Nummer') or '').strip()
            if not titel:
                continue
            item_id = make_id(item.get('Id') or titel)
            if item_id in existing_ids:
                continue
            existing_ids.add(item_id)
            text = titel + ' ' + (item.get('Ondertitel') or '')
            thema = detect_thema(text)
            new_items.append({
                'id': item_id,
                'titel': titel,
                'indiener': detect_indiener(text),
                'datum': raw_date,
                'thema': thema,
                'status': 'in_behandeling',
                'alignment': 'neutraal',
                'vergadering': '',
                'tk_url': f"https://www.tweedekamer.nl/kamerstukken/moties/detail?id={item.get('Id','')}",
                'toelichting': (item.get('Ondertitel') or '')[:200],
                'stemmen': {}
            })
    else:
        print('   No data returned')

    time.sleep(1)

    # ── Zaak: Stemmingsuitslagen ──────────────────────────────────────────
    print('   Fetching Zaak (Stemmingen)...')
    data2 = api_get('/Zaak', {
        '$filter': f"Soort eq 'Motie' and GewijzigdOp gt {START_DATE}T00:00:00Z",
        '$orderby': 'GewijzigdOp desc',
        '$top': '50',
        '$select': 'Id,Nummer,Titel,Soort,GewijzigdOp,Datum',
    })

    if data2 and 'value' in data2:
        items2 = data2['value']
        print(f'   ✓ {len(items2)} zaken gevonden')
        for item in items2:
            raw_date = (item.get('Datum') or item.get('GewijzigdOp') or '')[:10]
            if raw_date < START_DATE:
                continue
            titel = (item.get('Titel') or item.get('Nummer') or '').strip()
            if not titel:
                continue
            item_id = make_id(item.get('Id') or titel)
            if item_id in existing_ids:
                continue
            existing_ids.add(item_id)
            thema = detect_thema(titel)
            new_items.append({
                'id': item_id,
                'titel': titel,
                'indiener': detect_indiener(titel),
                'datum': raw_date,
                'thema': thema,
                'status': 'in_behandeling',
                'alignment': 'neutraal',
                'vergadering': '',
                'tk_url': f"https://www.tweedekamer.nl/kamerstukken/moties/detail?id={item.get('Id','')}",
                'toelichting': '',
                'stemmen': {}
            })
    else:
        print('   No data from Zaak endpoint')

    print(f'\n   Nieuwe moties: {len(new_items)}')

    all_items = existing + new_items
    all_items.sort(key=lambda x: x.get('datum',''), reverse=True)

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)
    print(f'✅ moties.json bijgewerkt — totaal {len(all_items)} moties')

if __name__ == '__main__':
    main()
