# Twinkle 프론트엔드 보완 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Twinkle 피드 내비게이션, 마크다운 렌더링, 모바일 태그 스트립, 아카이브 툴팁 4가지를 보완한다.

**Architecture:** `twinkle/index.html` 인라인 JS + DOM 구조 수정, `style.css` CSS 추가. `#mobile-tags` 를 `#twinkle-feed` 바깥 `.twinkle-feed-col` 래퍼로 분리해서 `renderFeed()` 가 innerHTML 재빌드할 때 모바일 태그 이벤트 리스너가 소멸되는 문제를 원천 차단. 외부 의존성 추가는 marked.js CDN 1개(이미 post 템플릿에서 사용 중인 버전).

**Tech Stack:** Vanilla JS, marked.js CDN (`https://cdn.jsdelivr.net/npm/marked/marked.min.js`), CSS media query

---

## 파일 맵

| 파일 | 변경 |
|------|------|
| `twinkle/index.html` | marked.js 스크립트, DOM 구조(래퍼 추가), JS 로직 전체 |
| `style.css` | `.twinkle-feed-col`, `.twinkle-nav`, `.twinkle-mobile-tags`, `.twinkle-mobile-tag-chip` |

---

## Task 1: CSS — 새 컴포넌트 추가

**Files:**
- Modify: `style.css`

현재 `style.css` 의 Twinkle 섹션 끝:

```css
.archive-date {
  color: #2a2a2a;
  font-size: 0.6rem;
  margin-right: 0.3rem;
}

@media (max-width: 767px) {
  .twinkle-archive { display: none; }
  .twinkle-feed { padding: 1rem 0; }
}
```

- [ ] **Step 1: `@media` 블록 바로 앞에 새 CSS 삽입**

아래처럼 교체:

```css
.archive-date {
  color: #2a2a2a;
  font-size: 0.6rem;
  margin-right: 0.3rem;
}

.twinkle-feed-col {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.twinkle-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-top: 1px solid #1a1a1a;
  margin-top: 0.25rem;
}

.twinkle-nav-btn {
  background: none;
  border: 1px solid rgba(74, 98, 255, 0.3);
  color: #4a62ff;
  font-size: 0.65rem;
  padding: 0.2rem 0.6rem;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}

.twinkle-nav-btn:disabled {
  color: #252525;
  border-color: #1a1a1a;
  cursor: default;
}

.twinkle-nav-info {
  font-size: 0.6rem;
  color: #333;
}

.twinkle-mobile-tags {
  display: none;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
  padding: 0.4rem 0;
  margin-bottom: 0.5rem;
  border-bottom: 1px solid #1a1a1a;
}

.twinkle-mobile-tag-chip {
  display: inline-block;
  font-size: 0.62rem;
  color: #444;
  border: 1px solid #222;
  padding: 0.15rem 0.45rem;
  cursor: pointer;
  transition: color 0.1s, border-color 0.1s;
}

.twinkle-mobile-tag-chip:hover {
  color: #777;
  border-color: #444;
}

.twinkle-mobile-tag-chip.active {
  color: #dc00c9;
  border-color: rgba(220, 0, 201, 0.4);
  background: rgba(220, 0, 201, 0.07);
}

@media (max-width: 767px) {
  .twinkle-archive { display: none; }
  .twinkle-feed { padding: 1rem 0; }
  .twinkle-mobile-tags { display: flex; }
}
```

- [ ] **Step 2: 커밋**

```bash
git add style.css
git commit -m "style: add twinkle-feed-col, twinkle-nav, twinkle-mobile-tags CSS"
```

---

## Task 2: HTML — DOM 구조 재배치 + marked.js CDN

**Files:**
- Modify: `twinkle/index.html`

- [ ] **Step 1: `<head>` 에 marked.js 스크립트 태그 추가**

현재:
```html
  <link rel="stylesheet" href="../style.css">
</head>
```

교체:
```html
  <link rel="stylesheet" href="../style.css">
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
</head>
```

