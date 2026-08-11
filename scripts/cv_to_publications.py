#!/usr/bin/env python3
"""
Parse the JOURNAL PUBLICATIONS section straight out of Dr. Peng's CV (.docx)
into candidate entries for _data/publications.yml. This is the primary
source now -- it's the author's own authoritative, already-curated list
(journal papers only, no conference items to filter out), with no Google
Scholar rate-limit risk at all.

WHAT IT DOES
    1. Extracts the CV's raw XML text (no pandoc dependency -- see
       extract_cv_text()) and isolates the "JOURNAL PUBLICATIONS" section.
    2. Parses each citation line into authors / year / title / journal.
    3. Flags `highlight: true` when Dr. Peng appears as corresponding
       ("Peng, B.*") or equal-contribution-marked first author.
    4. Suggests `themes:` via keyword matching against the title (same
       heuristic as sync_publications.py) -- still needs verification.
    5. Cross-references scripts/.scholar_cache.json (from the earlier
       Scholar backfill) by normalized title to pull a real DOI/article
       URL where one is already cached; falls back to a Google Scholar
       *search* link (a plain URL, not a scrape) when no cached match
       exists, clearly flagged for follow-up.
    6. Diffs against the existing _data/publications.yml by normalized
       title -- never touches entries already on the site.
    7. Writes everything new to _data/publications_review.yml, same as
       the Scholar-based script -- nothing is written to the live
       publications.yml automatically.

USAGE
    python scripts/cv_to_publications.py --cv PATH
    (or set the WACI_CV_PATH environment variable instead of passing --cv)
"""
import argparse
import json
import os
import re
import sys
import unicodedata
import urllib.parse
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PUBLICATIONS_PATH = ROOT / "_data" / "publications.yml"
REVIEW_PATH = ROOT / "_data" / "publications_review.yml"
CACHE_PATH = ROOT / "scripts" / ".scholar_cache.json"
# No hardcoded personal path here (this repo is public) -- set WACI_CV_PATH
# locally, or pass --cv PATH each run.
DEFAULT_CV = os.environ.get("WACI_CV_PATH")

THEME_KEYWORDS = {
    "Hydrology": [
        "hydrolog", "watershed", "streamflow", "drainage", "runoff", "flood",
        "groundwater", "drought", "tile drain", "irrigation",
        "evapotranspiration", "precipitation", "soil moisture", "river",
        "discharge", "water supply", "water stress", "aquifer", "rainfall",
    ],
    "Water quality": [
        "water quality", "nitrate", "nitrogen export", "nitrogen loss",
        "phosphorus", "nutrient loss", "nutrient export", "ammonia",
        "nitrous oxide", "pollutant", "contaminant", "n2o", "no3",
    ],
    "Crop and soil": [
        "crop", "soil", "yield", "corn", "soybean", "maize", "wheat",
        "biomass", "root", "rhizosphere", "canopy", "photosynthesis",
        "plant-soil", "phenology", "cover crop", "tillage",
    ],
    "Land management": [
        "land management", "land use", "grazing", "farm", "cropland",
        "cropping system", "rotation", "agrivoltaics", "precision",
        "decision support", "field-level", "field level",
    ],
    "Earth system": [
        "earth system", "climate", "global ", "biogeochemical cycle",
        "carbon cycle", "land surface model", "climate change", "climate-",
        "atmospher", "greenhouse gas", "carbon budget", "carbon footprint",
    ],
    "Conservation": [
        "conservation", "sustainab", "ecosystem service", "environmental quality",
        "resilien", "biodiversity", "cover crop", "best management practice",
    ],
    "Remote sensing": [
        "satellite", "remote sensing", "landsat", "sentinel", "modis",
        "uav ", "unmanned aerial", "fluorescence", "spectral", "hyperspectral",
        "radiance", "radar", "imagery", "aerial",
    ],
    "Modeling": [
        "model", "simulation", "framework", "process-based", "knowledge-guided",
        "data assimilation", "ecosys", "dssat", "apsim", "community land model",
        "calibration", "parameteriz",
    ],
    "AI": [
        "machine learning", "deep learning", "artificial intelligence",
        "neural network", "large language model", "llm", "transfer learning",
        "knowledge-guided machine learning", " ai ", "graph machine learning",
    ],
    "Measurement": [
        "sensor", "in-situ", "in situ", "monitoring", "measurement",
        "instrument", "spectrophotomet", "network", "observation", "gauge",
    ],
}


