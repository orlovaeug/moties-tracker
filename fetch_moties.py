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
    # D66 (26) — largest party, elected Oct 2025
    "Van Asten": "D66", "Bamenga": "D66", "Belhirch": "D66", "Biekman": "D66",
    "Heera Dijk": "D66", "El Boujdaini": "D66", "Huidekooper": "D66", "Huizenga": "D66",
    "Jagtenberg": "D66", "Klos": "D66", "Köse": "D66", "Kose": "D66",
    "Van Leijen": "D66", "Mathlouti": "D66", "Neijenhuis": "D66", "Oosterhuis": "D66",
    "Oualhadj": "D66", "Paternotte": "D66", "Paulusma": "D66", "Podt": "D66",
    "Rooderkerk": "D66", "Schoonis": "D66", "Sneller": "D66", "Synhaeve": "D66",
    "Vellinga-Beemsterboer": "D66", "Vervuurt": "D66", "Van der Werf": "D66",
    "Jetten": "D66", "Van Weyenberg": "D66", "Van Lanschot": "D66",
    "Hammelburg": "D66", "Ten Hove": "D66",
    # VVD (22)
    "Becker": "VVD", "Martin de Beer": "VVD", "Bevers": "VVD", "Bikkers": "VVD",
    "Brekelmans": "VVD", "Van Campen": "VVD", "Van Eijk": "VVD", "Ellian": "VVD",
    "Peter de Groot": "VVD", "Den Hollander": "VVD", "Kisteman": "VVD",
    "De Kort": "VVD", "Van der Maas": "VVD", "Maes": "VVD", "Martens": "VVD",
    "Meulenkamp": "VVD", "Michon-Derkzen": "VVD", "Müller": "VVD", "Muller": "VVD",
    "Nobel": "VVD", "Rajkowski": "VVD", "Schutz": "VVD", "Wendel": "VVD",
    "Yesilgöz": "VVD", "Yesilgoz": "VVD", "Hermans": "VVD",
    # GL-PvdA (20)
    "Abdi": "GL-PvdA", "Bromet": "GL-PvdA", "Bushoff": "GL-PvdA",
    "De Hoop": "GL-PvdA", "Kathmann": "GL-PvdA", "Klaver": "GL-PvdA",
    "Kröger": "GL-PvdA", "Kroger": "GL-PvdA", "Lahlah": "GL-PvdA",
    "Van der Lee": "GL-PvdA", "Mohandis": "GL-PvdA", "Moorman": "GL-PvdA",
    "Mutluer": "GL-PvdA", "Van Oosterhout": "GL-PvdA", "Patijn": "GL-PvdA",
    "Piri": "GL-PvdA", "Stultiens": "GL-PvdA", "Tseggai": "GL-PvdA",
    "Vliegenthart": "GL-PvdA", "Westerveld": "GL-PvdA", "Zalinyan": "GL-PvdA",
    "Nijboer": "GL-PvdA",
    # PVV (19)
    "Boon": "PVV", "Bosma": "PVV", "Van Dijck": "PVV", "Emiel van Dijk": "PVV",
    "Faber": "PVV", "Graus": "PVV", "Chris Jansen": "PVV", "Kops": "PVV",
    "Maeijer": "PVV", "Van Meetelen": "PVV", "Mooiman": "PVV", "Mulder": "PVV",
    "Prickaertz": "PVV", "Raijer": "PVV", "De Roon": "PVV", "Stöteler": "PVV",
    "Soteler": "PVV", "Vlottes": "PVV", "Vondeling": "PVV", "Wilders": "PVV",
    # CDA (18)
    "Van Ark": "CDA", "Armut": "CDA", "Boelsma-Hoekstra": "CDA", "Bontenbal": "CDA",
    "Van den Brink": "CDA", "Bühler": "CDA", "Buhler": "CDA", "Inge van Dijk": "CDA",
    "Hamstra": "CDA", "Jumelet": "CDA", "Koorevaar": "CDA", "Krul": "CDA",
    "Maes van Lanschot": "CDA", "Lohman": "CDA", "Poortman": "CDA",
    "Steen": "CDA", "Straatman": "CDA", "Tijmstra": "CDA", "Zwinkels": "CDA",
    "Amhaouch": "CDA",
    # JA21 (9)
    "Van den Berg": "JA21", "Boomsma": "JA21", "Ceulemans": "JA21",
    "Clemminck-Croci": "JA21", "Coenradie": "JA21", "Eerdmans": "JA21",
    "Goudzwaard": "JA21", "Hoogeveen": "JA21", "Nanninga": "JA21",
    # FvD (7)
    "Dekker": "FvD", "Van Duijvenvoorde": "FvD", "Van Houwelingen": "FvD",
    "Freek Jansen": "FvD", "Van Meijeren": "FvD", "Russcher": "FvD", "De Vos": "FvD",
    # Gr.Markuszower (7)
    "Claassen": "Gr.Markuszower", "Heutink": "Gr.Markuszower",
    "Ten Hove": "Gr.Markuszower", "Lammers": "Gr.Markuszower",
    "Markuszower": "Gr.Markuszower", "Moinat": "Gr.Markuszower",
    "Schilder": "Gr.Markuszower",
    # BBB (3)
    "Van der Plas": "BBB", "Vermeer": "BBB", "Wiersma": "BBB",
    # CU (3)
    "Bikker": "CU", "Ceder": "CU", "Grinwis": "CU", "Segers": "CU",
    # DENK (3)
    "El Abassi": "DENK", "Stephan van Baarle": "DENK", "Ergin": "DENK", "Azarkan": "DENK", "Van Baarle": "DENK",
    # PvdD (3)
    "Kostić": "PvdD", "Kostic": "PvdD", "Ouwehand": "PvdD", "Teunissen": "PvdD",
    "Wassenberg": "PvdD",
    # SGP (3)
    "Diederik van Dijk": "SGP", "Flach": "SGP", "Stoffer": "SGP", "Van der Staaij": "SGP",
    # SP (3)
    "Beckerman": "SP", "Jimmy Dijk": "SP", "Dobbe": "SP", "Leijten": "SP",
    # 50PLUS (2)
    "Van Brenk": "50PLUS", "Struijs": "50PLUS",
    # Groep-Keijzer (1)
    "Keijzer": "Groep-Keijzer",
    # Volt (1)
    "Dassen": "Volt",
    # NSC (2 remaining after coalition changes)
    "Omtzigt": "NSC", "Nicolaï": "NSC",
}


