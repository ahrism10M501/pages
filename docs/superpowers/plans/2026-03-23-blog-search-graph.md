# Blog Search & Graph Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 블로그에 키워드/TF-IDF 검색, 태그 필터, Cytoscape.js 그래프 탐색, 포스트별 서브그래프 추천 기능을 추가한다.

**Architecture:** Python 빌드 스크립트가 임베딩(ko-sroberta-multitask) + TF-IDF로 `graph.json`을 생성하고, 프론트엔드가 이를 소비한다. `app.js`는 데이터 레이어(검색/필터), `graph.js`는 Cytoscape.js 프레젠테이션 레이어를 담당한다.

**Tech Stack:** Python (sentence-transformers, scikit-learn, konlpy, uv), Cytoscape.js + fcose (CDN), vanilla JS

**Spec:** `docs/superpowers/specs/2026-03-23-blog-search-graph-design.md`

---

## File Map

| 파일 | 역할 | 상태 |
|------|------|------|
| `scripts/pyproject.toml` | uv 프로젝트, Python 의존성 | 생성 |
| `scripts/build_graph.py` | 임베딩 + TF-IDF → graph.json 생성 | 생성 |
| `scripts/test_build_graph.py` | build_graph.py 단위 테스트 | 생성 |
| `blog/graph.json` | 빌드 산출물 (노드/엣지/TF-IDF) | 생성 |
| `app.js` | 데이터 레이어: fetchGraph, searchPosts, filterByTags 추가 | 수정 |
| `graph.js` | Cytoscape.js 래퍼 (initGraph, highlightNodes, renderSubgraph) | 생성 |
| `style.css` | 검색바, 태그 필터, 뷰 토글, 슬라이더, 그래프 컨테이너 | 수정 |
| `blog/index.html` | 그래프/리스트 토글 뷰 + 검색/필터 UI | 수정 |
| `posts/_template/index.html` | 하단 서브그래프 섹션 | 수정 |

---

### Task 1: Python 프로젝트 초기화 (uv + pyproject.toml)

**Files:**
- Create: `scripts/pyproject.toml`

- [ ] **Step 1: scripts 디렉토리에 pyproject.toml 생성**

```toml
[project]
name = "ahrism-graph-builder"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "sentence-transformers>=3.0.0",
    "scikit-learn>=1.5.0",
    "konlpy>=0.6.0",
    "torch>=2.0.0",
]

[dependency-groups]
dev = ["pytest>=8.0.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.backends"
```

- [ ] **Step 2: .gitignore에 Python 아티팩트 추가**

프로젝트 루트 `.gitignore`에 추가:
```
scripts/.venv/
__pycache__/
*.pyc
```

- [ ] **Step 3: uv sync로 의존성 설치 확인**

Run: `cd scripts && uv sync`
Expected: 의존성 설치 완료, `.venv` 생성

- [ ] **Step 4: Mecab 사전 설치 확인**

Run: `cd scripts && uv run python -c "from konlpy.tag import Mecab; m = Mecab(); print(m.morphs('테스트 문장입니다'))"`
Expected: `['테스트', '문장', '입니다']` 또는 유사한 형태소 분석 결과. 만약 Mecab이 시스템에 없으면 `sudo apt install mecab mecab-ko-dic libmecab-dev` 실행.

- [ ] **Step 5: Commit**

```bash
git add scripts/pyproject.toml .gitignore
git commit -m "chore: init uv project for graph builder"
```

---

### Task 2: build_graph.py 핵심 로직 — 임베딩 + 유사도 계산

**Files:**
- Create: `scripts/build_graph.py`
- Create: `scripts/test_build_graph.py`

- [ ] **Step 1: 테스트 파일 생성 — 유사도 계산 테스트**

