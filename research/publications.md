---
layout: page
title: Publications
eyebrow: Research
description: Journal publications from the WACI Lab and Dr. Peng, listed in reverse chronological order.
permalink: /research/publications/
subnav:
  - title: Overview
    url: /research/
  - title: Research Themes
    url: /research/themes/
  - title: Research Projects
    url: /research/projects/
  - title: Publications
    url: /research/publications/
---

{%- assign total_papers = 0 -%}
{%- for group in site.data.publications -%}{%- assign total_papers = total_papers | plus: group.items.size -%}{%- endfor -%}

<div class="hero-stats" style="margin: 0 0 1.6em; padding-bottom: 2em; border-bottom: 1px solid var(--surface-line);">
  <div class="stat"><strong>{{ total_papers }}</strong><span>Peer-reviewed journal papers</span></div>
  <div class="stat"><strong>{{ site.data.team.stats.citations }}</strong><span>Total citations</span></div>
</div>

{%- assign c2027 = 0 -%}{%- assign c2026 = 0 -%}{%- assign c2025 = 0 -%}{%- assign c2024 = 0 -%}{%- assign cmid = 0 -%}{%- assign cearly = 0 -%}
{%- for group in site.data.publications -%}
  {%- case group.year -%}
    {%- when 2027 -%}{%- assign c2027 = c2027 | plus: group.items.size -%}
    {%- when 2026 -%}{%- assign c2026 = c2026 | plus: group.items.size -%}
    {%- when 2025 -%}{%- assign c2025 = c2025 | plus: group.items.size -%}
    {%- when 2024 -%}{%- assign c2024 = c2024 | plus: group.items.size -%}
    {%- else -%}
      {%- if group.year >= 2017 -%}
        {%- assign cmid = cmid | plus: group.items.size -%}
      {%- else -%}
        {%- assign cearly = cearly | plus: group.items.size -%}
      {%- endif -%}
  {%- endcase -%}
{%- endfor -%}

{%- assign all_themes_raw = "" -%}
{%- for group in site.data.publications -%}
  {%- for pub in group.items -%}
    {%- for t in pub.themes -%}
      {%- assign all_themes_raw = all_themes_raw | append: t | append: "||" -%}
    {%- endfor -%}
  {%- endfor -%}
{%- endfor -%}
{%- assign all_themes = all_themes_raw | split: "||" | uniq | sort -%}

{%- assign highlight_count = 0 -%}
{%- for group in site.data.publications -%}
  {%- for pub in group.items -%}
    {%- if pub.highlight -%}{%- assign highlight_count = highlight_count | plus: 1 -%}{%- endif -%}
  {%- endfor -%}
{%- endfor -%}

<div class="filter-bar" role="group" aria-label="Filter publications by author role">
  <button type="button" class="filter-chip active" data-filter="all">All ({{ total_papers }})</button>
  {% if highlight_count > 0 %}
  <button type="button" class="filter-chip" data-filter="__highlight__">PI corresponding / lead author ({{ highlight_count }})</button>
  {% endif %}
</div>
<div class="filter-bar" role="group" aria-label="Filter publications by year">
  {% if c2027 > 0 %}<button type="button" class="filter-chip" data-filter="2027">2027 ({{ c2027 }})</button>{% endif %}
  {% if c2026 > 0 %}<button type="button" class="filter-chip" data-filter="2026">2026 ({{ c2026 }})</button>{% endif %}
  {% if c2025 > 0 %}<button type="button" class="filter-chip" data-filter="2025">2025 ({{ c2025 }})</button>{% endif %}
  {% if c2024 > 0 %}<button type="button" class="filter-chip" data-filter="2024">2024 ({{ c2024 }})</button>{% endif %}
  {% if cmid > 0 %}<button type="button" class="filter-chip" data-filter="2016-2023">2016-2023 ({{ cmid }})</button>{% endif %}
  {% if cearly > 0 %}<button type="button" class="filter-chip" data-filter="2016 and before">2016 and before ({{ cearly }})</button>{% endif %}
</div>
<div class="filter-bar" role="group" aria-label="Filter publications by topic">
  {% for t in all_themes %}
    {%- assign theme_count = 0 -%}
    {%- for group in site.data.publications -%}
      {%- for pub in group.items -%}
        {%- if pub.themes contains t -%}{%- assign theme_count = theme_count | plus: 1 -%}{%- endif -%}
      {%- endfor -%}
    {%- endfor -%}
  <button type="button" class="filter-chip" data-filter="{{ t }}">{{ t }} ({{ theme_count }})</button>
  {% endfor %}
</div>

<p style="color: var(--text-secondary); font-size: 0.92rem;">* Corresponding author &nbsp;·&nbsp; † Equal contribution &nbsp;·&nbsp; <em>bold italics underline</em> indicates group members supervised by Dr. Peng &nbsp;·&nbsp; Citation count and Dr. Peng's full publication record are on <a href="{{ site.google_scholar }}">Google Scholar</a>.</p>

{%- assign prev_bucket = "" -%}
{%- assign pub_index = 0 -%}
{% for group in site.data.publications %}
  {%- if group.year >= 2024 -%}
    {%- assign bucket = group.year | append: "" -%}
  {%- elsif group.year >= 2017 -%}
    {%- assign bucket = "2016-2023" -%}
  {%- else -%}
    {%- assign bucket = "2016 and before" -%}
  {%- endif -%}
  {%- if bucket != prev_bucket -%}
<div class="pub-year">
  <h3>{{ bucket }}</h3>
  <div class="rule"></div>
</div>
  {%- assign prev_bucket = bucket -%}
  {%- endif -%}
  {% for pub in group.items %}
    {%- assign pub_index = pub_index | plus: 1 -%}
    {%- assign display_number = total_papers | minus: pub_index | plus: 1 -%}
{% include pub-entry.html pub=pub year=group.year number=display_number bucket=bucket %}
  {% endfor %}
{% endfor %}

<script>
  (function () {
    var buttons = document.querySelectorAll('.filter-chip');
    var pubs = document.querySelectorAll('.pub');
    var yearGroups = document.querySelectorAll('.pub-year');
    var yearBuckets = ['2027', '2026', '2025', '2024', '2016-2023', '2016 and before'];

    function applyFilter(filter) {
      pubs.forEach(function (pub) {
        var show;
        if (filter === 'all') {
          show = true;
        } else if (filter === '__highlight__') {
          show = pub.getAttribute('data-highlight') === 'true';
        } else if (yearBuckets.indexOf(filter) !== -1) {
          show = pub.getAttribute('data-bucket') === filter;
        } else {
          var themes = (pub.getAttribute('data-themes') || '').split('|');
          show = themes.indexOf(filter) !== -1;
        }
        if (show) { pub.removeAttribute('hidden'); } else { pub.setAttribute('hidden', ''); }
      });
      yearGroups.forEach(function (yg) {
        var node = yg.nextElementSibling;
        var hasVisible = false;
        while (node && !node.classList.contains('pub-year')) {
          if (node.classList.contains('pub') && !node.hasAttribute('hidden')) hasVisible = true;
          node = node.nextElementSibling;
        }
        if (hasVisible) { yg.removeAttribute('hidden'); } else { yg.setAttribute('hidden', ''); }
      });
    }

    buttons.forEach(function (btn) {
      btn.addEventListener('click', function () {
        buttons.forEach(function (b) { b.classList.remove('active'); });
        btn.classList.add('active');
        applyFilter(btn.getAttribute('data-filter'));
      });
    });
  })();
</script>