COALITIE = {"D66", "VVD", "CDA", "BBB", "NSC"}
OPPOSITIE = {"GL-PvdA", "PVV", "SP", "PvdD", "CU", "SGP", "Volt", "DENK", "FvD", "JA21", "50PLUS", "Gr.Markuszower"}

# Keywords that suggest a motie conflicts with the coalition agreement
STRIJDIG_KEYWORDS = [
    "niet verhogen", "van tafel", "terugtrekken", "intrekken", "afwijzen", "verwerpen",
    "geen bezuinig", "stop", "verbod", "moratorium", "schrap", "afschaffen",
    "niet korten", "niet verlagen", "geen korting", "geen verlaging",
    "geen uitzetting", "niet uitzetten", "niet deporteren",
    "geen samenwerking met", "distantieert", "veroordeelt kabinet",
    "onverantwoord", "onacceptabel", "onaanvaardbaar",
]

# Keywords that suggest a motie aligns with the coalition agreement
CONFORM_KEYWORDS = [
    "conform akkoord", "uitvoering geven", "verzoekt de regering te",
    "zo snel mogelijk", "versterken", "uitbreiden", "verhogen",
    "meer investeren", "extra middelen", "extra budget",
    "wettelijk vastleggen", "invoeren", "oprichten", "realiseren",
    "nationaal programma", "taskforce", "actieplan",
]

# Akkoord thema's — moties over deze onderwerpen zijn eerder conform
AKKOORD_THEMAS = {
    "Defensie": "conform",           # 3.5% bbp — kernpunt
    "Wonen & Bouwen": "conform",     # 100k woningen/jaar
    "Klimaat & Energie": "neutraal", # kernenergie ja, maar ook veel oppositie
    "Asiel & Migratie": "conform",   # strengere asielwet — coalitiestandpunt
    "Financien": "neutraal",
    "Economie & Ondernemen": "conform",
}

