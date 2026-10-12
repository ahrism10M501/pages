"""Atomic writes protect existing metadata and skip unchanged updates."""

import json

import pytest

from pipeline import io


def test_atomic_write_json_creates_file_and_removes_temp(tmp_path):
    target = tmp_path / "metadata" / "out.json"
    io.atomic_write_json({"key": "값"}, target)
    assert io.load_json(target) == {"key": "값"}
    assert not target.with_suffix(".tmp").exists()


def test_load_json_missing_returns_default(tmp_path):
    assert io.load_json(tmp_path / "missing.json", default={"fallback": True}) == {"fallback": True}


def test_failed_write_preserves_previous_metadata(tmp_path, monkeypatch):
    target = tmp_path / "posts.json"
    io.atomic_write_json(["existing"], target)

    def fail_replace(source, destination):
        raise OSError("replace failed")

    monkeypatch.setattr(io.os, "replace", fail_replace)
    with pytest.raises(OSError, match="replace failed"):
        io.atomic_write_json(["new"], target)
    assert io.load_json(target) == ["existing"]


def test_save_posts_refreshes_source_metadata_and_skips_unchanged(tmp_path):
    target = tmp_path / "posts.json"
    io.atomic_write_json([{"slug": "deleted", "date": "2020-01-01"}], target)
    posts = [
        {"slug": "older", "date": "2025-01-01"},
        {"slug": "newer", "date": "2026-01-01"},
    ]
    assert io.save_posts_json(posts, target)
    assert json.loads(target.read_text()) == [
        {"slug": "newer", "date": "2026-01-01"},
        {"slug": "older", "date": "2025-01-01"},
    ]
    assert not io.save_posts_json(posts, target)
