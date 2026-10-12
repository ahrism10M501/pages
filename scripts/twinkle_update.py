#!/usr/bin/env python3
"""Scan short Markdown notes and update their metadata atomically."""

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.io import atomic_write_json
from pipeline.scanner import parse_frontmatter_text

TWINKLE_DIR = ROOT / "twinkle"
TWINKLES_JSON = TWINKLE_DIR / "twinkles.json"


def scan_twinkles(twinkle_dir: Path | None = None) -> list[dict]:
    twinkles = []
    for path in sorted((twinkle_dir or TWINKLE_DIR).glob("*.md")):
        fm, body = parse_frontmatter_text(path.read_text(encoding="utf-8"))
        if not fm.get("title"):
            print(f"  [SKIP] {path.name}: frontmatter에 title 없음", file=sys.stderr)
            continue
        twinkles.append({
            "slug": path.stem,
            "title": str(fm["title"]),
            "date": str(fm.get("date", date.today())),
            "tags": [str(tag) for tag in fm.get("tags", [])],
            "content": body.strip(),
        })
    return sorted(twinkles, key=lambda twinkle: twinkle["date"], reverse=True)


def update_twinkles_json(twinkles: list[dict] | None = None, path: Path | None = None) -> bool:
    if twinkles is None:
        twinkles = scan_twinkles()
    target = path or TWINKLES_JSON
    new_text = json.dumps(twinkles, ensure_ascii=False, indent=2)
    if target.exists() and new_text == target.read_text(encoding="utf-8"):
        return False
    atomic_write_json(twinkles, target)
    return True


if __name__ == "__main__":
    changed = update_twinkles_json()
    print("twinkles.json 업데이트됨" if changed else "twinkles.json 변경 없음")