def detect_alignment(titel, indiener, thema):
    titel_lower = titel.lower()

    # 1. Explicit keywords override everything
    for kw in STRIJDIG_KEYWORDS:
        if kw in titel_lower:
            return "strijdig"
    for kw in CONFORM_KEYWORDS:
        if kw in titel_lower:
            return "conform"

    # 2. If submitted by coalition party → likely conform
    if indiener in COALITIE:
        return AKKOORD_THEMAS.get(thema, "conform")

    # 3. If submitted by opposition → likely strijdig or neutraal
    if indiener in OPPOSITIE:
        # Some opposition moties are still adopted (procedural, broad support)
        return "neutraal"

    return "neutraal"

def detect_thema(text):
    t = text.lower()
    best, best_score = "Overig", 0
    for thema, kws in THEMA_KEYWORDS.items():
        score = sum(1 for k in kws if k in t)
        if score > best_score:
            best, best_score = thema, score
    return best

def detect_indiener(titel):
    m = re.search(r'(?:Gewijzigde\s+)?[Mm]otie\s+van\s+(?:het\s+lid|de\s+leden)\s+([A-Z][a-zA-Z\u00C0-\u017E\-]+(?:\s+[a-zA-Z\u00C0-\u017E\-]+){0,4}?)(?:\s+c\.s\.|\s+over\s|\s+en\s+[A-Z]|\s+-\s+[A-Z]|$)', titel)
    name_ctx = m.group(1).strip() if m else titel
    for naam in sorted(LEDEN_PARTIJ.keys(), key=len, reverse=True):
        pat = r'(?<![A-Za-z\u00C0-\u017E])' + re.escape(naam) + r'(?![A-Za-z\u00C0-\u017E])'
        if re.search(pat, name_ctx, re.IGNORECASE):
            return LEDEN_PARTIJ[naam]
    for p in ["PVV","VVD","NSC","BBB","D66","GL-PvdA","CDA","SP","PvdD","CU","SGP",
              "Volt","DENK","FvD","JA21","50PLUS","Gr.Markuszower"]:
        if p in titel:
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

FRACTIE_MAP = {
    'VVD': 'VVD', 'D66': 'D66', 'GL-PvdA': 'GL-PvdA', 'GroenLinks-PvdA': 'GL-PvdA',
    'PVV': 'PVV', 'CDA': 'CDA', 'SP': 'SP', 'PvdD': 'PvdD',
    'ChristenUnie': 'CU', 'CU': 'CU', 'SGP': 'SGP', 'Volt': 'Volt',
    'DENK': 'DENK', 'FvD': 'FvD', 'JA21': 'JA21', 'BBB': 'BBB',
    '50PLUS': '50PLUS', 'NSC': 'NSC',
    'Markuszower': 'Gr.Markuszower', 'Groep Markuszower': 'Gr.Markuszower',
    'Groep-Keijzer': 'Groep-Keijzer',
}
STEM_MAP = {'Voor': 'voor', 'Tegen': 'tegen', 'Onthouden': 'onthouden'}


def extract_doc_ids(url):
    """Extract document IDs from a TK motie URL (both id= and did= params)."""
    ids = re.findall(r'[?&](?:id|did)=([A-Za-z0-9]+)', url or '')
    return list(dict.fromkeys(ids))  # deduplicated, order preserved


