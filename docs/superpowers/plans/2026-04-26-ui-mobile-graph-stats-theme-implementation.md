# UI Mobile Graph Stats Theme Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve the mobile navigation, Twinkle filters, home graph interaction, home blog statistics, and theme color system without changing the Python pipeline.

**Architecture:** Keep the site static and data-driven. Templates provide semantic containers, focused JavaScript modules own behavior, and `style.css` owns visual states through semantic CSS tokens. Each task adds a small regression test before implementation and ends with a commit.

**Tech Stack:** Jinja2 templates, vanilla JavaScript, Pico.css, Cytoscape.js, CSS custom properties, pytest static regression tests, Playwright for browser verification when implementation is complete.

---

## File Structure

- `tests/test_ui_static.py`: New static regression tests for templates, JavaScript behavior contracts, and theme token usage.
- `templates/partials/sidebar.html`: Add mobile header and mobile drawer while preserving the existing desktop sidebar loop from `templates/nav.json`.
- `templates/pages/home.html`: Add explicit graph controls and a home statistics section.
- `templates/pages/twinkle.html`: Keep the existing mobile tags mount point but add clearer semantic wrapping for mobile filters.
- `src/sidebar.js`: Extend navigation behavior to mobile drawer open/close while preserving desktop navigation.
- `src/home-graph.js`: Remove pull-to-expand and implement explicit fullscreen graph mode.
- `src/home-stats.js`: New module that fetches static JSON and renders blog statistics.
- `src/twinkle-feed.js`: Render tag chips as accessible buttons and keep filtering behavior unchanged.
- `style.css`: Introduce semantic theme tokens and style the new mobile header, drawer, fullscreen graph mode, stats section, and improved Twinkle mobile tags.

## Task 1: Theme Tokens And Color Baseline

**Files:**
- Create: `tests/test_ui_static.py`
- Modify: `style.css`

- [ ] **Step 1: Add failing static tests for theme tokens**

Create `tests/test_ui_static.py` with:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_style_defines_semantic_theme_tokens():
    css = read("style.css")
    for token in [
        "--color-bg",
        "--color-surface",
        "--color-surface-raised",
        "--color-border",
        "--color-text",
        "--color-muted",
        "--color-accent",
        "--color-accent-strong",
        "--color-info",
        "--color-danger",
        "--color-success",
    ]:
        assert token in css


def test_pink_is_not_used_as_general_state_color():
    css = read("style.css")
    assert css.count("#dc00c9") <= 4
```

- [ ] **Step 2: Run the new theme tests and confirm they fail**

Run:

```bash
uv run pytest tests/test_ui_static.py::test_style_defines_semantic_theme_tokens tests/test_ui_static.py::test_pink_is_not_used_as_general_state_color -v
```

Expected: FAIL because semantic tokens are not defined and `#dc00c9` appears more than four times.

- [ ] **Step 3: Add semantic tokens at the top of `style.css`**

Replace the existing top-level `:root` declaration block in `style.css` with:

```css
:root {
  --color-bg: #0a0a0a;
  --color-surface: #111111;
  --color-surface-raised: #151515;
  --color-border: #1e1e1e;
  --color-text: #cccccc;
  --color-muted: #666666;
  --color-muted-soft: #444444;
  --color-accent: #7c5cff;
  --color-accent-strong: #dc00c9;
  --color-info: #4a9eff;
  --color-danger: #ff4d5a;
  --color-success: #00cc66;

  --pico-background-color: var(--color-bg);
  --pico-card-background-color: var(--color-surface);
  --pico-card-border-color: var(--color-border);
  --pico-primary: var(--color-accent);
  --pico-primary-hover: #6d4ef0;
  --pico-secondary: var(--color-info);
  --pico-secondary-hover: #3d86dd;
  --pico-color: var(--color-text);
  --pico-muted-color: var(--color-muted);
  --pico-border-color: var(--color-border);
  color-scheme: dark;
}
```

- [ ] **Step 4: Replace broad color usage with tokens**

Use search and replace carefully in `style.css`:

```text
#0a0a0a -> var(--color-bg)
#111111 -> var(--color-surface)
#111 -> var(--color-surface)
#1e1e1e -> var(--color-border)
#cccccc -> var(--color-text)
#ccc -> var(--color-text)
#555555 -> var(--color-muted)
#555 -> var(--color-muted)
#4a62ff -> var(--color-info)
#ff0000 -> var(--color-danger)
```

Then replace most `#dc00c9` usages with intent-specific tokens:

```text
active navigation -> var(--color-accent)
selected filters -> var(--color-info)
dates and metadata -> var(--color-muted)
graph hover/root state -> var(--color-accent)
rare brand emphasis -> var(--color-accent-strong)
```

Leave at most these direct `#dc00c9` occurrences:

```css
--color-accent-strong: #dc00c9;
.accent-primary { color: #dc00c9; }
```

- [ ] **Step 5: Run tests for the theme task**

Run:

```bash
uv run pytest tests/test_ui_static.py::test_style_defines_semantic_theme_tokens tests/test_ui_static.py::test_pink_is_not_used_as_general_state_color -v
```

