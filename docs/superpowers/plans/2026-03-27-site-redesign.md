# Site Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 에디토리얼 톤(좌측 보더, 섹션 레이블, 날짜 우측 정렬) + 그래프 rubber-band spring 확장으로 포트폴리오/블로그 리디자인.

**Architecture:** `style.css`에 에디토리얼 CSS 컴포넌트를 추가하고, `index.html` 인라인 스크립트로 rubber-band spring scroll을 구현한다. 나머지 페이지(blog, post)는 HTML 마크업 수정 + JS 렌더링 변경만. 빌드 없음 — 정적 파일 그대로.

**Tech Stack:** Pico.css v2 (CDN), Cytoscape.js (CDN), marked.js + highlight.js (post 페이지), 순수 HTML/CSS/JS.

---

## 파일 변경 범위

| 파일 | 역할 |
|------|------|
| `style.css` | 에디토리얼 CSS classes, `--graph-h` var, post-item, 뷰토글 아이콘 스타일 |
| `index.html` | About 섹션 마크업 + 인라인 spring scroll `<script>` |
| `blog/index.html` | 검색바 최상단, H1 제거, 뷰토글 아이콘, 전체 태그 칩 |
| `app.js` | `renderPostList` 날짜 포맷 + 에디토리얼 마크업 |
| `post.js` | 포스트 헤더 meta 에디토리얼 렌더링 |
| `posts/_template/index.html` | `#post-header` 클래스, ← Blog, Related Posts |
| `posts/*/index.html` (8개) | 동일 변경 일괄 적용 |

---

### Task 1: style.css — 에디토리얼 CSS 기반

**Files:**
- Modify: `style.css`

- [ ] **Step 1: `.graph-container` height를 CSS variable로 교체**

`style.css`의 `.graph-container` 블록(228번째 줄 근처)을 수정. `height: 500px` → `var(--graph-h, 45vh)`, transition + will-change 추가:

```css
/* Graph container */
.graph-container {
  width: 100%;
  height: var(--graph-h, 45vh);
  background: #0a0a0a;
  border: 1px solid #1e1e1e;
  border-radius: 8px;
  margin-bottom: 1rem;
  overflow: hidden;
  transition: height 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
  will-change: height;
}
.graph-container.subgraph {
  height: 350px;
  transition: none;
  will-change: auto;
}
```

- [ ] **Step 2: `.post-item` 클래스를 에디토리얼 스타일로 교체**

`style.css`의 `.post-item` 블록(79번째 줄 근처)을 아래로 교체:

```css
/* Blog post list item */
.post-item {
  display: block;
  padding: 0.8rem 0;
  border-bottom: 1px solid #111;
  text-decoration: none;
  color: inherit;
}
.post-item-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 1rem;
}
.post-item h3 {
  margin-bottom: 0;
  font-size: 1rem;
  flex: 1;
}
.post-date-inline {
  font-size: 0.75rem;
  color: #444;
  white-space: nowrap;
  flex-shrink: 0;
}
```

기존 `.post-item h3`, `.post-meta` 규칙은 제거 (위 블록이 대체).

- [ ] **Step 3: 뷰토글 버튼 아이콘 스타일 조정**

`style.css`의 `.view-toggle button` 블록을 수정 (아이콘 크기에 맞게 패딩 조정):

```css
.view-toggle button {
  background: #111;
  color: #555;
  border: none;
  padding: 0.4rem 0.6rem;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.15s;
  line-height: 1;
}
.view-toggle button.active {
  background: #dc00c9;
  color: #fff;
}
```

- [ ] **Step 4: `style.css` 맨 끝에 에디토리얼 컴포넌트 + 전역 규칙 추가**

```css
/* Prevent pull-to-refresh on all pages */
body { overscroll-behavior-y: contain; }

/* Editorial left-border block */
.editorial-header {
  border-left: 2px solid #dc00c9;
  padding-left: 0.75rem;
  margin-bottom: 1.5rem;
}
.editorial-label {
  font-size: 0.7rem;
  color: #dc00c9;
  text-transform: uppercase;
  letter-spacing: 2px;
  margin-bottom: 0.2rem;
  display: block;
}

/* Mobile: smaller default graph height */
@media (max-width: 640px) {
  :root { --graph-h: 40vh; }
}
```