def fetch_odata(path, params):
    """Fetch JSON from TK OData API with proper URL encoding."""
    import urllib.parse
    url = 'https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0' + path + '?' + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    try:
        req = urllib.request.Request(url, headers={'Accept': 'application/json', 'User-Agent': 'MotieTracker/1.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'    OData fout: {e}')
        return None


def fetch_detail_status(url):
    """Use TK OData API to get real date, status and per-party stemmen."""
    ids = extract_doc_ids(url)
    if not ids:
        return 'in_behandeling', None, {}

    FRACTIE_MAP = {
        'VVD':'VVD','D66':'D66','GL-PvdA':'GL-PvdA','GroenLinks-PvdA':'GL-PvdA',
        'PVV':'PVV','CDA':'CDA','SP':'SP','PvdD':'PvdD','ChristenUnie':'CU','CU':'CU',
        'SGP':'SGP','Volt':'Volt','DENK':'DENK','FvD':'FvD','JA21':'JA21','BBB':'BBB',
        '50PLUS':'50PLUS','NSC':'NSC','Markuszower':'Gr.Markuszower',
        'Groep Markuszower':'Gr.Markuszower','Groep-Keijzer':'Groep-Keijzer',
    }
    STEM_MAP = {'Voor':'voor','Tegen':'tegen','Onthouden':'onthouden'}

    best_datum = None
    best_stemmen = {}
    best_status = 'in_behandeling'

    for doc_id in ids:
        # 1. Get real document date
        doc_data = fetch_odata('/Document', {
            '$filter': f"Id eq '{doc_id}'",
            '$select': 'Id,Datum'
        })
        if doc_data and doc_data.get('value'):
            raw = doc_data['value'][0].get('Datum','')
            if raw and not best_datum:
                best_datum = raw[:10]

        # 2. Get stemming via Zaak
        for filt in [
            f"Zaak/Documenten/any(d:d/Id eq '{doc_id}')",
            f"Besluit/Zaak/Documenten/any(d:d/Id eq '{doc_id}')",
        ]:
            data = fetch_odata('/Stemming', {
                '$filter': filt,
                '$expand': 'Fractie($select=Afkorting)',
                '$select': 'Soort,ActorFractie',
            })
            if not data or not data.get('value'):
                continue
            stemmen = {}
            voor = tegen = 0
            for item in data['value']:
                soort = item.get('Soort','')
                stem = STEM_MAP.get(soort, soort.lower() if soort else '')
                naam = (item.get('Fractie') or {}).get('Afkorting') or item.get('ActorFractie','')
                naam = FRACTIE_MAP.get(naam, naam)
                if naam and stem:
                    stemmen[naam] = stem
                if stem == 'voor': voor += 1
                elif stem == 'tegen': tegen += 1
            if stemmen:
                best_stemmen = stemmen
                best_status = 'aangenomen' if voor >= tegen else 'verworpen'
                break
        if best_stemmen:
            break

    return best_status, best_datum, best_stemmen


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

    # On first run (no scraped moties yet), fetch up to 50 pages to backfill since START_DATE
    # On daily runs (existing scraped moties), just check recent pages
    scraped_count = sum(1 for x in existing if str(x.get('id','')).startswith('tk'))
    max_pages = 50 if scraped_count == 0 else 5
    print(f'  Mode: {"backfill" if scraped_count == 0 else "daily"} (max {max_pages} paginas)')
    for page in range(max_pages):
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
            indiener = detect_indiener(r['titel'])

            # Use OData API to get real date, status and stemmen
            detail_status, detail_datum, detail_stemmen = fetch_detail_status(r['link'])
            time.sleep(0.3)
            motie_datum = detail_datum or r['datum']

            new_items.append({
                'id': item_id,
                'titel': r['titel'],
                'indiener': indiener,
                'datum': motie_datum,
                'thema': thema,
                'status': detail_status,
                'alignment': detect_alignment(r['titel'], indiener, thema),
                'vergadering': '',
                'tk_url': r['link'],
                'toelichting': '',
                'stemmen': detail_stemmen
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

    # Archive logic:
    # - aangenomen/verworpen: always active permanently (unarchive if needed)
    # - in_behandeling older than 7 days -> archief
    # - aangehouden older than 60 days -> archief
    from datetime import date
    today = date.today()
    archived = 0
    unarchived = 0
    for m in all_items:
        status = m.get('status', 'in_behandeling')
        # Voted moties always stay active — unarchive if they were previously archived
        if status in ('aangenomen', 'verworpen'):
            if m.get('archief'):
                m['archief'] = False
                unarchived += 1
            continue
        # Already archived and not voted — leave it
        if m.get('archief'):
            continue
        try:
            motie_date = date.fromisoformat(m.get('datum', str(today)))
            days_old = (today - motie_date).days
        except:
            continue
        if status == 'in_behandeling' and days_old > 7:
            m['archief'] = True
            archived += 1
        elif status == 'aangehouden' and days_old > 60:
            m['archief'] = True
            archived += 1
    if unarchived:
        print(f'  {unarchived} moties teruggehaald uit archief (gestemd)')

    if archived:
        print(f'  {archived} moties gearchiveerd')

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)
    print(f'Klaar — totaal {len(all_items)} moties in moties.json ({sum(1 for m in all_items if not m.get("archief"))} actief)')

if __name__ == '__main__':
    main()
