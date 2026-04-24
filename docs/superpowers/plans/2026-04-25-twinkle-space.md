# Twinkle 공간 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 짧은 단상·디버깅 기록·아이디어 스케치 전용 경량 콘텐츠 섹션(`/twinkle/`)을 구축한다.

**Architecture:** `twinkle/*.md` 파일을 `twinkle_update.py`가 스캔해 `twinkle/twinkles.json`을 생성하고, `twinkle/index.html`이 이를 fetch해 피드(좌) + 아카이브(우) 레이아웃으로 렌더링한다. 태그 필터, 아카이브 클릭 재정렬, URL 앵커, sessionStorage 펼침 상태 유지를 지원한다.

**Tech Stack:** Python 3.10+ (pyyaml), 순수 HTML/CSS/JS, Pico.css v2 (다크 테마)

---

## 파일 맵

| 경로 | 작업 |
|------|------|
| `scripts/twinkle_update.py` | 신규 — twinkle 스캐너 + JSON 생성 |
| `scripts/test_twinkle_update.py` | 신규 — 단위 테스트 |
| `twinkle/images/.gitkeep` | 신규 — 디렉토리 플레이스홀더 |
| `twinkle/2026-04-25-sample-a.md` | 신규 — 샘플 트윈클 A |
| `twinkle/2026-04-24-sample-b.md` | 신규 — 샘플 트윈클 B |
| `twinkle/2026-04-20-sample-c.md` | 신규 — 샘플 트윈클 C (긴 본문) |
| `twinkle/index.html` | 신규 — 피드 + 아카이브 페이지 |
| `scripts/post_update.py` | 수정 — twinkle_update import + 호출 |
| `style.css` | 수정 — twinkle 레이아웃 + 카드 스타일 |
| `index.html` | 수정 — 사이드바 ✦ 버튼 |
| `blog/index.html` | 수정 — 사이드바 ✦ 버튼 |
| `posts/_template/index.html` | 수정 — 사이드바 ✦ 버튼 |

---

## Task 1: scripts/twinkle_update.py + 테스트

**Files:**
- Create: `scripts/test_twinkle_update.py`
- Create: `scripts/twinkle_update.py`

- [ ] **Step 1: 테스트 파일 작성**

`scripts/test_twinkle_update.py`:
```python
import json
import pytest
from pathlib import Path


def make_md(tmp_path, name, fm_lines, body):
    p = tmp_path / name
    p.write_text(f"---\n{fm_lines}\n---\n{body}", encoding="utf-8")
    return p


def test_scan_twinkles_parses_frontmatter(monkeypatch, tmp_path):
    import twinkle_update
    monkeypatch.setattr(twinkle_update, "TWINKLE_DIR", tmp_path)
    make_md(tmp_path, "2026-04-24-test.md",
            "title: 테스트\ndate: 2026-04-24\ntags: [딥러닝]", "본문 내용")
    result = twinkle_update.scan_twinkles()
    assert len(result) == 1
    assert result[0]["slug"] == "2026-04-24-test"
    assert result[0]["title"] == "테스트"
    assert result[0]["date"] == "2026-04-24"
    assert result[0]["tags"] == ["딥러닝"]
    assert result[0]["content"] == "본문 내용"


def test_scan_twinkles_skips_no_title(monkeypatch, tmp_path):
    import twinkle_update
    monkeypatch.setattr(twinkle_update, "TWINKLE_DIR", tmp_path)
    make_md(tmp_path, "2026-04-24-notitle.md", "date: 2026-04-24", "내용")
    result = twinkle_update.scan_twinkles()
    assert result == []


def test_scan_twinkles_sorted_desc(monkeypatch, tmp_path):
    import twinkle_update
    monkeypatch.setattr(twinkle_update, "TWINKLE_DIR", tmp_path)
    make_md(tmp_path, "2026-04-20-older.md", "title: 오래된\ndate: 2026-04-20", "")
    make_md(tmp_path, "2026-04-24-newer.md", "title: 새로운\ndate: 2026-04-24", "")
    result = twinkle_update.scan_twinkles()
    assert result[0]["date"] == "2026-04-24"
    assert result[1]["date"] == "2026-04-20"


def test_scan_twinkles_ignores_subdirs(monkeypatch, tmp_path):
    import twinkle_update
    monkeypatch.setattr(twinkle_update, "TWINKLE_DIR", tmp_path)
    make_md(tmp_path, "2026-04-24-valid.md", "title: 유효\ndate: 2026-04-24", "")
    subdir = tmp_path / "images"
    subdir.mkdir()
    (subdir / "ignore.md").write_text("---\ntitle: 무시\ndate: 2026-04-24\n---\n", encoding="utf-8")
    result = twinkle_update.scan_twinkles()
    assert len(result) == 1


def test_update_twinkles_json_writes_file(monkeypatch, tmp_path):
    import twinkle_update
    monkeypatch.setattr(twinkle_update, "TWINKLES_JSON", tmp_path / "twinkles.json")
    twinkles = [{"slug": "a", "date": "2026-04-24", "title": "A", "tags": [], "content": "내용"}]
    changed = twinkle_update.update_twinkles_json(twinkles)
    assert changed is True
    data = json.loads((tmp_path / "twinkles.json").read_text())
    assert data[0]["slug"] == "a"


def test_update_twinkles_json_no_change(monkeypatch, tmp_path):
    import twinkle_update
    json_path = tmp_path / "twinkles.json"
    monkeypatch.setattr(twinkle_update, "TWINKLES_JSON", json_path)
    twinkles = [{"slug": "a", "date": "2026-04-24", "title": "A", "tags": [], "content": "내용"}]
    twinkle_update.update_twinkles_json(twinkles)
    changed = twinkle_update.update_twinkles_json(twinkles)
    assert changed is False
```

