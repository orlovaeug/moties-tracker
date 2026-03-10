#!/usr/bin/env python3
"""
fix_indieners.py — eenmalig script om indieners te corrigeren in moties.json
Run dit EENMALIG lokaal of als extra stap in GitHub Actions.
"""
import json, re

LEDEN_PARTIJ = {
    # PVV
    "Wilders": "PVV", "Heutink": "PVV", "Agema": "PVV", "Maeijer": "PVV",
    "Kisteman": "PVV", "Freek Jansen": "PVV",
    # VVD
    "Yesilgöz": "VVD", "Hermans": "VVD", "Peter de Groot": "VVD", "Brekelmans": "VVD",
    "Rajkowski": "VVD", "Six Dijkstra": "VVD", "Karremans": "VVD", "Van Ark": "VVD",
    "Bevers": "VVD", "Martens-America": "VVD", "Van Meetelen": "VVD",
    # NSC
    "Omtzigt": "NSC", "Nicolaï": "NSC", "Boomsma": "NSC",
    # BBB
    "Van der Plas": "BBB", "Vedder": "BBB", "Struijs": "BBB",
    # D66
    "Paternotte": "D66", "Jetten": "D66", "Van Weyenberg": "D66", "Van Lanschot": "D66",
    "Ten Hove": "D66", "Kathmann": "D66", "Hammelburg": "D66", "Biekman": "D66",
    "Van Berkel": "D66", "Kröger": "D66",
    # GL-PvdA
    "Klaver": "GL-PvdA", "Nijboer": "GL-PvdA", "Westerveld": "GL-PvdA",
    "Mutluer": "GL-PvdA", "Lahlah": "GL-PvdA", "El Abassi": "GL-PvdA",
    "Abdi": "GL-PvdA", "Belhirch": "GL-PvdA", "Armut": "GL-PvdA",
    "Van den Berg": "GL-PvdA",
    # CDA
    "Bontenbal": "CDA", "Amhaouch": "CDA", "Van Campen": "CDA",
    "Palmen": "CDA", "Lohman": "CDA", "De Beer": "CDA", "Bikkers": "CDA",
    "Maes": "CDA", "Mathlouti": "CDA",
    # SP
    "Dijk": "SP", "Leijten": "SP", "Koudstaal": "SP",
    # PvdD
    "Teunissen": "PvdD", "Wassenberg": "PvdD", "Warmerdam": "PvdD",
    # CU
    "Bikker": "CU", "Segers": "CU", "Ceder": "CU",
    # SGP
    "Stoffer": "SGP", "Diederik van Dijk": "SGP", "Van der Staaij": "SGP",
    # Volt
    "Koekkoek": "Volt",
    # DENK
    "Azarkan": "DENK", "Ergin": "DENK", "Stephan van Baarle": "DENK",
    # FvD
    "Van Houwelingen": "FvD", "Baudet": "FvD", "Chris Jansen": "FvD", "Van der Maas": "FvD",
    # JA21
    "Eerdmans": "JA21", "Van Meijeren": "JA21", "Aartsen": "JA21", "Jumelet": "JA21",
    # 50PLUS
    "Boelsma-Hoekstra": "50PLUS", "Jagtenberg": "50PLUS",
    # Gr.Markuszower
    "Markuszower": "Gr.Markuszower",
}

PARTIJEN = ["PVV","VVD","NSC","BBB","D66","GL-PvdA","CDA","SP","PvdD","CU","SGP",
            "Volt","DENK","FvD","JA21","50PLUS","Gr.Markuszower"]

def detect_indiener(titel):
    # Try to extract name from "Motie van het lid X" or "Motie van de leden X en Y"
    m = re.search(r'lid(?:en)?\s+([A-Z][a-zA-Z\u00C0-\u017E\s\-]+?)(?:\s+c\.s\.|\s+en\s+[A-Z]|\s*-\s*[A-Z]|$)', titel)
    if m:
        name = m.group(1).strip()
        for naam, partij in LEDEN_PARTIJ.items():
            if naam.lower() in name.lower():
                return partij
    for p in PARTIJEN:
        if p in titel:
            return p
    return None  # None = leave as-is

with open('moties.json', 'r', encoding='utf-8') as f:
    moties = json.load(f)

fixed = 0
for m in moties:
    if m.get('indiener') == 'Onbekend':
        detected = detect_indiener(m.get('titel', ''))
        if detected:
            print(f"  Fix: {m['titel'][:60]} → {detected}")
            m['indiener'] = detected
            fixed += 1

with open('moties.json', 'w', encoding='utf-8') as f:
    json.dump(moties, f, ensure_ascii=False, indent=2)

print(f"\n✅ {fixed} indieners gecorrigeerd in moties.json")
print("Voer daarna embed_moties.py uit om index.html te updaten.")
