#!/usr/bin/env python3
"""
fix_indieners.py — corrigeert indieners, alignment en status in moties.json
Draait dagelijks in GitHub Actions na fetch_moties.py
"""
import json, re, urllib.request, html as html_module, time
from datetime import date

# ── Constanten ────────────────────────────────────────────────────────────────

LEDEN_PARTIJ = {
    # D66
    "Van Asten": "D66", "Bamenga": "D66", "Belhirch": "D66", "Biekman": "D66",
    "Heera Dijk": "D66", "El Boujdaini": "D66", "Huidekooper": "D66", "Huizenga": "D66",
    "Jagtenberg": "D66", "Klos": "D66", "Köse": "D66", "Kose": "D66",
    "Van Leijen": "D66", "Mathlouti": "D66", "Neijenhuis": "D66", "Oosterhuis": "D66",
    "Oualhadj": "D66", "Paternotte": "D66", "Paulusma": "D66", "Podt": "D66",
    "Rooderkerk": "D66", "Schoonis": "D66", "Sneller": "D66", "Synhaeve": "D66",
    "Vellinga-Beemsterboer": "D66", "Vervuurt": "D66", "Van der Werf": "D66",
    "Jetten": "D66", "Van Weyenberg": "D66", "Van Lanschot": "D66",
    "Hammelburg": "D66",
    # VVD
    "Becker": "VVD", "Martin de Beer": "VVD", "Bevers": "VVD", "Bikkers": "VVD",
    "Brekelmans": "VVD", "Van Campen": "VVD", "Van Eijk": "VVD", "Ellian": "VVD",
    "Peter de Groot": "VVD", "Den Hollander": "VVD", "Kisteman": "VVD",
    "De Kort": "VVD", "Van der Maas": "VVD", "Maes": "VVD", "Martens": "VVD",
    "Meulenkamp": "VVD", "Michon-Derkzen": "VVD", "Müller": "VVD", "Muller": "VVD",
    "Nobel": "VVD", "Rajkowski": "VVD", "Schutz": "VVD", "Wendel": "VVD",
    "Yesilgöz": "VVD", "Yesilgoz": "VVD", "Hermans": "VVD",
    # GL-PvdA
    "Abdi": "GL-PvdA", "Bromet": "GL-PvdA", "Bushoff": "GL-PvdA",
    "De Hoop": "GL-PvdA", "Kathmann": "GL-PvdA", "Klaver": "GL-PvdA",
    "Kröger": "GL-PvdA", "Kroger": "GL-PvdA", "Lahlah": "GL-PvdA",
    "Van der Lee": "GL-PvdA", "Mohandis": "GL-PvdA", "Moorman": "GL-PvdA",
    "Mutluer": "GL-PvdA", "Van Oosterhout": "GL-PvdA", "Patijn": "GL-PvdA",
    "Piri": "GL-PvdA", "Stultiens": "GL-PvdA", "Tseggai": "GL-PvdA",
    "Vliegenthart": "GL-PvdA", "Westerveld": "GL-PvdA", "Zalinyan": "GL-PvdA",
    "Nijboer": "GL-PvdA",
    # PVV
    "Boon": "PVV", "Bosma": "PVV", "Van Dijck": "PVV", "Emiel van Dijk": "PVV",
    "Faber": "PVV", "Graus": "PVV", "Chris Jansen": "PVV", "Kops": "PVV",
    "Maeijer": "PVV", "Van Meetelen": "PVV", "Mooiman": "PVV", "Mulder": "PVV",
    "Prickaertz": "PVV", "Raijer": "PVV", "De Roon": "PVV", "Stöteler": "PVV",
    "Soteler": "PVV", "Vlottes": "PVV", "Vondeling": "PVV", "Wilders": "PVV",
    # CDA
    "Van Ark": "CDA", "Armut": "CDA", "Boelsma-Hoekstra": "CDA", "Bontenbal": "CDA",
    "Van den Brink": "CDA", "Bühler": "CDA", "Buhler": "CDA", "Inge van Dijk": "CDA",
    "Hamstra": "CDA", "Jumelet": "CDA", "Koorevaar": "CDA", "Krul": "CDA",
    "Maes van Lanschot": "CDA", "Lohman": "CDA", "Poortman": "CDA",
    "Steen": "CDA", "Straatman": "CDA", "Tijmstra": "CDA", "Zwinkels": "CDA",
    "Amhaouch": "CDA",
    # JA21
    "Van den Berg": "JA21", "Boomsma": "JA21", "Ceulemans": "JA21",
    "Clemminck-Croci": "JA21", "Coenradie": "JA21", "Eerdmans": "JA21",
    "Goudzwaard": "JA21", "Hoogeveen": "JA21", "Nanninga": "JA21",
    # FvD
    "Dekker": "FvD", "Van Duijvenvoorde": "FvD", "Van Houwelingen": "FvD",
    "Freek Jansen": "FvD", "Van Meijeren": "FvD", "Russcher": "FvD", "De Vos": "FvD",
    # Gr.Markuszower
    "Claassen": "Gr.Markuszower", "Heutink": "Gr.Markuszower",
    "Ten Hove": "Gr.Markuszower", "Lammers": "Gr.Markuszower",
    "Markuszower": "Gr.Markuszower", "Moinat": "Gr.Markuszower",
    "Schilder": "Gr.Markuszower",
    # BBB
    "Van der Plas": "BBB", "Vermeer": "BBB", "Wiersma": "BBB",
    # CU
    "Bikker": "CU", "Ceder": "CU", "Grinwis": "CU", "Segers": "CU",
    # DENK
    "El Abassi": "DENK", "Stephan van Baarle": "DENK", "Van Baarle": "DENK",
    "Ergin": "DENK", "Azarkan": "DENK",
    # PvdD
    "Kostić": "PvdD", "Kostic": "PvdD", "Ouwehand": "PvdD",
    "Teunissen": "PvdD", "Wassenberg": "PvdD",
    # SGP
    "Diederik van Dijk": "SGP", "Flach": "SGP", "Stoffer": "SGP", "Van der Staaij": "SGP",
    # SP
    "Beckerman": "SP", "Jimmy Dijk": "SP", "Dobbe": "SP", "Leijten": "SP",
    # 50PLUS
    "Van Brenk": "50PLUS", "Struijs": "50PLUS",
    # Groep-Keijzer
    "Keijzer": "Groep-Keijzer",
    # Volt
    "Dassen": "Volt",
    # NSC
    "Omtzigt": "NSC", "Nicolaï": "NSC",
}