```python
# scripts/test_build_graph.py
import json
import pytest

def test_compute_similarities_returns_symmetric_matrix():
    """임베딩 기반 유사도 행렬이 대칭이고 대각선이 1.0인지 확인"""
    from build_graph import compute_similarities
    import numpy as np

    # 간단한 임베딩 3개 (정규화된 벡터)
    embeddings = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.7071, 0.7071, 0.0],
    ])
    sim = compute_similarities(embeddings)
    assert sim.shape == (3, 3)
    # 대칭
    assert abs(sim[0][1] - sim[1][0]) < 1e-6
    # 대각선 ≈ 1.0
    for i in range(3):
        assert abs(sim[i][i] - 1.0) < 1e-6


def test_build_edges_respects_threshold_and_max():
    """threshold 미만 엣지 제거, 노드당 max_edges 제한 확인"""
    from build_graph import build_edges
    import numpy as np

    slugs = ["a", "b", "c", "d"]
    # a-b: 0.9, a-c: 0.5, a-d: 0.2 (threshold 미만)
    # b-c: 0.4, b-d: 0.35, c-d: 0.6
    sim = np.array([
        [1.0, 0.9, 0.5, 0.2],
        [0.9, 1.0, 0.4, 0.35],
        [0.5, 0.4, 1.0, 0.6],
        [0.2, 0.35, 0.6, 1.0],
    ])
    edges = build_edges(sim, slugs, threshold=0.3, max_edges_per_node=2)
    # a-d (0.2) 는 threshold 미만이므로 제외
    sources_targets = [(e["source"], e["target"]) for e in edges]
    assert ("a", "d") not in sources_targets
    assert ("d", "a") not in sources_targets
    # 각 노드의 엣지 수가 max_edges_per_node 이하
    from collections import Counter
    counts = Counter()
    for e in edges:
        counts[e["source"]] += 1
        counts[e["target"]] += 1
    for node, count in counts.items():
        assert count <= 2, f"Node {node} has {count} edges, max is 2"


def test_extract_tfidf_keywords():
    """TF-IDF 키워드 추출이 상위 N개를 반환하는지 확인"""
    from build_graph import extract_tfidf_keywords

    texts = [
        "머신러닝 딥러닝 인공지능 모델 학습",
        "웹 개발 프론트엔드 자바스크립트 리액트",
        "머신러닝 모델 학습 데이터 전처리",
    ]
    keywords_list = extract_tfidf_keywords(texts, top_n=3)
    assert len(keywords_list) == 3
    for kw in keywords_list:
        assert len(kw) <= 3
        # 각 키워드는 (단어, 점수) 형태의 dict
        for word, score in kw.items():
            assert isinstance(word, str)
            assert isinstance(score, float)
            assert score > 0
```

- [ ] **Step 2: 테스트 실행 — 실패 확인**

Run: `cd scripts && uv run python -m pytest test_build_graph.py -v`
Expected: FAIL (build_graph 모듈 없음)

- [ ] **Step 3: build_graph.py 구현 — 핵심 함수**

