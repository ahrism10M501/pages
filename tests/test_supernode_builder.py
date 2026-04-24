"""Tests for pipeline.supernode_builder."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from pipeline import config


def _make_posts(n: int) -> list:
    """포스트 더미 데이터. 짝수는 AI 태그, 홀수는 하드웨어 태그."""
    return [
        {
            "slug": f"post-{i}",
            "title": f"Post {i}",
            "date": "2026-01-01",
            "tags": ["딥러닝", "신경망"] if i % 2 == 0 else ["하드웨어", "FPGA"],
        }
        for i in range(n)
    ]


def _make_tag_cache() -> dict:
    """공간적으로 두 군집이 명확한 태그 임베딩."""
    return {
        "딥러닝": [1.0, 0.0, 0.0],
        "신경망": [0.95, 0.05, 0.0],
        "하드웨어": [0.0, 0.0, 1.0],
        "FPGA": [0.05, 0.0, 0.95],
    }


def test_returns_empty_below_threshold(tmp_path):
    """포스트 수 < MIN_POSTS_FOR_SUPERNODES 이면 [] 반환, graph.json에 빈 배열 inject."""
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(json.dumps({"nodes": [], "edges": []}), encoding="utf-8")

    from pipeline.supernode_builder import build_supernodes

    posts = _make_posts(5)  # 30 미만
    result = build_supernodes(posts, graph_path=graph_path)

    assert result == []
    data = json.loads(graph_path.read_text(encoding="utf-8"))
    assert data["supernodes"] == []


def test_cluster_tags_groups_similar_tags(tmp_path):
    """유사한 태그들이 같은 슈퍼노드로 묶인다."""
    from pipeline.supernode_builder import _cluster_tags

    tag_cache = _make_tag_cache()
    posts = _make_posts(4)  # _cluster_tags는 직접 호출 — 게이트 없음

    with patch.object(config, "SUPERNODE_DISTANCE_THRESHOLD", 0.3):
        supernodes = _cluster_tags(tag_cache, posts)

    assert len(supernodes) >= 1
    all_tags = [t for s in supernodes for t in s["tags"]]
    assert set(all_tags) <= {"딥러닝", "신경망", "하드웨어", "FPGA"}
    # 각 슈퍼노드는 id, label, tags를 가짐
    for s in supernodes:
        assert "id" in s and "label" in s and "tags" in s
        assert isinstance(s["tags"], list)


def test_inject_supernodes_writes_to_graph_json(tmp_path):
    """_inject_supernodes_into_graph이 graph.json의 supernodes 키를 덮어쓴다."""
    from pipeline.supernode_builder import _inject_supernodes_into_graph

    graph_path = tmp_path / "graph.json"
    graph_path.write_text(
        json.dumps({"nodes": [{"id": "nn1"}], "edges": []}), encoding="utf-8"
    )
    supernodes = [{"id": "supernode-0", "label": "딥러닝", "tags": ["딥러닝", "신경망"]}]

    _inject_supernodes_into_graph(supernodes, graph_path=graph_path)

    data = json.loads(graph_path.read_text(encoding="utf-8"))
    assert data["supernodes"] == supernodes
    assert data["nodes"] == [{"id": "nn1"}]  # 기존 노드 유지


def test_build_supernodes_runs_clustering_above_threshold(tmp_path):
    """포스트 수 >= 30이면 tag_cache 기반 클러스터링이 실행된다."""
    graph_path = tmp_path / "graph.json"
    graph_path.write_text(json.dumps({"nodes": [], "edges": []}), encoding="utf-8")

    from pipeline.supernode_builder import build_supernodes

    posts = _make_posts(30)
    tag_cache = _make_tag_cache()

    with patch("pipeline.supernode_builder.io.load_tag_cache", return_value=tag_cache), \
         patch.object(config, "SUPERNODE_DISTANCE_THRESHOLD", 0.3):
        result = build_supernodes(posts, graph_path=graph_path)

    assert len(result) >= 1
    data = json.loads(graph_path.read_text(encoding="utf-8"))
    assert len(data["supernodes"]) == len(result)
