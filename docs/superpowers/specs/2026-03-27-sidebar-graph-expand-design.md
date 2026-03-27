# Sidebar Nav + Graph Upward Expand — Design Spec

**Date:** 2026-03-27
**Goal:** 모든 페이지에 VSCode 스타일 고정 사이드바 추가. 인덱스 그래프가 위아래 모두로 확장되도록 개선.

---

## 1. 사이드바 (모든 페이지)

### 구조

현재 `<header class="container">` 제거. `<body>` 최상단에 `<aside id="sidebar">` 삽입.

```html
<aside id="sidebar">
  <div class="sidebar-icons">
    <button class="sidebar-btn" data-panel="" data-label="Home" data-href="{root}/">⌂</button>
    <button class="sidebar-btn" data-panel="about" data-label="About">◉</button>
    <button class="sidebar-btn" data-panel="blog" data-label="Blog" data-href="{root}/blog/">≡</button>
    <button class="sidebar-btn" data-panel="github" data-label="GitHub">⬡</button>
  </div>
  <div id="panel-about" class="sidebar-panel">
    <div class="panel-header">About</div>
    <p class="panel-placeholder">준비 중</p>
  </div>
  <div id="panel-github" class="sidebar-panel">
    <div class="panel-header">GitHub</div>
    <p class="panel-placeholder">준비 중</p>
  </div>
</aside>
```

- Home, Blog 버튼: `data-href` 경로로 이동 (패널 없음)
- About, GitHub 버튼: 패널 토글

### CSS

```
#sidebar {
  position: fixed; left: 0; top: 0;
  width: 48px; height: 100vh;
  background: #111111; border-right: 1px solid #1e1e1e;
  z-index: 100;
  display: flex; flex-direction: column;
}

.sidebar-btn {
  width: 48px; height: 48px;
  background: transparent; border: none;
  color: #555; font-size: 1.2rem;
  cursor: pointer;
  position: relative;
  border-left: 2px solid transparent;
  transition: color 0.15s, border-color 0.15s;
}

/* 현재 페이지 활성 표시 */
.sidebar-btn.active {
  color: #dc00c9;
  border-left-color: #dc00c9;
}

/* 호버 tooltip */
.sidebar-btn::after {
  content: attr(data-label);
  position: absolute;
  left: calc(100% + 8px); top: 50%;
  transform: translateY(-50%);
  background: #1e1e1e; color: #ccc;
  font-size: 0.7rem; white-space: nowrap;
  padding: 0.25rem 0.5rem; border-radius: 4px;
  pointer-events: none;
  opacity: 0; transition: opacity 0.15s;
}
.sidebar-btn:hover::after { opacity: 1; }

/* 패널 */
.sidebar-panel {
  position: fixed;
  left: 48px; top: 0;
  width: 220px; height: 100vh;
  background: #111111; border-right: 1px solid #1e1e1e;
  z-index: 99;
  transform: translateX(-100%);
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  overflow-y: auto;
}
.sidebar-panel.open { transform: translateX(0); }

.panel-header {
  padding: 1rem 1rem 0.5rem;
  font-size: 0.7rem; color: #dc00c9;
  text-transform: uppercase; letter-spacing: 2px;
  border-bottom: 1px solid #1e1e1e;
}
.panel-placeholder { padding: 1rem; color: #555; font-size: 0.85rem; }
```

### body offset

```css
body { padding-left: 48px; }
```

패널 오버레이 방식이므로 패널 열려도 body padding은 변하지 않음. 패널이 콘텐츠 위에 떠오름.

### JS (공유 — sidebar.js, 모든 페이지에 포함)

- `data-href` 있는 버튼: 클릭 시 해당 경로로 이동
- 패널 버튼: 클릭 시 해당 `.sidebar-panel` 토글 (`.open` 클래스)
- 패널 외부 클릭 시 닫힘
- 현재 URL 기반으로 해당 버튼에 `.active` 자동 부여

### 현재 페이지 active 판별

| 페이지 | active 버튼 |
|--------|-------------|
| `/` | Home |
| `/blog/` | Blog |
| `/posts/*/` | Blog |

### 파일 변경 목록

- `style.css` — 사이드바/패널 CSS 추가
- `sidebar.js` — 신규, 공유 JS
- `index.html` — `<header>` 제거, `<aside>` + `<script src="./sidebar.js">` 삽입
- `blog/index.html` — 동일
- `posts/_template/index.html` — 동일
- `posts/*/index.html` (9개) — 동일

---

## 2. 그래프 위쪽 확장 (index.html만)

### 현재 상태

- `<header>` 높이만큼 그래프 상단이 눌려있음
- `height: 45vh → 80vh` 확장 시 아래쪽만 커짐

### 변경

헤더가 사라지므로 `#post-graph`에 `padding-top: 1.5rem` 여백만 남음.

Expand 시 동시 애니메이션:
1. `.graph-container` height: `45vh → 100vh`
2. `#post-graph` padding-top: `1.5rem → 0`
3. `#graph-hint` opacity: `1 → 0` (fade out)

Collapse 시 반대 복원.

```css
#post-graph {
  padding-top: 1.5rem;
  transition: padding-top 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}
#post-graph.expanded { padding-top: 0; }
#graph-hint {
  transition: opacity 0.2s ease;
}
#post-graph.expanded #graph-hint { opacity: 0; pointer-events: none; }
```

`EXPANDED_VH` 상수: `80 → 100`.

---

## 3. 성능 제약 (기존 스펙 유지)

- 사이드바 CSS 추가 ~60줄
- `sidebar.js` ~40줄
- 애니메이션: `transform`, `opacity`, `padding` 만 사용 (GPU 가속 가능 범위)
- 새 CDN 의존성 없음
