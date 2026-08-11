---
layout: page
title: News
eyebrow: Lab updates
description: Publications, talks, awards, and other lab happenings.
permalink: /news/
---

{% assign all_news = site.news | sort: 'date' | reverse %}
{% for item in all_news %}
<div class="news-item">
  <div class="news-item-inner">
    {%- assign news_thumb = item.image | default: "/assets/img/waci-logo.svg" -%}
    <button type="button" class="news-item-thumb" data-lightbox-src="{{ news_thumb | relative_url }}" aria-label="Enlarge photo for {{ item.title }}">
      <img src="{{ news_thumb | relative_url }}" alt="">
    </button>
    <div class="news-item-body">
      <div class="date" style="display:flex; align-items:center; gap:10px;">
        {{ item.date | date: "%B %-d, %Y" }}
        {% include news-chip.html category=item.category %}
      </div>
      <h3><a href="{{ item.url | relative_url }}" style="color:inherit; text-decoration:none;">{{ item.title }}</a></h3>
      <p style="margin:0;">{{ item.excerpt }}</p>
    </div>
  </div>
</div>
{% endfor %}