- [ ] **Step 2: `twinkle-layout` 내부 구조 재배치 — feed를 `.twinkle-feed-col` 래퍼로 감싸고, `#mobile-tags` 를 feed 바깥에 배치**

현재:
```html
    <div class="twinkle-layout">
      <div class="twinkle-feed" id="twinkle-feed">
        <div class="label">✦ TWINKLE</div>
        <p style="color:#555;font-size:0.85rem">로딩 중...</p>
      </div>
      <div class="twinkle-archive" id="twinkle-archive">
```

교체:
```html
    <div class="twinkle-layout">
      <div class="twinkle-feed-col">
        <div id="mobile-tags" class="twinkle-mobile-tags"></div>
        <div class="twinkle-feed" id="twinkle-feed">
          <div class="label">✦ TWINKLE</div>
          <p style="color:#555;font-size:0.85rem">로딩 중...</p>
        </div>
      </div>
      <div class="twinkle-archive" id="twinkle-archive">
```

`style.css` 의 기존 `.twinkle-feed { flex: 1; min-width: 0; ... }` 에서 `flex: 1` 과 `min-width: 0` 은 이제 `.twinkle-feed-col` 이 담당하므로, `style.css` 의 `.twinkle-feed` 블록도 수정:

현재:
```css
.twinkle-feed {
  flex: 1;
  padding: 1rem 1rem 1rem 0;
  min-width: 0;
}
```

교체:
```css
.twinkle-feed {
  flex: 1;
  padding: 1rem 1rem 1rem 0;
  min-width: 0;
}
```

(`.twinkle-feed` 는 `.twinkle-feed-col` 의 flex child 가 되므로 `flex: 1` 유지. 변경 없음.)

- [ ] **Step 3: 브라우저 콘솔에서 확인**

```
typeof marked
// Expected: "object"
document.getElementById('mobile-tags')
// Expected: <div id="mobile-tags" ...>
```

- [ ] **Step 4: 커밋**

```bash
git add twinkle/index.html
git commit -m "feat: add marked.js CDN, wrap feed in twinkle-feed-col, add mobile-tags sibling"
```

---

## Task 3: JS — state.page + Prev/Next 내비게이션

**Files:**
- Modify: `twinkle/index.html` (인라인 `<script>`)

- [ ] **Step 1: `state` 에 `page: 0` 추가**

현재:
```js
  const state = {
    twinkles: [],
    anchor: null,
    tag: null,
    expanded: new Set(),
  };
```

교체:
```js
  const state = {
    twinkles: [],
    anchor: null,
    tag: null,
    expanded: new Set(),
    page: 0,
  };
```

- [ ] **Step 2: `getFeedWindow` 를 page 기반으로 교체**

현재:
```js
  function getFeedWindow(list) {
    if (!state.anchor) return list.slice(0, WINDOW_SIZE);
    const idx = list.findIndex(t => t.slug === state.anchor);
    if (idx === -1) return list.slice(0, WINDOW_SIZE);
    const start = Math.max(0, idx - 2);
    const end = Math.min(list.length, start + WINDOW_SIZE);
    return list.slice(start, end);
  }
```

교체:
```js
  function getFeedWindow(list) {
    const start = state.page * WINDOW_SIZE;
    return list.slice(start, start + WINDOW_SIZE);
  }
```

- [ ] **Step 3: `renderFeed` 에 Prev/Next 네비게이션 바 추가**

현재:
```js
  function renderFeed() {
    const filtered = filterByTag(state.twinkles);
    const window = getFeedWindow(filtered);
    const feedEl = document.getElementById('twinkle-feed');
    feedEl.innerHTML = '<div class="label">✦ TWINKLE</div>' + (
      window.length
        ? window.map(renderCard).join('')
        : '<p style="color:#555;font-size:0.85rem">트윈클이 없습니다.</p>'
    );
    feedEl.querySelectorAll('.twinkle-more-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const slug = btn.dataset.slug;
        state.expanded.has(slug) ? state.expanded.delete(slug) : state.expanded.add(slug);
        saveExpanded();
        renderFeed();
      });
    });
  }
```

