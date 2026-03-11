#!/usr/bin/env python3
"""fetch_moties.py — haalt moties op en verrijkt met datum + stemmen in één run."""
import json, re, time, hashlib, urllib.request, urllib.parse
import html as html_module
from datetime import date

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

MONTHS = {'januari':1,'februari':2,'maart':3,'april':4,'mei':5,'juni':6,
          'juli':7,'augustus':8,'september':9,'oktober':10,'november':11,'december':12}

COALITIE  = {"D66","VVD","CDA"}
OPPOSITIE = {"PVV","GL-PvdA","SP","PvdD","CU","SGP","Volt","DENK","FvD","JA21","50PLUS","Gr.Markuszower","Groep-Keijzer","BBB","NSC"}

LEDEN_PARTIJ = {
    # PVV
    "Geert Wilders":"PVV","Fleur Agema":"PVV","Martin Bosma":"PVV","Barry Madlener":"PVV",
    "Emiel van Dijk":"PVV","Léon de Jong":"PVV","El Boujdaini":"PVV","Heutink":"PVV",
    "Markuszower":"Gr.Markuszower","Groep Markuszower":"Gr.Markuszower",
    # VVD
    "Hermans":"VVD","Michon-Derkzen":"VVD","Rajkowski":"VVD","Becker":"VVD",
    "Bikkers":"VVD","Ellian":"VVD","Brekelmans":"VVD","Hagen":"VVD",
    "Six Dijkstra":"VVD","Klink":"VVD","Peter de Groot":"VVD","Abdi":"VVD","Klos":"VVD",
    # NSC
    "Omtzigt":"NSC","Van Hijum":"NSC","Struijs":"NSC","Boelsma-Hoekstra":"NSC","Lammers":"NSC",
    # BBB
    "Van der Plas":"BBB","Hamstra":"BBB","Wendel":"BBB","Jumelet":"BBB",
    "Van Oosterhout":"BBB","Vermeer":"BBB",
    # D66
    "Vervuurt":"D66","Paternotte":"D66","Dassen":"Volt",  # Dassen is Volt not D66
    # CDA
    "Bontenbal":"CDA","Inge van Dijk":"CDA","Boswijk":"CDA","Vedder":"CDA",
    "Krul":"CDA","Van den Berg":"CDA","Tijs van den Brink":"CDA",
    # GL-PvdA
    "Klaver":"GL-PvdA","Maatoug":"GL-PvdA","Nijboer":"GL-PvdA","Bushoff":"GL-PvdA",
    "Kathmann":"GL-PvdA","Mohandis":"GL-PvdA","Köse":"GL-PvdA","Moorman":"GL-PvdA",
    # SP
    "Jimmy Dijk":"SP","Beckerman":"SP","Temmink":"SP",
    # PvdD
    "Simons":"PvdD","Teunissen":"PvdD",
    # CU
    "Bikker":"CU","Ceder":"CU","Grinwis":"CU",
    # SGP
    "Diederik van Dijk":"SGP","Stoffer":"SGP","Flach":"SGP",
    # Volt
    "Koekkoek":"Volt",
    # DENK
    "Van Baarle":"DENK","Stephan van Baarle":"DENK","El Abassi":"DENK",
    # JA21
    "Eerdmans":"JA21",
    # FvD
    "Baudet":"FvD",
}

STRIJDIG_KEYWORDS = [
    "klimaatdoel","kinderopvang gratis","eigen risico afschaffen",
    "asielzoekers meer","vluchtelingen opvang","discriminatie aanpakken",
    "aow volledig van tafel","ww-verkorting niet",
]
CONFORM_KEYWORDS = [
    "asielinstroom beperken","grenzen sluiten","defensie versterken",
    "kernenergie","belastingverlaging","vrijheidsbijdrage","navo",
    "terugkeer","grenscontrole",
]

