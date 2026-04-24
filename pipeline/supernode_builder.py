"""
Builds supernodes (thematic anchors) from tag embeddings via agglomerative clustering.
Injects `supernodes` array into graph.json after graph construction.

Gate: skips clustering if post count < config.MIN_POSTS_FOR_SUPERNODES.
TODO: 포스트가 30개 이상이 되면 build_supernodes()의 게이트 조건문 전체를 삭제할 것.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import normalize

from pipeline import config, io
from pipeline.models import PostRecord, SupernodeData, TagCache


def build_supernodes(
    posts: list[PostRecord],
    graph_path: Path | None = None,
) -> list[SupernodeData]:
    """
    포스트 수 < MIN_POSTS_FOR_SUPERNODES이면 빈 supernodes를 graph.json에 inject 후 반환.
    이상이면 tag_cache 임베딩을 AgglomerativeClustering으로 군집화해 슈퍼노드 생성.
    """
    if len(posts) < config.MIN_POSTS_FOR_SUPERNODES:
        # TODO: 포스트가 30개 이상이 되면 이 조건문 전체를 삭제할 것
        _inject_supernodes_into_graph([], graph_path)
        return []

    tag_cache = io.load_tag_cache()
    supernodes = _cluster_tags(tag_cache, posts)
    _inject_supernodes_into_graph(supernodes, graph_path)
    print(f"슈퍼노드 생성 완료 ({len(supernodes)}개 클러스터)")
    return supernodes


def _cluster_tags(
    tag_cache: TagCache,
    posts: list[PostRecord],
) -> list[SupernodeData]:
    """태그 임베딩을 AgglomerativeClustering으로 군집화해 SupernodeData 목록 반환."""
    all_post_tags = [tag for p in posts for tag in p.get("tags", [])]
    tag_freq = Counter(all_post_tags)

    # 포스트에 등장하고 임베딩이 있는 태그만 사용
    known_tags = [t for t in tag_freq if t in tag_cache]
    if len(known_tags) < 2:
        return []

    embeddings = np.array([tag_cache[t] for t in known_tags], dtype=np.float32)
    # cosine distance를 위해 L2 정규화
    embeddings = normalize(embeddings, norm="l2")

    model = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=config.SUPERNODE_DISTANCE_THRESHOLD,
        linkage="average",
        metric="cosine",
    )
    labels = model.fit_predict(embeddings)

    clusters: dict[int, list[str]] = {}
    for tag, label in zip(known_tags, labels.tolist()):
        clusters.setdefault(label, []).append(tag)

    supernodes: list[SupernodeData] = []
    for cluster_id, tags in sorted(clusters.items()):
        label = max(tags, key=lambda t: tag_freq[t])
        supernodes.append({
            "id": f"supernode-{cluster_id}",
            "label": label,
            "tags": sorted(tags, key=lambda t: -tag_freq[t]),
        })

    return supernodes


def _inject_supernodes_into_graph(
    supernodes: list[SupernodeData],
    graph_path: Path | None = None,
) -> None:
    """graph.json을 읽어 supernodes 키를 upsert하고 원자적으로 저장."""
    target = graph_path or config.GRAPH_JSON
    graph = io.load_json(target, default={"nodes": [], "edges": [], "supernodes": []})
    graph["supernodes"] = supernodes
    io.save_graph_json(graph, target)