- [ ] **Step 2: 테스트 실행 — FAIL 확인**

```bash
cd scripts && uv run pytest test_twinkle_update.py -v
```

Expected: `ModuleNotFoundError: No module named 'twinkle_update'`

- [ ] **Step 3: twinkle_update.py 구현**

`scripts/twinkle_update.py`:
```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pyyaml",
# ]
# ///
"""
twinkle/*.md 파일을 스캔해 twinkle/twinkles.json을 생성한다.

Usage:
  uv run python twinkle_update.py
"""

import json
import sys
from pathlib import Path

from posts_list_update import parse_frontmatter_text

ROOT = Path(__file__).resolve().parent.parent
TWINKLE_DIR = ROOT / "twinkle"
TWINKLES_JSON = TWINKLE_DIR / "twinkles.json"


def scan_twinkles() -> list[dict]:
    """twinkle/*.md 스캔 → 메타데이터 + 본문 목록 (날짜 내림차순)."""
    twinkles = []
    for path in sorted(TWINKLE_DIR.glob("*.md")):
        fm, body = parse_frontmatter_text(path.read_text(encoding="utf-8"))
        if not fm.get("title"):
            print(f"  [SKIP] {path.name}: frontmatter에 title 없음", file=sys.stderr)
            continue
        twinkles.append({
            "slug": path.stem,
            "date": str(fm.get("date", "")),
            "title": str(fm["title"]),
            "tags": [str(t) for t in fm.get("tags", [])],
            "content": body.strip(),
        })
    twinkles.sort(key=lambda t: t["date"], reverse=True)
    return twinkles


def update_twinkles_json(twinkles: list[dict] | None = None) -> bool:
    """twinkles.json 생성/업데이트. 변경이 있으면 True 반환."""
    if twinkles is None:
        twinkles = scan_twinkles()
    new_text = json.dumps(twinkles, ensure_ascii=False, indent=2)
    old_text = TWINKLES_JSON.read_text(encoding="utf-8") if TWINKLES_JSON.exists() else ""
    if new_text == old_text:
        return False
    TWINKLES_JSON.write_text(new_text, encoding="utf-8")
    return True


def main():
    print("트윈클 스캔 중...")
    twinkles = scan_twinkles()
    print(f"  {len(twinkles)}개 트윈클 발견")
    changed = update_twinkles_json(twinkles)
    print("twinkles.json 업데이트됨" if changed else "twinkles.json 변경 없음")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 테스트 실행 — PASS 확인**

```bash
cd scripts && uv run pytest test_twinkle_update.py -v
```

Expected:
```
PASSED test_scan_twinkles_parses_frontmatter
PASSED test_scan_twinkles_skips_no_title
PASSED test_scan_twinkles_sorted_desc
PASSED test_scan_twinkles_ignores_subdirs
PASSED test_update_twinkles_json_writes_file
PASSED test_update_twinkles_json_no_change
6 passed
```

- [ ] **Step 5: 샘플 트윈클 파일 생성**

`twinkle/images/.gitkeep` — 빈 파일 생성:
```bash
mkdir -p twinkle/images && touch twinkle/images/.gitkeep
```

`twinkle/2026-04-25-sample-a.md`:
```markdown
---
title: "BatchNorm 위치가 결정적이었다"
date: 2026-04-25
tags: [딥러닝, 디버깅]
---
gradient vanishing 디버깅 중 발견 — Conv → BN → ReLU 순서가 맞다. BN을 ReLU 뒤에 두면 gradient flow가 눈에 띄게 나빠진다. 논문에서는 activation 이전 배치 정규화를 권장하지만 실제로는 구조마다 다름.
```

`twinkle/2026-04-24-sample-b.md`:
```markdown
---
title: "sparse attention 아이디어 스케치"
date: 2026-04-24
tags: [아이디어, 트랜스포머]
---
긴 시퀀스에서 full attention 대신 local window + global token 방식으로 O(n²) → O(n√n) 가능. Flash Attention과 조합하면 메모리도 절약. 실험 필요.
```

`twinkle/2026-04-20-sample-c.md`:
```markdown
---
title: "PyTorch DataLoader 병목 디버깅"
date: 2026-04-20
tags: [파이썬, 딥러닝]
---
학습 루프가 GPU보다 CPU bound인 것 같아서 프로파일링해봄. `num_workers=0`이 문제였다. `num_workers=4`로 바꾸고 `pin_memory=True` 추가하니 epoch당 12분 → 4분으로 단축됐다. `persistent_workers=True`도 추가하면 worker 재생성 비용이 사라진다. 다음에는 처음부터 `torch.profiler`로 bottleneck을 먼저 찾자. 추측으로 설정 바꾸는 건 시간 낭비다. `torch.utils.data.DataLoader`의 기본 설정이 single-threaded라는 걸 까먹고 있었다. GPU utilization이 낮으면 항상 DataLoader 쪽을 먼저 의심할 것.
```

- [ ] **Step 6: 단독 실행 확인**

```bash
cd scripts && uv run python twinkle_update.py
```

Expected:
```
트윈클 스캔 중...
  3개 트윈클 발견