Expected: PASS.

- [ ] **Step 6: Commit the theme baseline**

Run:

```bash
git add tests/test_ui_static.py style.css
git commit -m "refactor: introduce semantic theme tokens"
```

## Task 2: Mobile Header And Drawer

**Files:**
- Modify: `tests/test_ui_static.py`
- Modify: `templates/partials/sidebar.html`
- Modify: `src/sidebar.js`
- Modify: `style.css`

- [ ] **Step 1: Add failing tests for mobile navigation markup and behavior hooks**

Append these tests to `tests/test_ui_static.py`:

```python
def test_sidebar_partial_contains_mobile_header_and_drawer():
    html = read("templates/partials/sidebar.html")
    assert 'id="mobile-site-header"' in html
    assert 'id="mobile-nav-toggle"' in html
    assert 'id="mobile-nav-drawer"' in html
    assert 'mobile-nav-link' in html
    assert 'aria-expanded="false"' in html


def test_sidebar_js_controls_mobile_drawer():
    js = read("src/sidebar.js")
    assert "mobile-nav-toggle" in js
    assert "mobile-nav-drawer" in js
    assert "mobile-nav-open" in js
    assert "setAttribute('aria-expanded'" in js
```

- [ ] **Step 2: Run the new mobile navigation tests and confirm they fail**

Run:

```bash
uv run pytest tests/test_ui_static.py::test_sidebar_partial_contains_mobile_header_and_drawer tests/test_ui_static.py::test_sidebar_js_controls_mobile_drawer -v
```

Expected: FAIL because the mobile header, drawer, and JS hooks do not exist yet.

- [ ] **Step 3: Replace `templates/partials/sidebar.html`**

Replace the full file with:

```html
<header id="mobile-site-header">
  <button id="mobile-nav-toggle" type="button" aria-label="메뉴 열기" aria-controls="mobile-nav-drawer" aria-expanded="false">☰</button>
  <a class="mobile-site-title" href="{{ root }}">Ahrism</a>
  <span class="mobile-current-page">
    {% for item in nav %}
    {% if item.id == current_page %}{{ item.icon }} {{ item.label }}{% endif %}
    {% endfor %}
  </span>
</header>

<aside id="mobile-nav-drawer" aria-label="모바일 내비게이션">
  <div class="mobile-nav-drawer-inner">
    {% for item in nav %}
    <button class="mobile-nav-link{% if item.id == current_page %} active{% endif %}" data-href="{{ root }}{{ item.href }}">
      <span class="mobile-nav-icon">{{ item.icon }}</span>
      <span>{{ item.label }}</span>
    </button>
    {% endfor %}
  </div>
</aside>
<div id="mobile-nav-backdrop"></div>

<button id="sidebar-toggle" aria-label="메뉴">☰</button>
<aside id="sidebar">
  <div class="sidebar-icons">
    {% for item in nav %}
    <button class="sidebar-btn{% if item.id == current_page %} active{% endif %}" data-label="{{ item.label }}" data-href="{{ root }}{{ item.href }}">{{ item.icon }}</button>
    {% endfor %}
  </div>
</aside>
```

- [ ] **Step 4: Extend `src/sidebar.js`**

Replace the full file with:

```javascript
// sidebar.js — shared navigation: desktop sidebar and mobile drawer
(function () {
  function navigateTo(href) {
    if (href) window.location.href = href;
  }

  document.querySelectorAll('.sidebar-btn[data-panel]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var panelId = 'panel-' + btn.dataset.panel;
      var panel = document.getElementById(panelId);
      if (!panel) return;
      var isOpen = panel.classList.contains('open');
      document.querySelectorAll('.sidebar-panel').forEach(function (p) {
        p.classList.remove('open');
      });
      if (!isOpen) panel.classList.add('open');
    });
  });

  document.querySelectorAll('.sidebar-btn[data-href], .mobile-nav-link[data-href]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      navigateTo(btn.dataset.href);
    });
  });

  document.addEventListener('click', function (e) {
    if (!e.target.closest('#sidebar')) {
      document.querySelectorAll('.sidebar-panel').forEach(function (p) {
        p.classList.remove('open');
      });
    }
  });

  var legacyToggleBtn = document.getElementById('sidebar-toggle');
  var sidebar = document.getElementById('sidebar');
  if (legacyToggleBtn && sidebar) {
    legacyToggleBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      sidebar.classList.toggle('open');
      legacyToggleBtn.classList.toggle('active');
    });
    document.addEventListener('click', function (e) {
      if (sidebar.classList.contains('open') &&
          !e.target.closest('#sidebar') &&
          e.target !== legacyToggleBtn) {
        sidebar.classList.remove('open');
        legacyToggleBtn.classList.remove('active');
      }
    });
  }

  var mobileToggle = document.getElementById('mobile-nav-toggle');
  var mobileDrawer = document.getElementById('mobile-nav-drawer');
  var mobileBackdrop = document.getElementById('mobile-nav-backdrop');

  function setMobileDrawer(open) {
    if (!mobileToggle || !mobileDrawer) return;
    document.body.classList.toggle('mobile-nav-open', open);
    mobileDrawer.classList.toggle('open', open);
    mobileToggle.classList.toggle('active', open);
    mobileToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
  }

  if (mobileToggle && mobileDrawer) {
    mobileToggle.addEventListener('click', function (e) {
      e.stopPropagation();
      setMobileDrawer(!mobileDrawer.classList.contains('open'));
    });

    if (mobileBackdrop) {
      mobileBackdrop.addEventListener('click', function () {
        setMobileDrawer(false);
      });
    }

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') setMobileDrawer(false);
    });
  }
})();
```