```python
#!/usr/bin/env python3
"""blog/graph.json을 생성하는 빌드 스크립트.

Usage: cd scripts && uv run build_graph.py
"""

import json
import sys
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# --- 프로젝트 루트 경로 ---
ROOT = Path(__file__).resolve().parent.parent
POSTS_JSON = ROOT / "blog" / "posts.json"
POSTS_DIR = ROOT / "posts"
OUTPUT = ROOT / "blog" / "graph.json"

# --- 설정 ---
SIMILARITY_THRESHOLD = 0.3
MAX_EDGES_PER_NODE = 8
TFIDF_TOP_N = 20
MODEL_NAME = "jhgan/ko-sroberta-multitask"


def load_posts():
    """posts.json과 각 포스트의 content.md를 읽어 반환."""
    with open(POSTS_JSON, "r", encoding="utf-8") as f:
        posts = json.load(f)

    for post in posts:
        md_path = POSTS_DIR / post["slug"] / "content.md"
        if md_path.exists():
            post["content"] = md_path.read_text(encoding="utf-8")
        else:
            post["content"] = ""

    return posts


def get_post_text(post):
    """임베딩에 사용할 텍스트 조합: 제목 + 요약 + 본문."""
    parts = [post.get("title", ""), post.get("summary", ""), post.get("content", "")]
    return "\n".join(parts)


def compute_embeddings(texts):
    """sentence-transformers로 텍스트 임베딩 생성."""
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(MODEL_NAME)
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    return embeddings


def compute_similarities(embeddings):
    """cosine similarity 행렬 계산."""
    return cosine_similarity(embeddings)


def build_edges(sim_matrix, slugs, threshold=SIMILARITY_THRESHOLD, max_edges_per_node=MAX_EDGES_PER_NODE):
    """유사도 행렬에서 엣지 목록 생성. threshold 이상, 노드당 max_edges 제한."""
    n = len(slugs)
    # 각 노드별 후보 엣지를 weight 내림차순으로 정렬
    node_edges = {slug: [] for slug in slugs}

    for i in range(n):
        for j in range(i + 1, n):
            w = float(sim_matrix[i][j])
            if w >= threshold:
                node_edges[slugs[i]].append((j, w))
                node_edges[slugs[j]].append((i, w))

    # 각 노드별 상위 max_edges만 유지
    selected = set()
    for slug_idx, slug in enumerate(slugs):
        candidates = node_edges[slug]
        candidates.sort(key=lambda x: x[1], reverse=True)
        for other_idx, w in candidates[:max_edges_per_node]:
            pair = (min(slug_idx, other_idx), max(slug_idx, other_idx))
            selected.add(pair)

    edges = []
    for i, j in selected:
        edges.append({
            "source": slugs[i],
            "target": slugs[j],
            "weight": round(float(sim_matrix[i][j]), 4),
        })

    return edges


def extract_tfidf_keywords(texts, top_n=TFIDF_TOP_N):
    """각 텍스트에서 TF-IDF 상위 키워드 추출. Mecab 토크나이저 사용."""
    try:
        from konlpy.tag import Mecab
        mecab = Mecab()
        tokenizer = mecab.morphs
    except Exception:
        # Mecab 불가 시 공백 분리 폴백
        tokenizer = str.split

    vectorizer = TfidfVectorizer(tokenizer=tokenizer, max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(texts)
    feature_names = vectorizer.get_feature_names_out()

    keywords_list = []
    for i in range(tfidf_matrix.shape[0]):
        row = tfidf_matrix[i].toarray().flatten()
        top_indices = row.argsort()[-top_n:][::-1]
        kw = {}
        for idx in top_indices:
            if row[idx] > 0:
                kw[feature_names[idx]] = round(float(row[idx]), 4)
        keywords_list.append(kw)

    return keywords_list


def build_graph_json(posts, sim_matrix, keywords_list):
    """최종 graph.json 구조 생성."""
    slugs = [p["slug"] for p in posts]
    edges = build_edges(sim_matrix, slugs)

    nodes = []
    for i, post in enumerate(posts):
        nodes.append({
            "id": post["slug"],
            "title": post["title"],
            "date": post["date"],
            "tags": post["tags"],
            "summary": post.get("summary", ""),
            "tfidf": keywords_list[i],
        })

    return {"nodes": nodes, "edges": edges}


def main():
    posts = load_posts()

    if not posts:
        OUTPUT.write_text(json.dumps({"nodes": [], "edges": []}, ensure_ascii=False, indent=2))
        print("No posts found. Empty graph.json written.")
        return

    texts = [get_post_text(p) for p in posts]

    print(f"Computing embeddings for {len(posts)} posts...")
    embeddings = compute_embeddings(texts)

    print("Computing similarities...")
    sim_matrix = compute_similarities(embeddings)

    print("Extracting TF-IDF keywords...")
    keywords_list = extract_tfidf_keywords(texts)

    graph = build_graph_json(posts, sim_matrix, keywords_list)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(graph, ensure_ascii=False, indent=2))
    print(f"graph.json written to {OUTPUT} ({len(graph['nodes'])} nodes, {len(graph['edges'])} edges)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 테스트 실행 — 통과 확인**

Run: `cd scripts && uv run python -m pytest test_build_graph.py -v`
Expected: 3 tests PASS

- [ ] **Step 5: 실제 graph.json 생성**

Run: `cd scripts && uv run build_graph.py`
Expected: `blog/graph.json` 생성 (현재 포스트 1개이므로 노드 1개, 엣지 0개)

- [ ] **Step 6: graph.json 내용 확인**

Run: `cat blog/graph.json`
Expected: nodes 배열에 hello-world 포스트 1개, edges 빈 배열, tfidf에 키워드 포함

- [ ] **Step 7: Commit**

```bash
git add scripts/build_graph.py scripts/test_build_graph.py blog/graph.json
git commit -m "feat: add build_graph.py — generates graph.json from post embeddings"
```

---

### Task 3: app.js 데이터 레이어 확장

**Files:**
- Modify: `app.js:1-38`

- [ ] **Step 1: fetchPosts에 try/catch 추가**

`app.js`의 기존 `fetchPosts` 함수를 다음으로 교체:

```javascript
// Fetch posts.json from a relative path and return parsed array
async function fetchPosts(jsonPath) {
  try {
    const res = await fetch(jsonPath);
    if (!res.ok) return [];
    return res.json();
  } catch (e) {
    return [];
  }
}
```

- [ ] **Step 2: fetchGraph 함수 추가**

`app.js` 끝에 추가:

```javascript
// Fetch graph.json and return parsed object { nodes, edges }
async function fetchGraph(jsonPath) {
  try {
    const res = await fetch(jsonPath);
    if (!res.ok) return null;
    return res.json();
  } catch (e) {
    return null;
  }
}
```

- [ ] **Step 3: searchPosts 함수 추가**

```javascript
// Search nodes by query. mode: "text" (default) or "tfidf"
// Returns array of matching node IDs
function searchPosts(nodes, query, mode) {
  if (!query || !query.trim()) return nodes.map(n => n.id);
  const q = query.trim().toLowerCase();

  if (mode === 'tfidf') {
    // TF-IDF 키워드 가중 매칭: 쿼리 단어와 노드 tfidf 키 매칭, 점수 합산
    const queryWords = q.split(/\s+/);
    const scored = nodes.map(node => {
      const tfidf = node.tfidf || {};
      let score = 0;
      for (const word of queryWords) {
        for (const [keyword, value] of Object.entries(tfidf)) {
          if (keyword.includes(word) || word.includes(keyword)) {
            score += value;
          }
        }
      }
      return { id: node.id, score };
    });
    // 점수 > 0인 노드만, 점수 내림차순
    return scored.filter(s => s.score > 0)
      .sort((a, b) => b.score - a.score)
      .map(s => s.id);
  }

  // 기본 텍스트 매칭: 제목 또는 요약에 쿼리 포함
  return nodes.filter(n =>
    (n.title && n.title.toLowerCase().includes(q)) ||
    (n.summary && n.summary.toLowerCase().includes(q))
  ).map(n => n.id);
}
```

- [ ] **Step 4: filterByTags 함수 추가**

```javascript
// Filter nodes by active tags (OR condition)
// Returns array of matching node IDs
function filterByTags(nodes, activeTags) {
  if (!activeTags || activeTags.length === 0) return nodes.map(n => n.id);
  return nodes.filter(n =>
    n.tags && n.tags.some(t => activeTags.includes(t))
  ).map(n => n.id);
}
```

- [ ] **Step 5: 브라우저 콘솔에서 수동 확인**

Run: `python3 -m http.server 8080` (프로젝트 루트)
브라우저에서 `http://localhost:8080/` 열고 콘솔에서:
```javascript
const g = await fetchGraph('./blog/graph.json');
console.log(g); // { nodes: [...], edges: [...] }
console.log(searchPosts(g.nodes, 'hello', 'text')); // ["hello-world"]
console.log(filterByTags(g.nodes, ['blog'])); // ["hello-world"]
```

