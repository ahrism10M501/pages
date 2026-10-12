#!/usr/bin/env python3
"""Build metadata and HTML from the existing Markdown and notebook sources."""

import sys
from pathlib import Path
from urllib.parse import quote

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline import io, scanner
from scripts import twinkle_update

SITE_URL = "https://ahrism10m501.github.io/pages"
PAGES = [
    ("pages/home.html", "index.html", "home"),
    ("pages/about.html", "about/index.html", "about"),
    ("pages/blog.html", "blog/index.html", "blog"),
    ("pages/twinkle.html", "twinkle/index.html", "twinkle"),
    ("pages/github.html", "github/index.html", "github"),
]


def make_env():
    env = Environment(
        loader=FileSystemLoader(str(ROOT / "templates")),
        autoescape=select_autoescape(["html"]),
    )
    env.filters["urlencode"] = lambda value: quote(str(value), safe="")
    return env


def path_to_root(out_rel: str) -> str:
    depth = out_rel.count("/")
    return "../" * depth if depth else "./"


def render_page(env, context, template_name, out_rel, current_page, post=None):
    out_path = ROOT / out_rel
    out_path.parent.mkdir(parents=True, exist_ok=True)
    page_path = out_rel.removesuffix("index.html")
    html = env.get_template(template_name).render(
        **context,
        current_page=current_page,
        root=path_to_root(out_rel),
        post=post,
        canonical_url=f"{SITE_URL}/{quote(page_path, safe='/')}",
    )
    out_path.write_text(html, encoding="utf-8")
    print(f"  built {out_rel}")


def main():
    posts = sorted(scanner.scan_posts(ROOT / "posts"), key=lambda post: post["date"], reverse=True)
    io.save_posts_json(posts, ROOT / "blog" / "posts.json")
    twinkles = twinkle_update.scan_twinkles(ROOT / "twinkle")
    twinkle_update.update_twinkles_json(twinkles, ROOT / "twinkle" / "twinkles.json")
    context = {
        "nav": io.load_json(ROOT / "templates" / "nav.json"),
        "posts": posts,
        "twinkles": twinkles,
        "projects": io.load_json(ROOT / "projects.json", default=[]),
        "site_url": SITE_URL,
    }
    env = make_env()
    for template_name, out_rel, current_page in PAGES:
        render_page(env, context, template_name, out_rel, current_page)
    for post in posts:
        render_page(env, context, "pages/post.html", f"posts/{post['slug']}/index.html", "blog", post)
    print(f"Done. {len(PAGES)} pages + {len(posts)} posts, {len(twinkles)} short notes.")


if __name__ == "__main__":
    main()