def extract_cv_text(docx_path):
    with zipfile.ZipFile(docx_path) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    paras = re.findall(r"<w:p\b[^>]*>.*?</w:p>", xml, re.DOTALL)
    lines = []
    for p in paras:
        texts = re.findall(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", p, re.DOTALL)
        line = "".join(texts)
        line = line.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        line = line.replace(" ", " ")  # Word non-breaking spaces -> regular spaces
        line = line.replace(" ", " ")  # Word non-breaking spaces -> regular spaces
        lines.append(line)
    return lines


def isolate_journal_section(lines):
    start = end = None
    for i, line in enumerate(lines):
        if start is None and line.strip().startswith("JOURNAL PUBLICATIONS"):
            start = i + 1
            continue
        if start is not None and re.match(r"^[A-Z][A-Z ]{4,}$", line.strip()):
            end = i
            break
    if start is None:
        sys.exit("Could not find a 'JOURNAL PUBLICATIONS' heading in the CV.")
    return [l for l in lines[start : end or len(lines)] if l.strip()]


def looks_like_journal_name(name):
    return bool(name) and bool(re.search(r"[A-Za-z]{3,}", name))


def extract_journal_name(chunk):
    name = chunk.split(",")[0].strip()
    # strip a trailing volume number when there's no comma before it
    # (e.g. "Agricultural and Forest Meteorology 386" -> drop the "386")
    name = re.sub(r"\s+\d+[\d,()\-:]*$", "", name).strip()
    return name


def split_title_journal(rest):
    rest = rest.strip().rstrip(".")
    if ". " not in rest:
        return rest, ""
    title, chunk = rest.rsplit(". ", 1)
    journal = extract_journal_name(chunk)
    if looks_like_journal_name(journal):
        return title, journal
    # Older CV entries use "Title. Journal. Volume, Pages." (three segments)
    # instead of "Title. Journal, Volume, Pages." (two) -- peel off one more.
    if ". " in title:
        title2, chunk2 = title.rsplit(". ", 1)
        journal2 = extract_journal_name(chunk2)
        if looks_like_journal_name(journal2):
            return title2, journal2
    return title, journal


def parse_citation(line):
    m = re.search(r"\(?((?:19|20)\d{2})\)?\.?\s+", line)
    if not m:
        return None
    authors = line[: m.start()].strip().rstrip(",")
    rest = line[m.end() :].strip()
    year = int(m.group(1))

    # Strip a trailing explanatory parenthetical note, e.g. "(All authors
    # contributed equally to ...)" -- only long ones, so a real "(2020)"-
    # style year/volume marker (already consumed above) is never touched.
    rest = re.sub(r"\s*\([^()]{20,}\)\.?$", "", rest).strip()

    title, journal = split_title_journal(rest)

    return {
        "authors_raw": authors,
        "year": year,
        "title": title,
        "journal": journal,
        "citation_line": line,
    }


def is_highlight(authors_raw):
    return bool(re.search(r"Peng,\s*B\.?\s*[*\u2020]", authors_raw))


def normalize_title(title):
    t = unicodedata.normalize("NFKD", title or "")
    t = re.sub(r"[^\w\s]", "", t).lower()
    return re.sub(r"\s+", " ", t).strip()


def normalize_authors(authors_raw):
    """CV author strings already match the site's 'Last, F.' style -- just
    tidy up ' and ' connectors and stray whitespace."""
    a = re.sub(r"\s+and\s+", ", ", authors_raw)
    a = re.sub(r",\s*,", ",", a)
    a = re.sub(r"\s{2,}", " ", a)
    return a.strip()


def suggest_themes(title):
    text = title.lower()
    return [theme for theme, kws in THEME_KEYWORDS.items() if any(kw in text for kw in kws)]


def load_scholar_cache():
    if not CACHE_PATH.exists():
        return {}
    cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    by_title = {}
    for pub_id, bib in cache.items():
        norm = normalize_title(bib.get("title", ""))
        if norm:
            by_title[norm] = bib
    return by_title


def load_existing_titles():
    if not PUBLICATIONS_PATH.exists():
        return set()
    data = yaml.safe_load(PUBLICATIONS_PATH.read_text(encoding="utf-8")) or []
    titles = set()
    for group in data:
        for item in group.get("items", []):
            titles.add(normalize_title(item.get("title", "")))
    return titles


def scholar_search_url(title):
    return "https://scholar.google.com/scholar?q=" + urllib.parse.quote(title)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cv", default=DEFAULT_CV)
    args = ap.parse_args()
    if not args.cv:
        sys.exit("No CV path given. Pass --cv PATH or set the WACI_CV_PATH environment variable.")

    lines = extract_cv_text(Path(args.cv))
    citation_lines = isolate_journal_section(lines)
    print(f"Found {len(citation_lines)} citation lines in the CV's journal-publications section.")

    parsed = []
    unparsed = []
    for line in citation_lines:
        rec = parse_citation(line)
        if rec is None:
            unparsed.append(line)
        else:
            parsed.append(rec)

    if unparsed:
        print(f"\n{len(unparsed)} lines couldn't be parsed automatically (no year found) -- add these by hand:")
        for l in unparsed:
            print(f"  {l[:100]}")

    existing_titles = load_existing_titles()
    scholar_by_title = load_scholar_cache()

    candidates = [p for p in parsed if normalize_title(p["title"]) not in existing_titles]
    print(f"\n{len(parsed)} parsed, {len(parsed) - len(candidates)} already on the site, {len(candidates)} new candidates.")

    by_year = {}
    matched_url_count = 0
    for p in candidates:
        norm = normalize_title(p["title"])
        scholar_hit = scholar_by_title.get(norm)
        if scholar_hit:
            url = scholar_hit.get("pub_url") or scholar_hit.get("eprint_url") or scholar_search_url(p["title"])
            if scholar_hit.get("pub_url") or scholar_hit.get("eprint_url"):
                matched_url_count += 1
            url_note = "matched to cached Scholar entry"
        else:
            url = scholar_search_url(p["title"])
            url_note = "NO DOI FOUND -- this is a Scholar *search* link, replace with the real DOI"

        note = "REVIEW: verify authors/journal/url/themes before copying into publications.yml"
        if not p["journal"] or not re.search(r"[A-Za-z]{3,}", p["journal"]):
            note = "PARSE WARNING: title/journal split looks wrong (unusual citation format) -- fix by hand. " + note

        entry = {
            "title": p["title"],
            "authors": normalize_authors(p["authors_raw"]),
            "journal": p["journal"],
            "url": url,
            "url_note": url_note,
            "highlight": is_highlight(p["authors_raw"]),
            "themes_suggested": suggest_themes(p["title"]),
            "note": note,
        }
        by_year.setdefault(p["year"], []).append(entry)

    review = [{"year": y, "items": by_year[y]} for y in sorted(by_year, reverse=True)]

    REVIEW_PATH.write_text(
        "# Auto-generated by scripts/cv_to_publications.py -- REVIEW, then hand-copy\n"
        "# accepted entries into _data/publications.yml with themes/highlight verified.\n"
        "# This file is safe to delete/regenerate; it is never read by the site.\n\n"
        + yaml.dump(review, allow_unicode=True, sort_keys=False, width=100),
        encoding="utf-8",
    )
    print(f"\n{matched_url_count} of {len(candidates)} candidates got a real DOI/article URL from the Scholar cache.")
    print(f"Wrote {len(candidates)} candidates to {REVIEW_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
