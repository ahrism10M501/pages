# Twinkle 프론트엔드 보완 설계

**날짜:** 2026-04-25  
**범위:** `twinkle/index.html`, `style.css`

## 문제

1. 피드 내비게이션 없음 — 윈도우(5개) 이동 수단이 아카이브 클릭뿐
2. 인라인 코드 미렌더링 — 백틱이 plain text로 출력
3. 모바일에서 아카이브 완전 숨김 — 태그 필터/목록 접근 불가
4. 아카이브 항목 제목 잘림 — 전체 제목 볼 방법 없음

## 해결책 (B안 — Balanced)

### 1. 피드 Prev / Next 내비게이션

피드 카드 목록 하단에 네비게이션 바 추가.

- `state.page` (0-based) 도입. `getFeedWindow()` 를 page 기반으로 교체.
- `renderFeed()` 하단에 `<div class="twinkle-nav">` 삽입:
  - `← 이전` 버튼 (첫 페이지에서 disabled)
  - `{start}–{end} / {total}` 카운터
  - `다음 →` 버튼 (마지막 페이지에서 disabled)
- 태그 필터 변경 또는 아카이브 클릭 시 `state.page = 0` 리셋.
- anchor 클릭 시 해당 포스트가 속한 페이지로 자동 이동.

### 2. 카드 본문 마크다운 렌더링

`post.js` 와 동일하게 CDN에서 로드된 `marked.js` 활용.

- `renderCard()` 내 `escapeHtml(t.content)` → `marked.parse(t.content)` 로 교체.
- `marked.js` CDN 스크립트 태그를 `twinkle/index.html` `<head>` 에 추가 (`post.js` 와 동일 버전).
- 더보기/접기 truncation은 plain text 길이 기준 유지 (`t.content.length > PREVIEW_LEN`), 렌더는 markdown으로.
- XSS: marked의 `breaks: true` 옵션만 사용. 사용자 입력이 아닌 로컬 JSON이므로 DOMPurify 불필요.

### 3. 모바일 태그 스트립

`max-width: 767px` 에서만 표시. 기존 아카이브 패널은 데스크탑 전용 유지.

- `twinkle/index.html` 피드 상단(`<div class="label">✦ TWINKLE</div>` 앞)에 `<div class="twinkle-mobile-tags" id="mobile-tags">` 삽입.
- `renderArchive()` 에서 `#mobile-tags` 도 함께 업데이트.
- 태그 7개 초과 시 `태그 ▾` 토글 버튼으로 접기/펼치기 (`data-expanded` 속성).
- CSS: `.twinkle-mobile-tags { display: none }` 기본, `@media (max-width: 767px) { display: flex; }`.

### 4. 아카이브 항목 title 속성

`renderArchive()` 의 `.archive-item` 렌더 템플릿에 `title="${escapeHtml(t.title)}"` 추가. 1줄 변경.

## 변경 파일

| 파일 | 변경 내용 |
|------|-----------|
| `twinkle/index.html` | marked.js CDN 추가, mobile-tags DOM, JS 로직 4가지 |
| `style.css` | `.twinkle-nav`, `.twinkle-mobile-tags`, `.twinkle-mobile-tag-chip` 추가 |

## 변경 없는 파일

- `twinkles.json` — 데이터 구조 변경 없음
- `sidebar.js`, `app.js`, `post.js` — 영향 없음
- `scripts/` — 빌드 파이프라인 변경 없음
