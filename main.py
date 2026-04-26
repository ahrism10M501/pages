#!/usr/bin/env python3
"""
메인 빌드 스크립트 — 포스트/트윙클 업데이트 + 정적 사이트 빌드

Usage:
  python main.py               # 증분 업데이트
  python main.py --force       # 캐시 무시, 전체 임베딩 재계산
  python main.py --posts-only  # posts.json만 업데이트 (그래프 스킵)
"""

import argparse

from pipeline.orchestrator import run


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="posts.json + graph.json + tags 자동 업데이트")
    parser.add_argument("--force", action="store_true", help="캐시 무시, 전체 임베딩 재계산")
    parser.add_argument("--posts-only", action="store_true", help="posts.json만 업데이트 (그래프 스킵)")
    args = parser.parse_args()
    run(force=args.force, posts_only=args.posts_only)