- [ ] **Step 5: 서버 시작 후 육안 확인**

```bash
cd /home/ahris/ahrism-pages && python3 -m http.server 8080
```

http://localhost:8080 에서:
- 그래프가 45vh 높이로 표시되어야 함 (기존 500px보다 약간 달라 보임)
- 레이아웃 깨짐 없어야 함
- http://localhost:8080/blog/ 포스트 목록 레이아웃 유지되어야 함

- [ ] **Step 6: 커밋**

```bash
cd /home/ahris/ahrism-pages
git add style.css
git commit -m "style: editorial CSS + graph-h var + overscroll-behavior"
```

---

### Task 2: app.js — renderPostList 에디토리얼 업데이트

**Files:**
- Modify: `app.js`

- [ ] **Step 1: 날짜 포맷 헬퍼 추가**

`app.js` 맨 위(1번째 줄 앞)에 추가:

```js
// Format YYYY-MM-DD → "Jan 15"
function formatPostDate(dateStr) {
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}
```

- [ ] **Step 2: `renderPostList` 함수의 item 생성 부분 교체**

`app.js` `renderPostList` 함수 내부 전체를 아래로 교체:

```js
function renderPostList(posts, container, postsBasePath) {
  container.innerHTML = '';
  posts.forEach(post => {
    const item = document.createElement('a');
    item.href = `${postsBasePath}${post.slug}/`;
    item.className = 'post-item';
    item.innerHTML = `
      <div class="post-item-row">
        <h3>${post.title}</h3>
        <span class="post-date-inline">${formatPostDate(post.date)}</span>
      </div>
      <div class="post-meta" style="margin-top:0.25rem">
        ${post.tags.map(t => `<span class="tag">${t}</span>`).join(' ')}
      </div>
      ${post.summary ? `<p style="color:#666;font-size:0.85rem;margin-top:0.3rem;margin-bottom:0">${post.summary}</p>` : ''}
    `;
    container.appendChild(item);
  });
}
```

- [ ] **Step 3: 육안 확인**

http://localhost:8080/blog/ 에서:
- 포스트 제목과 날짜("Jan 15" 형식)가 같은 행에 양끝 정렬되어야 함
- 태그 칩이 날짜 아래 다음 행에 표시되어야 함

- [ ] **Step 4: 커밋**

```bash
cd /home/ahris/ahrism-pages
git add app.js
git commit -m "feat: post list — date right-aligned in Jan 15 format"
```

---

### Task 3: blog/index.html — 검색 상단 이동 + 뷰토글 아이콘화

**Files:**
- Modify: `blog/index.html`

- [ ] **Step 1: `<main>` 내부 구조 전면 교체**

`blog/index.html`의 `<main class="container">` 안 전체를 아래로 교체:

```html
<main class="container">
  <!-- 1. 검색바 최상단 -->
  <div class="search-bar" style="margin-top:1rem">
    <input type="text" id="search-input" placeholder="검색...">
    <label class="toggle-label" id="tfidf-label" style="display:none">
      <input type="checkbox" id="tfidf-toggle">
      키워드 가중
    </label>
  </div>

  <!-- 2. 태그 필터 + 뷰 토글 -->
  <div style="display:flex;align-items:flex-start;gap:0.5rem;margin-bottom:1rem">
    <div class="tag-filters" id="tag-filters" style="flex:1;margin-bottom:0"></div>
    <div class="view-toggle" style="margin-bottom:0;flex-shrink:0;margin-top:0.15rem">
      <button id="btn-graph" title="그래프 뷰">⬡</button>
      <button id="btn-list" class="active" title="리스트 뷰">☰</button>
    </div>
  </div>

  <!-- 3. 그래프 뷰 -->
  <div id="graph-view" style="display:none">
    <div class="graph-container" id="graph-container"></div>
  </div>

  <!-- 4. 리스트 뷰 -->
  <div id="list-view">
    <div id="posts-container"></div>
  </div>
</main>
```

- [ ] **Step 2: 태그 렌더링 + 전체 칩 JS 교체**

`blog/index.html` 인라인 스크립트 내 태그 렌더링 블록을 아래로 교체:

```js
// --- 태그 필터 렌더링 (전체 칩 포함) ---
const allTags = [...new Set(nodes.flatMap(n => n.tags || []))].sort();
const tagContainer = document.getElementById('tag-filters');

// "전체" 칩
const allChip = document.createElement('span');
allChip.className = 'tag-filter active';
allChip.textContent = '전체';
allChip.dataset.all = '1';
allChip.addEventListener('click', () => {
  document.querySelectorAll('.tag-filter:not([data-all])').forEach(c => c.classList.remove('active'));
  allChip.classList.add('active');
  applyFilters();
});
tagContainer.appendChild(allChip);

allTags.forEach(tag => {
  const chip = document.createElement('span');
  chip.className = 'tag-filter';
  chip.textContent = tag;
  chip.addEventListener('click', () => {
    allChip.classList.remove('active');
    chip.classList.toggle('active');
    applyFilters();
  });
  tagContainer.appendChild(chip);
});
```

- [ ] **Step 3: `applyFilters` 내 태그 쿼리 수정**

`applyFilters` 함수 내 activeTags 쿼리를 수정하여 `data-all` 칩 제외:

```js
const activeTags = [...document.querySelectorAll('.tag-filter:not([data-all]).active')]
  .map(el => el.textContent);
```

- [ ] **Step 4: 검색 입력 이벤트에 tfidf 토글 노출 로직 추가**

기존 `searchInput.addEventListener('input', ...)` 블록을 아래로 교체:

```js
const tfidfLabel = document.getElementById('tfidf-label');
searchInput.addEventListener('input', () => {
  tfidfLabel.style.display = searchInput.value.trim() ? '' : 'none';
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(applyFilters, 300);
});
```

- [ ] **Step 5: 육안 확인**

http://localhost:8080/blog/ 에서:
- 검색바가 nav 바로 아래 최상단에 있어야 함
- "키워드 가중" 토글이 기본 숨김 → 검색어 입력 시 나타나야 함
- 태그 필터 행 오른쪽에 ⬡ / ☰ 아이콘 버튼이 있어야 함
- "전체" 칩이 태그 필터 맨 앞에 active 상태여야 함
- 개별 태그 클릭 시 "전체" 비활성화 / "전체" 클릭 시 개별 태그 전체 해제

- [ ] **Step 6: 커밋**

```bash
cd /home/ahris/ahrism-pages
git add blog/index.html
git commit -m "feat: blog — search top, icon view toggle, 전체 tag chip"
```

---

### Task 4: index.html — About 섹션 에디토리얼 마크업

**Files:**
- Modify: `index.html`

- [ ] **Step 1: About 섹션 에디토리얼 헤더로 교체**

`index.html`의 `<section id="about">` 내부에서:

```html
<!-- 기존 -->
<div class="section-label">About</div>
<h1>ahrism</h1>
<p>Building Practical Systems.</p>
<p>알고리즘을 밑바닥부터 이해하고, 소프트웨어 지능과 현실 세계의 접점을 만듭니다.</p>
<div>
  <span class="tag">Python</span>
  ...
</div>
```

→ 아래로 교체:

```html
<div class="editorial-header">
  <span class="editorial-label">About</span>
  <h1>ahrism</h1>
  <p>Building Practical Systems.</p>
  <p>알고리즘을 밑바닥부터 이해하고, 소프트웨어 지능과 현실 세계의 접점을 만듭니다.</p>
  <div>
    <span class="tag">Python</span>
    <span class="tag">C++</span>
    <span class="tag">PyTorch</span>
    <span class="tag">OpenCV</span>
    <span class="tag">Linux</span>
    <span class="tag">Docker</span>
  </div>
</div>
```

- [ ] **Step 2: 학력 섹션 아래에 Blog 링크 추가**

`<h3>학력</h3>` 블록 뒤에 추가:

```html
<p style="margin-top:2rem">
  <a href="./blog/" style="color:#4a62ff;font-size:0.9rem">Blog →</a>
</p>
```

- [ ] **Step 3: 그래프 힌트 텍스트 추가**

`<section id="post-graph">` 안, `graph-container` 바로 앞에 추가:

```html
<div id="graph-hint" style="text-align:center;font-size:0.65rem;color:#2a2a2a;letter-spacing:2px;padding:0.3rem 0;user-select:none">↑ PULL</div>
```

