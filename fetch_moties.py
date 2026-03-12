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

MONTHS = {
    'januari':1,'februari':2,'maart':3,'april':4,'mei':5,'juni':6,
    'juli':7,'augustus':8,'september':9,'oktober':10,'november':11,'december':12
}

# Coalitie kabinet-Jetten: VVD, D66, CDA
COALITIE  = {"VVD","D66","CDA"}
OPPOSITIE = {"PVV","GL-PvdA","NSC","BBB","SP","PvdD","CU","SGP","Volt","DENK","FvD","JA21","50PLUS","Gr.Markuszower","Groep-Keijzer"}

LEDEN_PARTIJ = {
    # PVV
    "Wilders":"PVV","Geert Wilders":"PVV","Agema":"PVV","Fleur Agema":"PVV",
    "Bosma":"PVV","Martin Bosma":"PVV","Madlener":"PVV","Barry Madlener":"PVV",
    "Emiel van Dijk":"PVV","Léon de Jong":"PVV","Leon de Jong":"PVV",
    "El Boujdaini":"PVV","Heutink":"PVV","Helder":"PVV","Faber":"PVV",
    "Fritsma":"PVV","Graus":"PVV","Beertema":"PVV","De Graaf":"PVV",
    "Duvekot":"PVV","Kerseboom":"PVV",
    # VVD
    "Hermans":"VVD","Yesilgöz":"VVD","Dilan Yesilgöz":"VVD",
    "Michon-Derkzen":"VVD","Rajkowski":"VVD","Becker":"VVD","Bikkers":"VVD",
    "Ellian":"VVD","Brekelmans":"VVD","Hagen":"VVD","Six Dijkstra":"VVD",
    "Klink":"VVD","Peter de Groot":"VVD","Klos":"VVD","Erkens":"VVD",
    "Minhas":"VVD","Palmen":"VVD","Soepboer":"VVD","Wesselink":"VVD",
    "Gündogan":"VVD","Van der Werf":"VVD",
    # NSC
    "Omtzigt":"NSC","Pieter Omtzigt":"NSC","Van Hijum":"NSC","Struijs":"NSC",
    "Boelsma-Hoekstra":"NSC","Lammers":"NSC","Crijns":"NSC","Podt":"NSC","Hartman":"NSC",
    # BBB
    "Van der Plas":"BBB","Caroline van der Plas":"BBB","Hamstra":"BBB","Aardema":"BBB","Tuinman":"BBB",
    "Wendel":"BBB","Jumelet":"BBB","Van Oosterhout":"BBB","Vermeer":"BBB","Kostić":"BBB",
    # GL-PvdA
    "Klaver":"GL-PvdA","Jesse Klaver":"GL-PvdA","Timmermans":"GL-PvdA",
    "Maatoug":"GL-PvdA","Nijboer":"GL-PvdA","Bushoff":"GL-PvdA",
    "Kathmann":"GL-PvdA","Mohandis":"GL-PvdA","Köse":"GL-PvdA","Moorman":"GL-PvdA",
    "Bromet":"GL-PvdA","Chakor":"GL-PvdA","Gijs van Dijk":"GL-PvdA",
    "Hammelburg":"GL-PvdA","Mutluer":"GL-PvdA","Piri":"GL-PvdA",
    "Thijssen":"GL-PvdA","Westerveld":"GL-PvdA","Kuiken":"GL-PvdA",
    "Fatihya Abdi":"GL-PvdA",
    # D66
    "Paternotte":"D66","Jan Paternotte":"D66","Vervuurt":"D66",
    "Van Asten":"D66","Wuite":"D66","Raemakers":"D66","White":"D66","Van der Laan":"D66",
    # CDA
    "Bontenbal":"CDA","Henri Bontenbal":"CDA","Boswijk":"CDA","Vedder":"CDA",
    "Krul":"CDA","Van den Berg":"CDA","Van Ark":"CDA","Armut":"CDA",
    "Van den Brink":"CDA","Inge van Dijk":"CDA",
    # SP
    "Jimmy Dijk":"SP","Dobbe":"SP","Beckerman":"SP","Temmink":"SP","Van Nispen":"SP","Leijten":"SP","Fleur":"SP",
    # PvdD
    "Simons":"PvdD","Teunissen":"PvdD","Vestering":"PvdD","Van Raan":"PvdD",
    # CU
    "Bikker":"CU","Mirjam Bikker":"CU","Ceder":"CU","Grinwis":"CU",
    # SGP
    "Diederik van Dijk":"SGP","Stoffer":"SGP","Flach":"SGP",
    # Volt
    "Dassen":"Volt","Koekkoek":"Volt","Nanninga":"Volt",
    # DENK
    "Stephan van Baarle":"DENK","Van Baarle":"DENK","El Abassi":"DENK","Ergin":"DENK","Kırcalı":"DENK","Kircali":"DENK",
    # JA21
    "Eerdmans":"JA21",
    # FvD
    "Baudet":"FvD",
    # Groep Markuszower
    "Markuszower":"Gr.Markuszower",
    # Groep Keijzer
    "Keijzer":"Groep-Keijzer",
    # 50PLUS
    "Baay-Timmerman":"50PLUS",
}

