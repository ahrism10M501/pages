#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["jinja2>=3.1"]
# ///
"""
Static site builder.

Renders templates/pages/*.html to top-level HTML files using Jinja2.
Each template extends base.html and receives:
  - nav: list of sidebar items (from templates/nav.json)
  - current_page: id of current page (e.g. "home", "blog")
  - root: relative path to repo root (e.g. "./", "../", "../../")

Usage:
  uv run python scripts/build_site.py
"""

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).parent.parent
TEMPLATES = ROOT / "templates"

# (template path, output path relative to ROOT, current_page id)
PAGES = [
    ("pages/home.html",    "index.html",         "home"),
    ("pages/about.html",   "about/index.html",   "about"),
    ("pages/blog.html",    "blog/index.html",    "blog"),
    ("pages/twinkle.html", "twinkle/index.html", "twinkle"),
    ("pages/github.html",  "github/index.html",  "github"),
]


def load_nav():
    return json.loads((TEMPLATES / "nav.json").read_text(encoding="utf-8"))


def make_env():
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )


def path_to_root(out_rel: str) -> str:
    """'index.html' → './', 'foo/index.html' → '../', 'a/b/index.html' → '../../'"""
    depth = out_rel.count("/")
    return "../" * depth if depth else "./"


def render_page(env, nav, template_name, out_rel, current_page):
    out_path = ROOT / out_rel
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tpl = env.get_template(template_name)
    html = tpl.render(
        nav=nav,
        current_page=current_page,
        root=path_to_root(out_rel),
    )
    out_path.write_text(html, encoding="utf-8")
    print(f"  built {out_rel}")


def render_post_pages(env, nav):
    """Render posts/<slug>/index.html for every posts/<slug>/content.md."""
    posts_dir = ROOT / "posts"
    if not posts_dir.exists():
        return 0
    count = 0
    seen = set()
    # Posts may use content.md or content.ipynb (notebooks).
    for content in sorted(list(posts_dir.glob("*/content.md")) + list(posts_dir.glob("*/content.ipynb"))):
        slug = content.parent.name
        if slug in seen or slug.startswith("_"):
            continue
        seen.add(slug)
        render_page(env, nav, "pages/post.html", f"posts/{slug}/index.html", "blog")
        count += 1
    return count


def main():
    print("Building site...")
    env = make_env()
    nav = load_nav()
    for tpl, out_rel, current in PAGES:
        if not (TEMPLATES / tpl).exists():
            print(f"  skip {out_rel} (template missing: {tpl})")
            continue
        render_page(env, nav, tpl, out_rel, current)
    posts_built = render_post_pages(env, nav)
    print(f"Done. {len(PAGES)} pages + {posts_built} posts built.")


if __name__ == "__main__":
    main()
