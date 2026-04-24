"""
Change detection and run state tracking.
Computes which posts are stale (need re-embedding) by comparing SHA256 hashes.
No direct file I/O — delegates reads to io.py.
"""
from __future__ import annotations

import hashlib

from pipeline import config, io
from pipeline.models import PostCache, PostRecord, RunState


def content_hash(text: str) -> str:
    """SHA256 hex digest (first 16 chars) used for cache invalidation."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def compute_post_text(post: PostRecord) -> str:
    """
    Assemble the canonical text for a post: title + summary + _body.
    Same text is used for both hashing and embedding — must stay in sync with embedder.py.
    """
    return "\n".join([
        post.get("title", ""),
        post.get("summary", ""),
        post.get("_body", ""),
    ])


def detect_stale_posts(
    posts: list[PostRecord],
    cache: PostCache,
    force: bool = False,
) -> tuple[list[PostRecord], list[PostRecord]]:
    """
    Partition posts into (stale, unchanged).
    A post is stale if: force=True, slug missing from cache, or hash changed.
    Returns (stale_posts, unchanged_posts).
    """
    stale: list[PostRecord] = []
    unchanged: list[PostRecord] = []

    for post in posts:
        slug = post["slug"]
        text = compute_post_text(post)
        if force or slug not in cache or cache[slug]["hash"] != content_hash(text):
            stale.append(post)
        else:
            unchanged.append(post)

    return stale, unchanged


def build_run_state(
    posts: list[PostRecord],
    force: bool,
    posts_only: bool,
    cache_path=None,
) -> RunState:
    """
    Construct the initial RunState for a pipeline run.
    Loads post cache and partitions posts into stale / unchanged / tagless.
    """
    cache = io.load_post_cache(cache_path)
    stale, unchanged = detect_stale_posts(posts, cache, force=force)

    run_state = RunState(force=force, posts_only=posts_only)
    run_state.stale_slugs = {p["slug"] for p in stale}
    run_state.unchanged_slugs = {p["slug"] for p in unchanged}
    run_state.tagless_slugs = {p["slug"] for p in posts if not p.get("tags")}

    return run_state