STRIJDIG_KEYWORDS = [
    "klimaatdoel","kinderopvang gratis","eigen risico afschaffen",
    "asielzoekers meer","vluchtelingen opvang","discriminatie aanpakken",
]
CONFORM_KEYWORDS = [
    "asielinstroom beperken","grenzen sluiten","defensie versterken",
    "kernenergie","belastingverlaging","navo","terugkeer","grenscontrole",
]

THEMA_KEYWORDS = {
    "Defensie":["defensie","militair","navo","leger","oekra","wapen","krijgsmacht","luchtmacht","marine"],
    "Bestaanszekerheid":["aow","pensioen","uitkering","armoede","minimumloon","bijstand","bestaanszekerheid"],
    "Klimaat & Energie":["klimaat","energie","windmolen","kerncentrale","co2","netcongestie","zonnepaneel","warmtepomp","fossiel"],
    "Wonen & Bouwen":["woning","huur","hypotheek","bouwen","nieuwbouw","woningmarkt","huurder","corporatie"],
    "Zorg":["zorg","eigen risico","ggz","ziekenhuis","verpleging","mantelzorg","huisarts","medicijn","apotheek"],
    "Asiel & Migratie":["asiel","migratie","vluchteling","ind","azc","verblijf","inburgering","grenstoezicht","asielzoekers"],
    "Onderwijs":["onderwijs","school","leraar","student","universiteit","mbo","kinderopvang","studie"],
    "Landbouw & Natuur":["landbouw","boer","stikstof","natuur","natura","veehouderij","mest","visserij"],
    "Financiën":["belasting","begroting","box 3","btw","rijksbegroting","staatsschuld","belastingdienst"],
    "Buitenlandse Zaken":["europa","oekra","buitenland","sanctie","diplomatie","israel","gaza","ukraine"],
    "Democratie & Rechtsstaat":["democratie","grondwet","rechtsstaat","referendum","verkiezing","rechter"],
    "Economie":["economie","ondernemen","mkb","arbeidsmarkt","concurrentie","export","innovatie"],
    "Bereikbaarheid":["trein","spoor","fiets","ov","snelweg","mobiliteit","bereikbaarheid","schiphol"],
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
    for p in ["PVV","VVD","NSC","BBB","D66","GL-PvdA","CDA","SP","PvdD","CU","SGP","Volt","DENK","FvD","JA21","50PLUS"]:
        if p in titel:
            return p
    return "Onbekend"

def detect_alignment(titel, indiener):
    t = titel.lower()
    for kw in STRIJDIG_KEYWORDS:
        if kw in t: return "strijdig"
    for kw in CONFORM_KEYWORDS:
        if kw in t: return "conform"
    if indiener in COALITIE: return "conform"
    if indiener in OPPOSITIE: return "strijdig"
    return "neutraal"

def make_id(val):
    return 'tk' + hashlib.md5(str(val).encode()).hexdigest()[:10]

def parse_dutch_date(s):
    if not s:
        return None
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
            raw = r.read().decode('utf-8', errors='replace')
        return html_module.unescape(raw)
    except Exception as e:
        print(f'  Fetch fout: {e}')
        return ''

def extract_zaak_id(url_or_str):
    """Extract zaak ID from URL — any year (2025Z, 2026Z, etc.)"""
    m = re.search(r'[?&]id=(\d{4}Z\w+)', url_or_str)
    return m.group(1) if m else None

# ── Live Kamerleden scrape ──

def fetch_leden_partij():
    PARTY_NORM = {
        "GroenLinks-PvdA":"GL-PvdA","ChristenUnie":"CU",
        "Groep Markuszower":"Gr.Markuszower","Lid Keijzer":"Groep-Keijzer","FVD":"FvD",
    }
    result = {}
    html = fetch_html("https://www.tweedekamer.nl/kamerleden_en_commissies/alle_kamerleden")
    if not html:
        return {}
    cards = re.findall(
        r'/alle_kamerleden/[^"]+">([^<]+)</a>\s*</h3>\s*<[^>]+>\s*([A-Za-z0-9\-\s]+?)[\s<]',
        html
    )
    for full_name, party in cards:
        full_name = full_name.strip()
        party = PARTY_NORM.get(party.strip(), party.strip())
        if not full_name or not party or len(party) > 25:
            continue
        result[full_name] = party
        parts = full_name.split()
        for i in range(len(parts)-1, -1, -1):
            if parts[i][0].isupper():
                if parts[i] not in result:
                    result[parts[i]] = party
                break
    print(f'  Kamerleden geladen: {len(result)} namen')
    return result

# ── Stemmingsuitslagen ──

def scrape_stemmingen():
    """
    Scrape stemmingsuitslagen since START_DATE.
    
    Real page structure (confirmed from live fetch):
    - URL: /stemmingsuitslagen/detail?id=2026P03693
    - Heading: "Plenaire vergadering 10 maart 2026" (in <h2>, after ~8KB of nav)
    - Motie links: href="/kamerstukken/detail?id=2026Z04746&did=2026D06518"
    - Besluit: plain text "Besluit: Aangenomen. (75-74)" — NOT inside <strong>
    - Footer link: "Bekijk de overige stemmingen van 10 maart 2026" with fromdate=2026-03-10
    
    Returns dict: zaak_id -> {datum, besluit}
    """
    stemmingen = {}
    base = (
        'https://www.tweedekamer.nl/kamerstukken/stemmingsuitslagen'
        '?qry=%2A&fld_tk_categorie=Kamerstukken'
        '&fld_prl_kamerstuk=Stemmingsuitslagen&srt=date%3Adesc%3Adate&page='
    )

    for page in range(25):
        html = fetch_html(base + str(page))
        if not html:
            break

        detail_links = list(dict.fromkeys(re.findall(
            r'href="(/kamerstukken/stemmingsuitslagen/detail\?[^"]+)"', html
        )))
        if not detail_links:
            print(f'  Stemmingen pagina {page+1}: geen links — stoppen')
            break

        print(f'  Stemmingen pagina {page+1}: {len(detail_links)} sessies')

        oldest_on_page = None

        for link in detail_links:
            link_url = 'https://www.tweedekamer.nl' + link.replace('&amp;', '&')
            detail = fetch_html(link_url)
            if not detail:
                continue

            detail = detail.replace('&amp;', '&')
            # Get session date — try 3 methods:
            # 1. fromdate= in footer link (most reliable, always present)
            session_datum = None
            footer_m = re.search(r'fromdate=(20\d{2}-\d{2}-\d{2})', detail)
            if footer_m:
                session_datum = footer_m.group(1)
            
            if not session_datum:
                # 2. Strip tags and find "Plenaire vergadering DD maand YYYY"
                detail_text = re.sub(r'<[^>]+>', ' ', detail)
                pv_m = re.search(
                    r'Plenaire\s+vergadering\s+(\d{1,2}\s+\w+\s+20\d{2})',
                    detail_text, re.IGNORECASE
                )
                if pv_m:
                    session_datum = parse_dutch_date(pv_m.group(1))
            
            if not session_datum:
                # 3. Any Dutch date in page text
                detail_text = re.sub(r'<[^>]+>', ' ', detail)
                any_m = re.search(
                    r'(\d{1,2}\s+(?:januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s+20\d{2})',
                    detail_text, re.IGNORECASE
                )
                if any_m:
                    session_datum = parse_dutch_date(any_m.group(1))

            if not session_datum:
                print(f'    Geen datum gevonden: {link_url[:80]}')
                continue

            # Track oldest on page
            if oldest_on_page is None or session_datum < oldest_on_page:
                oldest_on_page = session_datum

            # Skip sessions before our window
            if session_datum < START_DATE:
                print(f'    Sessie {session_datum} voor {START_DATE} — overslaan')
                continue

            # Split page into per-motie sections
            # Try multiple card boundary patterns used by TK website
            for split_pat in [
                r'(?=class="js-clickable[^"]*")',
                r'(?=class="search-result)',
                r'(?=<article)',
                r'(?=<li[^>]*kamerstuk)',
            ]:
                cards = re.split(split_pat, detail)
                if len(cards) > 2:
                    break
            
            # Fallback: split on every occurrence of the motie link pattern
            if len(cards) <= 2:
                # Split directly before each href containing a zaak ID
                cards = re.split(r'(?=href="[^"]*[?&]id=\d{4}Z)', detail)

            found_besluit = 0
            found_moties = 0

            for card in cards:
                id_m = re.search(r'[?&]id=(\d{4}Z\w+)', card)
                if not id_m:
                    continue
                zaak_id = id_m.group(1)
                found_moties += 1

                # Strip tags and search full card for Besluit
                card_text = re.sub(r'<[^>]+>', ' ', card)
                bm = re.search(r'Besluit:\s*(Aangenomen|Verworpen|Aangehouden)', card_text, re.IGNORECASE)
                besluit = bm.group(1).lower() if bm else None
                if besluit:
                    found_besluit += 1

                # Extract vote score e.g. "(75-74)" from Besluit line
                score_m = re.search(r'Besluit:[^(]*(\(\d+-\d+\))', card_text, re.IGNORECASE)
                score = score_m.group(1) if score_m else None

                if zaak_id not in stemmingen:
                    stemmingen[zaak_id] = {'datum': session_datum, 'besluit': besluit, 'score': score}
                else:
                    if besluit and not stemmingen[zaak_id].get('besluit'):
                        stemmingen[zaak_id]['besluit'] = besluit
                    if score and not stemmingen[zaak_id].get('score'):
                        stemmingen[zaak_id]['score'] = score

            print(f'    {session_datum}: {found_moties} moties, {found_besluit} besluit')
            time.sleep(0.5)

        # Stop when oldest session on this page is before START_DATE
        if oldest_on_page and oldest_on_page < START_DATE:
            print(f'  Oudste sessie: {oldest_on_page} — stoppen')
            break

        time.sleep(1)

    voted = sum(1 for v in stemmingen.values() if v.get('besluit'))
    print(f'  Stemmingen totaal: {len(stemmingen)} moties, {voted} met besluit')
    return stemmingen


# ── Motie detail page for real date ──

def fetch_motie_datum(url):
    if not url.startswith('http'):
        url = 'https://www.tweedekamer.nl' + url
    html = fetch_html(url)
    if not html:
        return None
    # Try multiple date patterns on the detail page
    for pattern in [
        r'Datum[:\s]+(\d{1,2}\s+\w+\s+20\d{2})',
        r'Voorgesteld\s+(\d{1,2}\s+\w+\s+20\d{2})',
        r'(\d{1,2}\s+(?:januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s+20\d{2})',
    ]:
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            d = parse_dutch_date(m.group(1))
            if d and d >= START_DATE:
                return d
    return None

def fetch_motie_title(url):
    """Fetch the real title from a motie detail page <title> tag."""
    if not url.startswith('http'):
        url = 'https://www.tweedekamer.nl' + url
    html = fetch_html(url)
    if not html:
        return None
    # Try <title> tag first — format: "Real Title | Tweede Kamer..."
    m = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
    if m:
        t = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        t = t.split('|')[0].strip()  # strip "| Tweede Kamer der Staten-Generaal"
        if t and len(t) > 10 and t.lower() not in ('motie','moties'):
            return t
    # Try h1
    m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.IGNORECASE | re.DOTALL)
    if m:
        t = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        t = re.sub(r'\s+', ' ', t)
        if t and len(t) > 10:
            return t
    return None

