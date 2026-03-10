#!/usr/bin/env python3
"""
fetch_moties.py — haalt moties op van tweedekamer.nl RSS feeds
Geen API-sleutel nodig. Draait dagelijks via GitHub Actions.
"""
import json, re, hashlib, time
from datetime import datetime, date
import urllib.request
import xml.etree.ElementTree as ET

DATA_FILE  = 'moties.json'
TODAY      = date.today().isoformat()
START_DATE = '2026-02-23'

# Tweede Kamer RSS feeds
TK_FEEDS = [
    ('https://www.tweedekamer.nl/kamerstukken/moties/rss', 'moties'),
    ('https://www.tweedekamer.nl/kamerstukken/stemmingsuitslagen/rss', 'stemmingen'),
    ('https://www.tweedekamer.nl/vergaderingen/plenaire_vergaderingen/rss', 'vergaderingen'),
]

THEMAS = ["Bestaanszekerheid","Asiel & Migratie","Landbouw & Natuur","Veiligheid & Justitie",
          "Zorg","Onderwijs & Wetenschap","Klimaat & Energie","Wonen & Bouwen","Financien",
          "Buitenlandse Zaken & Europa","Defensie","Overheid & Bestuur","Democratie & Rechtsstaat",
          "Nationale Veiligheid","Economie & Ondernemen","Digitalisering & AI",
          "Bereikbaarheid & Mobiliteit","Sociale Cohesie","Overig"]

THEMA_KEYWORDS = {
    "Defensie": ["defensie","militair","navo","leger","oekraine","wapen","krijgsmacht","bewapening","veiligheids"],
    "Bestaanszekerheid": ["aow","ww","uitkering","armoede","minimumloon","pensioen","bijstand","bestaanszekerheid","zzp","zelfstandige"],
    "Klimaat & Energie": ["klimaat","energie","windmolen","kerncentrale","co2","stikstof","gas","zonnepaneel","netcongestie","groene"],
    "Wonen & Bouwen": ["wonen","woning","huur","hypotheek","bouwen","nieuwbouw","woningmarkt","huurder"],
    "Zorg": ["zorg","eigen risico","ggz","ziekenhuis","verpleging","mantelzorg","medicijn","huisarts"],
    "Asiel & Migratie": ["asiel","migratie","vluchte","ind","spreidingswet","azc","verblijf","inburgering"],
    "Onderwijs & Wetenschap": ["onderwijs","school","leraar","student","universiteit","mbo","kinderopvang","studiefinanciering"],
    "Landbouw & Natuur": ["landbouw","boer","stikstof","natuur","natura","veehouderij","mest","gewas"],
    "Financien": ["belasting","begroting","box 3","btw","subsidie","financien","rijksbegroting","staatsschuld"],
    "Buitenlandse Zaken & Europa": ["europa","oekraine","navo","buitenland","eu","sanctie","diplomatie"],
    "Democratie & Rechtsstaat": ["democratie","grondwet","rechtsstaat","parlement","verkiezing","referendum"],
    "Economie & Ondernemen": ["economie","ondernemen","mkb","innovatie","concurrentie","bedrijf"],
    "Bereikbaarheid & Mobiliteit": ["mobiliteit","trein","ov","fiets","auto","schiphol","lelystad","verkeer"],
    "Digitalisering & AI": ["digitaal","ai","internet","data","algoritme","cyber","software"],
    "Veiligheid & Justitie": ["politie","criminaliteit","justitie","gevangenis","drugs","terrorisme"],
    "Nationale Veiligheid": ["inlichtingen","aivd","mivd","spionage","terrorisme","nationale veiligheid"],
    "Overheid & Bestuur": ["overheid","gemeente","provincie","bestuur","ambtenaar","uitvoering"],
    "Sociale Cohesie": ["cultuur","integratie","discriminatie","racisme","lhbti","emancipatie"],
}

STATUS_KEYWORDS = {
    "aangenomen": ["aangenomen","goedgekeurd","aanvaard","unaniem"],
    "verworpen": ["verworpen","afgewezen","niet aangenomen"],
    "aangehouden": ["aangehouden","uitgesteld","teruggetrokken"],
}

PARTIJEN = ["PVV","VVD","NSC","BBB","D66","GL-PvdA","CDA","SP","PvdD","CU","SGP","Volt","DENK","FvD","JA21","50PLUS","Gr.Markuszower"]

