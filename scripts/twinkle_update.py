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
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.scanner import parse_frontmatter_text
TWINKLE_DIR = ROOT / "twinkle"
TWINKLES_JSON = TWINKLE_DIR / "twinkles.json"
POSTS_JSON = ROOT / "blog" / "posts.json"


def _load_posts() -> list[dict]:
    if not POSTS_JSON.exists():
        return []
    try:
        return json.loads(POSTS_JSON.read_text(encoding="utf-8"))
    except Exception:
        return []


def _nearest_post(twinkle: dict, posts: list[dict]) -> str | None:
    """홈 그래프에 트윙클을 별처럼 연결하기 위한 최근접 포스트 슬러그.

    태그 겹침이 가장 큰 포스트를 선택한다. 동률이거나 겹침이 없으면 가장 최근 포스트.
    """
    if not posts:
        return None
    tw_tags = set(twinkle.get("tags") or [])
    if tw_tags:
        scored = [(len(tw_tags & set(p.get("tags") or [])), p) for p in posts]
        best_overlap, _ = max(scored, key=lambda x: x[0])
        if best_overlap > 0:
            ties = [p for s, p in scored if s == best_overlap]
            ties.sort(key=lambda p: p.get("date", ""), reverse=True)
            return ties[0]["slug"]
    most_recent = max(posts, key=lambda p: p.get("date", ""))
    return most_recent["slug"]


def scan_twinkles() -> list[dict]:
    """twinkle/*.md 스캔 → 메타데이터 + 본문 + nearest_post (날짜 내림차순)."""
    posts = _load_posts()
    twinkles = []
    for path in sorted(TWINKLE_DIR.glob("*.md")):
        fm, body = parse_frontmatter_text(path.read_text(encoding="utf-8"))
        if not fm.get("title"):
            print(f"  [SKIP] {path.name}: frontmatter에 title 없음", file=sys.stderr)
            continue
        tw = {
            "slug": path.stem,
            "date": str(fm.get("date", date.today())),
            "title": str(fm["title"]),
            "tags": [str(t) for t in fm.get("tags", [])],
            "content": body.strip(),
        }
        nearest = _nearest_post(tw, posts)
        if nearest:
            tw["nearest_post"] = nearest
        twinkles.append(tw)
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