def fetch_stemmen(url):
    """Fetch per-party vote breakdown from motie detail page."""
    if not url.startswith('http'):
        url = 'https://www.tweedekamer.nl' + url
    html = fetch_html(url)
    if not html:
        return {}
    # Parse HTML table rows: <tr><td>PVV</td><td>37</td><td>Tegen</td></tr>
    stemmen = {}
    for tr in re.findall(r'<tr\b[^>]*>(.*?)</tr>', html, re.IGNORECASE | re.DOTALL):
        cells = re.findall(r'<td\b[^>]*>(.*?)</td>', tr, re.IGNORECASE | re.DOTALL)
        if len(cells) >= 3:
            party = re.sub(r'<[^>]+>', '', cells[0]).strip()
            vote_raw = re.sub(r'<[^>]+>', '', cells[2]).strip()
            vote_match = re.match(r'(Voor|Tegen|Niet deelgenomen|Onthouden)', vote_raw, re.IGNORECASE)
            if party and vote_match and party.lower() not in ('fracties', 'fractie'):
                stemmen[party] = vote_match.group(1).lower().replace('niet deelgenomen', 'afwezig')
    return stemmen


def fetch_stemmen_odata(zaak_nummer):
    """Fetch per-party votes: reuse fetch_zaak_besluit to get BesluitId, then get Stemming."""
    PARTY_NORM = {
        'GroenLinks-PvdA': 'GL-PvdA', 'ChristenUnie': 'CU',
        'Groep Markuszower': 'Gr.Markuszower', 'Lid Keijzer': 'Groep-Keijzer', 'FVD': 'FvD',
        'Partij voor de Dieren': 'PvdD', 'Socialistische Partij': 'SP',
        'Volkspartij voor Vrijheid en Democratie': 'VVD',
        u'Democraten 66': 'D66', u'Christen-Democratisch App\u00e8l': 'CDA',
        'Partij voor de Vrijheid': 'PVV', 'Nieuw Sociaal Contract': 'NSC',
        'BoerBurgerBeweging': 'BBB', 'Forum voor Democratie': 'FvD',
        'Staatkundig Gereformeerde Partij': 'SGP',
    }
    VOTE_NORM = {'voor': 'voor', 'tegen': 'tegen', 'niet deelgenomen': 'afwezig'}
    BASE = 'https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0/'
    HDR = {**HEADERS, 'Accept': 'application/json'}
    try:
        # Get BesluitId from Zaak expand
        _, besluit_id = fetch_zaak_besluit(zaak_nummer)
        if not besluit_id:
            return {}
        time.sleep(0.2)
        # Get Stemming records for this Besluit
        url = (BASE + 'Stemming?$filter=' + urllib.parse.quote(f"BesluitId eq {besluit_id}")
               + '&$select=Soort,ActorNaam,ActorFractie&$top=50')
        req = urllib.request.Request(url, headers=HDR)
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode())
        stemmen = {}
        for item in data.get('value', []):
            naam = (item.get('ActorFractie') or item.get('ActorNaam') or '').strip()
            naam = PARTY_NORM.get(naam, naam)
            soort = (item.get('Soort') or '').lower()
            vote = VOTE_NORM.get(soort, soort)
            if naam and vote and naam not in stemmen:
                stemmen[naam] = vote
        return stemmen
    except Exception as e:
        try:
            body = e.read().decode()[:300]
            print(f'    OData stemmen fout ({zaak_nummer}): {e} | {body}')
        except:
            print(f'    OData stemmen fout ({zaak_nummer}): {e}')
        return {}