교체:
```js
  function renderFeed() {
    const filtered = filterByTag(state.twinkles);
    const window = getFeedWindow(filtered);
    const totalPages = Math.ceil(filtered.length / WINDOW_SIZE);
    const start = state.page * WINDOW_SIZE + 1;
    const end = Math.min((state.page + 1) * WINDOW_SIZE, filtered.length);
    const navHtml = filtered.length > WINDOW_SIZE ? `
      <div class="twinkle-nav">
        <button class="twinkle-nav-btn" id="nav-prev"${state.page === 0 ? ' disabled' : ''}>← 이전</button>
        <span class="twinkle-nav-info">${start}–${end} / ${filtered.length}</span>
        <button class="twinkle-nav-btn" id="nav-next"${state.page >= totalPages - 1 ? ' disabled' : ''}>다음 →</button>
      </div>` : '';
    const feedEl = document.getElementById('twinkle-feed');
    feedEl.innerHTML = '<div class="label">✦ TWINKLE</div>' + (
      window.length
        ? window.map(renderCard).join('')
        : '<p style="color:#555;font-size:0.85rem">트윈클이 없습니다.</p>'
    ) + navHtml;
    feedEl.querySelectorAll('.twinkle-more-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const slug = btn.dataset.slug;
        state.expanded.has(slug) ? state.expanded.delete(slug) : state.expanded.add(slug);
        saveExpanded();
        renderFeed();
      });
    });
    const prevBtn = feedEl.querySelector('#nav-prev');
    const nextBtn = feedEl.querySelector('#nav-next');
    if (prevBtn) prevBtn.addEventListener('click', () => { state.page--; renderFeed(); renderArchive(); });
    if (nextBtn) nextBtn.addEventListener('click', () => { state.page++; renderFeed(); renderArchive(); });
  }
```

- [ ] **Step 4: 아카이브 클릭 시 해당 페이지로 이동**

`renderArchive()` 내 `.archive-item` 클릭 핸들러 현재:
```js
    document.querySelectorAll('.archive-item').forEach(item => {
      item.addEventListener('click', () => {
        state.anchor = item.dataset.slug;
        history.replaceState(null, '', '#' + item.dataset.slug);
        renderFeed();
        renderArchive();
      });
    });
```

교체:
```js
    document.querySelectorAll('.archive-item').forEach(item => {
      item.addEventListener('click', () => {
        const filtered = filterByTag(state.twinkles);
        const idx = filtered.findIndex(t => t.slug === item.dataset.slug);
        state.anchor = item.dataset.slug;
        state.page = idx === -1 ? 0 : Math.floor(idx / WINDOW_SIZE);
        history.replaceState(null, '', '#' + item.dataset.slug);
        renderFeed();
        renderArchive();
      });
    });
```

- [ ] **Step 5: 태그 필터 클릭 시 page 리셋**

`renderArchive()` 내 `.archive-tag-chip` 클릭 핸들러 현재:
```js
    document.querySelectorAll('.archive-tag-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        state.tag = chip.dataset.tag === '전체' ? null : chip.dataset.tag;
        state.anchor = null;
        history.replaceState(null, '', location.pathname);
        renderFeed();
        renderArchive();
      });
    });
```

교체:
```js
    document.querySelectorAll('.archive-tag-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        state.tag = chip.dataset.tag === '전체' ? null : chip.dataset.tag;
        state.anchor = null;
        state.page = 0;
        history.replaceState(null, '', location.pathname);
        renderFeed();
        renderArchive();
      });
    });
```

- [ ] **Step 6: 초기 로드 시 hash anchor가 있으면 해당 페이지로 자동 이동**

초기화 IIFE 내 현재:
```js
    const hash = location.hash.slice(1);
    if (hash && state.twinkles.some(t => t.slug === hash)) {
      state.anchor = hash;
    }
```