- [ ] **Step 5: Add mobile header and drawer CSS**

Add this block near the sidebar section in `style.css`, before the existing mobile sidebar media rules:

```css
#mobile-site-header,
#mobile-nav-drawer,
#mobile-nav-backdrop {
  display: none;
}

.mobile-site-title {
  color: var(--color-text);
  text-decoration: none;
  font-weight: 600;
  letter-spacing: 0;
}

.mobile-current-page {
  color: var(--color-muted);
  font-size: 0.78rem;
  white-space: nowrap;
}

@media (max-width: 640px) {
  body {
    padding-left: 0;
    padding-top: 52px;
  }

  #mobile-site-header {
    position: fixed;
    inset: 0 0 auto 0;
    height: 52px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    padding: 0 0.85rem;
    background: rgba(10, 10, 10, 0.96);
    border-bottom: 1px solid var(--color-border);
    z-index: 120;
    backdrop-filter: blur(10px);
  }

  #mobile-nav-toggle {
    width: 36px;
    height: 36px;
    padding: 0;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    color: var(--color-text);
    font-size: 1rem;
  }

  #mobile-nav-toggle.active {
    color: var(--color-info);
    border-color: color-mix(in srgb, var(--color-info) 60%, transparent);
  }

  #mobile-nav-drawer {
    position: fixed;
    top: 52px;
    left: 0;
    bottom: 0;
    width: min(82vw, 300px);
    display: block;
    transform: translateX(-100%);
    transition: transform 0.2s ease;
    background: var(--color-bg);
    border-right: 1px solid var(--color-border);
    z-index: 119;
  }

  #mobile-nav-drawer.open {
    transform: translateX(0);
  }

  .mobile-nav-drawer-inner {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    padding: 0.75rem;
  }

  .mobile-nav-link {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    width: 100%;
    padding: 0.75rem;
    background: transparent;
    border: 1px solid transparent;
    color: var(--color-muted);
    text-align: left;
    font-size: 0.95rem;
  }

  .mobile-nav-link.active {
    color: var(--color-info);
    border-color: color-mix(in srgb, var(--color-info) 38%, transparent);
    background: color-mix(in srgb, var(--color-info) 8%, transparent);
  }

  .mobile-nav-icon {
    width: 1.25rem;
    text-align: center;
  }

  #mobile-nav-backdrop {
    position: fixed;
    inset: 52px 0 0 0;
    display: block;
    opacity: 0;
    pointer-events: none;
    background: rgba(0, 0, 0, 0.45);
    transition: opacity 0.2s ease;
    z-index: 118;
  }

  body.mobile-nav-open #mobile-nav-backdrop {
    opacity: 1;
    pointer-events: auto;
  }

  #sidebar,
  #sidebar-toggle {
    display: none;
  }
}
```

- [ ] **Step 6: Run mobile navigation tests and build**

Run:

```bash
uv run pytest tests/test_ui_static.py::test_sidebar_partial_contains_mobile_header_and_drawer tests/test_ui_static.py::test_sidebar_js_controls_mobile_drawer -v
uv run python scripts/build_site.py
```

Expected: tests PASS and build prints generated page paths ending with `Done. 5 pages + 8 posts built.`

- [ ] **Step 7: Commit mobile navigation**

Run:

```bash
git add tests/test_ui_static.py templates/partials/sidebar.html src/sidebar.js style.css
git commit -m "feat: add mobile header drawer navigation"
```

## Task 3: Twinkle Mobile Filter Area

**Files:**
- Modify: `tests/test_ui_static.py`
- Modify: `templates/pages/twinkle.html`
- Modify: `src/twinkle-feed.js`
- Modify: `style.css`

- [ ] **Step 1: Add failing tests for accessible Twinkle mobile filters**

Append these tests to `tests/test_ui_static.py`:

```python
def test_twinkle_template_has_mobile_filter_region():
    html = read("templates/pages/twinkle.html")
    assert 'class="twinkle-mobile-filter-panel"' in html
    assert 'id="mobile-tags"' in html
    assert '모바일 트윙클 필터' in html


def test_twinkle_tags_render_as_buttons_with_pressed_state():
    js = read("src/twinkle-feed.js")
    assert '<button type="button"' in js
    assert "aria-pressed" in js
    assert "chip.dataset.tag" in js
```

- [ ] **Step 2: Run Twinkle filter tests and confirm they fail**

