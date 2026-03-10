#!/usr/bin/env python3
"""
fetch_moties.py — scrapet moties van tweedekamer.nl/kamerstukken/moties
Geen API-sleutel, geen pip nodig. Draait dagelijks via GitHub Actions.
"""
import json, re, time, hashlib
from datetime import date
import urllib.request, urllib.parse
import html as html_module

DATA_FILE  = 'moties.json'
TODAY      = date.today().isoformat()
START_DATE = '2026-02-23'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; MotieTracker/1.0)',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'nl-NL,nl;q=0.9',
}

THEMA_KEYWORDS = {
    "Defensie": ["defensie","militair","navo","leger","oekra","wapen","krijgsmacht","luchtmacht","marine"],
    "Bestaanszekerheid": ["aow","pensioen","uitkering","armoede","minimumloon","bijstand","zzp","ww-duur"],
    "Klimaat & Energie": ["klimaat","energie","windmolen","kerncentrale","co2","netcongestie","zonnepaneel"],
    "Wonen & Bouwen": ["woning","huur","hypotheek","bouwen","nieuwbouw","woningmarkt","huurder","corporatie"],
    "Zorg": ["zorg","eigen risico","ggz","ziekenhuis","verpleging","mantelzorg","huisarts","medicijn"],
    "Asiel & Migratie": ["asiel","migratie","vluchteling","ind","spreidingswet","azc","verblijf","inburgering"],
    "Onderwijs & Wetenschap": ["onderwijs","school","leraar","student","universiteit","mbo","kinderopvang"],
    "Landbouw & Natuur": ["landbouw","boer","stikstof","natuur","natura 2000","veehouderij","mest"],
    "Financien": ["belasting","begroting","box 3","btw","financien","rijksbegroting","staatsschuld"],
    "Buitenlandse Zaken & Europa": ["europa","oekra","buitenland","sanctie","diplomatie","europese unie"],
    "Democratie & Rechtsstaat": ["democratie","grondwet","rechtsstaat","referendum","verkiezing"],
    "Economie & Ondernemen": ["economie","ondernemen","mkb","innovatie","bedrijf","concurrentie"],
    "Bereikbaarheid & Mobiliteit": ["mobiliteit","trein","openbaar vervoer","fiets","schiphol","lelystad"],
    "Digitalisering & AI": ["digitaal","algoritme","cyber","software","kunstmatige intelligentie"],
    "Veiligheid & Justitie": ["politie","criminaliteit","justitie","gevangenis","drugs","terrorisme"],
    "Sociale Cohesie": ["cultuur","integratie","discriminatie","racisme","lhbti","emancipatie"],
    "Overheid & Bestuur": ["overheid","gemeente","provincie","bestuur","ambtenaar","uitvoering"],
    "Nationale Veiligheid": ["inlichtingen","aivd","mivd","spionage","nationale veiligheid"],
}

PARTIJEN = ["PVV","VVD","NSC","BBB","D66","GL-PvdA","CDA","SP","PvdD","CU","SGP","Volt","DENK","FvD","JA21","50PLUS","Gr.Markuszower"]

LEDEN_PARTIJ = {
    "Wilders": "PVV", "Heutink": "PVV", "Agema": "PVV",
    "Yesilgöz": "VVD", "Hermans": "VVD", "Peter de Groot": "VVD", "Brekelmans": "VVD",
    "Omtzigt": "NSC", "Dassen": "NSC",
    "Van der Plas": "BBB", "Vedder": "BBB", "Struijs": "BBB",
    "Paternotte": "D66", "Jetten": "D66", "Van Weyenberg": "D66", "Van Lanschot": "D66", "Ten Hove": "D66",
    "Klaver": "GL-PvdA", "Nijboer": "GL-PvdA", "Westerveld": "GL-PvdA", "Van Baarle": "GL-PvdA",
    "Bontenbal": "CDA", "Boswijk": "CDA",
    "Dobbe": "SP", "Dijk": "SP", "Leijten": "SP",
    "Teunissen": "PvdD", "Wassenberg": "PvdD",
    "Bikker": "CU", "Segers": "CU",
    "Stoffer": "SGP", "Diederik van Dijk": "SGP",
    "Koekkoek": "Volt",
    "Azarkan": "DENK", "Ergin": "DENK",
    "Van Houwelingen": "FvD", "Baudet": "FvD",
    "Eerdmans": "JA21",
    "Markuszower": "Gr.Markuszower",
}

