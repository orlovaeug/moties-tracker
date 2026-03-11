#!/usr/bin/env python3
"""fix_indieners.py — fixes indieners, alignment, dates and stemmen by scraping stemmingsuitslagen."""
import json, re, urllib.request, html as html_module, time
from datetime import date

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8',
    'Accept-Language': 'nl-NL,nl;q=0.9',
    'Accept-Encoding': 'identity',
}

MONTHS = {'januari':1,'februari':2,'maart':3,'april':4,'mei':5,'juni':6,
          'juli':7,'augustus':8,'september':9,'oktober':10,'november':11,'december':12}

COALITIE  = {"D66","VVD","CDA","BBB","NSC"}
OPPOSITIE = {"PVV","GL-PvdA","SP","PvdD","CU","SGP","Volt","DENK","FvD","JA21","50PLUS","Gr.Markuszower","Groep-Keijzer"}
START_DATE = '2026-02-23'

LEDEN_PARTIJ = {
    "Fleur Agema": "PVV", "Martin Bosma": "PVV", "Barry Madlener": "PVV",
    "Geert Wilders": "PVV", "Emiel van Dijk": "PVV", "Markuszower": "Gr.Markuszower",
    "Michon-Derkzen": "VVD", "Rajkowski": "VVD", "Becker": "VVD", "Bikkers": "VVD",
    "Ellian": "VVD", "Hermans": "VVD", "Brekelmans": "VVD", "Hagen": "VVD",
    "Six Dijkstra": "VVD", "Klink": "VVD", "Maatoug": "GL-PvdA", "Nijboer": "GL-PvdA",
    "Bushoff": "GL-PvdA", "Dassen": "Volt", "Omtzigt": "NSC", "Bontenbal": "CDA",
    "Inge van Dijk": "CDA", "Boswijk": "CDA", "Diederik van Dijk": "SGP",
    "Stoffer": "SGP", "Bikker": "CU", "Ceder": "CU", "Van Baarle": "DENK",
    "Stephan van Baarle": "DENK", "Simons": "PvdD", "Teunissen": "PvdD",
    "Eerdmans": "JA21", "Léon de Jong": "PVV", "Van der Plas": "BBB",
    "Vedder": "CDA", "Flach": "SGP", "Grinwis": "CU", "Koekkoek": "Volt",
    "Kathmann": "GL-PvdA", "Mohandis": "GL-PvdA", "El Abassi": "DENK",
    "Temmink": "SP", "Jimmy Dijk": "SP", "Beckerman": "SP",
    "Peter de Groot": "VVD", "Krul": "CDA", "Van Hijum": "NSC",
}

STRIJDIG_KEYWORDS = ["klimaatdoel","kinderopvang gratis","eigen risico afschaffen",
                      "asielzoekers meer","vluchtelingen opvang","discriminatie aanpakken"]
CONFORM_KEYWORDS  = ["asielinstroom beperken","grenzen sluiten","defensie versterken",
                      "kernenergie","belastingverlaging"]

def detect_indiener(titel):
    m = re.search(r'(?:Gewijzigde\s+)?[Mm]otie\s+van\s+(?:het\s+lid|de\s+leden)\s+([A-Z][a-zA-Z\u00C0-\u017E\-]+(?:\s+[a-zA-Z\u00C0-\u017E\-]+){0,4}?)(?:\s+c\.s\.|\s+over\s|\s+en\s+[A-Z]|\s+-\s+[A-Z]|$)', titel)
    name_ctx = m.group(1).strip() if m else titel
    for naam in sorted(LEDEN_PARTIJ.keys(), key=len, reverse=True):
        pat = r'(?<![A-Za-z\u00C0-\u017E])' + re.escape(naam) + r'(?![A-Za-z\u00C0-\u017E])'
        if re.search(pat, name_ctx, re.IGNORECASE):
            return LEDEN_PARTIJ[naam]
    return "Onbekend"

def detect_alignment(titel, indiener, thema):
    t = titel.lower()
    for kw in STRIJDIG_KEYWORDS:
        if kw in t: return "strijdig"
    for kw in CONFORM_KEYWORDS:
        if kw in t: return "conform"
    if indiener in COALITIE: return "conform"
    return "neutraal"

