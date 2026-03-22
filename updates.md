# Updates to Maryland Medical Discipline Files

This document covers changes made to the application since the original working prototype. Changes are organized by category.

---

## Bug Fixes

### Missing Python imports in app.py
The app crashed on startup because `fn` (used for `fn.COUNT()` queries) and `OperationalError` were used but never imported from peewee. Added `from peewee import fn, OperationalError`. Also added `import re` for regex operations needed by slug generation.

### Scraper broken for 2026 data
The Maryland Board of Physicians changed their disciplinary page layout in 2026 from a 3-column table to a 4-column table. The scraper had a guard `if len(row.find_all('td')) > 3: continue` that silently skipped all 2026 rows. Additionally, 2026 rows use full absolute URLs instead of relative paths, which broke file ID extraction and caused doubled domain prefixes.

Fixed by replacing the skip guard with explicit `len(tds) == 4` and `len(tds) == 3` branches. The 4-column branch checks whether the href starts with `http` and handles file ID extraction and URL construction accordingly.

### Activity feed missing 2026 records
The homepage "Recent Actions" section queried the `DocumentJSON` table, whose latest records were from September 2025 (dependent on the LLM summary pipeline having run). Switched the query to use the `Alert` table joined with `Doctor`, ordered by date descending. This shows records as soon as they're scraped, regardless of whether summaries have been generated.

### License number format mismatch between tables
`DocumentJSON` stores license numbers like `D90487`, while the `Doctor` table uses zero-padded format `D0090487`. The `doctor_slug_for_license()` function now tries an exact match first, then falls back to zero-padding the numeric portion (e.g., extracting `D` + `90487` and padding to `D0090487`).

### Status badges showing wrong status for terminated suspensions
Doctors like Julia Olson had their suspension terminated and probation imposed, but the badge showed "Suspended" because the substring check for "suspension" matched before any termination logic ran. This was initially fixed with regex-based ordering, then replaced entirely by LLM classification (see below).

### Junk *.txt.txt files in pipeline
The `combine_text.sh` script produced `*.txt.txt` files when glob expansion failed on empty directories. These were cleaned up from `data/combined_text/`.

---

## Design Overhaul

### Color palette
Replaced the dark institutional navy theme with a muted Maryland-inspired palette:
- Red `#A03033` (primary actions, alerts)
- Gold `#D4A843` (highlights, secondary accents)
- Off-white `#F5F0E8` (page background)
- Charcoal `#2D2D2D` (body text)
- Navy `#152238` (navbar, headings)

### Typography
Added three font families: DM Serif Display for headlines, Roboto for body text, and Hind Siliguri for section headings.

### Base template
Created `templates/base.html` with consistent navigation (Home, Search, Topics, All Cases, About), a footer with data source attribution, and Jinja blocks for title, head_extra, content, and scripts. All page templates now extend this base.

### Homepage redesign
The original homepage had three equal-weight cards (Doctor Search, Document Search, AI Search) linking to `/search`. Replaced with:
1. Hero section with prominent doctor name search bar and autocomplete
2. Stats row showing total doctors disciplined, total actions, most common action type, and most common doctor type
3. Two-column layout: recent activity feed (left) and topic browse cards (right)
4. Doctors by type table (moved lower)
5. Advanced search section with similarity search modal

### Doctor detail page
Replaced raw data tables with a timeline layout. Header shows doctor name, type, license number, and a color-coded status badge. Case numbers display as Bootstrap badges. Disciplinary actions appear in a vertical timeline with dates, action descriptions, document summaries, and links to PDFs, document details, and similar cases.

### All other templates
Rewrote search, search results, keywords, keyword detail, type, dataset, document detail, similarity results, and contact pages to extend `base.html` and use the new design system. The dataset page uses DataTables for pagination and sorting.

---

## New Features

### Doctor name autocomplete
Added `/api/doctor_search` JSON endpoint. The homepage search bar queries this endpoint on keypress (debounced) and displays a dropdown of matching doctors with name, type, and license number. Selecting a result navigates to the doctor's page.

### Slugified URLs
Doctor pages use `{name}-{license}` format (e.g., `/doctor/joan-smith-h0048286`). Keyword pages use dash-separated lowercase (e.g., `/keyword/prescription-fraud`). Type pages use slugified type names (e.g., `/type/doctor-of-medicine`). Functions `doctor_slug()`, `doctor_slug_for_license()`, `keyword_slug()`, and `type_slug()` are registered as Jinja globals for use in all templates. The doctor route parses the license number from the end of the slug via regex, with fallback handling for "unlicensed" practitioners and old-style URLs.

### Topic categories
Added a `TOPIC_CATEGORIES` dictionary in `app.py` mapping four browseable categories to keyword lists:
- Prescribing & Drugs
- Patient Harm
- Licensing & Fraud
- Impairment

These appear as cards on the homepage linking to filtered keyword views.

### Dual links on search/keyword result pages
Previously, clicking a doctor name on keyword detail or search result pages went to the document, not the doctor. Now both pages show a link to the doctor's page and a separate "View Document" link.

### LLM-based doctor status classification
Replaced regex/substring status badge logic with LLM classification at build time. New pipeline script `pipeline/classify_status.py` sends each doctor's most recent alert type to Qwen 3.5:9b (local Ollama) with a classification prompt. The LLM returns one of nine standard labels: License Permanently Revoked, License Revoked, License Surrendered, Suspended, On Probation, Reinstated, Suspension Terminated, Reprimanded, or Fined. Results are stored in a new `status` column on the `Doctor` model. The script is idempotent (skips already-classified doctors) and includes retry logic for invalid responses.

This handles the varied and complex action description text that regex couldn't reliably parse, particularly cases where suspensions are terminated with probation imposed, or where multiple actions appear in a single order.

---

## Pipeline Changes

### Scraper handles both table formats
`pipeline/scrape.py` now has explicit branches for 3-column (pre-2026) and 4-column (2026+) table rows, with correct URL and file ID handling for each.

### New classification step
`pipeline/full_pipeline.sh` expanded from 10 to 11 steps. Step 9 (after database creation) runs `classify_status.py` to populate doctor status badges. Steps 10 and 11 are the existing JSON summary generation and embedding generation.

### Database schema change
Added nullable `status` column to the `doctor_info` table via the `Doctor` model in `models.py`.

---

## Organizational Work

### Shared models
Database models live in `models.py` and are imported by both `app.py` and pipeline scripts, avoiding duplicate model definitions.

### Dev server configuration
Added `.claude/launch.json` for Flask development server on port 5001.

### Template inheritance
All templates use a shared base with consistent navigation and footer, eliminating duplicated nav markup across pages.

### Stylesheet organization
`static/style.css` is structured into 15 labeled sections: base layout, navbar, hero, stats row, activity feed, topic cards, cards, tables, doctor detail/timeline, badges/keywords, buttons, search/forms, footer, responsive breakpoints, and utilities.
