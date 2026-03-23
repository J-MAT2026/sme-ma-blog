---
layout: default
title: J-MAT | 日本最大級M&Aニュース
---

<h2 class="section-title">🔥 今日の注目M&A</h2>

<div class="posts">
{% for post in site.posts limit:6 %}
  <div class="post-card">
    <a href="{{ post.url }}">
      <div class="post-title">{{ post.title }}</div>
      <div class="post-summary">{{ post.summary }}</div>
      <div class="post-date">{{ post.date | date: "%Y-%m-%d" }}</div>
    </a>
  </div>
{% endfor %}
</div>
