"""
Sentence-transformer model wrapper and embedding cache management.
Owns: model loading (lazy singleton), encode() calls, .post_cache.json updates.
Does NOT assign tags. Does NOT build graph edges.
"""
from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

import numpy as np

from pipeline import config, io
from pipeline.models import PostCache, PostRecord
from pipeline.state import compute_post_text, content_hash


@lru_cache(maxsize=1)
def _load_model(model_name: str):
    """Load SentenceTransformer model (cached in process — loaded at most once per run)."""
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(model_name)


def encode_texts(texts: list[str], model_name: str | None = None) -> np.ndarray:
    """
    Encode a list of texts into embedding vectors.
    Returns shape (len(texts), embedding_dim) numpy array.
    """
    model = _load_model(model_name or config.MODEL_NAME)
    return model.encode(texts, show_progress_bar=True, convert_to_numpy=True)


def compute_post_embeddings(
    stale_posts: list[PostRecord],
    existing_cache: PostCache,
    force: bool = False,
    cache_path: Path | None = None,
) -> PostCache:
    """
    Compute embeddings for stale_posts, merge with existing_cache, save, and return.

    If force=True, existing_cache is ignored (all posts in stale_posts recomputed).
    Writes updated cache atomically via io.save_post_cache().
    Returns the complete updated PostCache (stale + previously cached entries).
    """
    cache = {} if force else dict(existing_cache)

    if not stale_posts:
        print("모든 임베딩 캐시 유효 — 모델 로딩 스킵.")
        return cache

    print(f"임베딩 재계산: {[p['slug'] for p in stale_posts]}")
    print("모델 로딩 중 (첫 실행 시 다운로드)...")

    texts = [compute_post_text(p) for p in stale_posts]
    new_embs = encode_texts(texts)

    for post, emb in zip(stale_posts, new_embs):
        slug = post["slug"]
        cache[slug] = {
            "hash": content_hash(compute_post_text(post)),
            "embedding": emb.tolist(),
        }

    io.save_post_cache(cache, cache_path)
    print(f"캐시 저장 완료 → {(cache_path or config.POST_CACHE).relative_to(config.PROJECT_ROOT)}")
    return cache


def get_embeddings_array(
    posts: list[PostRecord],
    cache: PostCache,
) -> tuple[list[str], np.ndarray]:
    """
    Extract embeddings for the given posts from cache.
    Returns (slugs, embeddings) where embeddings[i] corresponds to slugs[i].
    Warns and skips posts missing from cache.
    """
    slugs: list[str] = []
    vectors: list[list[float]] = []

    for post in posts:
        slug = post["slug"]
        if slug not in cache:
            print(f"  [WARN] 임베딩 없음, 스킵: [{slug}]", file=sys.stderr)
            continue
        slugs.append(slug)
        vectors.append(cache[slug]["embedding"])

    return slugs, np.array(vectors)
