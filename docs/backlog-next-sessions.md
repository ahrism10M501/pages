# 다음 세션 백로그

슈퍼노드 그래프 고도화 이후 구현 예정 기능들입니다.

---

## B — UI/UX 디테일

**우선순위:** 중 (독립적, 범위 작음)

### B-1: IPYNB Matplotlib 다크모드 동기화
- `.ipynb` 뷰어에서 차트/그래프 이미지가 흰 배경으로 나오는 문제
- 해결책 옵션:
  - 노트북 작성 시 `plt.style.use('dark_background')` 강제하는 가이드 문서 추가
  - 또는 CSS `img.cell-output-image { filter: invert(0.9) hue-rotate(180deg); }` 적용 (Matplotlib 이미지에만)

### B-2: 터미널 스타일 로딩 UI
- 현재 `.ipynb` 로딩 시 단순 `Loading...` 텍스트
- 개선: `[INFO] Fetching notebook data...` + 깜빡이는 커서 애니메이션
- 관련 파일: `posts/_template/index.html`, CSS `@keyframes` 추가

---

## C — Twinkle 공간

**우선순위:** 높 (새로운 콘텐츠 레이어)

짧은 단상·디버깅 기록·아이디어 스케치 전용 섹션. 긴 포스트와 분리된 경량 콘텐츠 공간.

### 구현 고려사항
- 새 콘텐츠 타입 → `posts.json` 스키마에 `type: "twinkle"` 필드 추가
- 별도 라우팅: `/twinkle/` 또는 blog 내 탭
- Frontmatter: `type: twinkle`, 본문 < 500자 제한 권장
- 그래프에 포함할지 여부 결정 필요 (별도 그래프 vs 메인 그래프에 다른 스타일로 포함)

---

## D — 포트폴리오 연결

**우선순위:** 중 (태그 시스템 활용)

About 페이지의 기술 스택(Python, PyTorch, Verilog 등) 클릭 → 관련 포스트/프로젝트만 그래프/리스트로 필터링.

### 구현 고려사항
- `index.html` About 섹션의 기술 스택 항목에 `data-tag` 속성 추가
- 클릭 시 `/blog/index.html?tags=<skill>` 이동 (URL 파라미터 기능 활용)
- `projects.json`에도 `tags` 필드 추가해 프로젝트 카드 필터링 연동
