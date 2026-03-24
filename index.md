---
layout: default
title: J-MAT | 日本最大級M&Aニュース
---

<h2 class="section-title">Today's M&A</h2>

<div class="posts">
{% if site.posts.size > 0 %}
  {% for post in site.posts limit:6 %}
  <div class="post-card">
    <a href="{{ site.baseurl }}{{ post.url }}">
      <div class="post-tag">M&A News</div>
      <div class="post-title">{{ post.title }}</div>
      <div class="post-summary">
        {% if post.summary %}
          {{ post.summary | truncate: 100 }}
        {% else %}
          {{ post.excerpt | strip_html | truncate: 100 }}
        {% endif %}
      </div>
      <div class="post-footer-row">
        <div class="post-date">{{ post.date | date: "%Y.%m.%d" }}</div>
        <div class="post-arrow">→</div>
      </div>
    </a>
  </div>
  {% endfor %}
{% else %}
  <p class="no-posts">Preparing Today's News</p>
{% endif %}
</div>
