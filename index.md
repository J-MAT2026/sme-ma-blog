# SME M&A News

このサイトは毎日自動更新される  
中小企業M&Aニュースサイトです。

## 最新記事

{% for post in site.posts limit:10 %}
- [{{ post.title }}]({{ post.url }})
{% endfor %}
