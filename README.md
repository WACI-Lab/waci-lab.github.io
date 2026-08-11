# WACI Lab website

Jekyll source for the Water, Agriculture, and Conservation Innovation Lab
website (Dr. Bin Peng, Department of Crop Sciences, UIUC).

## Structure

```
_config.yml         site settings + nav structure
_data/
  team.yml           PI, postdocs, students, alumni
  publications.yml    bibliography, grouped by year
_layouts/            page templates (default, page, news-item)
_includes/           nav, footer, head, contour SVG motif
_news/               news collection (one file per post)
assets/css/main.css  full design system (tokens, components)
research/            Research overview, Themes, Projects, Publications
resources/           Resources overview, Datasets, Models
index.html           Home
team.md, teaching.md, extension-outreach.md, hiring.md, news.md
```

## Run locally

```bash
bundle install
bundle exec jekyll serve
```

Visit `http://localhost:4000`.

## Deploy to GitHub Pages (waci-Lab org)

1. Create a repository under the org, e.g. `waci-Lab/waci-Lab.github.io`
   (an org/user-named repo like this serves at the bare
   `https://waci-lab.github.io` domain with no path prefix — recommended).
   If you'd rather use a project repo (e.g. `waci-Lab/lab-website`), it will
   serve at `https://waci-lab.github.io/lab-website/` — set `baseurl:
   "/lab-website"` in `_config.yml` in that case.
2. Push this folder as the repo's contents:
   ```bash
   git init
   git add .
   git commit -m "Initial site"
   git branch -M main
   git remote add origin https://github.com/waci-Lab/waci-Lab.github.io.git
   git push -u origin main
   ```
3. In the repo's **Settings → Pages**, set the source to the `main` branch
   (root). GitHub Pages will build the Jekyll site automatically — no
   GitHub Actions config needed since this only uses the plugins in the
   `github-pages` gem's allowlist (`jekyll-feed`, `jekyll-sitemap`).
4. (Optional) Custom domain: add a `CNAME` file with your domain, and set
   it in Settings → Pages. Ask your department IT to add a `CNAME` DNS
   record pointing to `waci-lab.github.io`.

## Editing content

- **Team**: edit `_data/team.yml`.
- **Publications**: add new entries at the top of `_data/publications.yml`
  under the current year (create a new year block each January).
- **News**: add a new file to `_news/`, named `YYYY-MM-DD-slug.md`, with
  `title`, `date`, and `excerpt` front matter.
- **Research Projects / Datasets / Models**: these are currently
  placeholder cards in `research/projects.md`, `resources/datasets.md`,
  and `resources/models.md` — replace with your actual funded projects,
  datasets, and model repositories.
- **Nav structure**: edit the `nav:` block in `_config.yml`.

## Design notes

Palette and type system are defined as CSS custom properties at the top of
`assets/css/main.css`. The recurring topographic contour-line motif
(`_includes/contours.html`) is the site's signature visual element, tying
back to watershed and field mapping — reuse it sparingly (hero sections
only) rather than on every page.
