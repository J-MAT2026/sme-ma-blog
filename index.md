---
layout: default
title: J-MAT | 日本最大級M&Aニュース
---

# 🔥 今日の注目M&A

{% assign first = site.posts.first %}

<div class="hero">
  <h2><a href="{{ first.url }}">{{ first.title }}</a></h2>
  <p class="meta">{{ first.date | date: "%Y-%m-%d" }}</p>
</div>

---

# 📰 速報

{% for post in site.posts limit:5 %}
<div class="card">
  <a href="{{ post.url }}">{{ post.title }}</a>
  <div class="meta">{{ post.date | date: "%Y-%m-%d" }}</div>
</div>
{% endfor %}

---

# 📊 最新ニュース

{% for post in site.posts offset:5 limit:20 %}
<div class="card">
  <a href="{{ post.url }}">{{ post.title }}</a>
  <div class="meta">{{ post.date | date: "%Y-%m-%d" }}</div>
</div>
{% endfor %}