twinkles.json 업데이트됨
```

`twinkle/twinkles.json` 파일이 생성되고 3개 항목이 날짜 내림차순으로 있는지 확인.

- [ ] **Step 7: 커밋**

```bash
git add scripts/twinkle_update.py scripts/test_twinkle_update.py \
        twinkle/images/.gitkeep \
        twinkle/2026-04-25-sample-a.md twinkle/2026-04-24-sample-b.md twinkle/2026-04-20-sample-c.md \
        twinkle/twinkles.json
git commit -m "feat: add twinkle_update.py scanner and sample twinkles"
```

---

## Task 2: post_update.py 통합

**Files:**
- Modify: `scripts/post_update.py`

- [ ] **Step 1: import 추가 및 main() 마지막에 호출 추가**

`scripts/post_update.py` 상단 import 블록에 추가:
```python
from twinkle_update import update_twinkles_json
```

`main()` 함수 마지막 줄 뒤에 추가 (기존 `if not args.posts_only:` 블록 바깥):
```python
    # twinkle (ML 없음, 항상 실행)
    twinkle_changed = update_twinkles_json()
    print("twinkles.json 업데이트됨" if twinkle_changed else "twinkles.json 변경 없음")
```

최종 `main()` 끝부분:
```python
    if not args.posts_only:
        # 태그 반영된 posts로 graph.json 재생성
        update_graph(posts, force=False)

    # twinkle (ML 없음, 항상 실행)
    twinkle_changed = update_twinkles_json()
    print("twinkles.json 업데이트됨" if twinkle_changed else "twinkles.json 변경 없음")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 통합 실행 확인**

```bash
cd scripts && uv run python post_update.py --posts-only
```

Expected 출력 마지막 줄:
```
twinkles.json 변경 없음
```
(이미 Task 1에서 생성됐으므로 변경 없음)

- [ ] **Step 3: 커밋**

```bash
git add scripts/post_update.py
git commit -m "feat: integrate twinkle_update into post_update pipeline"
```

---

## Task 3: style.css — twinkle 스타일 추가

**Files:**
- Modify: `style.css`

- [ ] **Step 1: style.css 파일 끝에 아래 블록 추가**