THEMA_KEYWORDS = {
    "Defensie":["defensie","militair","navo","leger","oekra","wapen","krijgsmacht","luchtmacht","marine"],
    "Bestaanszekerheid":["aow","pensioen","uitkering","armoede","minimumloon","bijstand","zzp","ww-duur","bestaanszekerheid"],
    "Klimaat & Energie":["klimaat","energie","windmolen","kerncentrale","co2","netcongestie","zonnepaneel","warmtepomp","fossiel"],
    "Wonen & Bouwen":["woning","huur","hypotheek","bouwen","nieuwbouw","woningmarkt","huurder","corporatie"],
    "Zorg":["zorg","eigen risico","ggz","ziekenhuis","verpleging","mantelzorg","huisarts","medicijn","apotheek"],
    "Asiel & Migratie":["asiel","migratie","vluchteling","ind","spreidingswet","azc","verblijf","inburgering","grenstoezicht"],
    "Onderwijs & Wetenschap":["onderwijs","school","leraar","student","universiteit","mbo","kinderopvang","studie"],
    "Landbouw & Natuur":["landbouw","boer","stikstof","natuur","natura 2000","veehouderij","mest","agrar","visserij"],
    "Financien":["belasting","begroting","box 3","btw","financien","rijksbegroting","staatsschuld","belastingdienst"],
    "Buitenlandse Zaken & Europa":["europa","oekra","buitenland","sanctie","diplomatie","europese unie"],
    "Democratie & Rechtsstaat":["democratie","grondwet","rechtsstaat","referendum","verkiezing","kiesrecht"],
    "Economie & Ondernemen":["economie","ondernemen","mkb","arbeidsmarkt","zzp","concurrentie","exportbevordering"],
    "Bereikbaarheid & Mobiliteit":["trein","spoor","fiets","ov","snelweg","ns ","mobiliteit","bereikbaarheid"],
    "Zorg & Preventie":["preventie","leefstijl","alcohol","roken","obesitas","vaccinatie"],
    "Overig":[],
}

def detect_thema(text):
    t = text.lower()
    best, best_score = "Overig", 0
    for thema, kws in THEMA_KEYWORDS.items():
        score = sum(1 for k in kws if k in t)
        if score > best_score:
            best, best_score = thema, score
    return best

def detect_indiener(titel):
    m = re.search(
        r'(?:(?:Nader\s+)?[Gg]ewijzigde\s+)?[Mm]otie\s+van\s+(?:het\s+lid|de\s+leden)\s+'
        r'([A-Z][a-zA-Z\u00C0-\u017E\-]+(?:\s+[a-zA-Z\u00C0-\u017E\-]+){0,4}?)'
        r'(?:\s+c\.s\.|\s+over\s|\s+en\s+[A-Z]|\s+-\s+[A-Z]|$)',
        titel
    )
    name_ctx = m.group(1).strip() if m else titel
    for naam in sorted(LEDEN_PARTIJ.keys(), key=len, reverse=True):
        pat = r'(?<![A-Za-z\u00C0-\u017E])' + re.escape(naam) + r'(?![A-Za-z\u00C0-\u017E])'
        if re.search(pat, name_ctx, re.IGNORECASE):
            return LEDEN_PARTIJ[naam]
    for p in ["PVV","VVD","NSC","BBB","D66","GL-PvdA","CDA","SP","PvdD","CU","SGP","Volt","DENK","FvD","JA21","50PLUS","Gr.Markuszower"]:
        if p in titel:
            return p
    return "Onbekend"

def detect_alignment(titel, indiener, thema):
    t = titel.lower()
    for kw in STRIJDIG_KEYWORDS:
        if kw in t: return "strijdig"
    for kw in CONFORM_KEYWORDS:
        if kw in t: return "conform"
    if indiener in COALITIE: return "conform"
    return "neutraal"

def make_id(val):
    return 'tk' + hashlib.md5(str(val).encode()).hexdigest()[:10]

def parse_dutch_date(s):
    m = re.search(
        r'(\d{1,2})\s+(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s+(20\d{2})',
        s, re.IGNORECASE
    )
    if m:
        mo = MONTHS.get(m.group(2).lower(), 0)
        if mo:
            return f"{m.group(3)}-{mo:02d}-{int(m.group(1)):02d}"
    return None

