# Motie Tracker — Bugfix Changes
## Files changed: fetch_moties.py only
## index.html, worker.js, debug_*.py — UNCHANGED

---

## Fix 1 — Party name normalization in stemmen
Added `PARTY_NORM_GLOBAL` dict and `norm_stemmen()` helper.
OData/HTML returns: "GroenLinks-PvdA", "FVD", "ChristenUnie", "Groep Markuszower"
Now normalized to: "GL-PvdA", "FvD", "CU", "Gr.Markuszower"
Applied at fetch time AND retroactively on all existing moties at startup.

## Fix 2 — indiener: "Onbekend" for known members (e.g. Dobbe)
Live Kamerleden scraper was overwriting LEDEN_PARTIJ entries.
Fix: only ADD new names, never overwrite existing ones.

## Fix 3 — Wrong thema (e.g. "Bereikbaarheid" for Evertsen/Defensie motie)
Thema was set once at first scrape and never re-evaluated.
Fix: bulk re-detection pass at startup re-runs detect_thema + detect_indiener
on every existing motie.

## Fix 4 — status: "in_behandeling" despite voting having happened
Old Step 1b only ran OData fallback for moties already in the stemmingen dict.
Moties absent from the stemmingen scrape were never re-checked.
Fix: two-pass Step 1b:
  Pass 1 — match stemmingen dict (fast)
  Pass 2 — OData check ALL remaining in_behandeling moties unconditionally

## Fix 5 — stemmen_na blocking vote fetch after status fix
stemmen_na was set when motie was in_behandeling (correct then).
But the reset ran BEFORE Step 1b fixed the status, so newly-fixed moties
still had stemmen_na=true and were skipped by needs_stemmen.
Fix: reset now runs AFTER Step 1b, so the full chain works:
  OData fixes status → stemmen_na cleared → votes fetched → names normalized