```css
/* ── Twinkle 공간 ─────────────────────────────────── */

.twinkle-layout {
  display: flex;
  gap: 0;
  min-height: 60vh;
}

.twinkle-feed {
  flex: 1;
  padding: 1rem 1rem 1rem 0;
  min-width: 0;
}

.twinkle-archive {
  width: 200px;
  flex-shrink: 0;
  border-left: 1px solid #1e1e1e;
  background: #080808;
  display: flex;
  position: relative;
}

.twinkle-archive-resize {
  cursor: col-resize;
  width: 16px;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 1rem;
  color: #2a2a2a;
  font-size: 0.8rem;
  flex-shrink: 0;
  user-select: none;
}

.twinkle-archive-inner {
  flex: 1;
  padding: 0.75rem;
  overflow-y: auto;
  min-width: 0;
}

.twinkle-card {
  border: 1px solid #2a0a28;
  background: #0d0d0d;
  padding: 1rem;
  margin-bottom: 0.75rem;
}

.twinkle-card.anchor {
  border-color: #4a62ff;
}

.twinkle-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  gap: 0.5rem;
}

.twinkle-card-date {
  color: #dc00c9;
  font-size: 0.7rem;
  white-space: nowrap;
  flex-shrink: 0;
}

.twinkle-card-body {
  color: #ccc;
  font-size: 0.85rem;
  line-height: 1.6;
  white-space: pre-wrap;
}

.twinkle-more-btn {
  background: none;
  border: none;
  color: #4a62ff;
  font-size: 0.7rem;
  cursor: pointer;
  padding: 0.3rem 0;
  display: block;
  margin-top: 0.4rem;
}

.archive-tag-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
  margin-bottom: 0.75rem;
}

.archive-tag-chip {
  display: inline-block;
  font-size: 0.6rem;
  color: #444;
  border: 1px solid #222;
  padding: 0.1rem 0.4rem;
  cursor: pointer;
  transition: color 0.1s, border-color 0.1s, background 0.1s;
}

.archive-tag-chip:hover {
  color: #777;
  border-color: #444;
}

.archive-tag-chip.active {
  color: #4a62ff;
  border-color: rgba(74, 98, 255, 0.5);
  background: rgba(74, 98, 255, 0.07);
}

.archive-list {
  border-left: 1px solid #1e1e1e;
  padding-left: 0.5rem;
}

.archive-item {
  padding: 0.35rem 0;
  border-bottom: 1px solid #111;
  cursor: pointer;
  font-size: 0.68rem;
  color: #444;
  transition: color 0.1s;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.archive-item:hover { color: #777; }
.archive-item.active { color: #dc00c9; }

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

- [ ] **Step 2: 커밋**

```bash
git add style.css
git commit -m "feat: add twinkle layout and card styles to style.css"
```

---

## Task 4: twinkle/index.html

**Files:**
- Create: `twinkle/index.html`

- [ ] **Step 1: twinkle/index.html 생성**

```html
<!DOCTYPE html>
<html lang="ko" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Twinkle — Ahrism</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">
  <link rel="stylesheet" href="../style.css">
</head>
<body data-page="2">
  <aside id="sidebar">
    <div class="sidebar-icons">
      <button class="sidebar-btn" data-label="Home" data-href="../">⌂</button>
      <button class="sidebar-btn" data-panel="about" data-label="About">◉</button>
      <button class="sidebar-btn" data-label="Blog" data-href="../blog/">≡</button>
      <button class="sidebar-btn active" data-label="Twinkle" data-href="../twinkle/">✦</button>
      <button class="sidebar-btn" data-label="GitHub" data-href="../github/">⬡</button>
    </div>
    <div id="panel-about" class="sidebar-panel">
      <div class="label">About</div>
      <p class="panel-placeholder">준비 중</p>
    </div>
  </aside>

  <div id="page-content">
  <main class="container">
    <div class="twinkle-layout">
      <div class="twinkle-feed" id="twinkle-feed">
        <div class="label">✦ TWINKLE</div>
        <p style="color:#555;font-size:0.85rem">로딩 중...</p>
      </div>
      <div class="twinkle-archive" id="twinkle-archive">
        <div class="twinkle-archive-resize" id="archive-resize-handle">⠿</div>
        <div class="twinkle-archive-inner">
          <div class="label">ARCHIVE</div>
          <div class="archive-tag-chips" id="archive-tags"></div>
          <div class="archive-list" id="archive-list"></div>
        </div>
      </div>
    </div>
  </main>
  </div>

  <script src="../sidebar.js"></script>
  <script>
