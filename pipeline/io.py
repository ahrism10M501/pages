"""JSON reads and atomic metadata writes."""

import json
import os
from pathlib import Path
from typing import Any

from pipeline import config
from pipeline.models import PostRecord


def atomic_write_json(data: Any, target: Path, *, ensure_ascii: bool = False, indent: int = 2) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=ensure_ascii, indent=indent), encoding="utf-8")
    os.replace(tmp, target)


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_posts_json(posts: list[PostRecord], path: Path | None = None) -> bool:
    target = path or config.POSTS_JSON
    result = sorted(posts, key=lambda post: post["date"], reverse=True)
    new_text = json.dumps(result, ensure_ascii=False, indent=2)
    if target.exists() and new_text == target.read_text(encoding="utf-8"):
        return False
    atomic_write_json(result, target)
    return True
