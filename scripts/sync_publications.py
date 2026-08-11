#!/usr/bin/env python3
"""
Sync journal-article publications from Google Scholar into the WACI Lab site.

WHAT THIS DOES
    1. Fetches the PI's full Google Scholar publication list via `scholarly`.
    2. Fills in full details (authors, journal, url) for every publication
       not already in the local cache, with a polite delay between requests
       and checkpointed saves so an interrupted/rate-limited run can resume.
    3. Classifies each publication as a real journal article vs. everything
       else (conference papers/abstracts, preprints, technical reports,
       symposium proceedings) -- Scholar has no clean field for this, so
       it's inferred from the filled bib data.
    4. Diffs the journal articles against the existing _data/publications.yml
       by normalized title.
    5. Writes NEW candidates to _data/publications_review.yml for a human
       to look over -- it NEVER writes to _data/publications.yml directly.
       Existing curated entries (with their `themes` / `highlight` tags)
       are never touched.

WHY A REVIEW FILE INSTEAD OF AUTO-MERGING
    Scholar has no concept of this lab's `themes` taxonomy or the
    `highlight` (PI-corresponding/lead-author) flag, and author-name
    formatting from Scholar ("Bin Peng") needs converting to the site's
    "Peng, B." style, which is a best-effort heuristic, not exact. Every
    candidate gets an auto-suggested `themes` guess (keyword match against
    the title) clearly marked for verification, plus the raw Scholar author
    string alongside the reformatted one -- review and fix both before
    copying an entry into _data/publications.yml.

USAGE
    python scripts/sync_publications.py [--scholar-id ID] [--limit N] [--dry-run]

    --scholar-id  Google Scholar author id (default: reads _config.yml's
                  google_scholar URL for the PI).
    --limit       Only process the first N not-yet-cached publications this
                  run (useful for incremental runs / staying under rate
                  limits). Default: no limit.
    --dry-run     Fetch and classify but don't write the review file.

REQUIRES
    pip install scholarly pyyaml
"""
import argparse
import json
import random
import re
import sys
import time
import unicodedata
from pathlib import Path

import yaml
from scholarly import scholarly, ProxyGenerator

# Windows consoles default to cp1252, which chokes on unicode dashes/accents
# in paper titles -- force utf-8 stdout so printing progress never crashes.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
CACHE_PATH = ROOT / "scripts" / ".scholar_cache.json"
PUBLICATIONS_PATH = ROOT / "_data" / "publications.yml"
REVIEW_PATH = ROOT / "_data" / "publications_review.yml"
CONFIG_PATH = ROOT / "_config.yml"

# Venue-name / field patterns that mean "not a journal article".
NON_JOURNAL_PATTERNS = re.compile(
    r"abstract|symposium|proceedings|conference|meeting|workshop|"
    r"arxiv|preprint|technical report|dissertation|thesis|"
    r"national laboratory|nationalbibliothek|patent",
    re.IGNORECASE,
)

THEME_KEYWORDS = {
    "Hydrology": [
        "hydrolog", "watershed", "water quality", "streamflow", "drainage",
        "runoff", "flood", "groundwater", "drought", "tile drain",
    ],
    "Sensing": [
        "sensor", "in-situ", "in situ", "uav ", "unmanned aerial",
        "monitoring network", "wireless sensor", "iot",
    ],
    "Crop modeling": [
        "crop model", "agroecosystem", "yield", "ecosys", "dssat", "apsim",
        "crop growth", "biomass", "tillage", "irrigation",
    ],
    "Earth system": [
        "earth system", "climate", "global ", "biogeochemical cycle",
        "carbon cycle", "land surface model", "climate change",
    ],
    "Plant-soil-microbe": [
        "soil microb", "rhizosphere", "plant-soil", "nutrient cycling",
        "soil organic", "microbial", "root ", "plant hydraulic",
    ],
    "Remote sensing": [
        "satellite", "remote sensing", "landsat", "sentinel", "modis",
        "uav imagery", "deep learning", "machine learning", "neural network",
    ],
}


def load_scholar_id(cli_value):
    if cli_value:
        return cli_value
    text = CONFIG_PATH.read_text(encoding="utf-8")
    m = re.search(r"google_scholar:\s*\"[^\"]*[?&]user=([\w-]+)", text)
    if not m:
        sys.exit("Could not find a Scholar user id in _config.yml -- pass --scholar-id.")
    return m.group(1)


def load_cache():
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {}


def save_cache(cache):
    CACHE_PATH.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")


def normalize_title(title):
    t = unicodedata.normalize("NFKD", title or "")
    t = re.sub(r"[^\w\s]", "", t).lower()
    return re.sub(r"\s+", " ", t).strip()


def load_existing_titles():
    if not PUBLICATIONS_PATH.exists():
        return set()
    data = yaml.safe_load(PUBLICATIONS_PATH.read_text(encoding="utf-8")) or []
    titles = set()
    for group in data:
        for item in group.get("items", []):
            titles.add(normalize_title(item.get("title", "")))
    return titles


def is_journal_article(bib):
    journal = bib.get("journal", "")
    if not journal:
        return False
    if NON_JOURNAL_PATTERNS.search(journal):
        return False
    return True