(function () {
  const WINDOW_SIZE = 5;
  const PREVIEW_LEN = 300;
  const SS_KEY = 'twinkle-expanded';

  const state = {
    twinkles: [],
    anchor: null,
    tag: null,
    expanded: new Set(),
  };

  function loadExpanded() {
    try { return new Set(JSON.parse(sessionStorage.getItem(SS_KEY) || '[]')); }
    catch { return new Set(); }
  }

  function saveExpanded() {
    sessionStorage.setItem(SS_KEY, JSON.stringify([...state.expanded]));
  }

  function filterByTag(list) {
    if (!state.tag) return list;
    return list.filter(t => t.tags.includes(state.tag));
  }

  function getFeedWindow(list) {
    if (!state.anchor) return list.slice(0, WINDOW_SIZE);
    const idx = list.findIndex(t => t.slug === state.anchor);
    if (idx === -1) return list.slice(0, WINDOW_SIZE);
    const start = Math.max(0, idx - 2);
    const end = Math.min(list.length, start + WINDOW_SIZE);
    return list.slice(start, end);
  }

  function escapeHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function renderCard(t) {
    const isAnchor = t.slug === state.anchor;
    const isExpanded = state.expanded.has(t.slug);
    const needsTrunc = t.content.length > PREVIEW_LEN;
    const body = (needsTrunc && !isExpanded)
      ? escapeHtml(t.content.slice(0, PREVIEW_LEN)) + '...'
      : escapeHtml(t.content);
    const tagsHtml = t.tags.map(tag =>
      `<span class="tag">${escapeHtml(tag)}</span>`
    ).join(' ');
    const moreBtn = needsTrunc
      ? `<button class="twinkle-more-btn" data-slug="${t.slug}">${isExpanded ? '▲ 접기' : '▼ 더보기'}</button>`
      : '';
    return `
      <div class="twinkle-card${isAnchor ? ' anchor' : ''}" id="card-${t.slug}">
        <div class="twinkle-card-header">
          <span class="twinkle-card-date">${t.date}</span>
          <span>${tagsHtml}</span>
        </div>
        <div class="twinkle-card-body">${body}</div>
        ${moreBtn}
      </div>`;
  }

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

  function renderArchive() {
    const filtered = filterByTag(state.twinkles);
    const allTags = [...new Set(state.twinkles.flatMap(t => t.tags))];
    document.getElementById('archive-tags').innerHTML =
      ['전체', ...allTags].map(tag => {
        const isActive = tag === '전체' ? !state.tag : state.tag === tag;
        return `<span class="archive-tag-chip${isActive ? ' active' : ''}" data-tag="${tag}">${escapeHtml(tag)}</span>`;
      }).join('');
    document.getElementById('archive-list').innerHTML =
      filtered.map(t =>
        `<div class="archive-item${t.slug === state.anchor ? ' active' : ''}" data-slug="${t.slug}">
          <span class="archive-date">${t.date.slice(5)}</span>${escapeHtml(t.title)}
        </div>`
      ).join('');

    document.querySelectorAll('.archive-tag-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        state.tag = chip.dataset.tag === '전체' ? null : chip.dataset.tag;
        state.anchor = null;
        history.replaceState(null, '', location.pathname);
        renderFeed();
        renderArchive();
      });
    });
    document.querySelectorAll('.archive-item').forEach(item => {
      item.addEventListener('click', () => {
        state.anchor = item.dataset.slug;
        history.replaceState(null, '', '#' + item.dataset.slug);
        renderFeed();
        renderArchive();
      });
    });
  }

  function initResizeDrag() {
    const handle = document.getElementById('archive-resize-handle');
    const archive = document.getElementById('twinkle-archive');
    if (!handle || !archive) return;
    let startX, startW;
    handle.addEventListener('mousedown', e => {
      startX = e.clientX;
      startW = archive.offsetWidth;
      function onMove(e) {
        const newW = Math.max(120, Math.min(400, startW + (startX - e.clientX)));
        archive.style.width = newW + 'px';
      }
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', () => {
        document.removeEventListener('mousemove', onMove);
      }, { once: true });
    });
  }

  (async () => {
    state.expanded = loadExpanded();
    try {
      const res = await fetch('./twinkles.json');
      if (!res.ok) throw new Error(res.status);
      state.twinkles = await res.json();
    } catch (e) {
      document.getElementById('twinkle-feed').innerHTML =
        '<div class="label">✦ TWINKLE</div><p style="color:#555">twinkles.json 로드 실패.</p>';
      return;
    }
    const hash = location.hash.slice(1);
    if (hash && state.twinkles.some(t => t.slug === hash)) {
      state.anchor = hash;
    }
    renderFeed();
    renderArchive();
    initResizeDrag();
  })();
})();
  </script>