def parse_dutch_date(s):
    m = re.search(r'(\d{1,2})\s+(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s+(20\d{2})', s, re.IGNORECASE)
    if m:
        d, mo, y = m.group(1), m.group(2).lower(), m.group(3)
        return f"{y}-{MONTHS[mo]:02d}-{int(d):02d}"
    return None

def fetch_html(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as r:
            return html_module.unescape(r.read().decode('utf-8', errors='replace'))
    except Exception as e:
        print(f'  Fetch fout {url[:60]}: {e}')
        return ''

# ── Scrape stemmingsuitslagen pages to build a lookup: zaak_id -> {datum, besluit} ──

def scrape_stemmingen(max_pages=10):
    """Scrape stemmingsuitslagen and return dict: zaak_id -> {datum, besluit}."""
    results = {}
    base = ('https://www.tweedekamer.nl/kamerstukken/stemmingsuitslagen'
            '?qry=%2A&fld_tk_categorie=Kamerstukken'
            '&fld_prl_kamerstuk=Stemmingsuitslagen&srt=date%3Adesc%3Adate&page=')

    for page in range(max_pages):
        html = fetch_html(base + str(page))
        if not html:
            break

        # Find links to stemmingsuitslag detail pages
        detail_links = re.findall(r'href="(/kamerstukken/stemmingsuitslagen/detail\?[^"]+)"', html)
        if not detail_links:
            break

        # Check dates only from result titles (format: "\n10 maart 2026\n" near start)
        # Look for dates in the search results section, not nav/footer
        results_section = html[html.find('Zoekresultaten'):] if 'Zoekresultaten' in html else html
        result_dates = re.findall(
            r'\n(\d{1,2})\s+(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s+(20\d{2})\n',
            results_section[:50000], re.IGNORECASE
        )
        if result_dates:
            last_date = parse_dutch_date(' '.join(result_dates[-1]))
            if last_date and last_date < START_DATE:
                print(f'  Pagina {page+1}: tot {last_date} — stoppen')
                for link in set(detail_links):
                    detail_results = scrape_stemming_detail('https://www.tweedekamer.nl' + link)
                    results.update(detail_results)
                break

        unique_links = list(set(detail_links))
        print(f'  Stemmingen pagina {page+1}: {len(unique_links)} uitslagen gevonden')
        if unique_links:
            print(f'    Eerste link: {unique_links[0][:80]}')
        for link in unique_links:
            detail_results = scrape_stemming_detail('https://www.tweedekamer.nl' + link)
            print(f'    Detail: {link[:60]} -> {len(detail_results)} moties')
            results.update(detail_results)
            time.sleep(0.3)

        time.sleep(1)

    return results

def scrape_stemming_detail(url):
    """Parse a stemmingsuitslag detail page. Returns dict: zaak_id -> {datum, besluit}."""
    html = fetch_html(url)
    if not html:
        return {}

    results = {}
    # Find all motie zaak IDs directly — works regardless of HTML structure
    # Pattern: id=2026Zxxxxx in href attributes (may have &amp; encoding)
    # Find all motie entries: each has an id=2026Z..., a date, and a Besluit
    
    # Split on any kamerstukken detail link containing a Zaak ID
    # The href may contain &amp; so normalise first
    html_norm = html.replace('&amp;', '&')
    
    # Split into blocks on each motie link
    blocks = re.split(r'(?=href="[^"]*[?&]id=2026Z)', html_norm)
    
    for block in blocks[:500]:  # safety limit
        id_m = re.search(r'[?&]id=(2026Z\w+)', block)
        if not id_m:
            continue
        zaak_id = id_m.group(1)
        
        # Date: look in first 400 chars of block
        datum = parse_dutch_date(block[:400])
        
        # Besluit: anywhere in block
        besluit_m = re.search(r'Besluit:\s*(Aangenomen|Verworpen|Aangehouden)', block, re.IGNORECASE)
        besluit = besluit_m.group(1).lower() if besluit_m else None
        
        if datum or besluit:
            results[zaak_id] = {'datum': datum, 'besluit': besluit}

    return results


# ── Hoofdprogramma ────────────────────────────────────────────────────────────

with open('moties.json', 'r', encoding='utf-8') as f:
    moties = json.load(f)

fixed_ind = 0
fixed_ali = 0
fixed_sta = 0
fixed_dat = 0
today = date.today()

# Pass 1: cheap fixes — indiener + alignment
for m in moties:
    titel = m.get('titel', '')
    if m.get('indiener') == 'Onbekend':
        detected = detect_indiener(titel)
        if detected != 'Onbekend':
            print(f"  Indiener: {titel[:55]} -> {detected}")
            m['indiener'] = detected
            fixed_ind += 1
    if m.get('alignment') == 'neutraal':
        new_ali = detect_alignment(titel, m.get('indiener',''), m.get('thema',''))
        if new_ali != 'neutraal':
            print(f"  Alignment: {titel[:50]} -> {new_ali}")
            m['alignment'] = new_ali
            fixed_ali += 1

# Pass 2: scrape stemmingsuitslagen pages to get dates + besluit
print('\nStemmingsuitslagen ophalen...')
stemmingen = scrape_stemmingen(max_pages=15)
print(f'  Gevonden: {len(stemmingen)} zaak-stemmingen')
# Debug: show sample zaak IDs from stemmingen
sample_keys = list(stemmingen.keys())[:3]
print(f'  Sample stemmingen keys: {sample_keys}')
# Debug: show sample zaak IDs from moties
sample_urls = [m.get('tk_url','') for m in moties if str(m.get('id','')).startswith('tk')][:3]
print(f'  Sample motie URLs: {[u[:70] for u in sample_urls]}')

# Build lookup: zaak_id from tk_url
removed = set()
for m in moties:
    tk_url = m.get('tk_url', '')
    zaak_m = re.search(r'[?&]id=(2026Z\w+)', tk_url)
    if not zaak_m:
        continue
    zaak_id = zaak_m.group(1)

    stemming = stemmingen.get(zaak_id)
    if not stemming:
        continue

    # Fix date
    if stemming.get('datum'):
        new_datum = stemming['datum']
        if new_datum < START_DATE:
            removed.add(m['id'])
            print(f"  Verwijderd (te oud {new_datum}): {m.get('titel','')[:50]}")
            continue
        if m.get('datum', '') != new_datum:
            m['datum'] = new_datum
            fixed_dat += 1

    # Fix status
    besluit = stemming.get('besluit')
    if besluit in ('aangenomen', 'verworpen') and m.get('status') == 'in_behandeling':
        m['status'] = besluit
        fixed_sta += 1
        print(f"  Status: {m.get('titel','')[:50]} -> {besluit}")
        if m.get('archief'):
            m['archief'] = False

# Also fix date for moties with scraping date (2026-03-11) that weren't in stemmingen
# by fetching their detail page HTML
needs_date = [m for m in moties
              if m.get('datum','') >= today.isoformat()
              and m.get('tk_url','')
              and m['id'] not in removed]
print(f'\nDatum fixup: {min(200, len(needs_date))} van {len(needs_date)} moties')
for m in needs_date[:200]:
    url = m['tk_url']
    if not url.startswith('http'):
        url = 'https://www.tweedekamer.nl' + url
    html = fetch_html(url)
    datum_m = re.search(
        r'Voorgesteld\s+(\d{1,2}\s+(?:januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s+20\d{2})',
        html, re.IGNORECASE
    )
    if datum_m:
        new_datum = parse_dutch_date(datum_m.group(1))
        if new_datum:
            if new_datum < START_DATE:
                removed.add(m['id'])
                print(f"  Verwijderd (te oud {new_datum}): {m.get('titel','')[:50]}")
            elif m.get('datum','') != new_datum:
                m['datum'] = new_datum
                fixed_dat += 1
    time.sleep(0.3)

if removed:
    moties = [m for m in moties if m.get('id') not in removed]
    print(f'  {len(removed)} moties verwijderd (voor {START_DATE})')

with open('moties.json', 'w', encoding='utf-8') as f:
    json.dump(moties, f, ensure_ascii=False, indent=2)

print(f'\n✅ {fixed_ind} indieners + {fixed_ali} alignments + {fixed_sta} statussen + {fixed_dat} datums gecorrigeerd')
