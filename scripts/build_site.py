#!/usr/bin/env python3
"""Build metadata and HTML from the existing Markdown and notebook sources."""

import sys
from itertools import combinations
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
    ("pages/graph.html", "graph/index.html", "graph"),
    ("pages/github.html", "github/index.html", "github"),
]


def build_graph(posts, twinkles):
    nodes = []
    related = {}
    for kind, records in (("post", posts), ("twinkle", twinkles)):
        for record in records:
            node_id = f"{kind}:{record['slug']}"
            references = record.get("related", [])
            if not isinstance(references, list) or any(not isinstance(ref, str) for ref in references):
                raise ValueError(f"{node_id}: related must be a list of post:<slug> or twinkle:<slug>")
            related[node_id] = references
            slug = quote(record["slug"], safe="")
            nodes.append({
                "id": node_id,
                "kind": kind,
                "title": record["title"],
                "date": record["date"],
                "tags": record["tags"],
                "summary": record.get("summary") or scanner.extract_summary(record.get("content", "")),
                "url": f"posts/{slug}/" if kind == "post" else f"twinkle/#{slug}",
            })
    ids = {node["id"] for node in nodes}
    for node_id, references in related.items():
        for reference in references:
            if reference not in ids or reference == node_id:
                raise ValueError(f"{node_id}: invalid related reference {reference!r}")
    edges = []
    for source, target in combinations(nodes, 2):
        tags = sorted(set(source["tags"]) & set(target["tags"]))
        manual = target["id"] in related[source["id"]] or source["id"] in related[target["id"]]
        if tags or manual:
            edges.append({"source": source["id"], "target": target["id"], "tags": tags, "manual": manual})
    return {"nodes": nodes, "edges": edges}


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
    twinkles = twinkle_update.scan_twinkles(ROOT / "twinkle")
    graph = build_graph(posts, twinkles)
    io.save_posts_json(posts, ROOT / "blog" / "posts.json")
    twinkle_update.update_twinkles_json(twinkles, ROOT / "twinkle" / "twinkles.json")
    context = {
        "nav": io.load_json(ROOT / "templates" / "nav.json"),
        "posts": posts,
        "twinkles": twinkles,
        "projects": io.load_json(ROOT / "projects.json", default=[]),
        "site_url": SITE_URL,
        "graph": graph,
    }
    env = make_env()
    for template_name, out_rel, current_page in PAGES:
        render_page(env, context, template_name, out_rel, current_page)
    for post in posts:
        render_page(env, context, "pages/post.html", f"posts/{post['slug']}/index.html", "blog", post)
    print(f"Done. {len(PAGES)} pages + {len(posts)} posts, {len(twinkles)} short notes.")


if __name__ == "__main__":
    main()
