"""
Scans posts/ directory and parses frontmatter from .md and .ipynb files.
Owns: directory traversal, YAML parsing, notebook cell extraction, summary extraction.
Does NOT write any files. Does NOT call ML models.
"""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

import yaml

from pipeline import config
from pipeline.models import FrontMatter, PostRecord


def parse_frontmatter_text(text: str) -> tuple[FrontMatter, str]:
    """
    Split text into (frontmatter_dict, body_str).
    Frontmatter is the YAML block between leading '---' delimiters.
    Returns ({}, text) if no valid frontmatter found.
    """
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm = yaml.safe_load(text[3:end]) or {}
    body = text[end + 4:].lstrip("\n")
    return fm, body


def parse_markdown_file(path: Path) -> tuple[FrontMatter, str]:
    """Read a content.md file and return (frontmatter, body)."""
    return parse_frontmatter_text(path.read_text(encoding="utf-8"))


def parse_notebook_file(path: Path) -> tuple[FrontMatter, str]:
    """
    Read a content.ipynb file.
    Frontmatter is parsed from the first markdown cell (if it starts with '---').
    Body is assembled from all cells: markdown as-is, code wrapped in ```python fences.
    """
    import nbformat
    nb = nbformat.read(str(path), as_version=4)

    fm: FrontMatter = {}
    body_parts: list[str] = []
    first = True

    for cell in nb.cells:
        source = cell.source.strip()
        if not source:
            continue
        if first and cell.cell_type == "markdown" and source.startswith("---"):
            fm, remaining = parse_frontmatter_text(source)
            if remaining.strip():
                body_parts.append(remaining.strip())
            first = False
            continue
        first = False
        if cell.cell_type == "markdown":
            body_parts.append(source)
        elif cell.cell_type == "code":
            body_parts.append(f"```python\n{source}\n```")

    return fm, "\n\n".join(body_parts)


def extract_summary(body: str, max_chars: int = 120) -> str:
    """
    Extract a plain-text summary from the first non-heading body paragraph.
    Strips markdown formatting (links, code spans, emphasis).
    Returns '' if no suitable paragraph found.
    """
    for line in body.splitlines():
        line = line.strip()
        if line and not line.startswith(("#", "```", "!", "|", "-", "*")):
            line = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', line)
            line = re.sub(r'[`*_]', '', line)
            return line[:max_chars] + ("..." if len(line) > max_chars else "")
    return ""


def scan_posts(posts_dir: Path | None = None) -> list[PostRecord]:
    """
    Scan posts/ directory and return a list of PostRecord dicts.

    Priority: content.ipynb > content.md when both exist.
    Skips directories starting with '_'.
    Skips posts missing a 'title' in frontmatter (logs to stderr).

    Returns PostRecord list with internal '_body' and '_path' keys set.
    These internal keys are stripped before any file is written.
    """
    base = posts_dir or config.POSTS_DIR

    sources: dict[str, dict] = {}
    for p in sorted(base.glob("*/content.ipynb")):
        slug = p.parent.name
        if not slug.startswith("_"):
            sources.setdefault(slug, {})["ipynb"] = p
    for p in sorted(base.glob("*/content.md")):
        slug = p.parent.name
        if not slug.startswith("_"):
            sources.setdefault(slug, {})["md"] = p

    posts: list[PostRecord] = []
    for slug, paths in sorted(sources.items()):
        if "ipynb" in paths:
            fm, body = parse_notebook_file(paths["ipynb"])
            is_notebook = True
        else:
            fm, body = parse_markdown_file(paths["md"])
            is_notebook = False

        if not fm.get("title"):
            print(f"  [SKIP] {slug}: frontmatter에 title 없음", file=sys.stderr)
            continue

        post: PostRecord = {
            "slug": slug,
            "title": str(fm["title"]),
            "date": str(fm.get("date", date.today())),
            "tags": [str(t) for t in fm.get("tags", [])],
            "summary": str(fm.get("summary") or extract_summary(body)),
            "_body": body,
            "_path": str(paths.get("ipynb") or paths.get("md")),
        }
        if is_notebook:
            post["notebook"] = True
        posts.append(post)

    return posts
