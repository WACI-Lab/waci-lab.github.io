#!/usr/bin/env python3
"""
Wire up journal-cover and article-highlight images by matching filenames
dropped into assets/img/journals/ and assets/img/publications/ against the
publications already listed in _data/publications.yml. Turns "add N images"
into a batch drop + one script run instead of hand-editing YAML per paper.

MATCHING CONVENTION
    Journal covers:   assets/img/journals/<journal-slug>.<ext>
                       <journal-slug> = the journal name, lowercased, with
                       any run of non-alphanumeric characters collapsed to a
                       single hyphen. E.g. "Agricultural and Forest
                       Meteorology" -> agricultural-and-forest-meteorology.jpg

    Highlight images: assets/img/publications/<doi-suffix>.<ext>
                       <doi-suffix> = everything after the last "/" in the
                       paper's DOI url. E.g.
                       https://doi.org/10.5194/hess-29-6393-2025
                       -> hess-29-6393-2025.jpg
                       (Papers whose url isn't a doi.org link are skipped
                       for highlight-image matching and listed separately.)

WHAT IT DOES
    - Backs up _data/publications.yml and _data/journal_covers.yml to
      *.bak before writing anything.
    - For every journal used in publications.yml that has no registered
      cover yet, checks assets/img/journals/ for a matching slug and
      registers it in _data/journal_covers.yml.
    - For every publication without a highlight_image, checks
      assets/img/publications/ for a matching DOI-suffix file and sets
      highlight_image on that entry in _data/publications.yml.
    - Never removes or overwrites an existing image reference -- safe to
      re-run any time after dropping more files in.
    - Prints what got wired this run, plus a prioritized checklist of
      what's still missing (journals sorted by how many papers use them;
      papers sorted with `highlight: true` entries first).

USAGE
    python scripts/wire_images.py [--dry-run]

NOTE ON IMAGE SOURCING (this script only wires up files you already have)
    Journal covers: the journal's own homepage almost always shows its
    current cover -- one image covers every paper published there.
    Highlight images: check your own submission records first (many
    journals require authors to submit a "graphical abstract" at
    submission time -- if one exists you already have it); otherwise export
    a key figure from the paper's own PDF. Never pull these from a
    publisher site via scraping -- they're the publisher's copyrighted
    material and that's exactly what this project avoids doing without an
    authorized file in hand.
"""
import argparse
import re
import shutil
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PUBLICATIONS_PATH = ROOT / "_data" / "publications.yml"
JOURNAL_COVERS_PATH = ROOT / "_data" / "journal_covers.yml"
JOURNALS_DIR = ROOT / "assets" / "img" / "journals"
PUBLICATIONS_DIR = ROOT / "assets" / "img" / "publications"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def slugify(text):
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug


def doi_suffix(url):
    if not url or "doi.org/" not in url:
        return None
    return url.rstrip("/").split("/")[-1]


def scan_images(directory):
    """slug -> relative site path, for every image file in directory."""
    found = {}
    if not directory.exists():
        return found
    for f in directory.iterdir():
        if f.suffix.lower() in IMAGE_EXTS:
            found[f.stem.lower()] = f"/assets/img/{directory.name}/{f.name}"
    return found


def backup(path):
    if path.exists():
        shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    publications = yaml.safe_load(PUBLICATIONS_PATH.read_text(encoding="utf-8")) or []
    journal_covers = {}
    if JOURNAL_COVERS_PATH.exists():
        journal_covers = yaml.safe_load(JOURNAL_COVERS_PATH.read_text(encoding="utf-8")) or {}

    journal_files = scan_images(JOURNALS_DIR)
    pub_files = scan_images(PUBLICATIONS_DIR)

    # --- journal covers: count papers per journal, wire matches ---
    journal_counts = defaultdict(int)
    for group in publications:
        for item in group.get("items", []):
            j = item.get("journal")
            if j:
                journal_counts[j] += 1

    newly_wired_journals = []
    for journal, count in journal_counts.items():
        if journal in journal_covers:
            continue
        slug = slugify(journal)
        if slug in journal_files:
            journal_covers[journal] = journal_files[slug]
            newly_wired_journals.append((journal, count))

    # --- highlight images: wire matches, track misses ---
    newly_wired_pubs = []
    missing_pubs = []
    for group in publications:
        for item in group.get("items", []):
            if item.get("highlight_image"):
                continue
            suffix = doi_suffix(item.get("url", ""))
            if suffix and suffix.lower() in pub_files:
                item["highlight_image"] = pub_files[suffix.lower()]
                newly_wired_pubs.append(item["title"])
            else:
                missing_pubs.append(item)

    print(f"Journal covers on file: {len(journal_covers)}")
    print(f"Newly wired this run:   {len(newly_wired_journals)}")
    for j, c in newly_wired_journals:
        print(f"  + {j} ({c} paper{'s' if c != 1 else ''})")

    print(f"\nHighlight images newly wired this run: {len(newly_wired_pubs)}")
    for t in newly_wired_pubs:
        print(f"  + {t[:70]}")

    if not args.dry_run and (newly_wired_journals or newly_wired_pubs):
        backup(JOURNAL_COVERS_PATH)
        backup(PUBLICATIONS_PATH)
        JOURNAL_COVERS_PATH.write_text(
            "# Maps a journal's exact name (must match the `journal:` field used in\n"
            "# _data/publications.yml) to a small cover-image badge shown next to that\n"
            "# journal's name in the publications list. Populated by\n"
            "# scripts/wire_images.py -- safe to hand-edit too.\n\n"
            + yaml.dump(journal_covers, allow_unicode=True, sort_keys=False, width=100),
            encoding="utf-8",
        )
        PUBLICATIONS_PATH.write_text(
            yaml.dump(publications, allow_unicode=True, sort_keys=False, width=100),
            encoding="utf-8",
        )
        print("\nWrote changes (originals backed up to *.bak).")
    elif args.dry_run:
        print("\n(dry run -- no files written)")
    else:
        print("\nNothing new to wire.")

    # --- checklists: what's still missing, prioritized ---
    missing_journals = sorted(
        ((j, c) for j, c in journal_counts.items() if j not in journal_covers),
        key=lambda kv: kv[1],
        reverse=True,
    )
    if missing_journals:
        total_missing_papers = sum(c for _, c in missing_journals)
        print(
            f"\nStill need a cover for {len(missing_journals)} journals "
            f"(covering {total_missing_papers} papers). Highest-leverage first:"
        )
        for j, c in missing_journals[:20]:
            print(f"  [{c:>3} papers] {j}  ->  assets/img/journals/{slugify(j)}.jpg")
        if len(missing_journals) > 20:
            print(f"  ...and {len(missing_journals) - 20} more")

    if missing_pubs:
        missing_pubs.sort(key=lambda it: not it.get("highlight"))
        print(f"\nStill need a highlight image for {len(missing_pubs)} papers. Highlighted (PI corresponding/lead) papers first:")
        for it in missing_pubs[:15]:
            suffix = doi_suffix(it.get("url", "")) or "(no DOI url -- can't auto-match, name file manually)"
            flag = "*" if it.get("highlight") else " "
            print(f"  [{flag}] {it['title'][:60]}  ->  assets/img/publications/{suffix}.jpg")
        if len(missing_pubs) > 15:
            print(f"  ...and {len(missing_pubs) - 15} more")


if __name__ == "__main__":
    main()