</body>
</html>
```

- [ ] **Step 2: 브라우저에서 확인**

```bash
cd /home/ahris/ahrism-pages && python3 -m http.server 8080
```

`http://localhost:8080/twinkle/` 접속 후 확인:
- 피드에 3개 카드 렌더링
- sample-c (긴 본문) 카드에 `▼ 더보기` 표시
- 더보기 클릭 → 펼침, 다시 클릭 → 접힘
- 아카이브 패널 오른쪽에 목록 표시
- 태그 칩 (딥러닝, 아이디어 등) 클릭 → 필터 적용
- 아카이브 항목 클릭 → 피드 재정렬 + URL `#slug` 변경
- 브라우저 창 767px 이하로 줄이면 아카이브 숨김
- 아카이브 `⠿` 핸들 드래그 → 너비 조절

- [ ] **Step 3: 커밋**

```bash
git add twinkle/index.html
git commit -m "feat: add twinkle/index.html with feed, archive, tag filter"
```

---

## Task 5: 사이드바 ✦ 버튼 추가

**Files:**
- Modify: `index.html`
- Modify: `blog/index.html`
- Modify: `posts/_template/index.html`

- [ ] **Step 1: index.html 사이드바 수정**

`index.html`에서 아래 줄을 찾아:
```html
      <button class="sidebar-btn" data-label="GitHub" data-href="./github/">⬡</button>
```

바로 위에 삽입:
```html
      <button class="sidebar-btn" data-label="Twinkle" data-href="./twinkle/">✦</button>
```

- [ ] **Step 2: blog/index.html 사이드바 수정**

`blog/index.html`에서 아래 줄을 찾아:
```html
      <button class="sidebar-btn" data-label="GitHub" data-href="../github/">⬡</button>
```

바로 위에 삽입:
```html
      <button class="sidebar-btn" data-label="Twinkle" data-href="../twinkle/">✦</button>
```

- [ ] **Step 3: posts/_template/index.html 사이드바 수정**

`posts/_template/index.html`에서 아래 줄을 찾아:
```html
      <button class="sidebar-btn" data-label="GitHub" data-href="../../github/">⬡</button>
```

바로 위에 삽입:
```html
      <button class="sidebar-btn" data-label="Twinkle" data-href="../../twinkle/">✦</button>
```

- [ ] **Step 4: 브라우저에서 확인**

`http://localhost:8080/` 와 `http://localhost:8080/blog/` 에서 사이드바에 ✦ 버튼이 보이는지 확인. 클릭 시 `/twinkle/`로 이동하는지 확인.

- [ ] **Step 5: 커밋**

```bash
git add index.html blog/index.html posts/_template/index.html
git commit -m "feat: add Twinkle sidebar button to index, blog, and post template"
```

---

## 최종 검증

- [ ] `uv run python scripts/twinkle_update.py` — twinkles.json 정상 생성
- [ ] `uv run python scripts/post_update.py --posts-only` — 마지막 줄에 twinkles.json 관련 출력
- [ ] `http://localhost:8080/twinkle/` — 피드 + 아카이브 렌더링
- [ ] 아카이브 클릭 → 피드 재정렬 + URL `#slug`
- [ ] 태그 필터 → 피드 + 아카이브 동시 필터링
- [ ] 더보기 클릭 → 펼침, sessionStorage에 저장됨
- [ ] 뒤로가기 후 재방문 → 펼침 상태 유지
- [ ] 767px 이하 뷰포트 → 아카이브 숨김
- [ ] `http://localhost:8080/` 사이드바 ✦ 클릭 → `/twinkle/` 이동

> **Note:** 기존 포스트(`posts/nn1/`, `posts/nn2/` 등)의 `index.html`은 이전에 템플릿을 복사한 파일이라 ✦ 버튼이 없다. 필요하다면 각 포스트 파일도 동일하게 수정할 것.
