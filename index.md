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

  <!-- 右：日付別ヘッドライン -->
  <div class="headline-section">
    <h2 class="section-title">Headlines</h2>

    <!-- 日付別アコーディオン -->
    {% for post in site.posts limit:7 %}
    <div class="headline-group">
      <button class="headline-group-btn {% if forloop.first %}active{% endif %}"
              onclick="toggleGroup(this)">
        <span class="headline-group-date">{{ post.date | date: "%Y年%m月%d日" }}</span>
        <span class="headline-group-count">
          {% if post.headlines %}
            {{ post.headlines | size }}件
          {% else %}
            -
          {% endif %}
        </span>
        <span class="headline-group-arrow">▾</span>
      </button>

      <div class="headline-list {% if forloop.first %}open{% endif %}">
        {% if post.headlines %}
          {% for h in post.headlines %}
          <a href="{{ h.link }}" class="headline-item" target="_blank" rel="noopener">
            <span class="headline-cat">{{ h.category | truncate: 8, "" }}</span>
            <span class="headline-text">{{ h.title | truncate: 45 }}</span>
            <span class="headline-arrow">↗</span>
          </a>
          {% endfor %}
        {% else %}
          <div class="headline-item">
            <span class="headline-text" style="color:#aaa">データを読み込み中...</span>
          </div>
        {% endif %}
      </div>
    </div>
    {% endfor %}

  </div>

</div>

<script>
function toggleGroup(btn) {
  const list = btn.nextElementSibling;
  const isOpen = list.classList.contains('open');
  // 全部閉じる
  document.querySelectorAll('.headline-list').forEach(el => el.classList.remove('open'));
  document.querySelectorAll('.headline-group-btn').forEach(el => el.classList.remove('active'));
  // クリックしたものだけ開く（すでに開いてたら閉じたまま）
  if (!isOpen) {
    list.classList.add('open');
    btn.classList.add('active');
  }
}
</script>
