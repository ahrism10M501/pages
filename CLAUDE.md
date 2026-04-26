# ahrism-pages

GitHub Pages 포트폴리오 + 블로그. 순수 HTML/JS, 서버 없음. 빌드 단계는 Jinja2 템플릿 렌더링뿐.

## 스택

- **CSS**: Pico.css v2 (CDN, dark theme) + `style.css` (오버라이드)
- **Markdown 렌더링**: marked.js (CDN) + highlight.js (CDN)
- **그래프**: Cytoscape.js (CDN) — 포스트 유사도 그래프 + 서브그래프
- **ML**: sentence-transformers (`jhgan/ko-sroberta-multitask`) — 임베딩 · 태그 추천
- **빌드**: Jinja2 (Python) — `templates/` → 정적 HTML
- **데이터**: `blog/posts.json`, `blog/graph.json`, `blog/tags.json`, `projects.json`

## 파일 구조

```
templates/              # Jinja2 소스 (편집 대상)
  base.html             # <head>+사이드바+content block+footer+scripts 공통 스켈레톤
  partials/
    sidebar.html        # nav.json 기반 자동 active
    footer.html         # 사회 링크
  pages/
    home.html, about.html, blog.html, twinkle.html, github.html, post.html
  nav.json              # 사이드바 항목 (항목 추가는 여기 한 곳)

src/                    # JS 모듈 (편집 대상)
  sidebar.js            # 사이드바 토글/네비
  page-fold.js          # 페이지 입장 애니메이션
  utils.js              # formatPostDate, stripFrontmatter
  posts.js              # fetchPosts, fetchGraph, renderPostList, search/filter
  projects.js           # renderProjectCards
  graph.js              # Cytoscape.js 그래프 렌더링
  post.js               # 포스트 페이지: marked + KaTeX + highlight + mermaid
  twinkle-feed.js       # 트윙클 피드/아카이브 (home + twinkle 공유)
  home-graph.js         # 홈 페이지 그래프: 펄스, pull-to-expand, 줌 프리셋
  github.js             # /github/ 페이지 repos 목록

style.css               # 다크 테마 CSS
projects.json, github-sources.json, ...

# 빌드 산출물 (build_site.py가 생성, git에 커밋됨):
index.html, about/index.html, blog/index.html, twinkle/index.html,
github/index.html, posts/<slug>/index.html

blog/
  posts.json, graph.json, tags.json    # 자동생성 (post_update.py)
  .post_cache.json, .tag_cache.json    # 임베딩 캐시 (gitignore)

posts/<slug>/
  content.md            # YAML frontmatter + 본문 (또는 content.ipynb)
  index.html            # 빌드 산출물
  images/

pipeline/              # 빌드 파이프라인 패키지
  __init__.py
  config.py             # 모든 경로/상수 단일 소스
  models.py             # 타입 정의
  io.py                 # 파일 I/O 집중
  state.py              # 변경 감지 (SHA256 기반)
  scanner.py            # posts/ 스캔 + MD/ipynb 파싱
  embedder.py           # 임베딩 모델 (lazy singleton)
  graph_builder.py      # TF-IDF + 유사도 → graph.json
  tagger.py             # 3단계 태그 할당
  supernode_builder.py  # 슈퍼노드 (AgglomerativeClustering)
  orchestrator.py       # 전체 파이프라인 오케스트레이터

scripts/
  build_site.py         # Jinja2 템플릿 → HTML 렌더러
  twinkle_update.py     # 트윙클 JSON 생성

docs/                   # 설계 문서
```

## 새 포스트 추가

1. 폴더 + content.md만 작성 (별도 index.html 복사 불필요):
```bash
mkdir -p posts/<slug>/images
```

2. `posts/<slug>/content.md` 작성 (YAML frontmatter 필수):
```markdown
---
title: "제목"
date: YYYY-MM-DD
tags: [tag1, tag2]  # 선택사항: 없으면 자동 추천
summary: "한 줄 요약 (없으면 본문에서 자동 추출)"
---

본문 내용...
```

3. 빌드 (포스트 메타 + 그래프 + 정적 HTML 모두 갱신):
```bash
uv run python main.py
```

| 옵션 | 설명 |
|------|------|
| (없음) | 증분 업데이트 — 바뀐 글만 임베딩 재계산 + 태그 할당 + HTML 빌드 |
| `--posts-only` | posts.json만 업데이트 (ML 모델 로딩 없음) + HTML 빌드 |
| `--force` | 캐시 무시, 전체 임베딩 재계산 |

HTML만 다시 렌더링하려면:
```bash
uv run python scripts/build_site.py
```

## 자동 태그 시스템

3단계 태그 할당 (우선순위 순, pipeline/tagger.py):

1. **Vocabulary matching** — `pipeline/tag_vocabulary.json`의 시드 태그를 본문에서 직접 매칭
2. **Embedding 추천** — 포스트 임베딩과 기존 태그 임베딩의 코사인 유사도 비교
3. **TF-IDF 생성** — 매칭 부족 시 키워드 기반 새 태그 생성

| 상수 | 값 | 설명 |
|------|-----|------|
| `MATCH_THRESHOLD` | 0.4 | 임베딩 유사도 추천 임계값 |
| `NEW_TAG_DEDUP_THRESHOLD` | 0.8 | 새 태그 중복 판정 임계값 |
| `MAX_TAGS` | 5 | 포스트당 최대 태그 수 |
| `MIN_TAGS` | 2 | 포스트당 최소 태그 수 |

## 그래프 시스템

**pipeline/graph_builder.py** — 포스트 간 유사도 계산:
- 모델: `jhgan/ko-sroberta-multitask` (pipeline/embedder.py에서 로드)
- `SIMILARITY_THRESHOLD = 0.3` / `MAX_EDGES_PER_NODE = 8` / `TFIDF_TOP_N = 20` (pipeline/config.py)
- SHA256 해시 기반 증분 캐싱 (`.post_cache.json`)

**graph.js** — 프론트엔드 렌더링:
- `setupHoverHighlight()` — 노드 호버 시 연결 강조 (weight >= 0.4)
- `applyDepthEffect()` — degree 기반 노드 크기 조절
- `renderSubgraph()` — BFS 기반 서브그래프 (포스트 페이지 관련 글 탐색, depth 2-5)

## 색상 시스템

| 역할 | 값 |
|------|-----|
| 배경 | `#0a0a0a` |
| 카드 | `#111111` |
| 테두리 | `#1e1e1e` |
| Primary (magenta) | `#dc00c9` |
| Secondary (blue) | `#4a62ff` |
| Critical (red) | `#ff0000` |
| 본문 | `#cccccc` |
| 흐린 텍스트 | `#555555` |

## 로컬 미리보기

```bash
python3 -m http.server 8080
# http://localhost:8080/
```

fetch() 때문에 file:// 직접 열기 불가 — 반드시 서버 필요.