Run:

```bash
uv run pytest tests/test_ui_static.py::test_twinkle_template_has_mobile_filter_region tests/test_ui_static.py::test_twinkle_tags_render_as_buttons_with_pressed_state -v
```

Expected: FAIL because the semantic filter panel and button rendering do not exist yet.

- [ ] **Step 3: Update the Twinkle mobile filter markup**

In `templates/pages/twinkle.html`, replace:

```html
      <div id="mobile-tags" class="twinkle-mobile-tags"></div>
```

with:

```html
      <section class="twinkle-mobile-filter-panel" aria-label="모바일 트윙클 필터">
        <div class="twinkle-mobile-filter-title">Filter</div>
        <div id="mobile-tags" class="twinkle-mobile-tags"></div>
      </section>
```

- [ ] **Step 4: Replace `renderTagChips` in `src/twinkle-feed.js`**

Replace the existing `renderTagChips(containerId, chipClass)` function with:

```javascript
    function renderTagChips(containerId, chipClass) {
      const el = document.getElementById(containerId);
      if (!el) return;
      const allTags = [...new Set(state.twinkles.flatMap(t => t.tags))];
      const tagLabels = ['전체', ...allTags];
      el.innerHTML = tagLabels.map(tag => {
        const isActive = tag === '전체' ? !state.tag : state.tag === tag;
        return `<button type="button" class="${chipClass}${isActive ? ' active' : ''}" data-tag="${escapeHtml(tag)}" aria-pressed="${isActive ? 'true' : 'false'}">${escapeHtml(tag)}</button>`;
      }).join('');
      el.querySelectorAll('.' + chipClass).forEach(chip => {
        chip.addEventListener('click', () => {
          state.tag = chip.dataset.tag === '전체' ? null : chip.dataset.tag;
          state.anchor = null;
          state.page = 0;
          setHash(null);
          renderFeed();
          renderArchive();
        });
      });
    }
```

- [ ] **Step 5: Replace Twinkle mobile tag CSS**

Replace the existing `.twinkle-mobile-tags`, `.twinkle-mobile-tag-chip`, `.twinkle-mobile-tag-chip:hover`, and `.twinkle-mobile-tag-chip.active` rules with:

```css
.twinkle-mobile-filter-panel {
  display: none;
}

.twinkle-mobile-filter-title {
  color: var(--color-muted);
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  margin-bottom: 0.45rem;
}

.twinkle-mobile-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  align-items: center;
}

.twinkle-mobile-tag-chip {
  display: inline-flex;
  align-items: center;
  min-height: 32px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-muted);
  padding: 0.25rem 0.6rem;
  cursor: pointer;
  font-size: 0.72rem;
  transition: color 0.12s, border-color 0.12s, background 0.12s;
}

.twinkle-mobile-tag-chip:hover {
  color: var(--color-text);
  border-color: var(--color-muted-soft);
}

.twinkle-mobile-tag-chip.active {
  color: var(--color-info);
  border-color: color-mix(in srgb, var(--color-info) 46%, transparent);
  background: color-mix(in srgb, var(--color-info) 10%, transparent);
}

@media (max-width: 767px) {
  .twinkle-mobile-filter-panel {
    display: block;
    padding: 0.85rem;
    margin: 0 0 0.75rem 0;
    border: 1px solid var(--color-border);
    background: var(--color-surface);
  }
}
```

Keep the existing mobile rule that hides `.twinkle-archive`, resets `.twinkle-layout`, and adjusts `.twinkle-feed`.

- [ ] **Step 6: Run Twinkle tests and build**

Run:

```bash
uv run pytest tests/test_ui_static.py::test_twinkle_template_has_mobile_filter_region tests/test_ui_static.py::test_twinkle_tags_render_as_buttons_with_pressed_state -v
uv run python scripts/build_site.py
```

Expected: tests PASS and build completes.

- [ ] **Step 7: Commit Twinkle filter work**

Run:

```bash
git add tests/test_ui_static.py templates/pages/twinkle.html src/twinkle-feed.js style.css
git commit -m "feat: improve twinkle mobile filters"
```

## Task 4: Home Graph Fullscreen Mode

**Files:**
- Modify: `tests/test_ui_static.py`
- Modify: `templates/pages/home.html`
- Modify: `src/home-graph.js`
- Modify: `style.css`

- [ ] **Step 1: Add failing tests for explicit graph fullscreen mode**

Append these tests to `tests/test_ui_static.py`:

```python
def test_home_template_uses_explicit_graph_controls():
    html = read("templates/pages/home.html")
    assert 'id="graph-open-btn"' in html
    assert 'id="graph-close-btn"' in html
    assert "Explore graph" in html


def test_home_graph_removes_pull_gesture_and_uses_fullscreen_mode():
    js = read("src/home-graph.js")
    assert "startPullToExpand" not in js
    assert "touchstart" not in js
    assert "touchmove" not in js
    assert "graph-fullscreen" in js
    assert "graph-modal-open" in js
    assert ".resize()" in js
```