교체:
```js
    const hash = location.hash.slice(1);
    if (hash) {
      const idx = state.twinkles.findIndex(t => t.slug === hash);
      if (idx !== -1) {
        state.anchor = hash;
        state.page = Math.floor(idx / WINDOW_SIZE);
      }
    }
```

- [ ] **Step 7: 브라우저에서 Prev/Next 동작 확인**

테스트용으로 `twinkles.json` 에 6개 이상 항목이 있어야 함 (현재 3개). 임시로 항목을 복사해서 확인 후 원복.

확인 항목:
- 5개 이하: nav 바 미표시
- 6개 이상 첫 페이지: `← 이전` disabled, `다음 →` active
- 다음 클릭: 카운터 업데이트 (`1–5 / N` → `6–10 / N`)
- 아카이브 클릭: 올바른 페이지로 이동 + anchor 스타일(`.anchor` 클래스)

- [ ] **Step 8: 커밋**

```bash
git add twinkle/index.html
git commit -m "feat: add page-based prev/next navigation to twinkle feed"
```

---

## Task 4: JS — 카드 본문 마크다운 렌더링

**Files:**
- Modify: `twinkle/index.html` (`renderCard` 함수)

- [ ] **Step 1: `renderCard` body 렌더링을 `marked.parse()` 로 교체**

현재:
```js
    const body = (needsTrunc && !isExpanded)
      ? escapeHtml(t.content.slice(0, PREVIEW_LEN)) + '...'
      : escapeHtml(t.content);
```

교체:
```js
    const rawBody = (needsTrunc && !isExpanded)
      ? t.content.slice(0, PREVIEW_LEN) + '...'
      : t.content;
    const body = marked.parse(rawBody);
```

- [ ] **Step 2: 브라우저에서 인라인 코드 렌더링 확인**

샘플 카드(`2026-04-20-sample-c`)에서:
- `` `num_workers=0` `` → `<code>num_workers=0</code>` 태그로 렌더링됨
- `escapeHtml` 이 더 이상 쓰이지 않으니, `escapeHtml` 함수는 아카이브/태그 렌더링에서 여전히 필요하므로 삭제하지 말 것

- [ ] **Step 3: 커밋**

```bash
git add twinkle/index.html
git commit -m "feat: render twinkle card body as markdown with marked.js"
```

---

## Task 5: JS — 모바일 태그 스트립

**Files:**
- Modify: `twinkle/index.html` (`renderArchive` 함수)

- [ ] **Step 1: `renderArchive` 에 `#mobile-tags` 업데이트 로직 추가**

`renderArchive()` 함수 현재:
```js
  function renderArchive() {
    const filtered = filterByTag(state.twinkles);
    const allTags = [...new Set(state.twinkles.flatMap(t => t.tags))];
    document.getElementById('archive-tags').innerHTML =
      ['전체', ...allTags].map(tag => {
        const isActive = tag === '전체' ? !state.tag : state.tag === tag;
        return `<span class="archive-tag-chip${isActive ? ' active' : ''}" data-tag="${tag}">${escapeHtml(tag)}</span>`;
      }).join('');
    document.getElementById('archive-list').innerHTML =
```

함수 시작 부분 교체 (`archive-tags` innerHTML 설정 직후에 모바일 태그 섹션 추가):
```js
  function renderArchive() {
    const filtered = filterByTag(state.twinkles);
    const allTags = [...new Set(state.twinkles.flatMap(t => t.tags))];
    const tagLabels = ['전체', ...allTags];

    document.getElementById('archive-tags').innerHTML =
      tagLabels.map(tag => {
        const isActive = tag === '전체' ? !state.tag : state.tag === tag;
        return `<span class="archive-tag-chip${isActive ? ' active' : ''}" data-tag="${tag}">${escapeHtml(tag)}</span>`;
      }).join('');

    const mobileTagsEl = document.getElementById('mobile-tags');
    if (mobileTagsEl) {
      mobileTagsEl.innerHTML = tagLabels.map(tag => {
        const isActive = tag === '전체' ? !state.tag : state.tag === tag;
        return `<span class="twinkle-mobile-tag-chip${isActive ? ' active' : ''}" data-tag="${tag}">${escapeHtml(tag)}</span>`;
      }).join('');
      mobileTagsEl.querySelectorAll('.twinkle-mobile-tag-chip').forEach(chip => {
        chip.addEventListener('click', () => {
          state.tag = chip.dataset.tag === '전체' ? null : chip.dataset.tag;
          state.anchor = null;
          state.page = 0;
          history.replaceState(null, '', location.pathname);
          renderFeed();
          renderArchive();
        });
      });
    }

    document.getElementById('archive-list').innerHTML =
```

