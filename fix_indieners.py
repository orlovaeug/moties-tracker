#!/usr/bin/env python3
"""
fix_indieners.py — eenmalig script om indieners te corrigeren in moties.json
Run dit EENMALIG lokaal of als extra stap in GitHub Actions.
"""
import json, re, urllib.request, html as html_module, time
from datetime import date

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

PARTIJEN = ["PVV","VVD","NSC","BBB","D66","GL-PvdA","CDA","SP","PvdD","CU","SGP",
            "Volt","DENK","FvD","JA21","50PLUS","Gr.Markuszower"]

COALITIE = {"D66","VVD","CDA","BBB","NSC"}

STRIJDIG_KEYWORDS = [
    "niet verhogen","van tafel","terugtrekken","geen bezuinig","verbod op","schrap",
    "afschaffen","niet korten","niet verlagen","stop met","verzet zich","verwerpt",
    "intrekken","geen steun","tegen het kabinet","wantrouwen",
]

CONFORM_KEYWORDS = [
    "conform akkoord","uitvoering geven","wettelijk vastleggen","invoeren","oprichten",
    "vaststellen","uitwerken","realiseren","uitvoeren","verankeren",
]

AKKOORD_THEMAS = {
    "Defensie": "conform", "Wonen & Bouwen": "conform", "Klimaat & Energie": "conform",
    "Asiel & Migratie": "conform", "Financien": "conform", "Bereikbaarheid & Mobiliteit": "conform",
    "Landbouw & Natuur": "conform", "Democratie & Rechtsstaat": "neutraal",
    "Bestaanszekerheid": "neutraal",
}

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

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; MotieTracker/1.0)',
    'Accept': 'text/html',
    'Accept-Language': 'nl-NL,nl;q=0.9',
}

def fetch_detail_status(url):
    """Fetch motie detail page and detect its real status."""
    if not url.startswith('http'):
        url = 'https://www.tweedekamer.nl' + url
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read().decode('utf-8', errors='replace')
        raw_u = html_module.unescape(raw).lower()
        if re.search(r'(stemming|uitslag|besluit).{0,100}aangenomen', raw_u) or re.search(r'aangenomen.{0,100}(stemming|uitslag|besluit)', raw_u):
            return 'aangenomen'
        if re.search(r'(stemming|uitslag|besluit).{0,100}verworpen', raw_u) or re.search(r'verworpen.{0,100}(stemming|uitslag|besluit)', raw_u):
            return 'verworpen'
        if 'aangehouden' in raw_u:
            return 'aangehouden'
        return None  # unknown, keep existing
    except Exception as e:
        print(f"    Detail fout: {e}")
        return None

with open('moties.json', 'r', encoding='utf-8') as f:
    moties = json.load(f)

fixed_ind = 0
fixed_ali = 0
fixed_sta = 0
today = date.today()

for m in moties:
    titel = m.get('titel', '')

    # Fix indiener
    if m.get('indiener') == 'Onbekend':
        detected = detect_indiener(titel)
        if detected:
            print(f"  Indiener: {titel[:55]} → {detected}")
            m['indiener'] = detected
            fixed_ind += 1

    # Fix alignment if still neutraal
    if m.get('alignment') == 'neutraal':
        new_ali = detect_alignment(titel, m.get('indiener',''), m.get('thema',''))
        if new_ali != 'neutraal':
            print(f"  Alignment: {titel[:50]} → {new_ali}")
            m['alignment'] = new_ali
            fixed_ali += 1

    # Re-check status for in_behandeling moties older than 1 day
    if m.get('status') == 'in_behandeling' and m.get('tk_url','').startswith('/'):
        try:
            motie_date = date.fromisoformat(m.get('datum', today.isoformat()))
            days_old = (today - motie_date).days
        except:
            days_old = 0
        if days_old >= 1:
            new_status = fetch_detail_status(m['tk_url'])
            if new_status and new_status != 'in_behandeling':
                print(f"  Status: {titel[:50]} → {new_status}")
                m['status'] = new_status
                fixed_sta += 1
            time.sleep(0.4)

with open('moties.json', 'w', encoding='utf-8') as f:
    json.dump(moties, f, ensure_ascii=False, indent=2)

print(f"\n✅ {fixed_ind} indieners + {fixed_ali} alignments + {fixed_sta} statussen gecorrigeerd")
print("Voer daarna embed_moties.py uit om index.html te updaten.")
