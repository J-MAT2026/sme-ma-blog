---
layout: default
title: J-MAT | 日本最大級M&Aニュース
---

{% comment %}
  同日の朝刊・夕刊を抽出。最新7件のpostsからslotで分類。
{% endcomment %}

{% assign today_posts = "" | split: "" %}
{% assign latest_date = "" %}
{% for p in site.posts limit:50 %}
  {% if p.featured %}
    {% assign latest_date = p.date | date: "%Y-%m-%d" %}
    {% break %}
  {% endif %}
{% endfor %}

{% for p in site.posts limit:50 %}
  {% assign p_date = p.date | date: "%Y-%m-%d" %}
  {% if p_date == latest_date and p.featured %}
    {% assign today_posts = today_posts | push: p %}
  {% endif %}
{% endfor %}

{% comment %} 朝刊・夕刊を分離 {% endcomment %}
{% assign morning_post = nil %}
{% assign evening_post = nil %}
{% for p in today_posts %}
  {% if p.slot == "morning" and morning_post == nil %}
    {% assign morning_post = p %}
  {% elsif p.slot == "evening" and evening_post == nil %}
    {% assign evening_post = p %}
  {% endif %}
{% endfor %}

<div class="top-layout">

  <!-- 左：ピックアップ（朝刊＋夕刊） -->
  <div class="featured-section">

    {% comment %} ===== 夕刊（上段） ===== {% endcomment %}
    {% if evening_post %}
    <h2 class="section-title">Today's Featured — 夕刊</h2>
    {% assign featured = evening_post.featured %}

    {% assign f = featured[0] %}
    <div class="featured-card featured-card--main">
      <a href="{% if f.link contains 'http' %}{{ f.link }}{% else %}{{ site.baseurl }}{{ f.link }}{% endif %}" class="featured-card-link">
        <div class="featured-img-wrap {% unless f.image and f.image != '' %}featured-img-fallback{% endunless %}">
          {% if f.image and f.image != "" %}
          <img src="{{ f.image }}" alt="{{ f.title }}" class="featured-img" loading="lazy" onerror="this.style.display='none'; this.parentNode.classList.add('featured-img-fallback');">
          {% endif %}
          <div class="featured-cat">{{ f.industry }}</div>
          <div class="featured-rank">#1</div>
        </div>
        <div class="featured-body">
          <div class="featured-title">{{ f.title }}</div>
          {% if f.analysis %}<div class="featured-analysis">📊 {{ f.analysis | truncate: 160 }}</div>{% endif %}
          {% if f.chart_pl != "" %}<div class="featured-charts"><img src="{{ site.baseurl }}{{ f.chart_pl }}" alt="PL推移" class="chart-img" loading="lazy"></div>{% endif %}
          <div class="featured-press-link">▶ 詳細分析を読む →</div>
        </div>
      </a>
    </div>
    <div class="featured-grid">
      {% for f in featured %}{% if f.rank >= 2 %}
      <div class="featured-card featured-card--sub">
        <a href="{% if f.link contains 'http' %}{{ f.link }}{% else %}{{ site.baseurl }}{{ f.link }}{% endif %}">
          <div class="featured-img-wrap {% unless f.image and f.image != '' %}featured-img-fallback{% endunless %}">
            {% if f.image and f.image != "" %}<img src="{{ f.image }}" alt="{{ f.title }}" class="featured-img" loading="lazy" onerror="this.style.display='none'; this.parentNode.classList.add('featured-img-fallback');">{% endif %}
            <div class="featured-cat">{{ f.industry }}</div>
            <div class="featured-rank">#{{ f.rank }}</div>
          </div>
          <div class="featured-body">
            <div class="featured-title">{{ f.title }}</div>
            {% if f.analysis %}<div class="featured-analysis-mini">{{ f.analysis | truncate: 80 }}</div>{% endif %}
          </div>
        </a>
      </div>
      {% endif %}{% endfor %}
    </div>
    {% endif %}

    {% comment %} ===== 朝刊（下段） ===== {% endcomment %}
    {% if morning_post %}
    <h2 class="section-title" {% if evening_post %}style="margin-top:48px;"{% endif %}>
      {% if evening_post %}Today's Featured — 朝刊{% else %}Today's Featured{% endif %}
    </h2>
    {% assign featured = morning_post.featured %}

    {% assign f = featured[0] %}
    <div class="featured-card featured-card--main">
      <a href="{% if f.link contains 'http' %}{{ f.link }}{% else %}{{ site.baseurl }}{{ f.link }}{% endif %}" class="featured-card-link">
        <div class="featured-img-wrap {% unless f.image and f.image != '' %}featured-img-fallback{% endunless %}">
          {% if f.image and f.image != "" %}
          <img src="{{ f.image }}" alt="{{ f.title }}" class="featured-img" loading="lazy" onerror="this.style.display='none'; this.parentNode.classList.add('featured-img-fallback');">
          {% endif %}
          <div class="featured-cat">{{ f.industry }}</div>
          <div class="featured-rank">#1</div>
        </div>
        <div class="featured-body">
          <div class="featured-title">{{ f.title }}</div>
          {% if f.analysis %}<div class="featured-analysis">📊 {{ f.analysis | truncate: 160 }}</div>{% endif %}
          {% if f.chart_pl != "" %}<div class="featured-charts"><img src="{{ site.baseurl }}{{ f.chart_pl }}" alt="PL推移" class="chart-img" loading="lazy"></div>{% endif %}
          <div class="featured-press-link">▶ 詳細分析を読む →</div>
        </div>
      </a>
    </div>
    <div class="featured-grid">
      {% for f in featured %}{% if f.rank >= 2 %}
      <div class="featured-card featured-card--sub">
        <a href="{% if f.link contains 'http' %}{{ f.link }}{% else %}{{ site.baseurl }}{{ f.link }}{% endif %}">
          <div class="featured-img-wrap {% unless f.image and f.image != '' %}featured-img-fallback{% endunless %}">
            {% if f.image and f.image != "" %}<img src="{{ f.image }}" alt="{{ f.title }}" class="featured-img" loading="lazy" onerror="this.style.display='none'; this.parentNode.classList.add('featured-img-fallback');">{% endif %}
            <div class="featured-cat">{{ f.industry }}</div>
            <div class="featured-rank">#{{ f.rank }}</div>
          </div>
          <div class="featured-body">
            <div class="featured-title">{{ f.title }}</div>
            {% if f.analysis %}<div class="featured-analysis-mini">{{ f.analysis | truncate: 80 }}</div>{% endif %}
          </div>
        </a>
      </div>
      {% endif %}{% endfor %}
    </div>
    {% endif %}

    {% unless morning_post or evening_post %}
      <h2 class="section-title">Today's Featured</h2>
      <p class="no-posts">本日のピックアップを準備中です</p>
    {% endunless %}

  </div>

  <!-- 右：日付別ヘッドライン -->
  <div class="headline-section">
    <h2 class="section-title">Headlines</h2>

    {% assign headline_count = 0 %}
    {% for post in site.posts limit:50 %}
    {% unless post.headlines %}{% continue %}{% endunless %}
    {% assign headline_count = headline_count | plus: 1 %}
    {% if headline_count > 7 %}{% break %}{% endif %}
    <div class="headline-group">
      <button class="headline-group-btn {% if forloop.first %}active{% endif %}" onclick="toggleGroup(this)">
        <span class="headline-group-date">{{ post.date | date: "%Y年%m月%d日" }}
          {% if post.slot == "morning" %}朝刊{% else %}夕刊{% endif %}
        </span>
        <span class="headline-group-count">{{ post.headlines | size }}件</span>
        <span class="headline-group-arrow">▾</span>
      </button>
      <div class="headline-list {% if forloop.first %}open{% endif %}">
        {% for h in post.headlines %}
        <a href="{{ h.link }}" class="headline-item" target="_blank" rel="noopener">
          <span class="headline-cat">{{ h.industry | truncate: 14, "" }}</span>
          <span class="headline-text">{{ h.title }}</span>
          <span class="headline-arrow">↗</span>
        </a>
        {% endfor %}
      </div>
    </div>
    {% endfor %}

  </div>

</div>

<script>
function toggleGroup(btn) {
  const list = btn.nextElementSibling;
  const isOpen = list.classList.contains('open');
  document.querySelectorAll('.headline-list').forEach(el => el.classList.remove('open'));
  document.querySelectorAll('.headline-group-btn').forEach(el => el.classList.remove('active'));
  if (!isOpen) { list.classList.add('open'); btn.classList.add('active'); }
}
</script>