- [ ] **Step 2: Run graph tests and confirm they fail**

Run:

```bash
uv run pytest tests/test_ui_static.py::test_home_template_uses_explicit_graph_controls tests/test_ui_static.py::test_home_graph_removes_pull_gesture_and_uses_fullscreen_mode -v
```

Expected: FAIL because the template still uses pull/back controls and the JS still contains touch gesture handling.

- [ ] **Step 3: Replace graph controls in `templates/pages/home.html`**

Inside `<section id="post-graph">`, replace:

```html
    <div id="graph-hint" style="text-align:center;font-size:0.65rem;color:#2a2a2a;letter-spacing:2px;padding:0.3rem 0;user-select:none">↑ PULL</div>
    <div class="graph-container" id="graph-container"></div>
    <div id="graph-zoom-controls">
      <button class="zoom-preset active" data-zoom="1">1x</button>
      <button class="zoom-preset" data-zoom="2">2x</button>
      <button class="zoom-preset" data-zoom="2.5">2.5x</button>
    </div>
    <button id="graph-back-btn" type="button">↓ BACK</button>
```

with:

```html
    <div class="graph-toolbar">
      <span class="graph-toolbar-label">Knowledge Graph</span>
      <button id="graph-open-btn" type="button">Explore graph</button>
    </div>
    <div class="graph-stage">
      <div class="graph-container" id="graph-container"></div>
      <button id="graph-close-btn" type="button" aria-label="그래프 닫기">Close</button>
      <div id="graph-zoom-controls">
        <button class="zoom-preset active" data-zoom="1">1x</button>
        <button class="zoom-preset" data-zoom="2">2x</button>
        <button class="zoom-preset" data-zoom="2.5">2.5x</button>
      </div>
    </div>
```

- [ ] **Step 4: Replace `src/home-graph.js`**

Replace the full file with:

```javascript
// home-graph.js — home page graph: init, random node pulse, fullscreen mode, zoom presets.
// Reads data URLs from current script's dataset:
//   data-graph, data-posts, data-twinkles, data-posts-base
//
// Required globals: cytoscape, fetchGraph, fetchPosts, renderPostList, initGraph

(function () {
  const ds = document.currentScript ? document.currentScript.dataset : {};
  const GRAPH_URL = ds.graph;
  const POSTS_URL = ds.posts;
  const TWINKLES_URL = ds.twinkles;
  const POSTS_BASE = ds.postsBase || '../posts/';

  startZoomPresets();
  startGraph();

  async function startGraph() {
    const graphData = await fetchGraph(GRAPH_URL);
    const posts = await fetchPosts(POSTS_URL);
    const twinkles = await fetch(TWINKLES_URL)
      .then(r => r.ok ? r.json() : [])
      .catch(() => []);

    const hasGraph = graphData && graphData.nodes.length > 1;
    if (!hasGraph) {
      document.getElementById('graph-container').style.display = 'none';
      document.getElementById('graph-fallback').style.display = '';
      renderPostList(posts, document.getElementById('posts-container'), POSTS_BASE);
      return;
    }

    const cy = initGraph(document.getElementById('graph-container'), graphData, {
      onNodeClick: slug => { window.location.href = POSTS_BASE + slug + '/'; },
      userZoomingEnabled: false,
      twinkles,
    });
    window.__indexCy = cy;
    startPulse(cy);
    startFullscreenMode(cy);
  }

  function startPulse(cy) {
    const SCALE = 1.7, GROW_MS = 500, HOLD_MS = 13000, SHRINK_MS = 500;
    const INTERVAL_MS = GROW_MS + HOLD_MS;
    const origSizes = {};
    cy.one('layoutstop', () => {
      cy.nodes().forEach(node => {
        origSizes[node.id()] = {
          w: parseFloat(node.style('width')),
          h: parseFloat(node.style('height')),
        };
      });
      pulse();
    });
    setInterval(pulse, INTERVAL_MS);

    function pulse() {
      if (!Object.keys(origSizes).length) return;
      const nodes = cy.nodes().toArray();
      const count = 2 + Math.floor(Math.random() * 2);
      const picks = nodes.slice().sort(() => Math.random() - 0.5).slice(0, Math.min(count, nodes.length));
      picks.forEach(node => {
        const orig = origSizes[node.id()];
        if (!orig) return;
        node.animate(
          { style: { width: orig.w * SCALE, height: orig.h * SCALE } },
          { duration: GROW_MS, easing: 'ease-in-out-quad', complete: () => {
            setTimeout(() => {
              node.animate(
                { style: { width: orig.w, height: orig.h } },
                { duration: SHRINK_MS, easing: 'ease-in-out-quad' }
              );
            }, HOLD_MS);
          }}
        );
      });
    }
  }

  function refreshGraphFrame(cy) {
    requestAnimationFrame(() => {
      cy.resize();
      cy.fit(undefined, 36);
    });
  }

  function startFullscreenMode(cy) {
    const section = document.getElementById('post-graph');
    const openBtn = document.getElementById('graph-open-btn');
    const closeBtn = document.getElementById('graph-close-btn');
    if (!section || !openBtn || !closeBtn) return;

    function open() {
      section.classList.add('graph-fullscreen');
      document.body.classList.add('graph-modal-open');
      refreshGraphFrame(cy);
    }

    function close() {
      section.classList.remove('graph-fullscreen');
      document.body.classList.remove('graph-modal-open');
      refreshGraphFrame(cy);
    }

    openBtn.addEventListener('click', open);
    closeBtn.addEventListener('click', close);
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && section.classList.contains('graph-fullscreen')) close();
    });
  }

  function startZoomPresets() {
    const buttons = document.querySelectorAll('.zoom-preset');
    if (!buttons.length) return;
    let baseZoom = null;
    const center = () => {
      const cy = window.__indexCy;
      if (!cy) return null;
      return { x: cy.container().offsetWidth / 2, y: cy.container().offsetHeight / 2 };
    };
    buttons.forEach(btn => {
      btn.addEventListener('click', () => {
        const cy = window.__indexCy;
        if (!cy) return;
        if (baseZoom === null) baseZoom = cy.zoom();
        cy.zoom({ level: baseZoom * parseFloat(btn.dataset.zoom), renderedPosition: center() });
        buttons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      });
    });
  }
})();
```

