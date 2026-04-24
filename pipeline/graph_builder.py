"""
Builds blog/graph.json from post embeddings and text.
Owns: TF-IDF extraction, cosine similarity matrix, edge pruning, graph.json output.
Does NOT load the embedding model (receives pre-computed embeddings from embedder.py).
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from pipeline import config, io
from pipeline.models import GraphData, GraphEdge, GraphNode, PostCache, PostRecord, TfidfKeywords


def clean_text(text: str) -> str:
    """Remove markdown syntax, code fences, URLs, LaTeX, file paths."""
    text = re.sub(r'```[\s\S]*?```', ' ', text)
    text = re.sub(r'`[^`]+`', ' ', text)
    text = re.sub(r'https?://\S+', ' ', text)
    text = re.sub(
        r'\S+\.(py|txt|json|md|yml|yaml|jpg|png|html|css|js|dockerfile)\b',
        ' ', text, flags=re.IGNORECASE,
    )
    text = re.sub(r'!\[.*?\]\(.*?\)', ' ', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'\$\$[\s\S]*?\$\$', ' ', text)
    text = re.sub(r'\$[^$]+\$', ' ', text)
    text = re.sub(r'[#*_|>~`]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def get_post_text(post: PostRecord) -> str:
    """Combine title + summary + body with cleaning. Used for TF-IDF and as embedding input."""
    raw = "\n".join([post.get("title", ""), post.get("summary", ""), post.get("_body", "")])
    return clean_text(raw)


def _simple_korean_tokenizer(text: str) -> list[str]:
    """Fallback Korean tokenizer (no Mecab). Strips common particles, filters short tokens."""
    tokens = text.split()
    result = []
    for token in tokens:
        cleaned = re.sub(
            r'(은|는|이|가|을|를|에|의|로|으로|와|과|도|만|까지|에서|부터|처럼|으로서|라고|이라|에게|한테|께)$',
            '', token,
        )
        if len(cleaned) >= 2:
            result.append(cleaned)
    return result


def extract_tfidf_keywords(
    texts: list[str],
    top_n: int | None = None,
) -> list[TfidfKeywords]:
    """
    Compute TF-IDF over all texts jointly (IDF from full corpus).
    Returns one dict per text: {keyword: score} for the top_n scoring terms.
    Falls back to _simple_korean_tokenizer if konlpy.Mecab is unavailable.
    """
    n = top_n if top_n is not None else config.TFIDF_TOP_N

    try:
        from konlpy.tag import Mecab
        tokenizer = Mecab().morphs
    except Exception:
        tokenizer = _simple_korean_tokenizer

    vec = TfidfVectorizer(tokenizer=tokenizer, max_features=5000)
    mat = vec.fit_transform(texts)
    names = vec.get_feature_names_out()

    result: list[TfidfKeywords] = []
    for i in range(mat.shape[0]):
        row = mat[i].toarray().flatten()
        top = row.argsort()[-n:][::-1]
        result.append({names[j]: round(float(row[j]), 4) for j in top if row[j] > 0})
    return result


def compute_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """Compute pairwise cosine similarity matrix. Returns symmetric (n, n) matrix."""
    return cosine_similarity(embeddings)


def build_edges(
    sim_matrix: np.ndarray,
    slugs: list[str],
    threshold: float | None = None,
    max_edges_per_node: int | None = None,
) -> list[GraphEdge]:
    """
    Convert similarity matrix into edge list.
    Filters edges below threshold, then greedily selects highest-weight edges
    while respecting max_edges_per_node degree cap.
    """
    thr = threshold if threshold is not None else config.SIMILARITY_THRESHOLD
    max_deg = max_edges_per_node if max_edges_per_node is not None else config.MAX_EDGES_PER_NODE
    n = len(slugs)

    candidates = [
        (float(sim_matrix[i][j]), i, j)
        for i in range(n)
        for j in range(i + 1, n)
        if float(sim_matrix[i][j]) >= thr
    ]
    candidates.sort(reverse=True)

    degree = [0] * n
    edges: list[GraphEdge] = []
    for w, i, j in candidates:
        if degree[i] < max_deg and degree[j] < max_deg:
            edges.append({"source": slugs[i], "target": slugs[j], "weight": round(w, 4)})
            degree[i] += 1
            degree[j] += 1
    return edges


def build_graph(
    posts: list[PostRecord],
    cache: PostCache,
    graph_path: Path | None = None,
) -> tuple[GraphData, list[TfidfKeywords]]:
    """
    Full graph construction pipeline.
    1. Extract per-post texts
    2. extract_tfidf_keywords across all posts
    3. compute_similarity_matrix from cached embeddings
    4. build_edges with threshold and degree cap
    5. Construct GraphNode + GraphEdge lists
    6. Atomically write graph.json

    Returns (graph_data, tfidf_keywords_per_post) — keywords passed to tagger.
    """
    if not posts:
        empty: GraphData = {"nodes": [], "edges": []}
        io.save_graph_json(empty, graph_path)
        print("포스트 없음. 빈 graph.json 생성.")
        return empty, []

    slugs = [p["slug"] for p in posts]
    texts = [get_post_text(p) for p in posts]

    print("TF-IDF 키워드 추출 중...")
    keywords_list = extract_tfidf_keywords(texts)

    embeddings = np.array([cache[slug]["embedding"] for slug in slugs])
    sim_matrix = compute_similarity_matrix(embeddings)
    edges = build_edges(sim_matrix, slugs)

    nodes: list[GraphNode] = [
        {
            "id": p["slug"],
            "title": p["title"],
            "date": p["date"],
            "tags": p["tags"],
            "summary": p.get("summary", ""),
            "tfidf": keywords_list[i],
        }
        for i, p in enumerate(posts)
    ]

    graph: GraphData = {"nodes": nodes, "edges": edges}
    io.save_graph_json(graph, graph_path)
    print(f"graph.json 생성 완료 ({len(nodes)} nodes, {len(edges)} edges)")

    return graph, keywords_list
