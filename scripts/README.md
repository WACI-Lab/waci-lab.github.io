# Publications & team-stats tooling

## Current pipeline (CV-based)

Google Scholar access from this machine has been rate-limit-blocked for a
long time, so the CV-based scripts below are the primary way to keep
`_data/publications.yml` and `_data/team.yml` up to date — not Scholar.
(`sync_publications.py`, further down, is kept only as a legacy fallback.)

### `cv_to_publications.py` — pull new papers from the CV

```bash
python scripts/cv_to_publications.py --cv PATH
# or: set WACI_CV_PATH once and omit --cv on every run
```

Parses the "JOURNAL PUBLICATIONS" section straight out of Dr. Peng's CV
`.docx`, diffs it against `_data/publications.yml` by normalized title, and
writes any not-yet-listed papers to `_data/publications_review.yml` —
**it never writes to `publications.yml` directly**. For each candidate,
hand-copy it into `publications.yml` under the right `year:` group, verify
`themes:` (a starting guess is included) and set `highlight: true` if
Dr. Peng is first author or marked `*`/`†`, matching the format of existing
entries.

### `format_authors.py` — CV-style author formatting

```bash
python scripts/format_authors.py
```

Generates an `authors_html` field on every entry in `publications.yml`
(bold for Peng, B.; bold-italic-underline for co-authors who are current or
former WACI Lab members per `_data/team.yml`) without touching the plain
`authors:` field. Re-run any time `_data/team.yml`'s roster changes, or
after adding new papers. **Read its printed review report before trusting
the output** — surname+initial collisions between a real lab member and an
unrelated external co-author are the main failure mode (see the
`COLLISION_EXCLUDE` set at the top of the script for known examples).

### `sync_citation_stats.py` — citation/paper counts

```bash
python scripts/sync_citation_stats.py --cv PATH
```

Updates `_data/team.yml`'s `stats.citations`/`stats.papers`. Tries a single
lightweight Google Scholar request first, falls back to parsing the CV's own
"Total Citations=..." line if Scholar is unreachable. Now that the repo is
on GitHub, a scheduled Action running this would hit Scholar from a
different IP range than this machine's blocked one — worth trying if you
want this automated.

### `wire_images.py` — batch-attach journal covers & highlight figures

```bash
python scripts/wire_images.py
```

Matches image files dropped into `assets/img/journals/` and
`assets/img/publications/` against `publications.yml` entries by filename
convention, and fills in `journal_covers.yml` / `highlight_image:` for you:

- Journal covers: `assets/img/journals/<journal-slug>.<ext>`, where
  `<journal-slug>` is the journal name lowercased with runs of
  non-alphanumeric characters collapsed to a hyphen (e.g. "Agricultural and
  Forest Meteorology" → `agricultural-and-forest-meteorology.jpg`).
- Highlight images: `assets/img/publications/<doi-suffix>.<ext>`, where
  `<doi-suffix>` is everything after the last `/` in the paper's DOI URL.

Files that don't follow this convention (e.g. a publisher's own asset
filename like `jame70063-fig-0003-m.jpg`) need matching by hand instead —
check the paper's DOI/journal against the image content, then add the
`highlight_image:`/`journal_covers.yml` entry directly.

### `finalize_publications.py` — one-time historical merge

Already run once, kept for reference. Retagged the original 23 curated
papers onto the current 10-label theme taxonomy and merged in the first
batch of CV-derived candidates. Not part of the regular workflow.

## Legacy: `sync_publications.py` (Google Scholar, currently blocked)

```bash
pip install -r scripts/requirements.txt
python scripts/sync_publications.py
```

Same idea as `cv_to_publications.py` but sourced from Dr. Peng's Google
Scholar profile instead of his CV — also writes to
`_data/publications_review.yml`, never directly to `publications.yml`. Kept
in case Scholar access becomes usable again (e.g. from a different network,
or a GitHub Action running from a different IP range); there is currently no
scheduled automation running this.