- [ ] **Step 5: Add fullscreen graph CSS**

Add this block near the graph container CSS in `style.css`:

```css
.graph-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.6rem;
}

.graph-toolbar-label {
  color: var(--color-muted);
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 1.4px;
}

#graph-open-btn,
#graph-close-btn {
  border: 1px solid color-mix(in srgb, var(--color-info) 45%, transparent);
  background: color-mix(in srgb, var(--color-info) 8%, transparent);
  color: var(--color-info);
  padding: 0.35rem 0.7rem;
  font-size: 0.78rem;
}

.graph-stage {
  position: relative;
}

#graph-close-btn {
  display: none;
}

body.graph-modal-open {
  overflow: hidden;
}

#post-graph.graph-fullscreen {
  position: fixed;
  inset: 0;
  z-index: 200;
  padding: 0.75rem;
  background: var(--color-bg);
}

#post-graph.graph-fullscreen .graph-toolbar {
  display: none;
}

#post-graph.graph-fullscreen .graph-stage {
  height: 100%;
}

#post-graph.graph-fullscreen .graph-container {
  height: calc(100vh - 1.5rem);
  margin-bottom: 0;
}

#post-graph.graph-fullscreen #graph-close-btn {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
  display: inline-flex;
  z-index: 2;
}

#post-graph.graph-fullscreen #graph-zoom-controls {
  position: absolute;
  left: 0.75rem;
  bottom: 0.75rem;
  z-index: 2;
}
```

- [ ] **Step 6: Run graph tests and build**

Run:

```bash
uv run pytest tests/test_ui_static.py::test_home_template_uses_explicit_graph_controls tests/test_ui_static.py::test_home_graph_removes_pull_gesture_and_uses_fullscreen_mode -v
uv run python scripts/build_site.py
```

Expected: tests PASS and build completes.

- [ ] **Step 7: Commit graph fullscreen mode**

Run:

```bash
git add tests/test_ui_static.py templates/pages/home.html src/home-graph.js style.css
git commit -m "feat: replace home graph pull gesture with fullscreen mode"
```

## Task 5: Home Blog Activity Statistics

**Files:**
- Modify: `tests/test_ui_static.py`
- Modify: `templates/pages/home.html`
- Create: `src/home-stats.js`
- Modify: `style.css`

- [ ] **Step 1: Add failing tests for home stats**

Append these tests to `tests/test_ui_static.py`:

```python
def test_home_template_includes_stats_mount_and_script():
    html = read("templates/pages/home.html")
    assert 'id="home-stats"' in html
    assert 'src="{{ root }}src/home-stats.js"' in html
    assert 'data-posts="{{ root }}blog/posts.json"' in html
    assert 'data-graph="{{ root }}blog/graph.json"' in html
    assert 'data-twinkles="{{ root }}twinkle/twinkles.json"' in html


def test_home_stats_module_computes_static_blog_stats():
    js = read("src/home-stats.js")
    assert "renderHomeStats" in js
    assert "buildHeatmapDays" in js
    assert "last90Days" in js
    assert "topTags" in js
    assert "twinkleCount" in js
```

- [ ] **Step 2: Run home stats tests and confirm they fail**

Run:

```bash
uv run pytest tests/test_ui_static.py::test_home_template_includes_stats_mount_and_script tests/test_ui_static.py::test_home_stats_module_computes_static_blog_stats -v
```

Expected: FAIL because the stats mount and script do not exist.

- [ ] **Step 3: Add the stats section to `templates/pages/home.html`**

Insert this section after `</section>` for `post-graph` and before `<section id="about-teaser">`:

