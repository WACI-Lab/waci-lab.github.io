---
layout: page
title: Lab Alumni
eyebrow: Who we are
description: Past researchers, students, and interns who trained with the WACI Lab.
permalink: /team/alumni/
wide: true
---

{% include team-stats-subnav.html %}

{% if site.data.team.alumni.researchers_staff.size > 0 %}
<div class="team-section-head">
  <h3>Researchers &amp; Staff</h3>
  <span class="count">{{ site.data.team.alumni.researchers_staff | size }}</span>
  <div class="rule"></div>
</div>
<div class="team-grid">
  {% for p in site.data.team.alumni.researchers_staff %}
  {% include team-card.html person=p accent="water" %}
  {% endfor %}
</div>
{% endif %}

{% if site.data.team.alumni.graduate_students.size > 0 %}
<div class="team-section-head">
  <h3>Graduate Students</h3>
  <span class="count">{{ site.data.team.alumni.graduate_students | size }}</span>
  <div class="rule"></div>
</div>
<div class="team-grid">
  {% for p in site.data.team.alumni.graduate_students %}
  {% include team-card.html person=p accent="crop" %}
  {% endfor %}
</div>
{% endif %}

{% if site.data.team.alumni.undergrads_interns.size > 0 %}
<div class="team-section-head">
  <h3>Undergraduates &amp; Interns</h3>
  <span class="count">{{ site.data.team.alumni.undergrads_interns | size }}</span>
  <div class="rule"></div>
</div>
<div class="team-grid">
  {% for p in site.data.team.alumni.undergrads_interns %}
  {% include team-card.html person=p accent="clay" %}
  {% endfor %}
</div>
{% endif %}

<div class="callout" style="margin-top: 2.4em;">
  <h3>Join us</h3>
  <p style="margin-bottom:0;">We're recruiting postdocs and graduate students across five research areas. See our <a href="{{ '/hiring/' | relative_url }}">open positions</a>.</p>
</div>