- [ ] **Step 4: 육안 확인**

http://localhost:8080/ 에서:
- About 섹션에 좌측 magenta 2px 보더가 있어야 함
- "ABOUT" 레이블(uppercase, letter-spacing)이 h1 위에 있어야 함
- 페이지 하단에 "Blog →" 링크가 파란색으로 있어야 함
- 그래프 위에 `↑ PULL` 텍스트가 거의 안 보이는 수준으로 있어야 함

- [ ] **Step 5: 커밋**

```bash
cd /home/ahris/ahrism-pages
git add index.html
git commit -m "feat: index — about editorial header + blog link + pull hint"
```

---

### Task 5: index.html — Spring Scroll JS

**Files:**
- Modify: `index.html` (마지막 `</body>` 직전에 `<script>` 추가)

- [ ] **Step 1: spring scroll 스크립트 추가**

`index.html`의 `</body>` 직전에 추가:

```html
<script>
(function () {
  const gc = document.getElementById('graph-container');
  if (!gc) return;

  const SNAP_THRESHOLD = 80; // px: 이 이상 당기면 확장
  const DEFAULT_VH = window.innerWidth <= 640 ? 40 : 45;
  const EXPANDED_VH = 80;
  const EASE = '0.35s cubic-bezier(0.34, 1.56, 0.64, 1)';

  let expanded = false;
  let startY = 0;
  let dragActive = false;

  function baseH() { return DEFAULT_VH / 100 * window.innerHeight; }

  function setHPx(px) {
    gc.style.transition = 'none';
    gc.style.height = px + 'px';
  }

  function snapTo(vh) {
    gc.style.transition = 'height ' + EASE;
    gc.style.height = vh + 'vh';
  }

  function snapExpand() {
    expanded = true;
    snapTo(EXPANDED_VH);
  }

  function snapCollapse() {
    expanded = false;
    snapTo(DEFAULT_VH);
  }

  // ── Touch (mobile) ─────────────────────────────
  document.addEventListener('touchstart', function (e) {
    if (window.scrollY > 2) return;
    startY = e.touches[0].clientY;
    dragActive = true;
  }, { passive: true });

  document.addEventListener('touchmove', function (e) {
    if (!dragActive) return;
    const delta = e.touches[0].clientY - startY; // 양수 = 손가락 아래로 = overscroll 위
    if (delta <= 0) { dragActive = false; return; }
    if (!expanded) {
      setHPx(baseH() + delta * 0.4); // rubber band 감쇠
    }
  }, { passive: true });

  document.addEventListener('touchend', function () {
    if (!dragActive) return;
    dragActive = false;
    if (!expanded) {
      const delta = gc.offsetHeight - baseH();
      if (delta > SNAP_THRESHOLD) {
        snapExpand();
      } else {
        snapCollapse();
      }
    }
  }, { passive: true });

  // ── Scroll (collapse when scrolling down) ──────
  document.addEventListener('scroll', function () {
    if (expanded && window.scrollY > 10) {
      snapCollapse();
    }
  }, { passive: true });

  // ── Wheel (desktop) ────────────────────────────
  document.addEventListener('wheel', function (e) {
    if (e.deltaY < 0 && window.scrollY < 2 && !expanded) {
      snapExpand();
    } else if (e.deltaY > 0 && window.scrollY < 2 && expanded) {
      snapCollapse();
    }
  }, { passive: true });
})();
</script>
```

- [ ] **Step 2: 육안 확인 — 데스크탑**

http://localhost:8080/ 에서:
- 페이지 최상단에서 마우스 휠 위로 스크롤 → 그래프가 45vh → 80vh로 spring 확장 (cubic-bezier 튕김 효과)
- 확장 상태에서 휠 아래로 → 45vh로 복귀
- 스크롤 내려서 scrollY > 10이 되면 자동 복귀

- [ ] **Step 3: 육안 확인 — 모바일 시뮬레이션**

브라우저 개발자 도구 → 기기 시뮬레이션(예: iPhone 12) → 터치 드래그:
- 최상단에서 아래로 드래그 → 그래프 높이가 손가락 따라 늘어남 (rubber band)
- 80px 이상 당기고 놓으면 → 80vh로 snap
- 80px 미만 당기고 놓으면 → 원위치 spring back