```html
  <section id="home-stats" class="home-stats" aria-label="블로그 활동 통계">
    <div class="home-stats-header">
      <span class="label--slash">Stats</span>
      <h2>Blog Activity</h2>
    </div>
    <div class="home-stats-grid" id="home-stats-grid"></div>
    <div class="home-heatmap" id="home-heatmap" aria-label="포스팅 활동 히트맵"></div>
    <div class="home-top-tags" id="home-top-tags"></div>
  </section>
```

Add this script before the existing `src/home-graph.js` script:

```html
<script src="{{ root }}src/home-stats.js" data-posts="{{ root }}blog/posts.json" data-graph="{{ root }}blog/graph.json" data-twinkles="{{ root }}twinkle/twinkles.json"></script>
```

- [ ] **Step 4: Create `src/home-stats.js`**

Create `src/home-stats.js` with:

```javascript
// home-stats.js — render static blog activity stats on the home page.
(function () {
  const ds = document.currentScript ? document.currentScript.dataset : {};
  const POSTS_URL = ds.posts;
  const GRAPH_URL = ds.graph;
  const TWINKLES_URL = ds.twinkles;

  function parseDate(value) {
    const date = new Date(value + 'T00:00:00');
    return Number.isNaN(date.getTime()) ? null : date;
  }

  function daysBetween(a, b) {
    const ms = 24 * 60 * 60 * 1000;
    return Math.floor((a - b) / ms);
  }

  function countRecentPosts(posts, now, windowDays) {
    return posts.filter(post => {
      const date = parseDate(post.date);
      return date && daysBetween(now, date) >= 0 && daysBetween(now, date) < windowDays;
    }).length;
  }

  function getTopTags(posts, limit) {
    const counts = new Map();
    posts.forEach(post => {
      (post.tags || []).forEach(tag => counts.set(tag, (counts.get(tag) || 0) + 1));
    });
    return [...counts.entries()]
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
      .slice(0, limit)
      .map(([tag, count]) => ({ tag, count }));
  }

  function buildHeatmapDays(posts, now, dayCount) {
    const counts = new Map();
    posts.forEach(post => {
      if (post.date) counts.set(post.date, (counts.get(post.date) || 0) + 1);
    });
    const days = [];
    for (let i = dayCount - 1; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(now.getDate() - i);
      const key = date.toISOString().slice(0, 10);
      days.push({ date: key, count: counts.get(key) || 0 });
    }
    return days;
  }

  function levelForCount(count) {
    if (count >= 3) return 3;
    if (count === 2) return 2;
    if (count === 1) return 1;
    return 0;
  }

  function renderStatCard(label, value, detail) {
    return `<article class="home-stat-card">
      <span class="home-stat-label">${label}</span>
      <strong>${value}</strong>
      <span class="home-stat-detail">${detail}</span>
    </article>`;
  }

  function renderHomeStats(posts, graph, twinkles) {
    const grid = document.getElementById('home-stats-grid');
    const heatmap = document.getElementById('home-heatmap');
    const tags = document.getElementById('home-top-tags');
    if (!grid || !heatmap || !tags) return;

    const now = new Date();
    const last90Days = countRecentPosts(posts, now, 90);
    const notebookCount = posts.filter(post => post.notebook).length;
    const graphEdges = graph && Array.isArray(graph.edges) ? graph.edges.length : 0;
    const twinkleCount = Array.isArray(twinkles) ? twinkles.length : 0;
    const topTags = getTopTags(posts, 6);

    grid.innerHTML = [
      renderStatCard('Posts', posts.length, 'published notes'),
      renderStatCard('Last 90 days', last90Days, 'recent posts'),
      renderStatCard('Notebooks', notebookCount, 'interactive posts'),
      renderStatCard('Graph links', graphEdges, 'content connections'),
      renderStatCard('Twinkles', twinkleCount, 'short notes'),
    ].join('');

    heatmap.innerHTML = buildHeatmapDays(posts, now, 84).map(day =>
      `<span class="heatmap-day level-${levelForCount(day.count)}" title="${day.date}: ${day.count} posts"></span>`
    ).join('');

    tags.innerHTML = topTags.map(item =>
      `<span class="home-top-tag"><span>${item.tag}</span><strong>${item.count}</strong></span>`
    ).join('');
  }

  async function start() {
    const [posts, graph, twinkles] = await Promise.all([
      fetch(POSTS_URL).then(r => r.ok ? r.json() : []),
      fetch(GRAPH_URL).then(r => r.ok ? r.json() : null).catch(() => null),
      fetch(TWINKLES_URL).then(r => r.ok ? r.json() : []).catch(() => []),
    ]);
    renderHomeStats(Array.isArray(posts) ? posts : [], graph, Array.isArray(twinkles) ? twinkles : []);
  }

  start().catch(() => {});
})();
```

- [ ] **Step 5: Add home stats CSS**

Add this block near the home/about teaser styles in `style.css`:

