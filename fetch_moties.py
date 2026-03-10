#!/usr/bin/env python3
"""
fetch_moties.py — scrapet moties van tweedekamer.nl
Gebruikt de officiele zoekpagina. Geen API-sleutel nodig.
"""
import json, re, time, hashlib
from datetime import date
import urllib.request, urllib.parse
import html as html_module

DATA_FILE  = 'moties.json'
TODAY      = date.today().isoformat()
START_DATE = '2026-02-23'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'nl-NL,nl;q=0.9,en;q=0.8',
    'Accept-Encoding': 'identity',
    'Connection': 'keep-alive',
}

MONTHS = {
    'januari':1,'februari':2,'maart':3,'april':4,'mei':5,'juni':6,
    'juli':7,'augustus':8,'september':9,'oktober':10,'november':11,'december':12
}

THEMA_KEYWORDS = {
    "Defensie": ["defensie","militair","navo","leger","oekra","wapen","krijgsmacht","luchtmacht","marine","veiligheidsraad"],
    "Bestaanszekerheid": ["aow","pensioen","uitkering","armoede","minimumloon","bijstand","zzp","ww-duur","bestaanszekerheid","werkloosheid"],
    "Klimaat & Energie": ["klimaat","energie","windmolen","kerncentrale","co2","netcongestie","zonnepaneel","warmtepomp","fossiel"],
    "Wonen & Bouwen": ["woning","huur","hypotheek","bouwen","nieuwbouw","woningmarkt","huurder","corporatie","woningnood"],
    "Zorg": ["zorg","eigen risico","ggz","ziekenhuis","verpleging","mantelzorg","huisarts","medicijn","apotheek","gezondheidszorg"],
    "Asiel & Migratie": ["asiel","migratie","vluchteling","ind","spreidingswet","azc","verblijf","inburgering","grenstoezicht"],
    "Onderwijs & Wetenschap": ["onderwijs","school","leraar","student","universiteit","mbo","kinderopvang","studie","basisschool"],
    "Landbouw & Natuur": ["landbouw","boer","stikstof","natuur","natura 2000","veehouderij","mest","agrar","visserij"],
    "Financien": ["belasting","begroting","box 3","btw","financien","rijksbegroting","staatsschuld","belastingdienst","accijns"],
    "Buitenlandse Zaken & Europa": ["europa","oekra","buitenland","sanctie","diplomatie","europese unie","buitenlandse"],
    "Democratie & Rechtsstaat": ["democratie","grondwet","rechtsstaat","referendum","verkiezing","kiesrecht","parlement"],
    "Economie & Ondernemen": ["economie","ondernemen","mkb","innovatie","bedrijf","concurrentie","arbeidsmarkt","loon"],
    "Bereikbaarheid & Mobiliteit": ["mobiliteit","trein","openbaar vervoer","fiets","schiphol","lelystad","verkeer","rijkswegen"],
    "Digitalisering & AI": ["digitaal","algoritme","cyber","software","kunstmatige intelligentie","internet","data"],
    "Veiligheid & Justitie": ["politie","criminaliteit","justitie","gevangenis","drugs","terrorisme","rechtbank","strafrecht"],
    "Sociale Cohesie": ["cultuur","integratie","discriminatie","racisme","lhbti","emancipatie","vrijwillig","religie"],
    "Overheid & Bestuur": ["overheid","gemeente","provincie","bestuur","ambtenaar","uitvoering","dienstverlening","toeslagen"],
    "Nationale Veiligheid": ["inlichtingen","aivd","mivd","spionage","nationale veiligheid","cybersecurity","terrorismebestrijding"],
}

PARTIJEN = ["PVV","VVD","NSC","BBB","D66","GL-PvdA","CDA","SP","PvdD","CU","SGP","Volt","DENK","FvD","JA21","50PLUS","Gr.Markuszower"]

LEDEN_PARTIJ = {
    "Wilders":"PVV","Heutink":"PVV","Agema":"PVV",
    "Yesilgöz":"VVD","Hermans":"VVD","Peter de Groot":"VVD","Brekelmans":"VVD","Rajkowski":"VVD","Six Dijkstra":"VVD",
    "Omtzigt":"NSC","Dassen":"NSC","Nicolaï":"NSC",
    "Van der Plas":"BBB","Vedder":"BBB","Struijs":"BBB","Grinwis":"BBB",
    "Paternotte":"D66","Jetten":"D66","Van Weyenberg":"D66","Van Lanschot":"D66","Ten Hove":"D66","Kathmann":"D66",
    "Klaver":"GL-PvdA","Nijboer":"GL-PvdA","Westerveld":"GL-PvdA","Van Baarle":"GL-PvdA","Dobbe":"GL-PvdA","Mutluer":"GL-PvdA",
    "Bontenbal":"CDA","Boswijk":"CDA","Amhaouch":"CDA","Van Campen":"CDA",
    "Dobbe":"SP","Dijk":"SP","Leijten":"SP","Koudstaal":"SP",
    "Teunissen":"PvdD","Wassenberg":"PvdD",
    "Bikker":"CU","Segers":"CU","Ceder":"CU",
    "Stoffer":"SGP","Diederik van Dijk":"SGP","Van der Staaij":"SGP",
    "Koekkoek":"Volt","Dassen":"Volt",
    "Azarkan":"DENK","Ergin":"DENK",
    "Van Houwelingen":"FvD","Baudet":"FvD",
    "Eerdmans":"JA21","Van Meijeren":"JA21",
    "Markuszower":"Gr.Markuszower",
}

