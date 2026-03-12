#!/usr/bin/env python3
"""fetch_moties.py — haalt moties op en verrijkt met datum + stemmen in één run.
   Tweede Kamer samenstelling: verkiezingen 29 oktober 2025, geïnstalleerd 12 november 2025.
   Kabinet-Jetten I: D66 + VVD + CDA
"""
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
HDR_JSON = {**HEADERS, 'Accept': 'application/json'}

MONTHS = {
    'januari':1,'februari':2,'maart':3,'april':4,'mei':5,'juni':6,
    'juli':7,'augustus':8,'september':9,'oktober':10,'november':11,'december':12
}

# Kabinet-Jetten I: D66, VVD, CDA
COALITIE  = {"D66", "VVD", "CDA"}
OPPOSITIE = {"PVV", "GL-PvdA", "JA21", "FvD", "Gr.Markuszower", "BBB", "SP",
             "PvdD", "CU", "SGP", "Volt", "DENK", "50PLUS", "Groep-Keijzer"}

# Tweede Kamer per 12 maart 2026 (verkiezingen 29 okt 2025, geïnstalleerd 12 nov 2025)
# Bron: parlement.com/de-huidige-tweede-kamer
# Primaire bron: live scrape via fetch_leden_partij(). Dit is fallback.
LEDEN_PARTIJ = {
    # ── D66 (26) ──
    "Van Asten":"D66", "Robert van Asten":"D66",
    "Bamenga":"D66", "Mpanzu Bamenga":"D66",
    "Belhirch":"D66", "Fatimazhra Belhirch":"D66",
    "Biekman":"D66", "Anouschka Biekman":"D66",
    "Heera Dijk":"D66",
    "El Boujdaini":"D66", "Sarah El Boujdaini":"D66",
    "Huidekooper":"D66", "Dion Huidekooper":"D66",
    "Huizenga":"D66", "Renilde Huizenga":"D66",
    "Jagtenberg":"D66", "Michelle Jagtenberg":"D66",
    "Klos":"D66", "Felix Klos":"D66",
    "Köse":"D66", "Kose":"D66", "Ulaş Köse":"D66",
    "Van Leijen":"D66", "Robin van Leijen":"D66",
    "Mathlouti":"D66", "Mahjoub Mathlouti":"D66",
    "Neijenhuis":"D66", "Stephan Neijenhuis":"D66",
    "Oosterhuis":"D66", "Henk-Jan Oosterhuis":"D66",
    "Oualhadj":"D66", "Ouafa Oualhadj":"D66",
    "Paternotte":"D66", "Jan Paternotte":"D66",
    "Paulusma":"D66", "Wieke Paulusma":"D66",
    "Podt":"D66", "Anne-Marijke Podt":"D66",
    "Rooderkerk":"D66", "Ilana Rooderkerk":"D66",
    "Schoonis":"D66", "Jan Schoonis":"D66",
    "Sneller":"D66", "Joost Sneller":"D66",
    "Synhaeve":"D66", "Marijke Synhaeve":"D66",
    "Vellinga-Beemsterboer":"D66", "Marieke Vellinga-Beemsterboer":"D66",
    "Vervuurt":"D66", "Marc Vervuurt":"D66",
    "Van der Werf":"D66", "Hanneke van der Werf":"D66",

    # ── VVD (22) ──
    "Becker":"VVD", "Bente Becker":"VVD",
    "De Beer":"VVD", "Martin de Beer":"VVD",
    "Bevers":"VVD", "Harry Bevers":"VVD",
    "Bikkers":"VVD", "Bart Bikkers":"VVD",
    "Brekelmans":"VVD", "Ruben Brekelmans":"VVD",
    "Van Campen":"VVD", "Thom van Campen":"VVD",
    "Van Eijk":"VVD", "Wendy van Eijk":"VVD",
    "Ellian":"VVD", "Ulysse Ellian":"VVD",
    "De Groot":"VVD", "Peter de Groot":"VVD",
    "Den Hollander":"VVD", "Renate den Hollander":"VVD",
    "Kisteman":"VVD", "Arend Kisteman":"VVD",
    "De Kort":"VVD", "Daan de Kort":"VVD",
    "Van der Maas":"VVD", "Erik van der Maas":"VVD",
    "Maes":"VVD", "Nicole Maes":"VVD",
    "Martens":"VVD", "Claire Martens":"VVD",
    "Meulenkamp":"VVD", "Wim Meulenkamp":"VVD",
    "Michon-Derkzen":"VVD", "Ingrid Michon-Derkzen":"VVD",
    "Müller":"VVD", "Alisha Müller":"VVD",
    "Nobel":"VVD", "Jurgen Nobel":"VVD",
    "Rajkowski":"VVD", "Queeny Rajkowski":"VVD",
    "Schutz":"VVD", "Björn Schutz":"VVD",
    "Wendel":"VVD", "Hilde Wendel":"VVD",

    # ── GL-PvdA (20) ──
    "Abdi":"GL-PvdA", "Fatihya Abdi":"GL-PvdA",
    "Bromet":"GL-PvdA", "Laura Bromet":"GL-PvdA",
    "Bushoff":"GL-PvdA", "Julian Bushoff":"GL-PvdA",
    "De Hoop":"GL-PvdA", "Habtamu de Hoop":"GL-PvdA",
    "Kathmann":"GL-PvdA", "Barbara Kathmann":"GL-PvdA",
    "Klaver":"GL-PvdA", "Jesse Klaver":"GL-PvdA",
    "Kröger":"GL-PvdA", "Suzanne Kröger":"GL-PvdA",
    "Lahlah":"GL-PvdA", "Esmah Lahlah":"GL-PvdA",
    "Van der Lee":"GL-PvdA", "Tom van der Lee":"GL-PvdA",
    "Mohandis":"GL-PvdA", "Mohammed Mohandis":"GL-PvdA",
    "Moorman":"GL-PvdA", "Marjolein Moorman":"GL-PvdA",
    "Mutluer":"GL-PvdA", "Songül Mutluer":"GL-PvdA",
    "Van Oosterhout":"GL-PvdA", "Sjoukje van Oosterhout":"GL-PvdA",
    "Patijn":"GL-PvdA", "Mariëtte Patijn":"GL-PvdA",
    "Piri":"GL-PvdA", "Kati Piri":"GL-PvdA",
    "Stultiens":"GL-PvdA", "Luc Stultiens":"GL-PvdA",
    "Tseggai":"GL-PvdA", "Mikal Tseggai":"GL-PvdA",
    "Vliegenthart":"GL-PvdA", "Lisa Vliegenthart":"GL-PvdA",
    "Westerveld":"GL-PvdA", "Lisa Westerveld":"GL-PvdA",
    "Zalinyan":"GL-PvdA", "Ani Zalinyan":"GL-PvdA",

    # ── PVV (19) ──
    "Wilders":"PVV", "Geert Wilders":"PVV",
    "Boon":"PVV", "Maikel Boon":"PVV",
    "Bosma":"PVV", "Martin Bosma":"PVV",
    "Van Dijck":"PVV", "Tony van Dijck":"PVV",
    "Emiel van Dijk":"PVV",
    "Faber-van de Klashorst":"PVV", "Marjolein Faber":"PVV",
    "Graus":"PVV", "Dion Graus":"PVV",
    "Jansen":"PVV", "Chris Jansen":"PVV",
    "Kops":"PVV", "Alexander Kops":"PVV",
    "Maeijer":"PVV", "Vicky Maeijer":"PVV",
    "Van Meetelen":"PVV", "Rachel van Meetelen":"PVV",
    "Mooiman":"PVV", "Jeremy Mooiman":"PVV",
    "Mulder":"PVV", "Edgar Mulder":"PVV",
    "Prickaertz":"PVV", "Erwin Prickaertz":"PVV",
    "Raijer":"PVV", "Annette Raijer":"PVV",
    "De Roon":"PVV", "Raymond de Roon":"PVV",
    "Stöteler":"PVV", "Sebastiaan Stöteler":"PVV",
    "Vlottes":"PVV", "Elmar Vlottes":"PVV",
    "Vondeling":"PVV", "Marina Vondeling":"PVV",

    # ── CDA (18) ──
    "Van Ark":"CDA", "Elles van Ark":"CDA",
    "Armut":"CDA", "Etkin Armut":"CDA",
    "Boelsma-Hoekstra":"CDA", "Luciënne Boelsma-Hoekstra":"CDA",
    "Bontenbal":"CDA", "Henri Bontenbal":"CDA",
    "Van den Brink":"CDA", "Tijs van den Brink":"CDA",
    "Bühler":"CDA", "Judith Bühler":"CDA",
    "Inge van Dijk":"CDA",
    "Hamstra":"CDA", "Sarath Hamstra":"CDA",
    "Jumelet":"CDA", "Henk Jumelet":"CDA",
    "Koorevaar":"CDA", "Jan Arie Koorevaar":"CDA",
    "Krul":"CDA", "Harmen Krul":"CDA",
    "Van Lanschot":"CDA", "Maes van Lanschot":"CDA",
    "Lohman":"CDA", "Joris Lohman":"CDA",
    "Poortman":"CDA", "André Poortman":"CDA",
    "Steen":"CDA", "Hanneke Steen":"CDA",
    "Straatman":"CDA", "Jeltje Straatman":"CDA",
    "Tijmstra":"CDA", "Eveline Tijmstra":"CDA",
    "Zwinkels":"CDA", "Jantine Zwinkels":"CDA",

    # ── JA21 (9) ──
    "Van den Berg":"JA21", "Daniël van den Berg":"JA21",
    "Boomsma":"JA21", "Diederik Boomsma":"JA21",
    "Ceulemans":"JA21", "Simon Ceulemans":"JA21",
    "Clemminck-Croci":"JA21", "Ranjith Clemminck-Croci":"JA21",
    "Coenradie":"JA21", "Ingrid Coenradie":"JA21",
    "Eerdmans":"JA21", "Joost Eerdmans":"JA21",
    "Goudzwaard":"JA21", "Maarten Goudzwaard":"JA21",
    "Hoogeveen":"JA21", "Michiel Hoogeveen":"JA21",
    "Nanninga":"JA21", "Annabel Nanninga":"JA21",

    # ── FvD (7) ──
    "Dekker":"FvD", "Ralf Dekker":"FvD",
    "Van Duijvenvoorde":"FvD", "Peter van Duijvenvoorde":"FvD",
    "Van Houwelingen":"FvD", "Pepijn van Houwelingen":"FvD",
    "Freek Jansen":"FvD",
    "Van Meijeren":"FvD", "Gideon van Meijeren":"FvD",
    "Russcher":"FvD", "Tom Russcher":"FvD",
    "De Vos":"FvD", "Lidewij de Vos":"FvD",

    # ── Groep Markuszower (7) ──
    "Markuszower":"Gr.Markuszower", "Gidi Markuszower":"Gr.Markuszower",
    "Claassen":"Gr.Markuszower", "René Claassen":"Gr.Markuszower",
    "Heutink":"Gr.Markuszower", "Hidde Heutink":"Gr.Markuszower",
    "Ten Hove":"Gr.Markuszower", "Tamara ten Hove":"Gr.Markuszower",
    "Lammers":"Gr.Markuszower", "Annelotte Lammers":"Gr.Markuszower",
    "Moinat":"Gr.Markuszower", "Nicole Moinat":"Gr.Markuszower",
    "Schilder":"Gr.Markuszower", "Shanna Schilder":"Gr.Markuszower",

    # ── BBB (3) ──
    "Van der Plas":"BBB", "Caroline van der Plas":"BBB",
    "Vermeer":"BBB", "Henk Vermeer":"BBB",
    "Wiersma":"BBB", "Femke Wiersma":"BBB",

    # ── ChristenUnie (3) ──
    "Bikker":"CU", "Mirjam Bikker":"CU",
    "Ceder":"CU", "Don Ceder":"CU",
    "Grinwis":"CU", "Chris Grinwis":"CU",

    # ── DENK (3) ──
    "El Abassi":"DENK", "Ismail el Abassi":"DENK",
    "Ergin":"DENK", "Stephan Ergin":"DENK",
    "Van Baarle":"DENK", "Stephan van Baarle":"DENK",
    "Kırcalı":"DENK", "Kircali":"DENK",

    # ── PvdD (3) ──
    "Teunissen":"PvdD", "Christine Teunissen":"PvdD",
    "Vestering":"PvdD", "Leonie Vestering":"PvdD",
    "Van Raan":"PvdD", "Lammert van Raan":"PvdD",

    # ── SGP (3) ──
    "Diederik van Dijk":"SGP",
    "Stoffer":"SGP", "Chris Stoffer":"SGP",
    "Flach":"SGP", "Bert-Jan Flach":"SGP",

    # ── SP (3) ──
    "Jimmy Dijk":"SP",
    "Dobbe":"SP", "Judith Dobbe":"SP",
    "Beckerman":"SP", "Sandra Beckerman":"SP",

    # ── 50PLUS (2) ──
    "Baay-Timmerman":"50PLUS", "Liane Baay-Timmerman":"50PLUS",

    # ── Groep Keijzer (1) ──
    "Keijzer":"Groep-Keijzer", "Mona Keijzer":"Groep-Keijzer",

    # ── Volt (1) ──
    "Dassen":"Volt", "Laurens Dassen":"Volt",
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
    "Buitenlandse Zaken":["europa","oekra","buitenland","sanctie","diplomatie","israel","gaza","ukraine","iran","hormuz"],
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
    for p in ["PVV","VVD","D66","GL-PvdA","CDA","JA21","FvD","Gr.Markuszower",
              "BBB","SP","PvdD","CU","SGP","Volt","DENK","50PLUS","Groep-Keijzer"]:
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
    m = re.search(r'[?&]id=(\d{4}Z\w+)', url_or_str)
    return m.group(1) if m else None

# ── Live Kamerleden scrape ──

def fetch_leden_partij():
    PARTY_NORM = {
        "GroenLinks-PvdA":"GL-PvdA", "ChristenUnie":"CU",
        "Groep Markuszower":"Gr.Markuszower", "Lid Keijzer":"Groep-Keijzer", "FVD":"FvD",
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
            session_datum = None
            footer_m = re.search(r'fromdate=(20\d{2}-\d{2}-\d{2})', detail)
            if footer_m:
                session_datum = footer_m.group(1)

            if not session_datum:
                detail_text = re.sub(r'<[^>]+>', ' ', detail)
                pv_m = re.search(
                    r'Plenaire\s+vergadering\s+(\d{1,2}\s+\w+\s+20\d{2})',
                    detail_text, re.IGNORECASE
                )
                if pv_m:
                    session_datum = parse_dutch_date(pv_m.group(1))

            if not session_datum:
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

            if oldest_on_page is None or session_datum < oldest_on_page:
                oldest_on_page = session_datum

            if session_datum < START_DATE:
                print(f'    Sessie {session_datum} voor {START_DATE} — overslaan')
                continue

            for split_pat in [
                r'(?=class="js-clickable[^"]*")',
                r'(?=class="search-result)',
                r'(?=<article)',
                r'(?=<li[^>]*kamerstuk)',
            ]:
                cards = re.split(split_pat, detail)
                if len(cards) > 2:
                    break

            if len(cards) <= 2:
                cards = re.split(r'(?=href="[^"]*[?&]id=\d{4}Z)', detail)

            found_besluit = 0
            found_moties = 0

            for card in cards:
                id_m = re.search(r'[?&]id=(\d{4}Z\w+)', card)
                if not id_m:
                    continue
                zaak_id = id_m.group(1)
                found_moties += 1

                card_text = re.sub(r'<[^>]+>', ' ', card)
                bm = re.search(r'Besluit:\s*(Aangenomen|Verworpen|Aangehouden)', card_text, re.IGNORECASE)
                besluit = bm.group(1).lower() if bm else None
                if besluit:
                    found_besluit += 1

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

        if oldest_on_page and oldest_on_page < START_DATE:
            print(f'  Oudste sessie: {oldest_on_page} — stoppen')
            break

        time.sleep(1)

    voted = sum(1 for v in stemmingen.values() if v.get('besluit'))
    print(f'  Stemmingen totaal: {len(stemmingen)} moties, {voted} met besluit')
    return stemmingen


# ── Motie detail: datum + titel in één request ──

def fetch_motie_detail(url):
    """Fetch both date and title from a motie detail page in a single HTTP request."""
    if not url.startswith('http'):
        url = 'https://www.tweedekamer.nl' + url
    html = fetch_html(url)
    if not html:
        return None, None

    # Title: <title> tag, strip site name
    title = None
    m = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
    if m:
        t = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        t = t.split('|')[0].strip()
        if t and len(t) > 10 and t.lower() not in ('motie', 'moties'):
            title = t
    if not title:
        m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.IGNORECASE | re.DOTALL)
        if m:
            t = re.sub(r'<[^>]+>', '', m.group(1)).strip()
            t = re.sub(r'\s+', ' ', t)
            if t and len(t) > 10:
                title = t

    # Date: try multiple patterns
    datum = None
    for pattern in [
        r'Datum[:\s]+(\d{1,2}\s+\w+\s+20\d{2})',
        r'Voorgesteld\s+(\d{1,2}\s+\w+\s+20\d{2})',
        r'(\d{1,2}\s+(?:januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s+20\d{2})',
    ]:
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            d = parse_dutch_date(m.group(1))
            if d and d >= START_DATE:
                datum = d
                break

    return datum, title


# ── OData: besluit + stemmen ──

def fetch_zaak_besluit(zaak_nummer):
    """Fetch besluit status and Besluit_Id via OData Zaak expand."""
    BASE = 'https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0/'
    try:
        url = (BASE + 'Zaak?$filter=' + urllib.parse.quote(f"Nummer eq '{zaak_nummer}'")
               + '&$expand=Besluit($select=Id,BesluitTekst,StemmingsSoort)'
               + '&$select=Id,Nummer&$top=1')
        req = urllib.request.Request(url, headers=HDR_JSON)
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


def fetch_stemmen_odata(zaak_nummer):
    """Fetch per-party vote breakdown via OData using Besluit_Id."""
    PARTY_NORM = {
        'GroenLinks-PvdA': 'GL-PvdA', 'ChristenUnie': 'CU',
        'Groep Markuszower': 'Gr.Markuszower', 'Lid Keijzer': 'Groep-Keijzer', 'FVD': 'FvD',
        'Partij voor de Dieren': 'PvdD', 'Socialistische Partij': 'SP',
        'Volkspartij voor Vrijheid en Democratie': 'VVD',
        'Democraten 66': 'D66', 'Christen-Democratisch Appèl': 'CDA',
        'Partij voor de Vrijheid': 'PVV', 'Nieuw Sociaal Contract': 'NSC',
        'BoerBurgerBeweging': 'BBB', 'Forum voor Democratie': 'FvD',
        'Staatkundig Gereformeerde Partij': 'SGP',
    }
    VOTE_NORM = {'voor': 'voor', 'tegen': 'tegen', 'niet deelgenomen': 'afwezig'}
    BASE = 'https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0/'

    try:
        # Single call: get besluit_id from zaak
        _, besluit_id = fetch_zaak_besluit(zaak_nummer)
        if not besluit_id:
            return {}
        time.sleep(0.2)

        # FIX: correct property name is Besluit_Id (with underscore)
        url = (BASE + 'Stemming?$filter=' + urllib.parse.quote(f"Besluit_Id eq '{besluit_id}'")
               + '&$select=Soort,ActorNaam,ActorFractie&$top=200')
        req = urllib.request.Request(url, headers=HDR_JSON)
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


def fetch_agenda():
    """Fetch plenaire agenda from TK OData API."""
    today = date.today().isoformat()
    future = (date.today() + __import__('datetime').timedelta(days=21)).isoformat()
    filter_str = f"Datum ge {today} and Datum le {future} and Verwijderd eq false"
    url = (
        "https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0/Activiteit"
        "?$filter=" + urllib.parse.quote(filter_str)
        + "&$orderby=" + urllib.parse.quote("Datum asc,Aanvangstijd asc")
        + "&$select=Id,Nummer,Onderwerp,Datum,Aanvangstijd,Locatie,Soort"
        + "&$top=60"
    )
    try:
        req = urllib.request.Request(url, headers=HDR_JSON)
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode('utf-8'))
        items = data.get('value', [])
        PLENAIR_SOORTEN = {
            'Plenair debat (debat)', 'Plenair debat (wetgeving)',
            'Plenair debat (tweeminutendebat)', 'Plenair debat (overig)',
            'Stemmingen', 'Hamerstukken', 'Regeling van werkzaamheden'
        }
        plenair = [a for a in items if a.get('Soort', '') in PLENAIR_SOORTEN]
        if not plenair:
            plenair = items
        agenda = []
        for a in plenair:
            datum = (a.get('Datum') or '')[:10]
            nummer = a.get('Nummer', '')
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
    seen_links = {}
    seen_dates = {}
    raw = html_module.unescape(raw)
    for m in re.finditer(r'<a\b[^>]*href="(/kamerstukken/moties/detail\?[^"]+)"[^>]*>(.*?)</a>', raw, re.DOTALL):
        link = 'https://www.tweedekamer.nl' + m.group(1).replace('&amp;', '&')
        title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        title = re.sub(r'\s+', ' ', title)
        title = re.sub(r'^[Mm]otie\s*:\s*', '', title).strip()
        if not title or len(title) < 15 or 'motie' not in title.lower():
            continue
        if '\n' in title:
            continue
        if link not in seen_links or len(title) > len(seen_links[link]):
            seen_links[link] = title
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
    return [{'titel': seen_links[l], 'list_date': seen_dates.get(l, ''), 'link': l} for l in seen_links]