COALITIE = {"D66", "VVD", "CDA", "BBB", "NSC"}

STRIJDIG_KEYWORDS = [
    "niet verhogen", "van tafel", "terugtrekken", "geen bezuinig", "verbod op", "schrap",
    "afschaffen", "niet korten", "niet verlagen", "stop met", "verzet zich", "verwerpt",
    "intrekken", "geen steun", "tegen het kabinet", "wantrouwen",
]

CONFORM_KEYWORDS = [
    "conform akkoord", "uitvoering geven", "wettelijk vastleggen", "invoeren", "oprichten",
    "vaststellen", "uitwerken", "realiseren", "uitvoeren", "verankeren",
]

AKKOORD_THEMAS = {
    "Defensie": "conform", "Wonen & Bouwen": "conform", "Klimaat & Energie": "conform",
    "Asiel & Migratie": "conform", "Financien": "conform", "Bereikbaarheid & Mobiliteit": "conform",
    "Landbouw & Natuur": "conform", "Democratie & Rechtsstaat": "neutraal",
    "Bestaanszekerheid": "neutraal",
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; MotieTracker/1.0)',
    'Accept': 'text/html',
    'Accept-Language': 'nl-NL,nl;q=0.9',
}

# ── Functies ──────────────────────────────────────────────────────────────────