- [ ] **Step 6: Commit**

```bash
git add app.js
git commit -m "feat: add fetchGraph, searchPosts, filterByTags to app.js"
```

---

### Task 4: graph.js — Cytoscape.js 프레젠테이션 레이어

**Files:**
- Create: `graph.js`

- [ ] **Step 1: initGraph 함수 구현**

```javascript
// graph.js — Cytoscape.js presentation layer
// CDN deps: cytoscape, cytoscape-fcose

/**
 * Initialize a Cytoscape graph instance.
 * @param {HTMLElement} container - DOM element for the graph
 * @param {Object} graphData - { nodes: [...], edges: [...] }
 * @param {Object} options - { onNodeClick: fn(slug), postsBasePath: string }
 * @returns {Object} Cytoscape instance
 */
function initGraph(container, graphData, options = {}) {
  const elements = [];

  for (const node of graphData.nodes) {
    elements.push({
      group: 'nodes',
      data: { id: node.id, label: node.title, ...node },
    });
  }

  for (const edge of graphData.edges) {
    elements.push({
      group: 'edges',
      data: {
        id: edge.source + '-' + edge.target,
        source: edge.source,
        target: edge.target,
        weight: edge.weight,
      },
    });
  }

  const cy = cytoscape({
    container: container,
    elements: elements,
    style: [
      {
        selector: 'node',
        style: {
          'label': 'data(label)',
          'background-color': '#4a62ff',
          'color': '#cccccc',
          'font-size': '11px',
          'text-wrap': 'ellipsis',
          'text-max-width': '120px',
          'text-valign': 'bottom',
          'text-margin-y': 8,
          'width': 30,
          'height': 30,
          'border-width': 2,
          'border-color': '#4a62ff',
        },
      },
      {
        selector: 'edge',
        style: {
          'width': 'mapData(weight, 0.3, 1.0, 1, 6)',
          'line-color': '#1e1e1e',
          'opacity': 'mapData(weight, 0.3, 1.0, 0.3, 0.8)',
          'curve-style': 'bezier',
        },
      },
      {
        selector: 'node.highlighted',
        style: {
          'background-color': '#dc00c9',
          'border-color': '#dc00c9',
          'color': '#ffffff',
        },
      },
      {
        selector: 'node.dimmed',
        style: {
          'opacity': 0.15,
        },
      },
      {
        selector: 'edge.dimmed',
        style: {
          'opacity': 0.05,
        },
      },
      {
        selector: 'node.root',
        style: {
          'background-color': '#dc00c9',
          'border-color': '#dc00c9',
          'color': '#ffffff',
          'width': 40,
          'height': 40,
          'font-size': '13px',
        },
      },
    ],
    layout: {
      name: 'fcose',
      animate: true,
      animationDuration: 500,
      idealEdgeLength: function (edge) {
        return 200 / (edge.data('weight') || 0.5);
      },
      nodeRepulsion: 8000,
      edgeElasticity: 0.45,
    },
    minZoom: 0.3,
    maxZoom: 3,
  });

  // 노드 클릭 이벤트
  if (options.onNodeClick) {
    cy.on('tap', 'node', function (evt) {
      options.onNodeClick(evt.target.data('id'));
    });
  }

  return cy;
}
```

- [ ] **Step 2: highlightNodes, resetHighlight 구현**

```javascript
/**
 * Highlight matched nodes, dim the rest.
 * @param {Object} cy - Cytoscape instance
 * @param {string[]} matchedIds - IDs of nodes to highlight
 */
function highlightNodes(cy, matchedIds) {
  const idSet = new Set(matchedIds);
  cy.batch(function () {
    cy.nodes().forEach(function (node) {
      if (idSet.has(node.data('id'))) {
        node.removeClass('dimmed').addClass('highlighted');
      } else {
        node.removeClass('highlighted').addClass('dimmed');
      }
    });
    cy.edges().forEach(function (edge) {
      const srcMatch = idSet.has(edge.data('source'));
      const tgtMatch = idSet.has(edge.data('target'));
      if (srcMatch && tgtMatch) {
        edge.removeClass('dimmed');
      } else {
        edge.addClass('dimmed');
      }
    });
  });
}

/**
 * Reset all highlights.
 * @param {Object} cy - Cytoscape instance
 */
function resetHighlight(cy) {
  cy.batch(function () {
    cy.elements().removeClass('highlighted dimmed root');
  });
}
```