def detect_thema(title, desc=""):
    text = (title + " " + desc).lower()
    best, best_score = "Overig", 0
    for thema, keywords in THEMA_KEYWORDS.items():
        score = sum(1 for k in keywords if k in text)
        if score > best_score:
            best, best_score = thema, score
    return best

def detect_status(title, desc=""):
    text = (title + " " + desc).lower()
    for status, keywords in STATUS_KEYWORDS.items():
        if any(k in text for k in keywords):
            return status
    return "in_behandeling"

def detect_indiener(title, desc=""):
    text = title + " " + desc
    for p in PARTIJEN:
        if p in text or p.lower() in text.lower():
            return p
    return "Onbekend"

def detect_alignment(thema, status):
    # Rough alignment detection based on coalition themes
    coalition_themes = {"Defensie","Wonen & Bouwen","Klimaat & Energie","Economie & Ondernemen",
                       "Digitalisering & AI","Bereikbaarheid & Mobiliteit"}
    if thema in coalition_themes:
        return "conform"
    return "neutraal"

def make_id(title):
    return 'tk' + hashlib.md5(title.lower().strip().encode()).hexdigest()[:10]

def parse_date(text):
    if not text: return TODAY
    for fmt in ['%a, %d %b %Y %H:%M:%S %z','%a, %d %b %Y %H:%M:%S GMT',
                '%Y-%m-%dT%H:%M:%S%z','%Y-%m-%dT%H:%M:%SZ','%Y-%m-%d']:
        try:
            return datetime.strptime(text.strip()[:30], fmt).strftime('%Y-%m-%d')
        except: pass
    m = re.search(r'(\d{4}-\d{2}-\d{2})', text)
    return m.group(1) if m else TODAY

HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; MotieTracker/1.0)'}

def fetch_tk_feed(url):
    results = []
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
        root = ET.fromstring(raw)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        entries = root.findall('.//item') or root.findall('.//atom:entry', ns)
        for entry in entries:
            def g(tag):
                el = entry.find(tag) or entry.find(f'atom:{tag}', ns)
                return (el.text or '').strip() if el is not None else ''
            title = g('title')
            if not title: continue
            desc = g('description') or g('summary') or ''
            link = g('link')
            pub = g('pubDate') or g('published') or g('updated')
            date_str = parse_date(pub)
            if date_str < START_DATE: continue
            results.append({
                'title': title, 'desc': desc,
                'link': link, 'date': date_str
            })
    except Exception as e:
        print(f'  ⚠️  {url}: {e}')
    return results

def main():
    print(f'🏛️  Moties ophalen — {TODAY}')

    # Load existing
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        print(f'   Bestaande moties: {len(existing)}')
    except FileNotFoundError:
        existing = []

    existing_ids = {x['id'] for x in existing}
    new_items = []

    for url, feed_type in TK_FEEDS:
        print(f'   Fetching {feed_type}: {url}')
        results = fetch_tk_feed(url)
        added = 0
        for r in results:
            item_id = make_id(r['title'])
            if item_id in existing_ids: continue
            existing_ids.add(item_id)
            thema = detect_thema(r['title'], r['desc'])
            status = detect_status(r['title'], r['desc'])
            indiener = detect_indiener(r['title'], r['desc'])
            item = {
                'id': item_id,
                'titel': r['title'],
                'indiener': indiener,
                'datum': r['date'],
                'thema': thema,
                'status': status,
                'alignment': detect_alignment(thema, status),
                'vergadering': '',
                'tk_url': r['link'] or 'https://www.tweedekamer.nl/kamerstukken/moties',
                'toelichting': r['desc'][:200] if r['desc'] else '',
                'stemmen': {}
            }
            new_items.append(item)
            added += 1
        print(f'   ✓ {len(results)} gevonden, {added} nieuw')
        time.sleep(0.5)

    print(f'\n   Nieuwe moties: {len(new_items)}')
    if new_items:
        all_items = existing + new_items
        all_items.sort(key=lambda x: x.get('datum', ''), reverse=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_items, f, ensure_ascii=False, indent=2)
        print(f'✅ moties.json bijgewerkt — totaal {len(all_items)} moties')
    else:
        print('✅ Geen nieuwe moties — ongewijzigd')

if __name__ == '__main__':
    main()