```css
.home-stats {
  margin: 2rem 0;
  padding: 1.25rem 0;
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
}

.home-stats-header {
  margin-bottom: 1rem;
}

.home-stats-header h2 {
  margin: 0.2rem 0 0;
  font-size: 1.15rem;
}

.home-stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 0.65rem;
  margin-bottom: 1rem;
}

.home-stat-card {
  margin: 0;
  padding: 0.8rem;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
}

.home-stat-label,
.home-stat-detail {
  display: block;
  color: var(--color-muted);
  font-size: 0.68rem;
}

.home-stat-card strong {
  display: block;
  color: var(--color-text);
  font-size: 1.45rem;
  line-height: 1.2;
  margin: 0.2rem 0;
}

.home-heatmap {
  display: grid;
  grid-template-columns: repeat(21, 1fr);
  gap: 3px;
  margin-bottom: 0.9rem;
  max-width: 520px;
}

.heatmap-day {
  aspect-ratio: 1;
  min-width: 8px;
  background: var(--color-surface);
  border: 1px solid color-mix(in srgb, var(--color-border) 70%, transparent);
}

.heatmap-day.level-1 { background: color-mix(in srgb, var(--color-info) 26%, var(--color-surface)); }
.heatmap-day.level-2 { background: color-mix(in srgb, var(--color-info) 50%, var(--color-surface)); }
.heatmap-day.level-3 { background: color-mix(in srgb, var(--color-accent) 70%, var(--color-surface)); }

.home-top-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.home-top-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.25rem 0.55rem;
  border: 1px solid var(--color-border);
  color: var(--color-muted);
  font-size: 0.72rem;
}

.home-top-tag strong {
  color: var(--color-info);
  font-size: 0.72rem;
}
```

- [ ] **Step 6: Run home stats tests and build**

Run:

```bash
uv run pytest tests/test_ui_static.py::test_home_template_includes_stats_mount_and_script tests/test_ui_static.py::test_home_stats_module_computes_static_blog_stats -v
uv run python scripts/build_site.py
```

Expected: tests PASS and build completes.

- [ ] **Step 7: Commit home statistics**

Run:

```bash
git add tests/test_ui_static.py templates/pages/home.html src/home-stats.js style.css
git commit -m "feat: add home blog activity stats"
```

## Task 6: Integrated Verification And Visual Pass

**Files:**
- Modify only files needed for small visual corrections found during verification.

- [ ] **Step 1: Run the full automated test suite**

Run:

```bash
uv run pytest
```

Expected: all tests PASS.

- [ ] **Step 2: Run the static site build**

Run:

```bash
uv run python scripts/build_site.py
```

Expected: build prints generated page paths ending with `Done. 5 pages + 8 posts built.`

- [ ] **Step 3: Start the local preview server**

Run:

```bash
python3 -m http.server 8080
```

Expected: server prints `Serving HTTP on 0.0.0.0 port 8080` or equivalent. Keep this process running until browser verification is complete.

- [ ] **Step 4: Verify mobile home behavior in browser**

Open `http://localhost:8080/` at 375px wide and verify:

```text
Mobile header is visible.
Desktop sidebar is hidden.
Menu button opens the drawer.
Graph preview does not resize while pulling down.
Explore graph opens fullscreen mode.
Close exits fullscreen mode.
Zoom buttons remain visible and clickable in fullscreen mode.
Blog stats render with cards, heatmap, and top tags.
No header overlaps content.
```

- [ ] **Step 5: Verify mobile Twinkle behavior in browser**

Open `http://localhost:8080/twinkle/` at 375px wide and verify:

```text
Mobile header is visible.
Desktop Twinkle archive is hidden.
Filter panel is visible near the top of the feed.
Tag buttons are easy to tap.
Selecting a tag filters cards.
Selecting 전체 clears the filter.
Active filter does not rely on pink.
```

- [ ] **Step 6: Verify desktop behavior in browser**

Open `http://localhost:8080/` and `http://localhost:8080/twinkle/` at 1280px wide and verify:

```text
Desktop sidebar is visible.
Mobile header is hidden.
Home graph preview and fullscreen mode work.
Twinkle archive remains fixed on the right.
Footer does not sit underneath the archive.
Theme accents look less dominated by pink.
```

- [ ] **Step 7: Fix only verification defects**

If verification reveals a concrete defect, make the smallest scoped change in the affected file and rerun:

```bash
uv run pytest
uv run python scripts/build_site.py
```

Expected: all tests PASS and build completes.

- [ ] **Step 8: Commit verification corrections**

If files changed during verification, run:

```bash
git add tests/test_ui_static.py templates/partials/sidebar.html templates/pages/home.html templates/pages/twinkle.html src/sidebar.js src/home-graph.js src/home-stats.js src/twinkle-feed.js style.css
git commit -m "fix: polish responsive UI verification issues"
```

If no files changed during verification, do not create an empty commit.

## Self-Review Notes

- Spec coverage: mobile header/drawer is Task 2, Twinkle mobile filters are Task 3, graph pull gesture removal and fullscreen mode are Task 4, static blog statistics are Task 5, theme token cleanup is Task 1, verification is Task 6.
- Visitor counts are excluded from all tasks.
- Python pipeline files are not modified.
- Static tests are added before each implementation slice.
- Each implementation task ends with a targeted test run, site build, and commit.
