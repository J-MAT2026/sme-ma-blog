---
layout: default
title: J-MAT | 日本最大級M&Aニュース
---

<h2 class="section-title">🔥 今日の注目M&A</h2>

<div class="posts">
{% if site.posts.size > 0 %}
  {% for post in site.posts limit:6 %}
  <div class="post-card">
    <a href="{{ site.baseurl }}{{ post.url }}">
      <div class="post-tag">M&Aニュース</div>
      <div class="post-title">{{ post.title }}</div>
      <div class="post-summary">
        {% if post.summary %}
          {{ post.summary | truncate: 100 }}
        {% else %}
          {{ post.excerpt | strip_html | truncate: 100 }}
        {% endif %}
      </div>
      <div class="post-date">📅 {{ post.date | date: "%Y年%m月%d日" }}</div>
    </a>
  </div>
  {% endfor %}
{% else %}
  <p class="no-posts">現在ニュースを準備中です。しばらくお待ちください。</p>
{% endif %}
</div>