def fetch_zaak_besluit(zaak_nummer):
    """Fetch besluit via Zaak?$expand=Besluit. BesluitTekst contains aangenomen/verworpen."""
    BASE = 'https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0/'
    HDR = {**HEADERS, 'Accept': 'application/json'}
    try:
        # Get Zaak with expanded Besluit in one call
        url = (BASE + 'Zaak?$filter=' + urllib.parse.quote(f"Nummer eq '{zaak_nummer}'")
               + '&$expand=Besluit($select=Id,BesluitTekst,StemmingsSoort)'
               + '&$select=Id,Nummer&$top=1')
        req = urllib.request.Request(url, headers=HDR)
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode())
        items = data.get('value', [])
        if not items:
            return None, None
        besluiten = items[0].get('Besluit', [])
        if not besluiten:
            return None, None
        b = besluiten[0]
        tekst = (b.get('BesluitTekst') or '').lower()
        besluit_id = b.get('Id', '')
        if 'aangenomen' in tekst:
            return 'aangenomen', besluit_id
        elif 'verworpen' in tekst:
            return 'verworpen', besluit_id
        elif 'aangehouden' in tekst:
            return 'aangehouden', besluit_id
        return None, besluit_id
    except Exception as e:
        try:
            body = e.read().decode()[:300]
            print(f'    OData besluit fout ({zaak_nummer}): {e} | {body}')
        except:
            print(f'    OData besluit fout ({zaak_nummer}): {e}')
        return None, None


