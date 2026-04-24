"""Unit tests for pipeline.graph_builder — migrated from scripts/test_build_graph.py."""
from collections import Counter

import numpy as np
import pytest

from pipeline.graph_builder import build_edges, compute_similarity_matrix, extract_tfidf_keywords


def test_compute_similarity_matrix_symmetric_diagonal():
    embeddings = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.7071, 0.7071, 0.0],
    ])
    sim = compute_similarity_matrix(embeddings)
    assert sim.shape == (3, 3)
    assert abs(sim[0][1] - sim[1][0]) < 1e-6
    for i in range(3):
        assert abs(sim[i][i] - 1.0) < 1e-6


def test_build_edges_respects_threshold_and_max():
    slugs = ["a", "b", "c", "d"]
    sim = np.array([
        [1.0, 0.9, 0.5, 0.2],
        [0.9, 1.0, 0.4, 0.35],
        [0.5, 0.4, 1.0, 0.6],
        [0.2, 0.35, 0.6, 1.0],
    ])
    edges = build_edges(sim, slugs, threshold=0.3, max_edges_per_node=2)

    sources_targets = [(e["source"], e["target"]) for e in edges]
    assert ("a", "d") not in sources_targets
    assert ("d", "a") not in sources_targets

    counts = Counter()
    for e in edges:
        counts[e["source"]] += 1
        counts[e["target"]] += 1
    for node, count in counts.items():
        assert count <= 2, f"Node {node} has {count} edges, max is 2"


def test_extract_tfidf_keywords():
    texts = [
        "머신러닝 딥러닝 인공지능 모델 학습",
        "웹 개발 프론트엔드 자바스크립트 리액트",
        "머신러닝 모델 학습 데이터 전처리",
    ]
    keywords_list = extract_tfidf_keywords(texts, top_n=3)
    assert len(keywords_list) == 3
    for kw in keywords_list:
        assert len(kw) <= 3
        for word, score in kw.items():
            assert isinstance(word, str)
            assert isinstance(score, float)
            assert score > 0