- [ ] **Step 3: renderSubgraph 구현**

```javascript
/**
 * Render a subgraph centered on rootId with BFS up to given depth.
 * Top 5 neighbors per depth level to prevent explosion.
 * @param {HTMLElement} container
 * @param {Object} graphData - { nodes, edges }
 * @param {string} rootId - slug of the center post
 * @param {number} depth - BFS depth (2-5)
 * @param {Object} options - { onNodeClick: fn(slug) }
 * @returns {Object} Cytoscape instance or null if no neighbors
 */
function renderSubgraph(container, graphData, rootId, depth, options = {}) {
  // Build adjacency list with weights
  const adj = {};
  for (const edge of graphData.edges) {
    if (!adj[edge.source]) adj[edge.source] = [];
    if (!adj[edge.target]) adj[edge.target] = [];
    adj[edge.source].push({ id: edge.target, weight: edge.weight });
    adj[edge.target].push({ id: edge.source, weight: edge.weight });
  }

  // Check if root has any neighbors
  if (!adj[rootId] || adj[rootId].length === 0) return null;

  // BFS with depth limit, top-5 per level
  const visited = new Set([rootId]);
  const nodeDepths = { [rootId]: 0 };
  let frontier = [rootId];

  for (let d = 1; d <= depth; d++) {
    const nextFrontier = [];
    for (const nodeId of frontier) {
      const neighbors = (adj[nodeId] || [])
        .filter(n => !visited.has(n.id))
        .sort((a, b) => b.weight - a.weight)
        .slice(0, 5);
      for (const neighbor of neighbors) {
        if (!visited.has(neighbor.id)) {
          visited.add(neighbor.id);
          nodeDepths[neighbor.id] = d;
          nextFrontier.push(neighbor.id);
        }
      }
    }
    frontier = nextFrontier;
    if (frontier.length === 0) break;
  }

  // Build subgraph data
  const nodeMap = {};
  for (const n of graphData.nodes) {
    if (visited.has(n.id)) nodeMap[n.id] = n;
  }

  const subNodes = graphData.nodes.filter(n => visited.has(n.id));
  const subEdges = graphData.edges.filter(
    e => visited.has(e.source) && visited.has(e.target)
  );

  const subData = { nodes: subNodes, edges: subEdges };

  // Render with initGraph
  const cy = initGraph(container, subData, options);

  // Style by depth
  cy.batch(function () {
    cy.nodes().forEach(function (node) {
      const d = nodeDepths[node.data('id')] || 0;
      if (d === 0) {
        node.addClass('root');
      } else {
        // Dim progressively with depth
        node.style('opacity', Math.max(0.2, 1.0 - d * 0.2));
      }
    });
  });

  return cy;
}
```

- [ ] **Step 4: 브라우저에서 수동 확인**

`http://localhost:8080/` 콘솔에서:
```javascript
const g = await fetchGraph('./blog/graph.json');
console.log(typeof initGraph, typeof highlightNodes, typeof renderSubgraph);
// 모두 "function"이면 OK (현재 포스트 1개라 실제 그래프는 Task 7에서 확인)
```

- [ ] **Step 5: Commit**

```bash
git add graph.js
git commit -m "feat: add graph.js — Cytoscape.js presentation layer"
```

---

### Task 5: style.css — 검색/필터/그래프 스타일 추가

**Files:**
- Modify: `style.css:1-104`

- [ ] **Step 1: 검색바 + 토글 스타일 추가**

`style.css` 끝에 추가:

```css
/* Search bar */
.search-bar {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.8rem;
}
.search-bar input {
  flex: 1;
  background: #111;
  border: 1px solid #1e1e1e;
  color: #ccc;
  padding: 0.5rem 0.8rem;
  border-radius: 6px;
  font-size: 0.9rem;
}
.search-bar input:focus {
  border-color: #dc00c9;
  outline: none;
}

/* Toggle switch (keyword weighted search) */
.toggle-label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.75rem;
  color: #555;
  white-space: nowrap;
  cursor: pointer;
}
.toggle-label input[type="checkbox"] {
  appearance: none;
  width: 36px;
  height: 20px;
  background: #1e1e1e;
  border-radius: 10px;
  position: relative;
  cursor: pointer;
}
.toggle-label input[type="checkbox"]::after {
  content: '';
  position: absolute;
  width: 16px;
  height: 16px;
  background: #555;
  border-radius: 50%;
  top: 2px;
  left: 2px;
  transition: transform 0.2s, background 0.2s;
}
.toggle-label input[type="checkbox"]:checked::after {
  transform: translateX(16px);
  background: #dc00c9;
}

/* Tag filter chips */
.tag-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-bottom: 1rem;
}
.tag-filter {
  display: inline-block;
  font-size: 0.75rem;
  color: #555;
  background: rgba(85, 85, 85, 0.1);
  padding: 0.15rem 0.5rem;
  border-radius: 3px;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.15s;
}
.tag-filter.active {
  color: #4a62ff;
  background: rgba(74, 98, 255, 0.1);
  border-color: #4a62ff;
}

/* View toggle (graph / list) */
.view-toggle {
  display: flex;
  gap: 0;
  margin-bottom: 1rem;
  border: 1px solid #1e1e1e;
  border-radius: 6px;
  overflow: hidden;
  width: fit-content;
}
.view-toggle button {
  background: #111;
  color: #555;
  border: none;
  padding: 0.4rem 1rem;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.15s;
}
.view-toggle button.active {
  background: #dc00c9;
  color: #fff;
}

/* Graph container */
.graph-container {
  width: 100%;
  height: 500px;
  background: #0a0a0a;
  border: 1px solid #1e1e1e;
  border-radius: 8px;
  margin-bottom: 1rem;
}
.graph-container.subgraph {
  height: 350px;
}
.graph-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #555;
  font-size: 0.85rem;
}

/* Depth slider */
.depth-control {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  margin-bottom: 1rem;
}
.depth-control label {
  font-size: 0.8rem;
  color: #555;
  white-space: nowrap;
}
.depth-control input[type="range"] {
  flex: 1;
  max-width: 200px;
  accent-color: #dc00c9;
}
.depth-control .depth-value {
  font-size: 0.8rem;
  color: #dc00c9;
  min-width: 1.5rem;
  text-align: center;
}
```

- [ ] **Step 2: Commit**

```bash
git add style.css
git commit -m "feat: add search, filter, graph, and slider styles"
```

---

### Task 6: blog/index.html — 그래프/리스트 토글 뷰 + 검색/필터

**Files:**
- Modify: `blog/index.html:1-36`

- [ ] **Step 1: HTML 구조 개편**

`blog/index.html`을 다음으로 교체:

```html
<!DOCTYPE html>
<html lang="ko" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Blog — ahrism</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">
  <link rel="stylesheet" href="../style.css">
</head>
<body>
  <header class="container">
    <nav>
      <ul><li><strong><a href="../">ahrism</a></strong></li></ul>
      <ul>
        <li><a href="../#about">About</a></li>
        <li><a href="../#projects">Projects</a></li>
        <li><a href="./" class="active">Blog</a></li>
      </ul>
    </nav>
  </header>
  <main class="container">
    <h1>Blog</h1>

    <!-- Search bar -->
    <div class="search-bar">
      <input type="text" id="search-input" placeholder="검색...">
      <label class="toggle-label">
        <input type="checkbox" id="tfidf-toggle">
        키워드 가중
      </label>
    </div>

    <!-- Tag filters -->
    <div class="tag-filters" id="tag-filters"></div>

    <!-- View toggle -->
    <div class="view-toggle">
      <button id="btn-graph" class="active">그래프</button>
      <button id="btn-list">리스트</button>
    </div>

    <!-- Graph view -->
    <div id="graph-view">
      <div class="graph-container" id="graph-container"></div>
    </div>

    <!-- List view (hidden by default) -->
    <div id="list-view" style="display:none">
      <div id="posts-container"></div>
    </div>
  </main>
  <footer class="container">
    <small>&copy; 2024 ahrism</small>
  </footer>

  <script src="https://cdn.jsdelivr.net/npm/cytoscape@3.30.4/dist/cytoscape.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/cytoscape-fcose@2.2.0/cytoscape-fcose.js"></script>
  <script src="../app.js"></script>
  <script src="../graph.js"></script>
  <script>
    (async () => {
      // --- 데이터 로드 ---
      const graphData = await fetchGraph('./graph.json');
      const posts = await fetchPosts('./posts.json');
      const nodes = graphData ? graphData.nodes : posts.map(p => ({
        id: p.slug, title: p.title, date: p.date, tags: p.tags, summary: p.summary, tfidf: {}
      }));
      const hasGraph = graphData && graphData.nodes.length > 1;

      // --- 태그 필터 렌더링 ---
      const allTags = [...new Set(nodes.flatMap(n => n.tags || []))].sort();
      const tagContainer = document.getElementById('tag-filters');
      allTags.forEach(tag => {
        const chip = document.createElement('span');
        chip.className = 'tag-filter';
        chip.textContent = tag;
        chip.addEventListener('click', () => {
          chip.classList.toggle('active');
          applyFilters();
        });
        tagContainer.appendChild(chip);
      });

      // --- 뷰 토글 ---
      const btnGraph = document.getElementById('btn-graph');
      const btnList = document.getElementById('btn-list');
      const graphView = document.getElementById('graph-view');
      const listView = document.getElementById('list-view');
      let currentView = hasGraph ? 'graph' : 'list';
      let cy = null;

      function setView(view) {
        currentView = view;
        if (view === 'graph') {
          graphView.style.display = '';
          listView.style.display = 'none';
          btnGraph.classList.add('active');
          btnList.classList.remove('active');
          if (!cy && hasGraph) initMainGraph();
        } else {
          graphView.style.display = 'none';
          listView.style.display = '';
          btnList.classList.add('active');
          btnGraph.classList.remove('active');
        }
        applyFilters();
      }

      btnGraph.addEventListener('click', () => setView('graph'));
      btnList.addEventListener('click', () => setView('list'));

      // 그래프 데이터가 없거나 노드 0~1개면 리스트로 폴백
      if (!hasGraph) {
        btnGraph.disabled = true;
        btnGraph.style.opacity = '0.3';
        document.getElementById('graph-container').innerHTML =
          '<div class="graph-empty">포스트가 더 추가되면 그래프가 표시됩니다</div>';
      }

      // --- 그래프 초기화 ---
      function initMainGraph() {
        cy = initGraph(document.getElementById('graph-container'), graphData, {
          onNodeClick: function (slug) {
            window.location.href = '../posts/' + slug + '/';
          },
        });
      }

      // --- 검색 + 필터 적용 ---
      let debounceTimer;
      const searchInput = document.getElementById('search-input');
      const tfidfToggle = document.getElementById('tfidf-toggle');

      function applyFilters() {
        const query = searchInput.value;
        const mode = tfidfToggle.checked ? 'tfidf' : 'text';
        const activeTags = [...document.querySelectorAll('.tag-filter.active')]
          .map(el => el.textContent);

        // 검색 결과
        let matchedIds = searchPosts(nodes, query, mode);
        // 태그 필터 교차
        if (activeTags.length > 0) {
          const tagMatched = new Set(filterByTags(nodes, activeTags));
          matchedIds = matchedIds.filter(id => tagMatched.has(id));
        }

        // 그래프 뷰 업데이트
        if (currentView === 'graph' && cy) {
          if (!query && activeTags.length === 0) {
            resetHighlight(cy);
          } else {
            highlightNodes(cy, matchedIds);
          }
        }

        // 리스트 뷰 업데이트
        if (currentView === 'list') {
          const matchedSet = new Set(matchedIds);
          const filtered = posts.filter(p => matchedSet.has(p.slug));
          renderPostList(filtered, document.getElementById('posts-container'), '../posts/');
        }
      }

      searchInput.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(applyFilters, 300);
      });
      tfidfToggle.addEventListener('change', applyFilters);

      // --- 초기 렌더 ---
      setView(currentView);
      if (currentView === 'list') {
        renderPostList(posts, document.getElementById('posts-container'), '../posts/');
      }
    })();
  </script>
</body>
</html>
```

