---
layout: default
title: J-MAT | Japan M&A Times
---

<div style="text-align:center; padding:40px 20px;">
  <img src="/assets/logo.png" width="200">
  <h1>J-MAT</h1>
  <p>Japan M&A Times</p>
  <p>日本最大級の中小企業M&Aニュース</p>
</div>

---

## 🔥 今日の注目M&A

{% for post in site.posts limit:3 %}
- **[{{ post.title }}]({{ post.url }})**
  - {{ post.summary }}
{% endfor %}

---

## 📰 最新ニュース

{% for post in site.posts limit:30 %}
### [{{ post.title }}]({{ post.url }})

{{ post.summary }}

---
{% endfor %}