def reformat_authors(author_string):
    """'Baoyu Jing and Si Zhang' -> 'Jing, B., Zhang, S.' (best-effort)."""
    if not author_string:
        return ""
    parts = [a.strip() for a in author_string.split(" and ") if a.strip()]
    out = []
    for name in parts:
        words = name.split()
        if len(words) < 2:
            out.append(name)
            continue
        surname = words[-1]
        initials = "".join(f"{w[0]}." for w in words[:-1] if w)
        out.append(f"{surname}, {initials}")
    return ", ".join(out)


def scholar_permalink(scholar_id, author_pub_id):
    return (
        "https://scholar.google.com/citations?view_op=view_citation&hl=en"
        f"&user={scholar_id}&citation_for_view={author_pub_id}"
    )


def suggest_themes(title, abstract=""):
    text = f"{title} {abstract}".lower()
    matches = [theme for theme, kws in THEME_KEYWORDS.items() if any(kw in text for kw in kws)]
    return matches


scholarly.set_timeout(20)
scholarly.set_retries(2)


def fetch_all_publications(scholar_id):
    author = scholarly.search_author_id(scholar_id)
    author = scholarly.fill(author, sections=["publications"], sortby="year")
    return author["publications"]


def fill_with_retry(pub, max_attempts=4):
    delay = 3
    for attempt in range(1, max_attempts + 1):
        try:
            return scholarly.fill(pub)
        except Exception as e:  # scholarly raises various exceptions on block/CAPTCHA
            if attempt == max_attempts:
                print(f"  giving up on '{pub['bib'].get('title', '?')[:60]}': {e}")
                return None
            print(f"  fetch error ({e}); retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scholar-id")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--offline",
        action="store_true",
        help="Skip fetching -- just re-classify/re-diff whatever is already in the cache "
        "and rewrite the review file. Useful after a partial run got rate-limited.",
    )
    args = ap.parse_args()

    scholar_id = load_scholar_id(args.scholar_id)
    print(f"Scholar profile: {scholar_id}")

    cache = load_cache()
    print(f"Cache has {len(cache)} previously-fetched publications.")

    if args.offline:
        print("(offline mode -- not contacting Google Scholar)")
    else:
        print("Fetching publication list...")
        pubs = fetch_all_publications(scholar_id)
        print(f"Scholar lists {len(pubs)} total publications.")

        to_fetch = [p for p in pubs if p["author_pub_id"] not in cache]
        if args.limit:
            to_fetch = to_fetch[: args.limit]
        print(f"{len(to_fetch)} publications need fetching this run.")

        for i, pub in enumerate(to_fetch, 1):
            title = pub["bib"].get("title", "?")
            print(f"[{i}/{len(to_fetch)}] {title[:70]}")
            filled = fill_with_retry(pub)
            if filled is not None:
                entry = dict(filled["bib"])
                entry["pub_url"] = filled.get("pub_url", "")
                entry["eprint_url"] = filled.get("eprint_url", "")
                entry["author_pub_id"] = pub["author_pub_id"]
                cache[pub["author_pub_id"]] = entry
                save_cache(cache)  # checkpoint after every success
            time.sleep(random.uniform(1.5, 3.5))

        print(f"\nCache now has {len(cache)} publications.")

    existing_titles = load_existing_titles()
    candidates = []
    for pub_id, bib in cache.items():
        if not is_journal_article(bib):
            continue
        norm = normalize_title(bib.get("title", ""))
        if not norm or norm in existing_titles:
            continue
        candidates.append((pub_id, bib))

    print(f"{len(candidates)} new journal-article candidates not already on the site.")

    if args.dry_run:
        print("(dry run -- not writing review file)")
        return

    review = []
    by_year = {}
    for pub_id, bib in sorted(candidates, key=lambda kv: kv[1].get("pub_year", 0), reverse=True):
        year = bib.get("pub_year")
        url = bib.get("pub_url") or bib.get("eprint_url") or scholar_permalink(scholar_id, pub_id)
        entry = {
            "title": bib.get("title", ""),
            "authors_raw_scholar": bib.get("author", ""),
            "authors_suggested": reformat_authors(bib.get("author", "")),
            "journal": bib.get("journal", ""),
            "url": url,
            "themes_suggested": suggest_themes(bib.get("title", ""), bib.get("abstract", "")),
            "note": "REVIEW: verify authors/themes before copying into publications.yml",
        }
        by_year.setdefault(year, []).append(entry)

    for year in sorted(by_year, reverse=True):
        review.append({"year": year, "items": by_year[year]})

    REVIEW_PATH.write_text(
        "# Auto-generated by scripts/sync_publications.py -- REVIEW, then hand-copy\n"
        "# accepted entries into _data/publications.yml with themes/highlight set.\n"
        "# This file is safe to delete/regenerate; it is never read by the site.\n\n"
        + yaml.dump(review, allow_unicode=True, sort_keys=False, width=100),
        encoding="utf-8",
    )
    print(f"Wrote {len(candidates)} candidates to {REVIEW_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