def fetch_html(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as r:
            return html_module.unescape(r.read().decode('utf-8', errors='replace'))
    except Exception as e:
        print(f'  Fetch fout: {e}')
        return ''

# ── Step 1: Scrape stemmingsuitslagen → build lookup zaak_id -> {datum, besluit} ──

def scrape_stemmingen():
    """Scrape stemmingsuitslagen pages since START_DATE. Returns zaak_id -> {datum, besluit}."""
    stemmingen = {}
    base = ('https://www.tweedekamer.nl/kamerstukken/stemmingsuitslagen'
            '?qry=%2A&fld_tk_categorie=Kamerstukken'
            '&fld_prl_kamerstuk=Stemmingsuitslagen&srt=date%3Adesc%3Adate&page=')

    for page in range(20):
        html = fetch_html(base + str(page))
        if not html:
            break

        # Find detail page links on list page
        detail_links = list(set(re.findall(
            r'href="(/kamerstukken/stemmingsuitslagen/detail\?[^"]+)"', html
        )))
        if not detail_links:
            print(f'  Stemmingen pagina {page+1}: geen links — stoppen')
            break

        print(f'  Stemmingen pagina {page+1}: {len(detail_links)} uitslagen')

        # Scrape each detail page
        all_old = True
        for link in detail_links:
            link_url = 'https://www.tweedekamer.nl' + link.replace('&amp;', '&')
            detail_html = fetch_html(link_url)
            if not detail_html:
                continue

            detail_html_norm = detail_html.replace('&amp;', '&')

            # Split into per-motie blocks on any link containing a Zaak ID
            blocks = re.split(r'(?=href="[^"]*[?&]id=2026Z)', detail_html_norm)

            for block in blocks[:300]:
                id_m = re.search(r'[?&]id=(2026Z\w+)', block)
                if not id_m:
                    continue
                zaak_id = id_m.group(1)

                datum = parse_dutch_date(block[:500])
                besluit_m = re.search(r'Besluit:\s*(Aangenomen|Verworpen|Aangehouden)', block, re.IGNORECASE)
                besluit = besluit_m.group(1).lower() if besluit_m else None

                if datum or besluit:
                    stemmingen[zaak_id] = {'datum': datum, 'besluit': besluit}
                    if datum and datum >= START_DATE:
                        all_old = False

            time.sleep(0.3)

        # Check if this page only has old stemmingen
        # Look for dates in result titles (lines starting with a date)
        page_dates = re.findall(
            r'\n(\d{1,2}\s+(?:januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s+20\d{2})\n',
            html[:30000], re.IGNORECASE
        )
        if page_dates:
            last = parse_dutch_date(page_dates[-1])
            if last and last < START_DATE:
                print(f'  Pagina {page+1}: oudste datum {last} — stoppen')
                break

        time.sleep(1)

    print(f'  Stemmingen totaal: {len(stemmingen)} moties met uitslag')
    return stemmingen

# ── Step 2: Get real date from motie detail page ──

def fetch_motie_datum(url):
    """Fetch motie detail page and extract 'Voorgesteld DD maand YYYY'."""
    if not url.startswith('http'):
        url = 'https://www.tweedekamer.nl' + url
    html = fetch_html(url)
    if not html:
        return None
    return parse_dutch_date(re.search(
        r'Voorgesteld\s+(\d{1,2}\s+\w+\s+20\d{2})', html, re.IGNORECASE
    ).group(1) if re.search(r'Voorgesteld\s+(\d{1,2}\s+\w+\s+20\d{2})', html, re.IGNORECASE) else '')

# ── Step 3: Scrape moties list pages ──

def fetch_page(page=0):
    url = ('https://www.tweedekamer.nl/kamerstukken/moties'
           '?qry=%2A&fld_tk_categorie=Kamerstukken&fld_prl_kamerstuk=Moties'
           f'&srt=date%3Adesc%3Adate&page={page}')
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read().decode('utf-8', errors='replace')
        print(f'  Pagina {page+1}: {len(raw)} bytes')
        return raw
    except Exception as e:
        print(f'  Fout pagina {page+1}: {e}')
        return ''

def parse_moties_from_html(raw):
    results = []
    raw = html_module.unescape(raw)
    items = re.split(r'class=["\']search-result-item["\']', raw)
    for item in items[1:]:
        link_m = re.search(r'href="(/kamerstukken/moties/detail\?[^"]+)"', item)
        if not link_m:
            continue
        link = 'https://www.tweedekamer.nl' + link_m.group(1).replace('&amp;', '&')
        title_m = re.search(r'<h3[^>]*>(.*?)</h3>', item, re.DOTALL)
        title = re.sub(r'<[^>]+>', '', title_m.group(1)).strip() if title_m else ''
        if not title or 'motie' not in title.lower():
            continue
        date_m = re.search(
            r'(\d{1,2})\s+(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s+(20\d{2})',
            item, re.IGNORECASE
        )
        list_date = ''
        if date_m:
            mo = MONTHS.get(date_m.group(2).lower(), 0)
            if mo:
                list_date = f"{date_m.group(3)}-{mo:02d}-{int(date_m.group(1)):02d}"
        results.append({'titel': title, 'datum': list_date or TODAY, 'link': link})
    return results

# ── Main ──

def main():
    print(f'Moties ophalen — {TODAY}')

    try:
        with open(DATA_FILE, encoding='utf-8') as f:
            existing = json.load(f)
    except FileNotFoundError:
        existing = []

    existing_ids   = {x['id'] for x in existing}
    existing_links = {x.get('tk_url','') for x in existing}
    existing_by_zaak = {
        re.search(r'[?&]id=(2026Z\w+)', x.get('tk_url','')).group(1): x
        for x in existing
        if re.search(r'[?&]id=(2026Z\w+)', x.get('tk_url',''))
    }
    print(f'Bestaande moties: {len(existing)}')

    scraped_count = sum(1 for x in existing if str(x.get('id','')).startswith('tk'))
    is_backfill   = scraped_count == 0
    max_pages     = 50 if is_backfill else 5
    print(f'Mode: {"backfill" if is_backfill else "daily"} (max {max_pages} paginas)')

    # Step 1: Always scrape stemmingsuitslagen first — fast bulk lookup
    print('\nStemmingsuitslagen ophalen...')
    stemmingen = scrape_stemmingen()

    # Apply stemmingen to existing moties that are still in_behandeling
    updated = 0
    for zaak_id, stemming in stemmingen.items():
        m = existing_by_zaak.get(zaak_id)
        if not m:
            continue
        changed = False
        if stemming.get('datum') and m.get('datum','') != stemming['datum']:
            m['datum'] = stemming['datum']
            changed = True
        if stemming.get('besluit') and m.get('status') == 'in_behandeling':
            m['status'] = stemming['besluit']
            changed = True
            if m.get('archief'):
                m['archief'] = False
        if changed:
            updated += 1
    print(f'  {updated} bestaande moties bijgewerkt via stemmingen')

    # Step 2: Scrape moties list pages for new moties
    new_items = []
    for page in range(max_pages):
        raw = fetch_page(page)
        if not raw:
            break

        results = parse_moties_from_html(raw)
        print(f'  Geparsed: {len(results)} moties')
        if not results:
            break

        found_new = False
        all_old = True
        for r in results:
            # Use stemmingen datum if available for list-page date check
            zaak_m = re.search(r'[?&]id=(2026Z\w+)', r['link'])
            zaak_id = zaak_m.group(1) if zaak_m else None
            stem_datum = stemmingen.get(zaak_id, {}).get('datum') if zaak_id else None
            real_date = stem_datum or r['datum']

            if real_date >= START_DATE:
                all_old = False
            if real_date < START_DATE:
                continue
            if r['link'] in existing_links:
                continue
            item_id = make_id(r['link'])
            if item_id in existing_ids:
                continue

            existing_ids.add(item_id)
            existing_links.add(r['link'])
            found_new = True

            thema    = detect_thema(r['titel'])
            indiener = detect_indiener(r['titel'])

            # Get real date: stemmingen first, then detail page HTML
            if stem_datum:
                motie_datum = stem_datum
                status = stemmingen[zaak_id].get('besluit') or 'in_behandeling'
            else:
                # Fetch detail page for real "Voorgesteld" date
                motie_datum = fetch_motie_datum(r['link']) or r['datum']
                status = 'in_behandeling'
                time.sleep(0.4)

            # Skip if before start date once we know real date
            if motie_datum < START_DATE:
                continue

            new_items.append({
                'id':         item_id,
                'titel':      r['titel'],
                'indiener':   indiener,
                'datum':      motie_datum,
                'thema':      thema,
                'status':     status,
                'alignment':  detect_alignment(r['titel'], indiener, thema),
                'vergadering':'',
                'tk_url':     r['link'],
                'toelichting':'',
                'stemmen':    {},
                'archief':    False,
            })

        if all_old:
            print(f'  Alle moties voor {START_DATE} — klaar')
            break

        time.sleep(1.5)

    # Fix dates for existing moties still showing TODAY as date
    needs_date = [
        m for m in existing
        if m.get('datum','') >= TODAY
        and m.get('tk_url','')
        and str(m.get('id','')).startswith('tk')
    ]
    if needs_date:
        print(f'\nDatum fixup: {min(150, len(needs_date))} van {len(needs_date)} moties')
        for m in needs_date[:150]:
            zaak_m = re.search(r'[?&]id=(2026Z\w+)', m.get('tk_url',''))
            zaak_id = zaak_m.group(1) if zaak_m else None
            if zaak_id and zaak_id in stemmingen and stemmingen[zaak_id].get('datum'):
                m['datum'] = stemmingen[zaak_id]['datum']
                continue
            nd = fetch_motie_datum(m['tk_url'])
            if nd:
                if nd < START_DATE:
                    m['_remove'] = True
                else:
                    m['datum'] = nd
            time.sleep(0.3)
        existing = [m for m in existing if not m.get('_remove')]

    # Merge
    print(f'\nNieuwe moties: {len(new_items)}')
    for m in new_items[:5]:
        print(f'  + {m["datum"]} | {m["titel"][:70]}')

    # Archive logic: in_behandeling > 7 days old
    all_moties = existing + new_items
    for m in all_moties:
        if m.get('status') in ('aangenomen','verworpen'):
            m['archief'] = False
            continue
        try:
            age = (date.today() - date.fromisoformat(m.get('datum', TODAY))).days
        except:
            age = 0
        if m.get('status') == 'in_behandeling' and age > 7 and not m.get('archief'):
            m['archief'] = True
        elif m.get('status') == 'aangehouden' and age > 60 and not m.get('archief'):
            m['archief'] = True

    active = sum(1 for m in all_moties if not m.get('archief'))
    print(f'Totaal: {len(all_moties)} moties ({active} actief)')

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_moties, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
