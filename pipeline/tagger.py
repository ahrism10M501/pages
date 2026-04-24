"""
3-tier tag assignment system.
  Tier 1: Vocabulary matching (exact/substring match against tag_vocabulary.json)
  Tier 2: Embedding similarity (cosine similarity against tag centroid vectors)
  Tier 3: TF-IDF keyword generation (fallback: create new tags from keywords)

Owns: all tag logic, .tag_cache.json management, tags.json writing.
Does NOT load the embedding model (receives pre-computed embeddings).
Does NOT build graph edges.
"""
from __future__ import annotations

import re
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from pipeline import config, io
from pipeline.models import PostCache, PostRecord, TagCache, TfidfKeywords


_PROGRAMMING_KEYWORDS: frozenset[str] = frozenset({
    "import", "from", "for", "in", "if", "else", "def", "class", "return",
    "print", "true", "false", "none", "self", "and", "or", "not", "is",
    "with", "as", "try", "except", "while", "break", "continue", "pass",
    "lambda", "yield", "raise", "del", "global", "assert", "finally",
    "elif", "async", "await", "var", "let", "const", "function",
})

_KOREAN_STOPWORDS: frozenset[str] = frozenset({
    "이", "그", "저", "것", "수", "등", "때", "및", "더", "또", "위",
    "후", "각", "번째", "이용해", "글입니다", "합니다", "있습니다",
    "됩니다", "입니다", "하는", "대한", "통해", "위한", "같은",
    "다른", "하여", "해서", "에서", "으로", "이런", "있는",
})

_CODE_CHARS_RE = re.compile(r'[(){}\[\]=<>;,\.+*/\\:\'"!@#$%^&`~]')
_KOREAN_PARTICLE_END_RE = re.compile(r'(를|을|에|의|는|은|가|이|다\.)$')


def normalize_tag(tag: str) -> str:
    return tag.strip().lower().replace(" ", "-").replace("_", "-")


def is_valid_tag(candidate: str) -> bool:
    """Reject tags containing code punctuation, Python keywords, Korean stopwords, or pure digits."""
    if _CODE_CHARS_RE.search(candidate):
        return False
    if candidate in _PROGRAMMING_KEYWORDS:
        return False
    if candidate in _KOREAN_STOPWORDS:
        return False
    if _KOREAN_PARTICLE_END_RE.search(candidate):
        return False
    if candidate.isdigit():
        return False
    return True


@lru_cache(maxsize=1)
def _load_vocabulary_cached(vocab_path_str: str) -> list[str]:
    return io.load_vocabulary(Path(vocab_path_str))


def load_vocabulary(vocab_path: Path | None = None) -> list[str]:
    """Load seed tags from tag_vocabulary.json (cached per path in process)."""
    return _load_vocabulary_cached(str(vocab_path or config.VOCAB_PATH))


def match_vocabulary_tags(text: str, vocabulary: list[str], max_tags: int = 3) -> list[str]:
    """Return normalized tags from vocabulary whose lowercase form appears in text."""
    text_lower = text.lower()
    matched: list[str] = []
    for tag in vocabulary:
        if tag.lower() in text_lower:
            matched.append(normalize_tag(tag))
        if len(matched) >= max_tags:
            break
    return matched


def compute_tag_centroids(
    posts: list[PostRecord],
    post_embeddings: dict[str, np.ndarray],
) -> dict[str, np.ndarray]:
    """
    Compute tag centroid vectors: mean of all post embeddings that carry that tag.
    Returns {normalized_tag: centroid_array}.
    """
    tag_vectors: dict[str, list[np.ndarray]] = {}
    for post in posts:
        slug = post["slug"]
        if slug not in post_embeddings:
            continue
        emb = post_embeddings[slug]
        for tag in post.get("tags", []):
            canonical = normalize_tag(tag)
            tag_vectors.setdefault(canonical, []).append(emb)

    return {tag: np.mean(vectors, axis=0) for tag, vectors in tag_vectors.items()}


def recommend_by_embedding(
    post_emb: np.ndarray,
    tag_cache: dict[str, np.ndarray],
    threshold: float | None = None,
    max_tags: int | None = None,
) -> list[tuple[str, float]]:
    """
    Rank tags by cosine similarity to post_emb.
    Returns [(tag, similarity), ...] in descending order, filtered by threshold.
    """
    if not tag_cache:
        return []

    thr = threshold if threshold is not None else config.MATCH_THRESHOLD
    max_t = max_tags if max_tags is not None else config.MAX_TAGS

    tag_names = list(tag_cache.keys())
    tag_embs = np.array([tag_cache[t] for t in tag_names])
    sims = cosine_similarity([post_emb], tag_embs)[0]

    ranked = sorted(zip(tag_names, sims), key=lambda x: x[1], reverse=True)
    return [(t, float(s)) for t, s in ranked if s >= thr][:max_t]


