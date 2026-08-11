#!/usr/bin/env python3
"""
Generate a CV-matching `authors_html` field for every entry in
_data/publications.yml, without disturbing anything else in the file.

CV convention being replicated:
    * Corresponding author, dagger Equal contribution (already present as
      literal characters in the `authors:` string -- untouched here).
    * Peng, B. is ALWAYS bold, regardless of his own */dagger marks.
    * Any co-author who is a current or former WACI Lab member (per
      _data/team.yml) is bold + italic + underline.

WHY A SEPARATE FIELD, AND WHY PYTHON NOT LIQUID
    Liquid has no regex, so name-matching free-text author strings can't
    happen at render time. This script precomputes the styled HTML once
    and writes it to a new `authors_html:` key -- the existing `authors:`
    plain-text field is left completely untouched (other code, or future
    features, may still want the plain string).

HOW IT FINDS NAMES
    A single regex finds every "Lastname(s), Initials[marks]" occurrence
    *anywhere* in the authors string -- it does not require parsing the
    whole string, so irregular entries like
        "Kimball, B. et al (including Peng, B.)."
    still work correctly: only the two clean name tokens get matched, the
    surrounding prose is left alone.

HOW IT WRITES THE RESULT
    A full yaml.dump() round-trip would lose this file's hand-formatting
    (quoting style, comments). Instead: parse with yaml.safe_load() to
    compute authors_html per entry in document order, then do a purely
    positional raw-text edit -- split the file on every "  - title:" line
    marker (one per entry, in the same order as the parsed data) and
    insert an "    authors_html: ...\n" line right before that chunk's
    "    journal:" line, which every entry has exactly once.

USAGE
    python scripts/format_authors.py
"""
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PUBLICATIONS_PATH = ROOT / "_data" / "publications.yml"
TEAM_PATH = ROOT / "_data" / "team.yml"

NAME_RE = re.compile(
    r"([A-Z][\w'’\-]*(?:\s[A-Z][\w'’\-]*)*),\s*((?:[A-Z]\.){1,4}[*†]*)"
)


# (lastname_lower, first_initial_lower) pairs excluded from auto-matching
# despite being real team members: their surname+initial collides with a
# long-time external co-author across a decade of older papers pre-dating
# these people's actual time in the lab (confirmed by manual spot-check --
# see the review report). "Wang, S." in particular matches ~15 papers
# spanning 2015-2026, almost certainly a different "S. Wang" from Kaiyu
# Guan's broader group, not current student Shijia Wang. "Xu, S." and
# "Chen, X." only ever matched pre-2026 papers, before those two
# undergrad interns' 2026 start dates per their own `role:` field.
COLLISION_EXCLUDE = {
    ("wang", "s"),  # Shijia Wang -- collides with an older external "S. Wang"
    ("xu", "s"),    # Shuwan Xu -- 2026 intern, matched only pre-2026 papers
    ("chen", "x"),  # Xinghan Chen -- 2026 intern, matched only pre-2026 papers
}


def build_team_lookup(team):
    """{(lastname_lower, first_initial_lower): display_name}, from every
    current/alumni sub-list. The PI is intentionally excluded -- he's
    handled separately (bold-only, not bold-italic-underline)."""
    lookup = {}
    for bucket in ("current", "alumni"):
        for _, people in (team.get(bucket) or {}).items():
            for person in people or []:
                name = re.sub(r"^Dr\.\s+", "", person["name"]).strip()
                parts = name.split()
                if len(parts) < 2:
                    continue
                last = parts[-1]
                first_initial = parts[0][0]
                key = (last.lower(), first_initial.lower())
                if key in COLLISION_EXCLUDE:
                    continue
                lookup[key] = person["name"]
    return lookup


def make_styler(team_lookup, matches_report):
    def style_token(m):
        lastname, marks = m.group(1), m.group(2)
        full = m.group(0)
        initial = marks[0] if marks else ""
        if lastname.lower() == "peng" and initial.lower() == "b":
            return f"<strong>{full}</strong>"
        key = (lastname.lower(), initial.lower())
        if key in team_lookup:
            matches_report.append((full, team_lookup[key]))
            return f"<strong><em><u>{full}</u></em></strong>"
        return full

    return style_token


def yaml_quote(s):
    # Reuse yaml's own scalar quoting so unicode (dagger, accented names)
    # and any stray quote/backslash characters are escaped correctly.
    return yaml.dump(s, allow_unicode=True, default_style='"').strip()


def main():
    team = yaml.safe_load(TEAM_PATH.read_text(encoding="utf-8"))
    team_lookup = build_team_lookup(team)
    print(f"Loaded {len(team_lookup)} lab-member name keys from team.yml.\n")

    data = yaml.safe_load(PUBLICATIONS_PATH.read_text(encoding="utf-8"))
    flat_entries = [item for group in data for item in group["items"]]

    per_entry_html = []
    no_match_titles = []
    lab_member_hits = []  # (title, [(matched_text, person_name), ...])

    for entry in flat_entries:
        matches_report = []
        styler = make_styler(team_lookup, matches_report)
        html = NAME_RE.sub(styler, entry["authors"])
        per_entry_html.append(html)
        if "<strong>" not in html:
            no_match_titles.append(entry["title"])
        if matches_report:
            lab_member_hits.append((entry["title"], matches_report))

    raw = PUBLICATIONS_PATH.read_text(encoding="utf-8")
    chunks = re.split(r"(?=^  - title:)", raw, flags=re.MULTILINE)
    # chunks[0] is the file header before the first entry.
    if len(chunks) - 1 != len(flat_entries):
        sys.exit(
            f"Entry-count mismatch: found {len(flat_entries)} entries via YAML "
            f"but {len(chunks) - 1} '  - title:' chunks in the raw text. "
            "Aborting without writing anything -- check publications.yml formatting."
        )

    out = [chunks[0]]
    for chunk, html in zip(chunks[1:], per_entry_html):
        line = f"    authors_html: {yaml_quote(html)}\n"
        if "\n    journal:" not in chunk:
            sys.exit(f"Couldn't find a 'journal:' line in a chunk starting: {chunk[:80]!r}")
        new_chunk = chunk.replace("\n    journal:", "\n" + line + "    journal:", 1)
        out.append(new_chunk)

    PUBLICATIONS_PATH.write_text("".join(out), encoding="utf-8")
    print(f"Wrote authors_html to all {len(flat_entries)} entries in {PUBLICATIONS_PATH.relative_to(ROOT)}.\n")

    print(f"=== Entries with a lab-member (bold-italic-underline) match: {len(lab_member_hits)} ===")
    for title, matches in lab_member_hits:
        matched_str = "; ".join(f"{text!r} -> {person}" for text, person in matches)
        print(f"  {title[:70]}\n      {matched_str}")

    print(f"\n=== Entries where NO 'Peng, B.' bold match was found (needs manual check): {len(no_match_titles)} ===")
    for title in no_match_titles:
        print(f"  {title[:90]}")


if __name__ == "__main__":
    main()
