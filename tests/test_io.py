"""Tests for pipeline.io — atomic writes, cache round-trips."""
import json
import tempfile
from pathlib import Path

from pipeline.io import (
    atomic_write_json,
    load_json,
    load_post_cache,
    load_tag_cache,
    save_post_cache,
    save_tag_cache,
    save_tags_json,
)


def test_atomic_write_json_creates_file():
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "out.json"
        atomic_write_json({"key": "value"}, target)
        assert target.exists()
        data = json.loads(target.read_text())
        assert data["key"] == "value"


def test_atomic_write_json_no_tmp_left():
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "out.json"
        atomic_write_json([1, 2, 3], target)
        tmp_file = target.with_suffix(".tmp")
        assert not tmp_file.exists()


def test_load_json_missing_returns_default():
    result = load_json(Path("/nonexistent/path.json"), default={"fallback": True})
    assert result == {"fallback": True}


def test_post_cache_round_trip():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / ".post_cache.json"
        cache = {"slug1": {"hash": "abc123", "embedding": [0.1, 0.2, 0.3]}}
        save_post_cache(cache, path)
        loaded = load_post_cache(path)
        assert loaded["slug1"]["hash"] == "abc123"
        assert loaded["slug1"]["embedding"] == [0.1, 0.2, 0.3]


def test_tag_cache_round_trip():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / ".tag_cache.json"
        cache = {"python": [0.5, 0.6, 0.7]}
        save_tag_cache(cache, path)
        loaded = load_tag_cache(path)
        assert loaded["python"] == [0.5, 0.6, 0.7]


def test_save_tags_json_deduplicates_and_sorts():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "tags.json"
        changed = save_tags_json(["python", "python", "numpy", "docker"], path)
        assert changed is True
        tags = json.loads(path.read_text())
        assert tags == sorted(set(["python", "numpy", "docker"]))


def test_save_tags_json_no_change_returns_false():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "tags.json"
        save_tags_json(["numpy", "python"], path)
        changed = save_tags_json(["numpy", "python"], path)
        assert changed is False