- [ ] **Step 4: 커밋**

```bash
cd /home/ahris/ahrism-pages
git add index.html
git commit -m "feat: spring scroll — rubber band graph expand/collapse"
```

---

### Task 6: post.js + 포스트 HTML — 에디토리얼 헤더

**Files:**
- Modify: `post.js`
- Modify: `posts/_template/index.html`
- Modify: `posts/docker-container/index.html`
- Modify: `posts/hello-world/index.html`
- Modify: `posts/opencv-basics/index.html`
- Modify: `posts/python-performance/index.html`
- Modify: `posts/test-post-1/index.html`
- Modify: `posts/간단ALU만들기_프로젝트/index.html`
- Modify: `posts/딥러닝과_신경망/index.html`
- Modify: `posts/인공신경망1/index.html`

- [ ] **Step 1: post.js — meta 렌더링 에디토리얼화**

`post.js` 31번째 줄 근처, `post-meta` innerHTML 설정 부분을 수정:

```js
// 기존:
document.getElementById('post-meta').innerHTML =
  `${post.date} ${post.tags.map(t => `<span class="tag">${t}</span>`).join(' ')}`;

// 변경 후:
document.getElementById('post-meta').innerHTML =
  `<span class="editorial-label">${post.date}</span>` +
  post.tags.map(t => `<span class="tag">${t}</span>`).join(' ');
```

- [ ] **Step 2: `posts/_template/index.html` 3가지 변경**

1. `<div id="post-header">` → `<div id="post-header" class="editorial-header">`
2. `← Back to Blog` → `← Blog` (anchor 태그의 class, style도 정리):
   ```html
   <!-- 기존 -->
   <a href="../../blog/" class="accent-secondary" style="font-size:0.85rem">← Back to Blog</a>
   <!-- 변경 후 -->
   <a href="../../blog/" style="font-size:0.85rem;color:#444">← Blog</a>
   ```
3. `<div class="section-label">관련 글 탐색</div>` → `<div class="section-label">Related Posts</div>`

- [ ] **Step 3: 기존 포스트 HTML 8개 일괄 업데이트**

```bash
cd /home/ahris/ahrism-pages
for dir in \
  "posts/docker-container" \
  "posts/hello-world" \
  "posts/opencv-basics" \
  "posts/python-performance" \
  "posts/test-post-1" \
  "posts/간단ALU만들기_프로젝트" \
  "posts/딥러닝과_신경망" \
  "posts/인공신경망1"; do
  f="$dir/index.html"
  sed -i 's/<div id="post-header">/<div id="post-header" class="editorial-header">/' "$f"
  sed -i 's/← Back to Blog/← Blog/' "$f"
  sed -i 's/관련 글 탐색/Related Posts/' "$f"
done
```

- [ ] **Step 4: 변경 확인**

```bash
cd /home/ahris/ahrism-pages
grep -l 'editorial-header' posts/*/index.html
```

Expected output (9줄):
```
posts/_template/index.html
posts/docker-container/index.html
posts/hello-world/index.html
posts/opencv-basics/index.html
posts/python-performance/index.html
posts/test-post-1/index.html
posts/간단ALU만들기_프로젝트/index.html
posts/딥러닝과_신경망/index.html
posts/인공신경망1/index.html
```

- [ ] **Step 5: 육안 확인**

http://localhost:8080/posts/hello-world/ 에서:
- 포스트 제목 왼쪽에 magenta 2px 보더가 있어야 함
- 날짜가 uppercase 레이블 스타일로 h1 위에 표시되어야 함
- "← Blog" 텍스트 색이 `#444` (회색)이어야 함
- 하단 관련 글 섹션 레이블이 "Related Posts"로 표시되어야 함

- [ ] **Step 6: 커밋**

```bash
cd /home/ahris/ahrism-pages
git add post.js posts/_template/index.html \
  posts/docker-container/index.html \
  posts/hello-world/index.html \
  posts/opencv-basics/index.html \
  posts/python-performance/index.html \
  posts/test-post-1/index.html \
  "posts/간단ALU만들기_프로젝트/index.html" \
  "posts/딥러닝과_신경망/index.html" \
  posts/인공신경망1/index.html
git commit -m "feat: post — editorial header, ← Blog, Related Posts"
```
