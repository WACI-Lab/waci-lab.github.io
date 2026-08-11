#!/usr/bin/env python3
"""
One-time merge: retag the 23 existing curated publications onto the new
10-label theme taxonomy, then merge in the 78 CV-derived candidates from
_data/publications_review.yml, writing the result to _data/publications.yml.

This is a first pass -- authors/journal/url/highlight/themes on the merged-in
entries should keep being reviewed and corrected over time (many still point
at a Google Scholar *search* link instead of a real DOI, flagged via
url_note in the review file this reads from).
"""
import re
import unicodedata
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PUBLICATIONS_PATH = ROOT / "_data" / "publications.yml"
REVIEW_PATH = ROOT / "_data" / "publications_review.yml"

# Hand-reviewed retag of the 23 already-curated papers onto the new taxonomy
# (title -> new themes list). Matched by normalized title.
RETAG = {
    "soil oxygen dynamics a key mediator of tile drainage impacts on coupled hydrological biogeochemical and crop systems": ["Hydrology", "Crop and soil"],
    "detecting the onset of rice field inundation in the lower mississippi river basin via harmonized landsat sentinel2 hls satellite time series": ["Remote sensing", "Hydrology"],
    "embracing large language model llm technologies in hydrology research": ["Hydrology", "AI"],
    "a unified framework to reconcile different approaches of modeling transpiration response to water stress plant hydraulics supplydemand balance and empirical soil water stress function": ["Crop and soil", "Modeling"],
    "a modeldata fusion approach for quantifying the carbon budget in cotton agroecosystems across the united states": ["Crop and soil", "Modeling"],
    "transfer learning for improved crop yield predictions in a crossscale pathway a case study for brazilian national soybean": ["Crop and soil", "AI"],
    "withinfield soil moisture variability and temporal stability of agricultural fields in the us midwest": ["Hydrology", "Measurement"],
    "knowledgebased artificial intelligence significantly improved agroecosystem carbon cycle quantification": ["AI", "Crop and soil"],
    "a scalable framework for quantifying fieldlevel agricultural carbon outcomes": ["Modeling", "Crop and soil"],
    "a flexible and efficient knowledgeguided machine learning data assimilation kgmlda framework for agroecosystem prediction in the us midwest": ["AI", "Modeling"],
    "improved quantification of cover crop biomass and ecosystem services through remote sensingbased modeldata fusion": ["Remote sensing", "Conservation"],
    "knowns uncertainties and challenges in agrivoltaics to sustainably intensify energy and food production": ["Land management", "Conservation"],
    "assessing longterm impacts of cover crops on soil organic carbon in the central us midwestern agroecosystems": ["Crop and soil", "Conservation"],
    "silver lining to a climate crisis in multiple prospects for alleviating crop waterlogging under future climates": ["Crop and soil", "Earth system"],
    "harmonizing climatesmart and sustainable agriculture": ["Land management", "Conservation"],
    "sustainable irrigation based on coregulation of soil water supply and atmospheric evaporative demand": ["Hydrology", "Land management"],
    "a generic risk assessment framework to evaluate historical and future climateinduced risk for rainfed corn and soybean yield in the us midwest": ["Crop and soil", "Earth system"],
    "quantifying carbon budget crop yields and their responses to environmental variability using the ecosys model for us midwestern agroecosystems": ["Modeling", "Crop and soil"],
    "towards a multiscale crop modelling framework for climate change adaptation assessment": ["Modeling", "Earth system"],
    "benefits of seasonal climate prediction and satellite data for forecasting us maize yield": ["Remote sensing", "Crop and soil"],
    "assessing the benefit of satellitebased solarinduced chlorophyll fluorescence in crop yield prediction": ["Remote sensing", "Crop and soil"],
    "multiscale computational models can guide experimentation and targeted measurements for crop improvement": ["Modeling", "Crop and soil"],
    "improving maize growth processes in the community land model implementation and evaluation": ["Modeling", "Earth system"],
}

# Known near-duplicate: CV wording ("supply demand balance") differs from the
# site's existing entry ("supply-demand balance") enough that title matching
# missed it -- exclude explicitly so it doesn't get added twice.
EXCLUDE_TITLES = {
    "a unified framework to reconcile different approaches of modeling transpiration response to water stress plant hydraulics supply demand balance and empirical soil water stress function",
}

# Hand-fixes for the 2 entries the parser flagged with PARSE WARNING (title
# ending in "?" right before the journal name confused the splitter).
MANUAL_FIXES = {
    "how does uncertainty of soil organic carbon stock affect the calculation of carbon budgets and soil carbon credits for croplands in the us midwest": {
        "title": "How does uncertainty of soil organic carbon stock affect the calculation of carbon budgets and soil carbon credits for croplands in the US Midwest?",
        "journal": "Geoderma",
    },
    "are we approaching a water ceiling to maize yields in the united states ecosphere": {
        "title": "Are We Approaching a Water Ceiling to Maize Yields in the United States?",
        "journal": "Ecosphere",
    },
}


def normalize_title(title):
    t = unicodedata.normalize("NFKD", title or "")
    t = re.sub(r"[^\w\s]", "", t).lower()
    return re.sub(r"\s+", " ", t).strip()


def main():
    existing = yaml.safe_load(PUBLICATIONS_PATH.read_text(encoding="utf-8")) or []
    review = yaml.safe_load(REVIEW_PATH.read_text(encoding="utf-8")) or []

    retagged = 0
    for group in existing:
        for item in group["items"]:
            norm = normalize_title(item["title"])
            if norm in RETAG:
                item["themes"] = RETAG[norm]
                retagged += 1
            else:
                print(f"WARNING: no retag found for existing paper: {item['title'][:70]}")

    by_year = {g["year"]: list(g["items"]) for g in existing}

    added = 0
    skipped = 0
    for group in review:
        for item in group["items"]:
            norm = normalize_title(item["title"])
            if norm in EXCLUDE_TITLES:
                skipped += 1
                continue

            fix = MANUAL_FIXES.get(norm)
            title = fix["title"] if fix else item["title"]
            journal = fix["journal"] if fix else item["journal"]

            entry = {
                "title": title,
                "authors": item["authors"],
                "journal": journal,
                "url": item["url"],
            }
            if item.get("highlight"):
                entry["highlight"] = True
            entry["themes"] = item.get("themes_suggested") or []
            if "NO DOI FOUND" in item.get("url_note", ""):
                entry["todo"] = "replace with real DOI"

            by_year.setdefault(group["year"], []).append(entry)
            added += 1

    merged = [{"year": y, "items": by_year[y]} for y in sorted(by_year, reverse=True)]

    PUBLICATIONS_PATH.write_text(
        yaml.dump(merged, allow_unicode=True, sort_keys=False, width=100),
        encoding="utf-8",
    )

    total = sum(len(g["items"]) for g in merged)
    print(f"Retagged {retagged} existing papers onto the new taxonomy.")
    print(f"Added {added} new papers from the CV ({skipped} skipped as duplicate).")
    print(f"publications.yml now has {total} total papers across {len(merged)} years.")


if __name__ == "__main__":
    main()