나머지 `renderArchive` 내용은 그대로 유지.

- [ ] **Step 2: 브라우저 개발자 도구에서 모바일 에뮬레이션 (375px) 확인**

- 피드 상단에 태그 칩 가로 나열
- `전체` 기본 active (magenta)
- 칩 클릭 → 필터 적용 + page 0 리셋

- [ ] **Step 3: 커밋**

```bash
git add twinkle/index.html
git commit -m "feat: add mobile tag strip to twinkle feed"
```

---

## Task 6: JS — 아카이브 항목 title 툴팁

**Files:**
- Modify: `twinkle/index.html` (`renderArchive` 내 `.archive-item` 렌더 템플릿)

- [ ] **Step 1: `.archive-item` 에 `title` 속성 추가**

`renderArchive()` 내 현재:
```js
    document.getElementById('archive-list').innerHTML =
      filtered.map(t =>
        `<div class="archive-item${t.slug === state.anchor ? ' active' : ''}" data-slug="${t.slug}">
          <span class="archive-date">${t.date.slice(5)}</span>${escapeHtml(t.title)}
        </div>`
      ).join('');
```

교체:
```js
    document.getElementById('archive-list').innerHTML =
      filtered.map(t =>
        `<div class="archive-item${t.slug === state.anchor ? ' active' : ''}" data-slug="${t.slug}" title="${escapeHtml(t.title)}">
          <span class="archive-date">${t.date.slice(5)}</span>${escapeHtml(t.title)}
        </div>`
      ).join('');
```

- [ ] **Step 2: 잘린 아카이브 항목 hover 시 전체 제목 브라우저 기본 tooltip 확인**

- [ ] **Step 3: 커밋**

```bash
git add twinkle/index.html
git commit -m "fix: show full title tooltip on truncated archive items"
```

---

## Task 7: 최종 통합 테스트

- [ ] **Step 1: 데스크탑 시나리오**

```
□ 피드 포스트 3개 (현재 샘플): nav 바 미표시
□ twinkles.json 에 6개 이상 있을 때: 첫 페이지 ← disabled / 다음 → active
□ 다음 → 클릭: 카운터 "6–N / M" 으로 업데이트
□ 아카이브 항목 클릭: 해당 페이지로 이동 + anchor 파란 테두리
□ 태그 필터 클릭: page 0 리셋
□ 카드 본문 백틱 코드 → <code> 렌더링
□ 아카이브 항목 hover tooltip
```

- [ ] **Step 2: 모바일 에뮬레이션 (375px)**

```
□ 아카이브 패널 숨김
□ 피드 상단 태그 스트립 표시
□ 태그 칩 클릭 → 피드 필터링
□ 전체 칩 클릭 → 전체 표시
```

- [ ] **Step 3: 최종 커밋 로그 확인**

```bash
git log --oneline -6
```

예상:
```
fix: show full title tooltip on truncated archive items
feat: add mobile tag strip to twinkle feed
feat: render twinkle card body as markdown with marked.js
feat: add page-based prev/next navigation to twinkle feed
feat: add marked.js CDN, wrap feed in twinkle-feed-col, add mobile-tags sibling
style: add twinkle-feed-col, twinkle-nav, twinkle-mobile-tags CSS
```
