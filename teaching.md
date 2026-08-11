---
layout: page
title: Teaching
eyebrow: In the classroom
description: Courses taught and mentoring philosophy.
permalink: /teaching/
---

## Courses

<table class="data-table">
  <thead><tr><th>Course</th><th>Title</th><th>Offered</th></tr></thead>
  <tbody>
    {% for c in site.data.courses %}
    <tr><td>{{ c.course }}</td><td>{{ c.title }}</td><td>{{ c.offered }}</td></tr>
    {% endfor %}
  </tbody>
</table>

## Mentoring

We mentor research scientists, postdocs, graduate students, and undergraduate interns across hydrology, agroecosystem modeling, remote sensing, and environmental data science. See the full roster on our <a href="{{ '/team/' | relative_url }}">Team</a> page.

<div class="callout">
  <h3>Prospective students</h3>
  <p style="margin-bottom:0;">We welcome graduate committee members and rotation students interested in water-agriculture-conservation research. See <a href="{{ '/hiring/' | relative_url }}">Hiring</a> for open positions, or reach out directly at <a href="mailto:{{ site.email }}">{{ site.email }}</a>.</p>
</div>