# ── Main ──

def main():
    print(f'Moties ophalen — {TODAY}')

    try:
        with open(DATA_FILE, encoding='utf-8') as f:
            existing = json.load(f)
    except FileNotFoundError:
        existing = []

    before = len(existing)
    existing = [m for m in existing if m.get('datum', '') >= START_DATE]
    if len(existing) < before:
        print(f'Gezuiverd: {before - len(existing)} moties voor {START_DATE} verwijderd')

    existing_links   = {x.get('tk_url', '') for x in existing}
    existing_by_zaak = {
        extract_zaak_id(x.get('tk_url', '')): x
        for x in existing
        if extract_zaak_id(x.get('tk_url', ''))
    }

    print(f'Bestaande moties: {len(existing)}')

    print('Kamerleden ophalen...')
    live_leden = fetch_leden_partij()
    if live_leden:
        LEDEN_PARTIJ.update(live_leden)

    scraped_count = sum(1 for x in existing if str(x.get('id', '')).startswith('tk'))
    is_backfill   = scraped_count == 0
    max_pages     = 50 if is_backfill else 30
    print(f'Mode: {"backfill" if is_backfill else "daily"} (max {max_pages} paginas)')

    # ── Step 1: Stemmingsuitslagen ──
    print('\nStemmingsuitslagen ophalen...')
    stemmingen = scrape_stemmingen()

    updated_vote = 0
    matched = 0
    for zaak_id, stemming in stemmingen.items():
        m = existing_by_zaak.get(zaak_id)
        if not m:
            continue
        matched += 1
        changed = False
        if stemming.get('datum') and m.get('datum', '') in ('', TODAY):
            m['datum'] = stemming['datum']
            changed = True
        if stemming.get('besluit') and m.get('status', '') not in ('aangenomen', 'verworpen', 'aangehouden'):
            m['status'] = stemming['besluit']
            m['archief'] = False
            m.pop('stemmen_na', None)
            changed = True
        if stemming.get('score') and not m.get('score'):
            m['score'] = stemming['score']
            changed = True
        if changed:
            updated_vote += 1

    print(f'  {updated_vote} bestaande moties bijgewerkt met stemresultaat ({matched}/{len(stemmingen)} stemmingen gematcht)')

    unmatched_stemmingen = [zid for zid in stemmingen if zid not in existing_by_zaak]
    if unmatched_stemmingen:
        print(f'  Ongematchte stemmingen ({len(unmatched_stemmingen)}): {unmatched_stemmingen[:10]}')

    needs_votes = [m for m in existing if m.get('status') in ('aangenomen', 'verworpen') and not m.get('stemmen') and not m.get('stemmen_na')]
    if needs_votes:
        print(f'  Moties gestemd maar zonder stemmen-breakdown ({len(needs_votes)}): {[extract_zaak_id(m.get("tk_url", "")) for m in needs_votes[:5]]}')

    # ── Step 1b: OData besluit check for in_behandeling ──
    in_behandeling_old = [
        m for m in existing
        if m.get('status') == 'in_behandeling'
        and m.get('datum', '') <= TODAY
        and m.get('tk_url')
    ]
    if in_behandeling_old:
        print(f'  OData besluit check: {min(30, len(in_behandeling_old))} moties in behandeling')
        fixed_besluit = 0
        for m in in_behandeling_old[:30]:
            zaak_id = extract_zaak_id(m.get('tk_url', ''))
            if not zaak_id:
                continue
            besluit, _ = fetch_zaak_besluit(zaak_id)
            if besluit:
                m['status'] = besluit
                m['archief'] = False
                m.pop('stemmen_na', None)
                fixed_besluit += 1
            time.sleep(0.3)
        if fixed_besluit:
            print(f'    {fixed_besluit} moties status bijgewerkt via OData')

    # Reset stemmen_na for voted moties with empty stemmen
    reset_count = 0
    for m in existing:
        if m.get('stemmen_na') and not m.get('stemmen') and m.get('status') in ('aangenomen', 'verworpen'):
            m.pop('stemmen_na', None)
            reset_count += 1
    if reset_count:
        print(f'  stemmen_na gereset voor {reset_count} moties')

    # Fetch per-party votes for voted moties without breakdown
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
            zaak_id = extract_zaak_id(m.get('tk_url', ''))
            stemmen = {}
            if zaak_id:
                stemmen = fetch_stemmen_odata(zaak_id)
                time.sleep(0.3)
            if stemmen:
                m['stemmen'] = stemmen
                fetched_stemmen += 1
            else:
                m['stemmen_na'] = True
        print(f'    {fetched_stemmen} moties partijstemmen opgehaald')

    # ── Step 2: Scrape new moties ──
    new_items = []
    seen_ids = {x['id'] for x in existing if 'id' in x}
    seen_zaak_ids = {extract_zaak_id(x.get('tk_url', '')) for x in existing if extract_zaak_id(x.get('tk_url', ''))}
    consecutive_empty = 0

    for page in range(max_pages):
        raw = fetch_page(page)
        if not raw:
            print(f'  Pagina {page+1}: fetch mislukt (leeg)')
            break

        results = parse_moties_from_html(raw)
        if not results:
            print(f'  Pagina {page+1}: geen moties gevonden (HTML len={len(raw)})')
            break
        print(f'  Pagina {page+1}: {len(results)} moties')
        if page == 0:
            for r in results:
                print(f'    - {extract_zaak_id(r["link"])} | {r["titel"][:60]}')

        found_new_on_page = False

        def _is_broken(t):
            t = (t or '').strip()
            tl = t.lower()
            if not t or len(tl) < 10: return True
            if tl in ('moties', 'motie'): return True
            if '\n' in t: return True
            if 'indiener' not in tl and 'lid' not in tl and 'leden' not in tl and len(tl) < 30: return True
            return False

        for r in results:
            link    = r['link']
            zaak_id = extract_zaak_id(link)
            item_id = make_id(link)

            if item_id in seen_ids:
                ex = next((x for x in existing if x.get('id') == item_id), None)
                if ex and _is_broken(ex.get('titel', '')):
                    _, real = fetch_motie_detail(link)
                    time.sleep(0.3)
                    if real:
                        ex['titel']     = real
                        ex['indiener']  = detect_indiener(real)
                        ex['thema']     = detect_thema(real)
                        ex['alignment'] = detect_alignment(real, ex['indiener'])
                        print(f'    FIX titel: {zaak_id} → {real[:60]}')
                continue

            if zaak_id and zaak_id in seen_zaak_ids:
                ex = next((x for x in existing if extract_zaak_id(x.get('tk_url', '')) == zaak_id), None)
                if ex and _is_broken(ex.get('titel', '')):
                    _, real = fetch_motie_detail(link)
                    time.sleep(0.3)
                    if real:
                        ex['titel']     = real
                        ex['indiener']  = detect_indiener(real)
                        ex['thema']     = detect_thema(real)
                        ex['alignment'] = detect_alignment(real, ex['indiener'])
                        print(f'    FIX titel (zaak): {zaak_id} → {real[:60]}')
                continue

            if link in existing_links:
                continue

            if zaak_id and zaak_id in existing_by_zaak:
                matched_m = existing_by_zaak[zaak_id]
                if _is_broken(matched_m.get('titel', '')):
                    matched_m['titel']     = r['titel']
                    matched_m['indiener']  = detect_indiener(r['titel'])
                    matched_m['thema']     = detect_thema(r['titel'])
                    matched_m['alignment'] = detect_alignment(r['titel'], matched_m['indiener'])
                continue

            # Get real date and title in one request
            real_date = None
            real_title = None
            status = 'in_behandeling'

            if zaak_id and zaak_id in stemmingen:
                real_date = stemmingen[zaak_id].get('datum')
                if stemmingen[zaak_id].get('besluit'):
                    status = stemmingen[zaak_id]['besluit']

            if not real_date or _is_broken(r['titel']):
                fetched_date, fetched_title = fetch_motie_detail(link)
                time.sleep(0.4)
                if not real_date:
                    real_date = fetched_date
                if fetched_title:
                    real_title = fetched_title

            if not real_date:
                real_date = r['list_date'] or TODAY

            if real_date != TODAY and real_date < START_DATE:
                print(f'    SKIP (datum {real_date} < {START_DATE}): {r["titel"][:60]}')
                continue

            titel = real_title or r['titel']
            found_new_on_page = True
            seen_ids.add(item_id)
            if zaak_id: seen_zaak_ids.add(zaak_id)
            existing_links.add(link)

            thema    = detect_thema(titel)
            indiener = detect_indiener(titel)

            new_items.append({
                'id':         item_id,
                'titel':      titel,
                'indiener':   indiener,
                'datum':      real_date,
                'thema':      thema,
                'status':     status,
                'alignment':  detect_alignment(titel, indiener),
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

    # ── Step 3: Fix dates still showing TODAY ──
    needs_date = [m for m in existing if m.get('datum', '') >= TODAY and m.get('tk_url', '')]
    if needs_date:
        print(f'\nDatum fixup: {min(150, len(needs_date))} van {len(needs_date)} moties')
        for m in needs_date[:150]:
            zaak_id = extract_zaak_id(m.get('tk_url', ''))
            if zaak_id and stemmingen.get(zaak_id, {}).get('datum'):
                m['datum'] = stemmingen[zaak_id]['datum']
                continue
            nd, _ = fetch_motie_detail(m['tk_url'])
            if nd:
                m['datum'] = nd if nd >= START_DATE else START_DATE
            time.sleep(0.3)

    print(f'\nNieuwe moties: {len(new_items)}')
    for m in new_items[:5]:
        print(f'  + {m["datum"]} | {m["status"]:15} | {m["titel"][:60]}')

    # ── Step 4: Archive logic ──
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
    voted  = sum(1 for m in all_moties if m.get('status') in ('aangenomen', 'verworpen'))
    print(f'Totaal: {len(all_moties)} moties ({active} actief, {voted} gestemd)')

    print('\nAgenda ophalen...')
    agenda = fetch_agenda()
    with open('agenda.json', 'w', encoding='utf-8') as f:
        json.dump(agenda, f, ensure_ascii=False, indent=2)

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_moties, f, ensure_ascii=False, indent=2)
    print('Opgeslagen.')

if __name__ == '__main__':
    main()
