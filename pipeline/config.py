"""Paths shared by the content scanner and metadata writer."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = PROJECT_ROOT / "posts"
POSTS_JSON = PROJECT_ROOT / "blog" / "posts.json"
