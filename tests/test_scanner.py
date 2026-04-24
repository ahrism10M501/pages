"""Unit tests for pipeline.scanner — migrated from scripts/test_notebook_parse.py."""
import json
import tempfile
from pathlib import Path

from pipeline.scanner import parse_frontmatter_text, parse_notebook_file


def _make_notebook(cells: list[dict]) -> dict:
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {"kernelspec": {"name": "python3"}},
        "cells": cells,
    }


def _md_cell(source: str) -> dict:
    return {"cell_type": "markdown", "source": source, "metadata": {}}


def _code_cell(source: str) -> dict:
    return {"cell_type": "code", "source": source, "metadata": {}, "outputs": [], "execution_count": None}


def test_parse_frontmatter_text_basic():
    text = "---\ntitle: Hello\ndate: 2026-01-01\n---\n본문"
    fm, body = parse_frontmatter_text(text)
    assert fm["title"] == "Hello"
    assert str(fm["date"]) == "2026-01-01"
    assert "본문" in body


def test_parse_frontmatter_text_no_frontmatter():
    fm, body = parse_frontmatter_text("그냥 본문")
    assert fm == {}
    assert body == "그냥 본문"


def test_parse_notebook_with_frontmatter():
    nb = _make_notebook([
        _md_cell("---\ntitle: 테스트 노트북\ndate: 2026-04-11\ntags: [python]\n---\n소개 문단"),
        _code_cell("x = 1 + 1\nprint(x)"),
        _md_cell("## 결론"),
    ])
    with tempfile.NamedTemporaryFile(suffix=".ipynb", mode="w", delete=False, encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False)
        tmp = Path(f.name)
    fm, body = parse_notebook_file(tmp)
    tmp.unlink()

    assert fm["title"] == "테스트 노트북"
    assert fm["tags"] == ["python"]
    assert "소개 문단" in body
    assert "```python" in body
    assert "x = 1 + 1" in body
    assert "## 결론" in body


def test_parse_notebook_without_frontmatter():
    nb = _make_notebook([
        _md_cell("# 제목 없는 노트북"),
        _code_cell("print('hello')"),
    ])
    with tempfile.NamedTemporaryFile(suffix=".ipynb", mode="w", delete=False, encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False)
        tmp = Path(f.name)
    fm, body = parse_notebook_file(tmp)
    tmp.unlink()

    assert fm == {}
    assert "# 제목 없는 노트북" in body


def test_parse_notebook_empty_cells_skipped():
    nb = _make_notebook([
        _md_cell("---\ntitle: 빈 셀 테스트\n---"),
        _md_cell(""),
        _code_cell("a = 1"),
    ])
    with tempfile.NamedTemporaryFile(suffix=".ipynb", mode="w", delete=False, encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False)
        tmp = Path(f.name)
    fm, body = parse_notebook_file(tmp)
    tmp.unlink()

    assert fm["title"] == "빈 셀 테스트"
    assert "a = 1" in body
