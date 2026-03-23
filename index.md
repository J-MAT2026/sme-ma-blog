---
layout: default
title: J-MAT | 日本最大級M&Aニュース
---

# 🔥 今日の注目M&A

{% for post in site.posts limit:3 %}
<div class="hero">
  <h2><a href="{{ post.url }}">{{ post.title }}</a></h2>
  <p>{{ post.excerpt }}</p>
  <div class="meta">{{ post.date | date: "%Y-%m-%d" }}</div>
</div>
{% endfor %}
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