def generate_from_tfidf(
    tfidf_keywords: list[str],
    existing_tag_names: set[str],
    max_new: int = 3,
) -> list[str]:
    """
    Create new tag candidates from TF-IDF keywords.
    Excludes keywords already present in existing_tag_names (after normalize).
    """
    candidates: list[str] = []
    for kw in tfidf_keywords:
        normalized = normalize_tag(kw)
        if (normalized
                and normalized not in existing_tag_names
                and len(normalized) >= 2
                and is_valid_tag(normalized)):
            candidates.append(normalized)
        if len(candidates) >= max_new:
            break
    return candidates


def assign_tags(
    post_emb: np.ndarray,
    tag_cache: dict[str, np.ndarray],
    tfidf_keywords: list[str],
    post_text: str = "",
    threshold: float | None = None,
    max_tags: int | None = None,
    min_tags: int | None = None,
) -> list[str]:
    """
    3-tier tag assignment for a single post:
      1. Vocabulary matching (most precise)
      2. Embedding similarity recommendation (semantic)
      3. TF-IDF keyword generation (fallback)
    Returns up to max_tags normalized tag strings.
    """
    max_t = max_tags if max_tags is not None else config.MAX_TAGS
    min_t = min_tags if min_tags is not None else config.MIN_TAGS

    tags: list[str] = []
    tag_set: set[str] = set()

    # Tier 1: vocabulary matching
    if post_text:
        vocab = load_vocabulary()
        for t in match_vocabulary_tags(post_text, vocab, max_tags=max_t):
            if t not in tag_set:
                tags.append(t)
                tag_set.add(t)

    # Tier 2: embedding similarity
    if len(tags) < min_t:
        for t, _ in recommend_by_embedding(post_emb, tag_cache, threshold, max_t):
            if t not in tag_set:
                tags.append(t)
                tag_set.add(t)
            if len(tags) >= max_t:
                break

    # Tier 3: TF-IDF new tag generation
    if len(tags) < min_t:
        for t in generate_from_tfidf(tfidf_keywords, set(tag_cache.keys()), max_new=min_t - len(tags)):
            if t not in tag_set:
                tags.append(t)
                tag_set.add(t)

    return tags[:max_t]


def init_tag_cache(
    posts: list[PostRecord],
    post_embeddings: dict[str, np.ndarray],
    force: bool = False,
    cache_path: Path | None = None,
) -> dict[str, np.ndarray]:
    """
    Build tag centroid cache from tagged posts.
    If force=True, ignores any existing .tag_cache.json and recomputes from scratch.
    (This fixes the --force / .tag_cache.json bug in the original post_update.py.)
    Writes result atomically via io.save_tag_cache().
    Returns {tag: centroid_array}.
    """
    if not force:
        existing_raw = io.load_tag_cache(cache_path)
        if existing_raw:
            return {t: np.array(e) for t, e in existing_raw.items()}

    tag_embs = compute_tag_centroids(posts, post_embeddings)
    io.save_tag_cache({t: e.tolist() for t, e in tag_embs.items()}, cache_path)
    return tag_embs


def run_auto_tagging(
    posts: list[PostRecord],
    cache: PostCache,
    tfidf_per_post: list[TfidfKeywords],
    force: bool = False,
    tags_path: Path | None = None,
    cache_path: Path | None = None,
) -> list[str]:
    """
    Full tagging pipeline for a run:
    1. Separate tagged vs tagless posts
    2. init_tag_cache() from tagged posts (respects force flag)
    3. For each tagless post: assign_tags() → mutate post['tags'] in-place
    4. Normalize all tags across all posts
    5. Save updated tags.json via io.save_tags_json()
    Returns sorted list of all known tags after this run.
    """
    post_embeddings: dict[str, np.ndarray] = {}
    for post in posts:
        slug = post["slug"]
        if slug in cache:
            post_embeddings[slug] = np.array(cache[slug]["embedding"])

    tagged_posts = [p for p in posts if p.get("tags")]
    tag_embs = init_tag_cache(tagged_posts, post_embeddings, force=force, cache_path=cache_path)

    slug_to_idx = {p["slug"]: i for i, p in enumerate(posts)}
    tagless_posts = [p for p in posts if not p.get("tags")]

    new_tags_added: list[str] = []

    if tagless_posts:
        from pipeline.graph_builder import get_post_text
        all_texts = [get_post_text(p) for p in posts]

        for post in tagless_posts:
            slug = post["slug"]
            if slug not in post_embeddings:
                print(f"  임베딩 없음, 스킵: [{slug}]", file=sys.stderr)
                continue
            idx = slug_to_idx[slug]
            kw_list = list(tfidf_per_post[idx].keys()) if idx < len(tfidf_per_post) else []
            post["tags"] = assign_tags(
                post_embeddings[slug],
                tag_embs,
                kw_list,
                post_text=all_texts[idx],
            )
            new_tags_added.extend(post["tags"])
            print(f"  태그 할당: [{slug}] → {post['tags']}")

    # Normalize all tags across all posts
    for post in posts:
        post["tags"] = [normalize_tag(t) for t in post.get("tags", [])]

    known_tags = sorted(set(tag_embs.keys()) | set(new_tags_added))
    io.save_tags_json(known_tags, tags_path)
    print(f"tags.json: {len(known_tags)}개 태그")

    return known_tags