def detect_thema(text):
    t = text.lower()
    best, best_score = "Overig", 0
    for thema, kws in THEMA_KEYWORDS.items():
        score = sum(1 for k in kws if k in t)
        if score > best_score:
            best, best_score = thema, score
    return best

def detect_indiener(title):
    m = re.search(r'lid(?:en)?\s+([A-Z][a-zA-Z\u00C0-\u017E\s\-]+?)(?:\s+c\.s\.|\s+en\s+[A-Z]|\s*-\s*[A-Z]|$)', title)
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

def parse_dutch_date(s):
    parts = s.strip().split()
    if len(parts) == 3:
        try:
            d = int(parts[0])
            mo = MONTHS.get(parts[1].lower(), 0)
            y = int(parts[2])
            if mo:
                return f'{y:04d}-{mo:02d}-{d:02d}'
        except:
            pass
    return None

def fetch_page(page=0):
    url = (
        'https://www.tweedekamer.nl/kamerstukken/moties'
        '?qry=%2A'
        '&fld_tk_categorie=Kamerstukken'
        '&fld_prl_kamerstuk=Moties'
        '&srt=date%3Adesc%3Adate'
        f'&page={page}'
    )
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read().decode('utf-8', errors='replace')
        print(f'  Pagina {page+1}: {len(raw)} bytes ontvangen')
        return raw
    except Exception as e:
        print(f'  Fout pagina {page+1}: {e}')
        return ''

def parse_moties_from_html(raw):
    """
    Parse moties from TK search results HTML.
    The page structure has search result items containing:
    - a date (in Dutch format)  
    - a link to /kamerstukken/moties/detail?id=...
    - a title text
    """
    results = []

    # Unescape HTML entities first
    raw = html_module.unescape(raw)

    # Strategy 1: find all motie detail links with their surrounding context
    # Each result block is roughly 500-800 chars
    link_pattern = re.compile(
        r'href=["\']?(/kamerstukken/moties/detail\?[^"\'>\s]+)["\']?[^>]*>([^<]{10,300})</a>',
        re.IGNORECASE
    )

    date_pattern = re.compile(
        r'\b(\d{1,2})\s+(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s+(20\d{2})\b',
        re.IGNORECASE
    )

    # Find all links first
    for lm in link_pattern.finditer(raw):
        link = lm.group(1)
        title = lm.group(2).strip()

        # Skip navigation/pagination links
        if not title or len(title) < 10:
            continue
        if not ('Motie' in title or 'motie' in title):
            continue

        # Look for a date in the 600 chars before this link
        start = max(0, lm.start() - 600)
        context = raw[start:lm.start()]
        dates = date_pattern.findall(context)

        if dates:
            d, mo, y = dates[-1]  # take the closest date
            iso_date = f'{y}-{MONTHS[mo.lower()]:02d}-{int(d):02d}'
        else:
            iso_date = TODAY

        full_link = 'https://www.tweedekamer.nl' + link if link.startswith('/') else link
        title_clean = re.sub(r'\s+', ' ', title).strip()

        results.append({
            'titel': title_clean,
            'datum': iso_date,
            'link': full_link
        })

    return results

def main():
    print(f'Moties ophalen van tweedekamer.nl — {TODAY}')

    try:
        with open(DATA_FILE, encoding='utf-8') as f:
            existing = json.load(f)
    except FileNotFoundError:
        existing = []

    existing_ids = {x['id'] for x in existing}
    existing_links = {x.get('tk_url', '') for x in existing}
    print(f'Bestaande moties: {len(existing)}')

    new_items = []

    for page in range(10):
        raw = fetch_page(page)
        if not raw:
            break

        results = parse_moties_from_html(raw)
        print(f'  Geparsed: {len(results)} moties')

        if not results:
            print(f'  Geen moties gevonden op pagina {page+1} — stoppen')
            break

        found_new = False
        all_old = True
        for r in results:
            if r['datum'] >= START_DATE:
                all_old = False
            if r['datum'] < START_DATE:
                continue
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
            found_new = True

        if all_old:
            print(f'  Alle moties voor {START_DATE} — klaar')
            break

        time.sleep(1.5)

    print(f'\nNieuwe moties gevonden: {len(new_items)}')
    if new_items:
        for m in new_items[:3]:
            print(f'  + {m["datum"]} | {m["titel"][:70]}')

    all_items = existing + new_items
    all_items.sort(key=lambda x: x.get('datum', ''), reverse=True)

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)
    print(f'Klaar — totaal {len(all_items)} moties in moties.json')

if __name__ == '__main__':
    main()
