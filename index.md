---
layout: default
title: J-MAT | 日本最大級M&Aニュース
---

🔥 今日の注目M&A

{% for post in site.posts limit:5 %}
<div class="card">
  <h3><a href="{{ post.url }}">{{ post.title }}</a></h3>
  <p class="meta">{{ post.date | date: "%Y-%m-%d" }}</p>
</div>
{% endfor %}
