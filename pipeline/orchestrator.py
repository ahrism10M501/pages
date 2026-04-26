"""
Full build pipeline orchestrator.
Replaces scripts/post_update.py functionality using pipeline modules.

Flow: scan → embeddings → graph(1) → tagging → graph(2) → posts_json → twinkle → build_site
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from pipeline import config, scanner, graph_builder, tagger, io, embedder, state
from pipeline.models import PostCache, PostRecord


def _import_scripts_module(name: str):
    """Import a module from scripts/ by file path."""
    spec = importlib.util.spec_from_file_location(
        name,
        config.PROJECT_ROOT / "scripts" / f"{name}.py"
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module {name} from scripts/")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def run(force: bool = False, posts_only: bool = False) -> None:
    """
    Full build orchestrator.

    Args:
        force: Ignore cache, recompute all embeddings from scratch
        posts_only: Skip graph/tagging, only update posts.json
    """
    # 1) Scan posts
    print("포스트 스캔 중...")
    posts = scanner.scan_posts()
    print(f"  {len(posts)}개 포스트 발견")

    if not posts_only:
        # 2) Load cache and detect stale posts
        print("\n변경 감지 중...")
        cache = io.load_post_cache()
        stale, unchanged = state.detect_stale_posts(posts, cache, force=force)
        print(f"  {len(stale)}개 재계산, {len(unchanged)}개 캐시 유효")

        # 3) Compute embeddings for stale posts
        print("\n임베딩 계산 중...")
        cache = embedder.compute_post_embeddings(stale, cache, force=force)
        print(f"  {len(cache)}개 포스트 임베딩")

        # 4) Build graph for TF-IDF keywords (1st pass)
        print("\n그래프 생성 중 (1차)...")
        graph_data, tfidf_per_post = graph_builder.build_graph(posts, cache)
        print(f"  graph.json 생성 완료 ({len(graph_data['nodes'])} nodes, {len(graph_data['edges'])} edges)")

        # 5) Auto-tag posts
        print("\n태그 할당 중...")
        tagger.run_auto_tagging(posts, cache, tfidf_per_post, force=force)

    # 6) Save posts.json
    print("\nposts.json 업데이트 중...")
    existing = io.load_posts_json()
    changed = io.save_posts_json(posts, existing, force=force)
    print("posts.json 업데이트됨" if changed else "posts.json 변경 없음")

    if not posts_only:
        # 7) Rebuild graph after tags are applied (2nd pass)
        print("\n그래프 재생성 중 (2차, 태그 반영)...")
        cache = io.load_post_cache()
        stale, unchanged = state.detect_stale_posts(posts, cache, force=False)
        if stale:
            cache = embedder.compute_post_embeddings(stale, cache, force=False)
        graph_data, _ = graph_builder.build_graph(posts, cache)
        print(f"  graph.json 업데이트 완료 ({len(graph_data['nodes'])} nodes, {len(graph_data['edges'])} edges)")

    # 8) Update twinkles
    print("\n트윙클 업데이트 중...")
    twinkle_update = _import_scripts_module("twinkle_update")
    twinkle_changed = twinkle_update.update_twinkles_json()
    print("twinkles.json 업데이트됨" if twinkle_changed else "twinkles.json 변경 없음")

    # 9) Build static site
    print("\n정적 사이트 빌드 중...")
    build_site = _import_scripts_module("build_site")
    build_site.main()
    print("HTML 빌드 완료")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="posts.json + graph.json + tags 자동 업데이트")
    parser.add_argument("--force", action="store_true", help="캐시 무시, 전체 임베딩 재계산")
    parser.add_argument("--posts-only", action="store_true", help="posts.json만 업데이트 (그래프 스킵)")
    args = parser.parse_args()
    run(force=args.force, posts_only=args.posts_only)