MONTHS = {
    'januari': 1, 'februari': 2, 'maart': 3, 'april': 4,
    'mei': 5, 'juni': 6, 'juli': 7, 'augustus': 8,
    'september': 9, 'oktober': 10, 'november': 11, 'december': 12
}

def detect_thema(text):
    text = text.lower()
    best, best_score = "Overig", 0
    for thema, kws in THEMA_KEYWORDS.items():
        score = sum(1 for k in kws if k in text)
        if score > best_score:
            best, best_score = thema, score
    return best

def detect_indiener(title):
    m = re.search(r'lid(?:en)?\s+([A-Z][a-zA-Z\u00C0-\u017E\s]+?)(?:\s+c\.s\.|\s+en\s|\s+-\s|$)', title)
    if m:
        name = m.group(1).strip()
        for naam, partij in LEDEN_PARTIJ.items():
            if naam.lower() in name.lower():
                return partij
    for p in PARTIJEN:
        if p in title:
            return p
    return "Onbekend"

def make_id(val):
    return 'tk' + hashlib.md5(str(val).encode()).hexdigest()[:10]

def parse_dutch_date(date_str):
    parts = date_str.strip().split()
    if len(parts) == 3:
        try:
            d = int(parts[0])
            m = MONTHS.get(parts[1].lower(), 0)
            y = int(parts[2])
            if m:
                return f'{y:04d}-{m:02d}-{d:02d}'
        except:
            pass
    return TODAY

def fetch_page(page=0):
    params = urllib.parse.urlencode({
        'qry': '*',
        'fld_tk_categorie': 'Kamerstukken',
        'fld_prl_kamerstuk': 'Moties',
        'srt': 'date:desc:date',
        'page': str(page)
    })
    url = 'https://www.tweedekamer.nl/kamerstukken/moties?' + params
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f'  Warning page {page}: {e}')
        return ''

def parse_moties(html):
    results = []
    # Find date blocks — each motie has a date header followed by title+link
    pattern = re.compile(
        r'(\d{1,2}\s+(?:januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s+\d{4})'
        r'.*?'
        r'href="(/kamerstukken/moties/detail\?[^"]+)"[^>]*>\s*([^<]+?)\s*</a>',
        re.DOTALL | re.IGNORECASE
    )
    for m in pattern.finditer(html):
        date_str, link, title = m.group(1), m.group(2), m.group(3)
        title = html_module.unescape(title.strip())
        iso_date = parse_dutch_date(date_str)
        full_link = 'https://www.tweedekamer.nl' + link
        if title:
            results.append({'titel': title, 'datum': iso_date, 'link': full_link})
    return results

def main():
    print(f'Moties scrapen van tweedekamer.nl — {TODAY}')

    try:
        with open(DATA_FILE, encoding='utf-8') as f:
            existing = json.load(f)
    except FileNotFoundError:
        existing = []

    existing_ids = {x['id'] for x in existing}
    existing_links = {x.get('tk_url','') for x in existing}
    print(f'Bestaande moties: {len(existing)}')

    new_items = []

    for page in range(10):  # max 10 pagina's = ~150 moties
        print(f'Pagina {page + 1} ophalen...')
        html = fetch_page(page)
        if not html:
            break

        results = parse_moties(html)
        print(f'  {len(results)} moties op pagina {page + 1}')

        if not results:
            break

        all_too_old = True
        for r in results:
            if r['datum'] < START_DATE:
                continue  # skip old, but keep going through page
            all_too_old = False
            if r['link'] in existing_links:
                continue
            item_id = make_id(r['link'])
            if item_id in existing_ids:
                continue
            existing_ids.add(item_id)
            existing_links.add(r['link'])
            thema = detect_thema(r['titel'])
            new_items.append({
                'id': item_id,
                'titel': r['titel'],
                'indiener': detect_indiener(r['titel']),
                'datum': r['datum'],
                'thema': thema,
                'status': 'in_behandeling',
                'alignment': 'neutraal',
                'vergadering': '',
                'tk_url': r['link'],
                'toelichting': '',
                'stemmen': {}
            })

        if all_too_old:
            print(f'  Alle moties op deze pagina voor {START_DATE} — klaar')
            break
        time.sleep(1)

    print(f'Nieuwe moties: {len(new_items)}')
    all_items = existing + new_items
    all_items.sort(key=lambda x: x.get('datum', ''), reverse=True)

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)
    print(f'moties.json bijgewerkt — totaal {len(all_items)} moties')

if __name__ == '__main__':
    main()
