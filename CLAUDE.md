# ahrism-pages

GitHub Pages 포트폴리오 + 블로그. 순수 HTML/JS, 서버 없음.

## 스택

- **CSS**: Pico.css v2 (CDN, dark theme) + `style.css` (오버라이드)
- **Markdown 렌더링**: marked.js (CDN) + highlight.js (CDN)
- **그래프**: Cytoscape.js (CDN) — 포스트 유사도 그래프 + 서브그래프
- **ML**: sentence-transformers (`jhgan/ko-sroberta-multitask`) — 임베딩 · 태그 추천
- **데이터**: `blog/posts.json`, `blog/graph.json`, `blog/tags.json`, `projects.json`

## 파일 구조

```
index.html              # 랜딩 (포스트 그래프 → About 소개)
style.css               # 다크 테마 CSS 변수 + 컴포넌트
app.js                  # 공유 JS: fetchPosts / renderPostList / renderProjectCards
post.js                 # 포스트 페이지 로직 (frontmatter 파싱 · 렌더링)
graph.js                # Cytoscape.js 그래프: 호버 강조 · 서브그래프 · BFS 탐색
projects.json           # 프로젝트 카드 데이터

blog/
  index.html            # 전체 블로그 목록 (태그 필터 · 뷰 토글)
  posts.json            # 포스트 메타데이터 배열 (최신순, 자동생성)
  graph.json            # 포스트 유사도 그래프 (자동생성)
  tags.json             # 정규화된 태그 목록 (자동생성)
  .post_cache.json      # 포스트 임베딩 캐시 (자동생성, gitignore)
  .tag_cache.json       # 태그 임베딩 캐시 (자동생성, gitignore)

posts/
  _template/index.html  # 새 포스트 만들 때 복사하는 템플릿 (서브그래프 포함)
  <slug>/
    index.html          # 템플릿 복사본
    content.md          # YAML frontmatter + 글 내용
    images/             # 이미지 (선택)

scripts/
  post_update.py        # 통합 빌드 오케스트레이터
  posts_list_update.py  # 포스트 스캔 · frontmatter 파싱 · posts.json 업데이트
  build_graph.py        # 임베딩 · TF-IDF · graph.json 생성 (캐시 지원)
  auto_tag.py           # 태그 추천 + 생성 + 임베딩 캐시 관리
  tag_vocabulary.json   # 시드 태그 목록 (30개, vocabulary matching 소스)
  test_build_graph.py   # 그래프 빌드 테스트
  test_auto_tag.py      # 자동 태그 테스트

docs/                   # 설계 문서 · 구현 계획
```

## 새 포스트 추가

1. 폴더 + 템플릿 생성:
```bash
mkdir -p posts/<slug>/images
cp posts/_template/index.html posts/<slug>/index.html
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

3. 빌드:
```bash
cd scripts && uv run python post_update.py
```

| 옵션 | 설명 |
|------|------|
| (없음) | 증분 업데이트 — 바뀐 글만 임베딩 재계산 + 태그 할당 |
| `--posts-only` | posts.json만 업데이트 (ML 모델 로딩 없음) |
| `--force` | 캐시 무시, 전체 임베딩 재계산 |

### 개별 스크립트 CLI

```bash
# 태그 관리
uv run python auto_tag.py init              # tags.json + 태그 임베딩 초기화
uv run python auto_tag.py suggest <slug>    # 특정 포스트 태그 추천
uv run python auto_tag.py suggest --all     # 전체 포스트 태그 추천

# 그래프 생성
uv run python build_graph.py                # 증분 업데이트
uv run python build_graph.py --force        # 전체 재빌드
```

## 자동 태그 시스템

3단계 태그 할당 (우선순위 순):

1. **Vocabulary matching** — `tag_vocabulary.json`의 시드 태그를 본문에서 직접 매칭
2. **Embedding 추천** — 포스트 임베딩과 기존 태그 임베딩의 코사인 유사도 비교
3. **TF-IDF 생성** — 매칭 부족 시 키워드 기반 새 태그 생성

| 상수 | 값 | 설명 |
|------|-----|------|
| `MATCH_THRESHOLD` | 0.4 | 임베딩 유사도 추천 임계값 |
| `NEW_TAG_DEDUP_THRESHOLD` | 0.8 | 새 태그 중복 판정 임계값 |
| `MAX_TAGS` | 5 | 포스트당 최대 태그 수 |
| `MIN_TAGS` | 2 | 포스트당 최소 태그 수 |

## 그래프 시스템

**build_graph.py** — 포스트 간 유사도 계산:
- 모델: `jhgan/ko-sroberta-multitask`
- `SIMILARITY_THRESHOLD = 0.3` / `MAX_EDGES_PER_NODE = 8` / `TFIDF_TOP_N = 20`
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
