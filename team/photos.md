---
layout: page
title: We as A Team
eyebrow: Who we are
description: Group photos of the WACI Lab at conferences, field trips, and lab gatherings.
permalink: /team/photos/
wide: true
---

{% include team-stats-subnav.html %}

<div class="team-photo-grid">
  {% for p in site.data.team_photos %}
  <figure class="team-photo-card">
    <img src="{{ p.image | relative_url }}" alt="{{ p.caption }}">
    <figcaption>
      <span class="caption-text">{{ p.caption }}</span>
      {% if p.date %}<span class="caption-date">{{ p.date }}</span>{% endif %}
    </figcaption>
  </figure>
  {% endfor %}
</div>
