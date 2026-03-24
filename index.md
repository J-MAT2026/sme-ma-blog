---
layout: default
title: J-MAT | 日本最大級M&Aニュース
---

{% assign latest = site.posts.first %}

<div class="top-layout">

  <!-- 左：ピックアップ5件 -->
  <div class="featured-section">
    <h2 class="section-title">Today's Featured</h2>

    {% if latest and latest.featured %}
      {% assign featured = latest.featured %}

      <!-- 1位：大カード -->
      {% assign f = featured[0] %}
      <div class="featured-card featured-card--main">
        <a href="{{ f.link }}" target="_blank" rel="noopener">
          <div class="featured-img-wrap">
            <img src="{{ f.image }}" alt="{{ f.title }}" class="featured-img" loading="lazy"
                 onerror="this.src='https://picsum.photos/seed/10/800/450'">
            <div class="featured-cat">{{ f.category }}</div>
            <div class="featured-rank">#1</div>
          </div>
          <div class="featured-body">
            <div class="featured-title">{{ f.title }}</div>
            <div class="featured-summary">{{ f.summary }}</div>
          </div>
        </a>
      </div>

      <!-- 2〜5位：小カード2列 -->
      <div class="featured-grid">
        {% for f in featured %}
          {% if f.rank >= 2 %}
          <div class="featured-card featured-card--sub">
            <a href="{{ f.link }}" target="_blank" rel="noopener">
              <div class="featured-img-wrap">
                <img src="{{ f.image }}" alt="{{ f.title }}" class="featured-img" loading="lazy"
                     onerror="this.src='https://picsum.photos/seed/{{ f.rank }}0/800/450'">
                <div class="featured-cat">{{ f.category }}</div>
                <div class="featured-rank">#{{ f.rank }}</div>
              </div>
              <div class="featured-body">
                <div class="featured-title">{{ f.title }}</div>
              </div>
            </a>
          </div>
          {% endif %}
        {% endfor %}
      </div>

    {% else %}
      <p class="no-posts">本日のピックアップを準備中です</p>
    {% endif %}
  </div>

  <!-- 右：全ヘッドライン -->
  <div class="headline-section">
    <h2 class="section-title">Headlines</h2>

    <div class="headline-date">
      {% if latest %}{{ latest.date | date: "%Y年%m月%d日" }}{% endif %}
    </div>

    <div class="headline-list">
      {% if latest %}
        {% assign content_lines = latest.content | split: "\n" %}
        {% assign in_headlines = false %}
        {% assign count = 0 %}
        {% for line in content_lines %}
          {% if line contains "本日の全M&Aヘッドライン" %}
            {% assign in_headlines = true %}
          {% elsif in_headlines and line contains ". [" and count < 20 %}
            {% assign count = count | plus: 1 %}
            {% assign parts = line | split: ". [" %}
            {% assign rest = parts[1] | split: "](" %}
            {% assign hl_title = rest[0] %}
            {% assign hl_url = rest[1] | split: ")" | first %}
            <a href="{{ hl_url }}" class="headline-item" target="_blank" rel="noopener">
              <span class="headline-num">{{ count }}</span>
              <span class="headline-text">{{ hl_title }}</span>
              <span class="headline-arrow">↗</span>
            </a>
          {% endif %}
        {% endfor %}
      {% else %}
        <p class="no-posts">ヘッドラインを準備中です</p>
      {% endif %}
    </div>

    <!-- 過去の記事 -->
    <div class="archive-section">
      <div class="archive-title">過去の記事</div>
      {% for post in site.posts limit:5 %}
      <a href="{{ site.baseurl }}{{ post.url }}" class="archive-item">
        <span class="archive-date">{{ post.date | date: "%m/%d" }}</span>
        <span class="archive-text">{{ post.title | truncate: 30 }}</span>
      </a>
      {% endfor %}
    </div>
  </div>

</div>
