---
layout: default
title: J-MAT | 日本最大級M&Aニュース
---

# 🔥 今日の注目M&A

{% for post in site.posts limit:1 %}
## [{{ post.title }}]({{ post.url }})
{% endfor %}

---

# 📰 最新ニュース

{% for post in site.posts limit:10 %}
- [{{ post.title }}]({{ post.url }})
{% endfor %}