- [ ] **Step 2: 브라우저에서 확인**

`http://localhost:8080/blog/`에서:
1. 검색바, 태그 필터, 뷰 토글이 표시되는지 확인
2. 현재 포스트 1개이므로 그래프 뷰는 비활성, 리스트로 자동 전환되는지 확인
3. 리스트 뷰에서 hello-world 포스트가 보이는지 확인
4. 검색에 "hello" 입력 시 필터 작동 확인

- [ ] **Step 3: Commit**

```bash
git add blog/index.html
git commit -m "feat: overhaul blog page with graph/list toggle and search/filter"
```

---

### Task 7: posts/_template/index.html — 서브그래프 섹션

**Files:**
- Modify: `posts/_template/index.html:1-82`

- [ ] **Step 1: 서브그래프 섹션 추가**

`posts/_template/index.html`의 `</article>` 태그 다음, `</main>` 태그 전에 삽입:

```html
    <!-- Related posts subgraph -->
    <section id="related-graph-section" style="display:none">
      <div class="section-label">관련 글 탐색</div>
      <div class="depth-control">
        <label for="depth-slider">깊이:</label>
        <input type="range" id="depth-slider" min="2" max="5" value="2">
        <span class="depth-value" id="depth-value">2</span>
      </div>
      <div class="graph-container subgraph" id="subgraph-container"></div>
    </section>
```

- [ ] **Step 2: CDN 스크립트 + 서브그래프 로직 추가**

`<script src="../../app.js"></script>` 바로 뒤에 CDN 추가:
```html
  <script src="https://cdn.jsdelivr.net/npm/cytoscape@3.30.4/dist/cytoscape.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/cytoscape-fcose@2.2.0/cytoscape-fcose.js"></script>
  <script src="../../graph.js"></script>
```

기존 `<script>` 블록의 IIFE 끝(line 78, `})();` 앞)에 서브그래프 로직 추가:

