# Motie Tracker — Bugfix Changes
## Only fetch_moties.py was changed. index.html / worker.js / debug_*.py unchanged.

---

## Fix 1 — Party name normalization in stemmen
Added PARTY_NORM_GLOBAL dict and norm_stemmen() helper.
OData/HTML returns: "GroenLinks-PvdA", "FVD", "ChristenUnie", "Groep Markuszower"
Normalized to: "GL-PvdA", "FvD", "CU", "Gr.Markuszower"
Applied at fetch time AND retroactively on all existing moties at startup.

## Fix 2 — indiener: "Onbekend" for known members (e.g. Dobbe)
Live Kamerleden scraper was overwriting LEDEN_PARTIJ entries.
Fix: only ADD new names, never overwrite existing.

## Fix 3 — Wrong thema (e.g. "Bereikbaarheid" for Evertsen/Defensie motie)
Thema was set once at first scrape and never re-evaluated.
Fix: bulk re-detection pass at startup for every existing motie.

## Fix 4 — status: "in_behandeling" + empty stemmen for Van Baarle/Evertsen
ROOT CAUSE: stemmingsuitslagen pages sometimes link moties by document ID
(?id=2026D11247) instead of zaak ID (?id=2026Z04934). The old regex only
matched Z-type IDs, so this motie was silently missing from the stemmingen
dict — never matched, never updated.

Fix:
- Added extract_doc_id() helper (extracts 2026D... from ?id= or ?did=)
- Added existing_by_doc secondary index (doc_id -> motie)
- Stemmingen dict now also stores D-type keys
- All lookup points (apply loop, Step 1b, unmatched check) try doc_id fallback

## Fix 5 — stemmen_na blocking vote fetch after status fix
stemmen_na was set while status was in_behandeling (correct then).
Reset now runs AFTER Step 1b, so newly-fixed moties get votes fetched.

## Fix 6 — Step 1b OData fallback scope
Old: only checked moties in stemmingen dict with missing besluit.
New: checks ALL remaining in_behandeling moties via OData unconditionally.
