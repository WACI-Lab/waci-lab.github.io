---
layout: page
title: Team
eyebrow: Who we are
description: The WACI Lab brings together researchers across plant and soil science, hydrology, agroecosystem, biogeochemistry, remote sensing, AI, and environmental data science.
permalink: /team/
wide: true
---

<div class="team-feature">
  <div class="team-feature-avatar">
    {% if site.data.team.pi.photo %}
      <img src="{{ site.data.team.pi.photo | relative_url }}" alt="{{ site.data.team.pi.name }}">
    {% else %}
      BP
    {% endif %}
  </div>
  <div class="team-feature-body">
    <div class="eyebrow no-rule" style="margin-bottom:0.4em;">Principal Investigator</div>
    <h3>{{ site.data.team.pi.name }}</h3>
    <div class="role">{{ site.data.team.pi.role }}</div>
    <p>{{ site.data.team.pi.bio }}</p>
    <div class="links">
      {% if site.data.team.pi.links.website %}<a class="link-chip" href="{{ site.data.team.pi.links.website }}" target="_blank" rel="noopener" aria-label="Website" title="Website">{% include icon.html name="website" %}</a>{% endif %}
      {% if site.data.team.pi.links.scholar %}<a class="link-chip" href="{{ site.data.team.pi.links.scholar }}" target="_blank" rel="noopener" aria-label="Google Scholar" title="Google Scholar">{% include icon.html name="scholar" %}</a>{% endif %}
      {% if site.data.team.pi.links.orcid %}<a class="link-chip" href="{{ site.data.team.pi.links.orcid }}" target="_blank" rel="noopener" aria-label="ORCID" title="ORCID">{% include icon.html name="orcid" %}</a>{% endif %}
      {% if site.data.team.pi.links.github %}<a class="link-chip" href="{{ site.data.team.pi.links.github }}" target="_blank" rel="noopener" aria-label="GitHub" title="GitHub">{% include icon.html name="github" %}</a>{% endif %}
      {% if site.linkedin %}<a class="link-chip" href="{{ site.linkedin }}" target="_blank" rel="noopener" aria-label="LinkedIn" title="LinkedIn">{% include icon.html name="linkedin" %}</a>{% endif %}
      <a class="link-chip" href="mailto:{{ site.email }}" aria-label="Email" title="Email">{% include icon.html name="email" %}</a>
    </div>
  </div>
</div>

{% include team-stats-subnav.html %}

{% if site.data.team.current.researchers_staff.size > 0 %}
<div class="team-section-head">
  <h3>Researchers &amp; Staff</h3>
  <span class="count">{{ site.data.team.current.researchers_staff | size }}</span>
  <div class="rule"></div>
</div>
<div class="team-grid">
  {% for p in site.data.team.current.researchers_staff %}
  {% include team-card.html person=p accent="water" %}
  {% endfor %}
</div>
{% endif %}

{% if site.data.team.current.graduate_students.size > 0 %}
<div class="team-section-head">
  <h3>Graduate Students</h3>
  <span class="count">{{ site.data.team.current.graduate_students | size }}</span>
  <div class="rule"></div>
</div>
<div class="team-grid">
  {% for p in site.data.team.current.graduate_students %}
  {% include team-card.html person=p accent="crop" %}
  {% endfor %}
</div>
{% endif %}

{% if site.data.team.current.undergrads_interns.size > 0 %}
<div class="team-section-head">
  <h3>Undergraduates &amp; Interns</h3>
  <span class="count">{{ site.data.team.current.undergrads_interns | size }}</span>
  <div class="rule"></div>
</div>
<div class="team-grid">
  {% for p in site.data.team.current.undergrads_interns %}
  {% include team-card.html person=p accent="clay" %}
  {% endfor %}
</div>
{% endif %}

<div class="callout" style="margin-top: 2.4em;">
  <h3>Join us</h3>
  <p style="margin-bottom:0;">We're recruiting postdocs and graduate students across five research areas. See our <a href="{{ '/hiring/' | relative_url }}">open positions</a>.</p>
</div>