def detect_indiener(titel):
    m = re.search(
        r'(?:Gewijzigde\s+)?[Mm]otie\s+van\s+(?:het\s+lid|de\s+leden)\s+'
        r'([A-Z][a-zA-Z\u00C0-\u017E\-]+(?:\s+[a-zA-Z\u00C0-\u017E\-]+){0,4}?)'
        r'(?:\s+c\.s\.|\s+over\s|\s+en\s+[A-Z]|\s+-\s+[A-Z]|$)',
        titel
    )
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


def detect_alignment(titel, indiener, thema):
    t = titel.lower()
    for kw in STRIJDIG_KEYWORDS:
        if kw in t:
            return "strijdig"
    for kw in CONFORM_KEYWORDS:
        if kw in t:
            return "conform"
    if indiener in COALITIE:
        return AKKOORD_THEMAS.get(thema, "conform")
    return "neutraal"


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
ODATA = 'https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0'


def extract_doc_ids(url):
    return list(dict.fromkeys(re.findall(r'[?&](?:id|did)=([A-Za-z0-9]+)', url or '')))


def fetch_odata(url):
    try:
        req = urllib.request.Request(url, headers={'Accept': 'application/json', 'User-Agent': 'MotieTracker/1.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"    OData fout: {e}")
        return None


def fetch_detail_status(url):
    """Use TK OData API to get real status and per-party stemmen."""
    ids = extract_doc_ids(url)
    if not ids:
        return None, {}
    for doc_id in ids:
        for filter_q in [
            'Zaak/Documenten/any(d:d/Id eq %27' + doc_id + '%27)',
            'Besluit/Zaak/Documenten/any(d:d/Id eq %27' + doc_id + '%27)',
        ]:
            data = fetch_odata(
                ODATA + '/Stemming?$filter=' + filter_q
                + '&$expand=Fractie($select=Afkorting)&$select=Soort,ActorFractie'
            )
            if not data or not data.get('value'):
                continue
            stemmen = {}
            voor = tegen = 0
            for item in data['value']:
                soort = item.get('Soort', '')
                stem = STEM_MAP.get(soort, soort.lower() if soort else '')
                naam = (item.get('Fractie') or {}).get('Afkorting') or item.get('ActorFractie', '')
                naam = FRACTIE_MAP.get(naam, naam)
                if naam and stem:
                    stemmen[naam] = stem
                if stem == 'voor': voor += 1
                elif stem == 'tegen': tegen += 1
            if stemmen:
                status = 'aangenomen' if voor >= tegen else 'verworpen'
                return status, stemmen
    return None, {}


def fetch_stemmen(url):
    """Use TK OData API to get per-fractie votes for a motie."""
    # Extract document ID from URL
    doc_id = extract_motie_id(url)
    if not doc_id:
        return {}
    # Try both id= and did= variants
    ids_to_try = [doc_id]
    m2 = re.search(r'[?&]id=([A-Za-z0-9]+).*[?&]did=([A-Za-z0-9]+)', url or '')
    if m2:
        ids_to_try = [m2.group(1), m2.group(2)]

    FRACTIE_MAP = {
        'VVD': 'VVD', 'D66': 'D66', 'GL-PvdA': 'GL-PvdA', 'GroenLinks-PvdA': 'GL-PvdA',
        'PVV': 'PVV', 'CDA': 'CDA', 'SP': 'SP', 'PvdD': 'PvdD',
        'ChristenUnie': 'CU', 'CU': 'CU', 'SGP': 'SGP', 'Volt': 'Volt',
        'DENK': 'DENK', 'FvD': 'FvD', 'JA21': 'JA21', 'BBB': 'BBB',
        '50PLUS': '50PLUS', 'NSC': 'NSC', 'Markuszower': 'Gr.Markuszower',
        'Groep Markuszower': 'Gr.Markuszower', 'Groep-Keijzer': 'Groep-Keijzer',
    }
    STEM_MAP = {'Voor': 'voor', 'Tegen': 'tegen', 'Onthouden': 'onthouden'}

    for doc_id in ids_to_try:
        try:
            api_url = (
                'https://gegevensmagazijn.tweedekamer.nl/OData/v4/2.0/Stemming'
                '?$filter=Zaak/Documenten/any(d:d/Id eq %27' + doc_id + '%27)'
                '&$expand=Fractie($select=Afkorting,NaamNl)'
                '&$select=Soort,ActorFractie'
            )
            req = urllib.request.Request(api_url, headers={'Accept': 'application/json'})
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read())
            items = data.get('value', [])
            if not items:
                continue
            stemmen = {}
            for item in items:
                soort = item.get('Soort', '')
                stem = STEM_MAP.get(soort, soort.lower())
                # Get fractie name
                fractie = item.get('Fractie') or {}
                naam = fractie.get('Afkorting') or fractie.get('NaamNl') or item.get('ActorFractie', '')
                naam = FRACTIE_MAP.get(naam, naam)
                if naam and stem:
                    stemmen[naam] = stem
            if stemmen:
                return stemmen
        except Exception as e:
            print(f"    Stemmen fout ({doc_id}): {e}")
    return {}


# ── Hoofdprogramma ────────────────────────────────────────────────────────────

with open('moties.json', 'r', encoding='utf-8') as f:
    moties = json.load(f)

fixed_ind = 0
fixed_ali = 0
fixed_sta = 0
fixed_stemmen = 0
today = date.today()

for m in moties:
    titel = m.get('titel', '')

    # Fetch stemmen for already-voted moties that have empty stemmen
    if m.get('status') in ('aangenomen', 'verworpen') and not m.get('stemmen'):
        _, new_stemmen = fetch_detail_status(m.get('tk_url', ''))
        if new_stemmen:
            m['stemmen'] = new_stemmen
            fixed_stemmen += 1
            print(f"  Stemmen: {titel[:50]} ({len(new_stemmen)} fracties)")
        time.sleep(0.3)

    # Fix indiener
    if m.get('indiener') == 'Onbekend':
        detected = detect_indiener(titel)
        if detected and detected != 'Onbekend':
            print(f"  Indiener: {titel[:55]} -> {detected}")
            m['indiener'] = detected
            fixed_ind += 1

    # Fix alignment als nog neutraal
    if m.get('alignment') == 'neutraal':
        new_ali = detect_alignment(titel, m.get('indiener', ''), m.get('thema', ''))
        if new_ali != 'neutraal':
            print(f"  Alignment: {titel[:50]} -> {new_ali}")
            m['alignment'] = new_ali
            fixed_ali += 1

    # Hercheck status: only in_behandeling moties with no stemmen yet
    # (OData may have failed during initial fetch, or vote happened after scraping)
    if m.get('status') == 'in_behandeling' and m.get('tk_url', '') != '' and not m.get('stemmen'):
        if True:
            new_status, new_stemmen = fetch_detail_status(m['tk_url'])
            if new_status and new_status != 'in_behandeling':
                print(f"  Status: {titel[:50]} -> {new_status}")
                m['status'] = new_status
                fixed_sta += 1
                if new_status in ('aangenomen', 'verworpen'):
                    if m.get('archief'):
                        m['archief'] = False
                        print(f"  Uit archief: {titel[:50]}")
                    if new_stemmen and not m.get('stemmen'):
                        m['stemmen'] = new_stemmen
                        print(f"  Stemmen: {len(new_stemmen)} fracties")
            time.sleep(0.4)

with open('moties.json', 'w', encoding='utf-8') as f:
    json.dump(moties, f, ensure_ascii=False, indent=2)

print(f"\n✅ {fixed_ind} indieners + {fixed_ali} alignments + {fixed_sta} statussen + {fixed_stemmen} stemmen gecorrigeerd")
