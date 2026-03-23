<p style="text-align:center; color:#666;">
日本最大級の中小企業M&Aニュースサイト。<br>
買収・事業承継・資本提携の最新情報を毎日配信。
</p>
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