def fetch_agenda():
    """Fetch plenaire agenda from TK OData API."""
    today = date.today().isoformat()
    future = (date.today() + __import__('datetime').timedelta(days=21)).isoformat()
    # Filter on date range only — no Soort filter (value may differ)
    filter_str = f"Datum ge {today} and Datum le {future} and Verwijderd eq false"
    url = (
        "https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0/Activiteit"
        "?$filter=" + urllib.parse.quote(filter_str)
        + "&$orderby=" + urllib.parse.quote("Datum asc,Aanvangstijd asc")
        + "&$select=Id,Nummer,Onderwerp,Datum,Aanvangstijd,Locatie,Soort"
        + "&$top=60"
    )
    try:
        req = urllib.request.Request(url, headers={**HEADERS, 'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode('utf-8'))
        items = data.get('value', [])
        PLENAIR_SOORTEN = {
            'Plenair debat (debat)', 'Plenair debat (wetgeving)',
            'Plenair debat (tweeminutendebat)', 'Plenair debat (overig)',
            'Stemmingen', 'Hamerstukken', 'Regeling van werkzaamheden'
        }
        plenair = [a for a in items if a.get('Soort','') in PLENAIR_SOORTEN]
        if not plenair:
            plenair = items
        agenda = []
        for a in plenair:
            datum = (a.get('Datum') or '')[:10]
            nummer = a.get('Nummer','')
            item_id = a.get('Id','')
            # Per TK Open Data docs: URL uses Nummer field
            if nummer:
                tk_url = f"https://www.tweedekamer.nl/debat_en_vergadering/plenaire_vergaderingen/details/activiteit?id={nummer}"
            else:
                tk_url = "https://www.tweedekamer.nl/debat_en_vergadering/plenaire_vergaderingen"
            agenda.append({
                'datum':   datum,
                'tijd':    (a.get('Aanvangstijd') or '')[:5],
                'titel':   a.get('Onderwerp') or a.get('Nummer') or 'Vergadering',
                'locatie': a.get('Locatie') or 'Plenaire zaal',
                'soort':   a.get('Soort') or 'Plenair',
                'url':     tk_url,
            })
        print(f'  Agenda: {len(agenda)} activiteiten geladen')
        return agenda
    except Exception as e:
        print(f'  Agenda ophalen mislukt: {e}')
        return []


# ── Moties list scrape ──

def fetch_page(page=0):
    url = (
        'https://www.tweedekamer.nl/kamerstukken/moties'
        '?qry=%2A&fld_tk_categorie=Kamerstukken&fld_prl_kamerstuk=Moties'
        f'&srt=date%3Adesc%3Adate&page={page}'
    )
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read().decode('utf-8', errors='replace')
        return raw
    except Exception as e:
        print(f'  Fout pagina {page+1}: {e}')
        return ''

def parse_moties_from_html(raw):
    seen_links = {}  # link -> best title found so far
    seen_dates = {}  # link -> date
    raw = html_module.unescape(raw)
    for m in re.finditer(r'<a\b[^>]*href="(/kamerstukken/moties/detail\?[^"]+)"[^>]*>(.*?)</a>', raw, re.DOTALL):
        link = 'https://www.tweedekamer.nl' + m.group(1).replace('&amp;', '&')
        title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        title = re.sub(r'\s+', ' ', title)
        # Clean up garbled titles like "Motie : Motie van het lid X"
        title = re.sub(r'^[Mm]otie\s*:\s*', '', title).strip()
        # Skip nav/breadcrumb links — real titles are long and contain 'motie'
        if not title or len(title) < 15 or 'motie' not in title.lower():
            continue
        # Skip if still garbled (contains colon-separated duplicate)
        if '\n' in title:
            continue
        # Keep the longest title for this link (breadcrumb = short, real title = long)
        if link not in seen_links or len(title) > len(seen_links[link]):
            seen_links[link] = title
            # Date from context
            start = max(0, m.start() - 300)
            ctx = raw[start:m.start()]
            date_m = re.search(
                r'(\d{1,2})\s+(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s+(20\d{2})',
                ctx, re.IGNORECASE
            )
            if date_m:
                mo = MONTHS.get(date_m.group(2).lower(), 0)
                seen_dates[link] = f"{date_m.group(3)}-{mo:02d}-{int(date_m.group(1)):02d}" if mo else ''
            else:
                seen_dates[link] = ''
    return [{'titel': seen_links[l], 'list_date': seen_dates.get(l,''), 'link': l} for l in seen_links]

# ── Main ──

def main():
    print(f'Moties ophalen — {TODAY}')

    try:
        with open(DATA_FILE, encoding='utf-8') as f:
            existing = json.load(f)
    except FileNotFoundError:
        existing = []

    # Purge any existing moties before START_DATE (cleanup from previous bad runs)
    before = len(existing)
    existing = [m for m in existing if m.get('datum','') >= START_DATE]
    if len(existing) < before:
        print(f'Gezuiverd: {before - len(existing)} moties voor {START_DATE} verwijderd')

    existing_links   = {x.get('tk_url','') for x in existing}
    existing_by_zaak = {
        extract_zaak_id(x.get('tk_url','')): x
        for x in existing
        if extract_zaak_id(x.get('tk_url',''))
    }

    print(f'Bestaande moties: {len(existing)}')

    # Load live Kamerleden
    print('Kamerleden ophalen...')
    live_leden = fetch_leden_partij()
    if live_leden:
        LEDEN_PARTIJ.update(live_leden)

    scraped_count = sum(1 for x in existing if str(x.get('id','')).startswith('tk'))
    is_backfill   = scraped_count == 0
    max_pages     = 50 if is_backfill else 30
    print(f'Mode: {"backfill" if is_backfill else "daily"} (max {max_pages} paginas)')

    # ── Step 1: Stemmingsuitslagen ──
    print('\nStemmingsuitslagen ophalen...')
    stemmingen = scrape_stemmingen()

    # Apply to existing moties
    updated_vote = 0
    matched = 0
    for zaak_id, stemming in stemmingen.items():
        m = existing_by_zaak.get(zaak_id)
        if not m:
            continue
        matched += 1
        changed = False
        if stemming.get('datum') and m.get('datum','') in ('', TODAY):
            m['datum'] = stemming['datum']
            changed = True
        if stemming.get('besluit') and m.get('status','') not in ('aangenomen','verworpen','aangehouden'):
            m['status'] = stemming['besluit']
            m['archief'] = False
            m.pop('stemmen_na', None)  # reset so party votes get fetched
            changed = True
        # Store vote score e.g. "(75-74)"
        if stemming.get('score') and not m.get('score'):
            m['score'] = stemming['score']
            changed = True
        # tk_url: /kamerstukken/moties/detail is correct — don't overwrite
        if changed:
            updated_vote += 1
    print(f'  {updated_vote} bestaande moties bijgewerkt met stemresultaat ({matched}/{len(stemmingen)} stemmingen gematcht)')
    # ── Step 1a: fetch moties that were voted but not yet in our list ──
    unmatched_stemmingen = [zid for zid in stemmingen if zid not in existing_by_zaak]
    if unmatched_stemmingen:
        print(f'  Ongematchte stemmingen ({len(unmatched_stemmingen)}): ophalen...')
        added_from_stemming = 0
        for zaak_id in unmatched_stemmingen[:80]:
            link = f'https://www.tweedekamer.nl/kamerstukken/moties/detail?id={zaak_id}'
            if link in existing_links:
                continue
            item_id = make_id(link)
            if item_id in seen_ids:
                continue
            real_date, real_title = fetch_motie_detail(link)
            time.sleep(0.4)
            if not real_title:
                continue
            if not real_date:
                real_date = stemmingen[zaak_id].get('datum') or TODAY
            if real_date < START_DATE:
                continue
            status = stemmingen[zaak_id].get('besluit') or 'in_behandeling'
            thema    = detect_thema(real_title)
            indiener = detect_indiener(real_title)
            new_m = {
                'id': item_id, 'titel': real_title, 'indiener': indiener,
                'datum': real_date, 'thema': thema, 'status': status,
                'alignment': detect_alignment(real_title, indiener),
                'vergadering': '', 'tk_url': link, 'toelichting': '',
                'stemmen': {}, 'archief': False,
            }
            if stemmingen[zaak_id].get('score'):
                new_m['score'] = stemmingen[zaak_id]['score']
            existing.append(new_m)
            existing_by_zaak[zaak_id] = new_m
            existing_links.add(link)
            seen_ids.add(item_id)
            added_from_stemming += 1
        print(f'  {added_from_stemming} nieuwe moties toegevoegd vanuit stemmingen')
        # Rebuild existing_by_zaak after additions
        existing_by_zaak = {
            extract_zaak_id(x.get('tk_url', '')): x
            for x in existing
            if extract_zaak_id(x.get('tk_url', ''))
        }

    # ── Step 1b: Fix moties still in_behandeling but actually in stemmingen dict ──
    fixed_besluit = 0
    for m in existing:
        if m.get('status') != 'in_behandeling':
            continue
        zaak_id = extract_zaak_id(m.get('tk_url', ''))
        if not zaak_id:
            continue
        stemming = stemmingen.get(zaak_id)
        if stemming and stemming.get('besluit'):
            m['status'] = stemming['besluit']
            m['archief'] = False
            m.pop('stemmen_na', None)
            if stemming.get('datum') and m.get('datum', '') in ('', TODAY):
                m['datum'] = stemming['datum']
            if stemming.get('score') and not m.get('score'):
                m['score'] = stemming['score']
            fixed_besluit += 1
    if fixed_besluit:
        print(f'  {fixed_besluit} in_behandeling moties bijgewerkt via stemmingen dict')

    # Reset stemmen_na for moties that were voted but still have no party breakdown
    # (stemmen_na was set when title was broken; now title is correct, retry)
    reset_count = 0
    for m in existing:
        if m.get('stemmen_na') and not m.get('stemmen') and m.get('status') in ('aangenomen','verworpen'):
            m.pop('stemmen_na', None)
            reset_count += 1
    if reset_count:
        print(f'  stemmen_na gereset voor {reset_count} moties (leeg stemmen, wel status)')

    # Fetch per-party votes for voted moties that don't have them yet (max 50 per run)
    needs_stemmen = [
        m for m in existing
        if m.get('status') in ('aangenomen', 'verworpen')
        and not m.get('stemmen')
        and not m.get('stemmen_na')
        and m.get('tk_url')
    ]
    if needs_stemmen:
        print(f'  Partijstemmen ophalen: {len(needs_stemmen)} moties')
        fetched_stemmen = 0
        for m in needs_stemmen[:60]:
            stemmen = {}
            # HTML scrape of stemmingsuitslag detail page (most reliable)
            if m.get('tk_url'):
                stemmen = fetch_stemmen(m['tk_url'])
                time.sleep(0.4)
            if stemmen:
                m['stemmen'] = stemmen
                fetched_stemmen += 1
            else:
                # No votes found — likely handopsteken
                m['stemmen_na'] = True
        print(f'    {fetched_stemmen} moties partijstemmen opgehaald')

    # ── Step 2: Scrape new moties ──
    new_items = []
    seen_ids = {x['id'] for x in existing if 'id' in x}
    seen_zaak_ids = {extract_zaak_id(x.get('tk_url','')) for x in existing if extract_zaak_id(x.get('tk_url',''))}
    consecutive_empty = 0

    for page in range(max_pages):
        raw = fetch_page(page)
        if not raw:
            print(f'  Pagina {page+1}: fetch mislukt (leeg)')
            break

        results = parse_moties_from_html(raw)
        if not results:
            import re as _re
            classes = _re.findall(r'class="([^"]{10,60})"', raw)
            motie_classes = [c for c in classes if any(x in c.lower() for x in ['result','item','search','motie','card','list'])]
            print(f'  Pagina {page+1}: geen moties gevonden (HTML len={len(raw)})')
            print(f'  Relevante classes: {list(set(motie_classes))[:10]}')
            break
        print(f'  Pagina {page+1}: {len(results)} moties')
        if page == 0:
            for r in results:
                print(f'    - {extract_zaak_id(r["link"])} | {r["titel"][:60]}')

        found_new_on_page = False
        for r in results:
            link    = r['link']
            zaak_id = extract_zaak_id(link)
            item_id = make_id(link)

            # Match on zaak_id (robust) or full link or item_id
            # If existing entry has a broken title, update it instead of skipping
            def _is_broken(t):
                t = (t or '').strip()
                tl = t.lower()
                if not t or len(tl) < 10: return True
                if tl in ('moties','motie'): return True
                if '\n' in t: return True  # garbled multiline title
                if tl.startswith('motie\n') or tl.startswith('motie :\n'): return True
                if 'indiener' not in tl and 'lid' not in tl and 'leden' not in tl and len(tl) < 30: return True
                return False

            if item_id in seen_ids:
                ex = next((x for x in existing if x.get('id') == item_id), None)
                if ex and _is_broken(ex.get('titel','')):
                    real = fetch_motie_title(link)
                    time.sleep(0.3)
                    if real:
                        ex['titel']     = real
                        ex['indiener']  = detect_indiener(real)
                        ex['thema']     = detect_thema(real)
                        ex['alignment'] = detect_alignment(real, ex['indiener'])
                        print(f'    FIX titel: {zaak_id} → {real[:60]}')
                    else:
                        print(f'    FIX failed: {zaak_id}')
                elif page == 0:
                    print(f'    SKIP item_id: {zaak_id}')
                continue
            if zaak_id and zaak_id in seen_zaak_ids:
                ex = next((x for x in existing if extract_zaak_id(x.get('tk_url','')) == zaak_id), None)
                if ex and _is_broken(ex.get('titel','')):
                    real = fetch_motie_title(link)
                    time.sleep(0.3)
                    if real:
                        ex['titel']     = real
                        ex['indiener']  = detect_indiener(real)
                        ex['thema']     = detect_thema(real)
                        ex['alignment'] = detect_alignment(real, ex['indiener'])
                        print(f'    FIX titel (zaak): {zaak_id} → {real[:60]}')
                    else:
                        print(f'    FIX failed: {zaak_id}')
                elif page == 0:
                    print(f'    SKIP zaak_id: {zaak_id}')
                continue
            if link in existing_links:
                if page == 0: print(f'    SKIP link: {zaak_id} → {link}')
                continue
            if zaak_id and zaak_id in existing_by_zaak:
                matched_m = existing_by_zaak[zaak_id]
                if _is_broken(matched_m.get('titel','')):
                    matched_m['titel']     = r['titel']
                    matched_m['indiener']  = detect_indiener(r['titel'])
                    matched_m['thema']     = detect_thema(r['titel'])
                    matched_m['alignment'] = detect_alignment(r['titel'], matched_m['indiener'])
                    print(f'    FIX titel (by_zaak): {zaak_id} → {r["titel"][:60]}')
                elif page == 0:
                    print(f'    SKIP zaak_id match: {zaak_id} → {matched_m.get("tk_url","?")}')
                continue

            # Get real date
            real_date = None
            status    = 'in_behandeling'

            if zaak_id and zaak_id in stemmingen:
                real_date = stemmingen[zaak_id].get('datum')
                if stemmingen[zaak_id].get('besluit'):
                    status = stemmingen[zaak_id]['besluit']

            if not real_date:
                real_date = fetch_motie_datum(link)
                time.sleep(0.4)

            if not real_date:
                real_date = r['list_date'] or TODAY

            # Hard filter — skip anything clearly before START_DATE
            # If date is uncertain (TODAY), always keep it
            if real_date != TODAY and real_date < START_DATE:
                print(f'    SKIP (datum {real_date} < {START_DATE}): {r["titel"][:60]}')
                continue

            found_new_on_page = True
            seen_ids.add(item_id)
            if zaak_id: seen_zaak_ids.add(zaak_id)
            existing_links.add(link)

            thema    = detect_thema(r['titel'])
            indiener = detect_indiener(r['titel'])

            new_items.append({
                'id':         item_id,
                'titel':      r['titel'],
                'indiener':   indiener,
                'datum':      real_date,
                'thema':      thema,
                'status':     status,
                'alignment':  detect_alignment(r['titel'], indiener),
                'vergadering':'',
                'tk_url':     link,
                'toelichting':'',
                'stemmen':    {},
                'archief':    False,
            })

        if not is_backfill and not found_new_on_page:
            consecutive_empty += 1
            if consecutive_empty >= 5:
                print(f'  Geen nieuwe moties meer — klaar')
                break
        else:
            consecutive_empty = 0

        time.sleep(1.5)

    # ── Step 2b: Fix broken titles (e.g. "Moties" from nav link) ──
    broken_titles = [m for m in existing if m.get('titel','').strip().lower() in ('moties','motie','')]
    if broken_titles:
        print(f'\n  Kapotte titels herstellen: {len(broken_titles)} moties')
        for m in broken_titles[:50]:
            if not m.get('tk_url'): continue
            real = fetch_motie_datum(m['tk_url'])  # reuse fetch, we'll extract title separately
            html_raw = fetch_html(m['tk_url'])
            if html_raw:
                t = re.search(r'<h1[^>]*>(.*?)</h1>', html_raw, re.DOTALL)
                if t:
                    title = re.sub(r'<[^>]+>','',t.group(1)).strip()
                    if title and len(title) > 10:
                        m['titel'] = title
                        m['indiener'] = detect_indiener(title)
                        m['thema'] = detect_thema(title)
            time.sleep(0.4)

    # ── Step 3: Fix dates still showing TODAY ──
    needs_date = [m for m in existing if m.get('datum','') >= TODAY and m.get('tk_url','')]
    if needs_date:
        print(f'\nDatum fixup: {min(150, len(needs_date))} van {len(needs_date)} moties')
        for m in needs_date[:150]:
            zaak_id = extract_zaak_id(m.get('tk_url',''))
            if zaak_id and stemmingen.get(zaak_id, {}).get('datum'):
                m['datum'] = stemmingen[zaak_id]['datum']
                continue
            nd = fetch_motie_datum(m['tk_url'])
            if nd:
                m['datum'] = nd if nd >= START_DATE else START_DATE
            time.sleep(0.3)

    print(f'\nNieuwe moties: {len(new_items)}')
    for m in new_items[:5]:
        print(f'  + {m["datum"]} | {m["status"]:15} | {m["titel"][:60]}')

    # ── Step 4: Archive logic ──
    # aangenomen/verworpen → always front page (archief=False)
    # in_behandeling       → In Process tab after 5 days
    # aangehouden          → In Process tab after 30 days
    all_moties = existing + new_items
    for m in all_moties:
        status = m.get('status', '')
        if status in ('aangenomen', 'verworpen'):
            m['archief'] = False
            continue
        try:
            age = (date.today() - date.fromisoformat(m.get('datum', TODAY))).days
        except Exception:
            age = 0
        if status == 'in_behandeling':
            m['archief'] = age > 5
        elif status == 'aangehouden':
            m['archief'] = age > 30

    active = sum(1 for m in all_moties if not m.get('archief'))
    voted  = sum(1 for m in all_moties if m.get('status') in ('aangenomen','verworpen'))
    print(f'Totaal: {len(all_moties)} moties ({active} actief, {voted} gestemd)')

    # Fetch and save agenda
    print('\nAgenda ophalen...')
    agenda = fetch_agenda()
    with open('agenda.json', 'w', encoding='utf-8') as f:
        json.dump(agenda, f, ensure_ascii=False, indent=2)

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_moties, f, ensure_ascii=False, indent=2)
    print('Opgeslagen.')

if __name__ == '__main__':
    main()