```javascript
      // --- 서브그래프 ---
      const graphData = await fetchGraph('../../blog/graph.json');
      if (graphData && slug) {
        const section = document.getElementById('related-graph-section');
        const container = document.getElementById('subgraph-container');
        const slider = document.getElementById('depth-slider');
        const depthValue = document.getElementById('depth-value');

        let subCy = renderSubgraph(container, graphData, slug, 2, {
          onNodeClick: function (id) {
            window.location.href = '../' + id + '/';
          },
        });

        if (subCy) {
          section.style.display = '';
          slider.addEventListener('input', function () {
            depthValue.textContent = slider.value;
            if (subCy) subCy.destroy();
            container.innerHTML = '';
            subCy = renderSubgraph(container, graphData, slug, parseInt(slider.value), {
              onNodeClick: function (id) {
                window.location.href = '../' + id + '/';
              },
            });
            if (!subCy) {
              container.innerHTML = '<div class="graph-empty">이 깊이에서 관련 글이 없습니다</div>';
            }
          });
        }
      }
```

- [ ] **Step 3: 기존 포스트 페이지 업데이트**

템플릿이 변경되었으므로 기존 포스트에도 반영:
```bash
cp posts/_template/index.html posts/hello-world/index.html
```

- [ ] **Step 4: 브라우저에서 확인**

`http://localhost:8080/posts/hello-world/`에서:
1. 포스트 본문이 정상 렌더링되는지 확인
2. 현재 포스트 1개이므로 서브그래프 섹션이 숨겨져 있는지 확인 (이웃 없음)

- [ ] **Step 5: Commit**

```bash
git add posts/_template/index.html posts/hello-world/index.html
git commit -m "feat: add related posts subgraph to post template"
```

---

### Task 8: 통합 테스트 — 포스트 추가 후 전체 플로우 확인

**Files:**
- 이전 태스크에서 생성/수정된 모든 파일

- [ ] **Step 1: 테스트용 더미 포스트 2개 추가**

```bash
mkdir -p posts/test-post-1/images posts/test-post-2/images
cp posts/_template/index.html posts/test-post-1/index.html
cp posts/_template/index.html posts/test-post-2/index.html
```

`posts/test-post-1/content.md`:
```markdown
# 머신러닝 기초

머신러닝의 기본 개념과 학습 방법론에 대해 알아봅니다.
지도학습, 비지도학습, 강화학습의 차이를 설명합니다.
```

`posts/test-post-2/content.md`:
```markdown
# 딥러닝과 신경망

딥러닝은 머신러닝의 하위 분야입니다.
신경망의 구조와 역전파 알고리즘을 다룹니다.
```

`blog/posts.json` 업데이트:
```json
[
  {
    "slug": "test-post-1",
    "title": "머신러닝 기초",
    "date": "2026-03-23",
    "tags": ["ml", "tutorial"],
    "summary": "머신러닝의 기본 개념과 학습 방법론"
  },
  {
    "slug": "test-post-2",
    "title": "딥러닝과 신경망",
    "date": "2026-03-23",
    "tags": ["ml", "deep-learning"],
    "summary": "딥러닝과 신경망 구조에 대한 설명"
  },
  {
    "slug": "hello-world",
    "title": "Hello World — 첫 번째 글",
    "date": "2026-03-23",
    "tags": ["blog"],
    "summary": "ahrism 블로그의 첫 번째 글입니다."
  }
]
```

- [ ] **Step 2: graph.json 재생성**

Run: `cd scripts && uv run build_graph.py`
Expected: 3 nodes, 일부 edges (머신러닝/딥러닝 포스트 간 유사도 높을 것)

- [ ] **Step 3: 블로그 페이지 통합 확인**

`http://localhost:8080/blog/`에서:
1. 그래프 뷰: 3개 노드가 보이고, 머신러닝-딥러닝 사이에 엣지가 있는지 확인
2. 리스트 뷰: 3개 포스트가 모두 보이는지 확인
3. 검색: "머신러닝" 입력 시 관련 포스트 필터링
4. 태그: "ml" 클릭 시 2개 포스트만 매칭
5. 키워드 가중 토글 ON + "학습" 검색 시 TF-IDF 기반 결과

- [ ] **Step 4: 서브그래프 확인**

`http://localhost:8080/posts/test-post-1/`에서:
1. 하단에 서브그래프 섹션이 보이는지 확인
2. 깊이 슬라이더 조작 시 서브그래프가 변하는지 확인
3. 노드 클릭 시 해당 포스트로 이동하는지 확인

- [ ] **Step 5: 테스트 더미 포스트 제거 (선택)**

테스트 후 더미 포스트를 유지할지 제거할지는 사용자 판단. 제거 시:
```bash
rm -rf posts/test-post-1 posts/test-post-2
# blog/posts.json에서 test-post-1, test-post-2 엔트리 제거
# graph.json 재생성
cd scripts && uv run build_graph.py
```

- [ ] **Step 6: CLAUDE.md 빌드 워크플로 업데이트**

`CLAUDE.md`의 "새 포스트 추가" 섹션 끝에 추가:
```markdown
`blog/graph.json` 재생성:
\`\`\`bash
cd scripts && uv run build_graph.py
\`\`\`
```

- [ ] **Step 7: 최종 Commit**

```bash
git add posts/ blog/posts.json blog/graph.json CLAUDE.md
git commit -m "test: integration test with dummy posts"
```
