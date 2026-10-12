# Ahrism Blog

기술 글과 짧은 생각을 기록하는 정적 블로그입니다. Markdown과 Jupyter 노트북을 HTML로 빌드해 GitHub Pages에서 제공합니다.

## 로컬 실행

Python 3.10 이상과 [uv](https://docs.astral.sh/uv/)가 필요합니다.

```sh
uv run python main.py
python3 -m http.server 8000
```

이 저장소에서 서버를 실행하면 `http://localhost:8000/`에서 확인합니다. 상위 폴더에서 실행하면 `http://localhost:8000/pages/`로 접속합니다.

## 글 작성

`posts/<slug>/content.md`를 만들고 첫 줄부터 다음 메타데이터를 작성합니다. 폴더명이 글 주소가 되므로 공개된 글의 폴더명은 유지합니다.

```markdown
---
title: "글 제목"
date: 2026-10-12
tags: [Python, AI]
summary: "글을 소개하는 한 문장"
---

# 글 제목

본문을 작성합니다.
```

이미지는 같은 폴더의 `images/`에 넣고 `![설명](./images/example.png)`처럼 참조합니다. 기존 `content.ipynb`도 지원하며, 첫 Markdown 셀에 같은 메타데이터를 넣습니다. `title`이 없는 글과 노트북은 목록에 노출되지 않습니다.

짧은 글은 `twinkle/<slug>.md`에 같은 메타데이터와 본문을 작성합니다. 작성 후 `uv run python main.py`로 다시 빌드합니다.

## 확인

```sh
uv run pytest
npm ci
npx playwright install chromium
npm test
```

Chromium 설치는 브라우저 테스트를 처음 실행할 때 필요합니다.

## 배포

GitHub 저장소의 **Settings → Pages → Source**를 **GitHub Actions**로 설정합니다. `main` 브랜치에 푸시하면 [배포 워크플로](.github/workflows/deploy.yml)가 사이트를 빌드하고 GitHub Pages에 배포합니다.
