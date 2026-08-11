#!/usr/bin/env python3
"""
Update _data/team.yml's stats (citations, papers) from the best available
source. Tries Google Scholar first with a single lightweight request (just
the author summary -- not the full 275-item publication list, so it's much
less likely to trip a rate-limit block than the full backfill). Falls back
to parsing the same "Total Citations=NNNN..." line already used by
cv_to_publications.py to isolate the journal-publications section, if
Scholar is unreachable.

Note: this machine's Scholar access has been blocked for a long time (see
scripts/README.md). A scheduled GitHub Action would run from a completely
different IP range and may well not be -- worth revisiting once the repo
is on GitHub with Actions wired up.

USAGE
    python scripts/sync_citation_stats.py --cv PATH
    (or set the WACI_CV_PATH environment variable instead of passing --cv;
    only needed if the Scholar fetch fails and it falls back to the CV)
"""
import argparse
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cv_to_publications import extract_cv_text, DEFAULT_CV  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TEAM_PATH = ROOT / "_data" / "team.yml"


def try_scholar(scholar_id="tkya-dMAAAAJ"):
    try:
        from scholarly import scholarly

        scholarly.set_timeout(15)
        scholarly.set_retries(1)
        author = scholarly.search_author_id(scholar_id, filled=False)
        author = scholarly.fill(author, sections=["basics"])
        citedby = author.get("citedby")
        if citedby:
            return {"citations": citedby, "hindex": author.get("hindex"), "source": "Google Scholar"}
    except Exception as e:
        print(f"Scholar fetch failed ({type(e).__name__}: {e}) -- falling back to the CV.")
    return None


def try_cv(cv_path):
    lines = extract_cv_text(Path(cv_path))
    text = "\n".join(lines)
    m = re.search(
        r"Total Journal Papers=(\d+).*?Total Citations=(\d+),?\s*h-index=(\d+)",
        text,
        re.DOTALL,
    )
    if not m:
        return None
    return {
        "papers": int(m.group(1)),
        "citations": int(m.group(2)),
        "hindex": int(m.group(3)),
        "source": "CV",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cv", default=DEFAULT_CV)
    args = ap.parse_args()

    result = try_scholar()
    if result is None:
        if not args.cv:
            sys.exit(
                "Scholar fetch failed and no CV path given. Pass --cv PATH or "
                "set the WACI_CV_PATH environment variable."
            )
        result = try_cv(args.cv)
    if result is None:
        sys.exit("Could not get citation stats from either Scholar or the CV.")

    print(f"Source: {result['source']}")
    print(f"Citations: {result['citations']}" + (f"  (h-index {result['hindex']})" if result.get("hindex") else ""))
    if result.get("papers"):
        print(f"Papers: {result['papers']}")

    team = yaml.safe_load(TEAM_PATH.read_text(encoding="utf-8"))
    old_citations = team["stats"]["citations"]
    team["stats"]["citations"] = str(result["citations"])
    if result.get("papers"):
        team["stats"]["papers"] = str(result["papers"])

    # Preserve the file's existing structure/comments as much as possible --
    # team.yml has a hand-written comment header and per-person layout that
    # a full yaml.dump would flatten, so just patch the two stats lines with
    # a targeted text replace instead of a full re-dump.
    text = TEAM_PATH.read_text(encoding="utf-8")
    text = text.replace(f'citations: "{old_citations}"', f'citations: "{result["citations"]}"', 1)
    if result.get("papers"):
        text = re.sub(r'papers: "[^"]*"', f'papers: "{result["papers"]}"', text, count=1)
    TEAM_PATH.write_text(text, encoding="utf-8")
    print(f"\nUpdated _data/team.yml: citations {old_citations} -> {result['citations']}")


if __name__ == "__main__":
    main()
