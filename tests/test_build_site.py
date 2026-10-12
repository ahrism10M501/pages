"""A complete build refreshes metadata and preserves encoded legacy URLs."""

import json

import nbformat
import pytest

import build_site


def test_build_refreshes_metadata_and_all_page_context(tmp_path, monkeypatch):
    monkeypatch.setattr(build_site, "ROOT", tmp_path)
    templates = tmp_path / "templates" / "pages"
    templates.mkdir(parents=True)
    (tmp_path / "templates" / "nav.json").write_text('[{"id":"home","href":""}]')
    (tmp_path / "projects.json").write_text('[{"name":"Existing project"}]')
    page = (
        '{{ current_page }}|{{ root }}|{{ site_url }}|{{ canonical_url }}|{{ nav[0].id }}|'
        '{{ projects[0].name }}|{{ twinkles[0].title }}|'
        '{% for item in posts %}{{ item.title }}:{{ item.slug|urlencode }};{% endfor %}'
    )
    for template_name, _, _ in build_site.PAGES:
        (tmp_path / "templates" / template_name).write_text(page)
    (templates / "post.html").write_text(page + '|{{ post.title }}|{{ post.notebook }}')
    source = tmp_path / "posts" / "with space"
    source.mkdir(parents=True)
    (source / "content.md").write_text('---\ntitle: Old markdown\ndate: 2020-01-01\n---\nbody')
    notebook = nbformat.v4.new_notebook(cells=[nbformat.v4.new_markdown_cell(
        '---\ntitle: Notebook <title>\ndate: 2026-10-12\ntags: [python]\n---\nNotebook summary'
    )])
    nbformat.write(notebook, source / "content.ipynb")
    older = tmp_path / "posts" / "older"
    older.mkdir()
    (older / "content.md").write_text('---\ntitle: Older\ndate: 2025-01-01\nrelated: ["post:with space"]\n---\nbody')
    draft = tmp_path / "posts" / "draft"
    draft.mkdir()
    (draft / "content.md").write_text('Unpublished draft without frontmatter')
    twinkle_dir = tmp_path / "twinkle"
    twinkle_dir.mkdir()
    (twinkle_dir / "note.md").write_text('---\ntitle: Short note\ndate: 2026-10-10\nrelated: ["post:older"]\n---\nNote body')
    build_site.main()

    posts_path = tmp_path / "blog" / "posts.json"
    posts = json.loads(posts_path.read_text())
    assert [post["slug"] for post in posts] == ["with space", "older"]
    assert posts[0]["notebook"] is True
    assert posts[0]["summary"] == "Notebook summary"
    assert posts[1]["related"] == ["post:with space"]
    assert (source / "content.ipynb").exists()
    assert not (draft / "index.html").exists()
    assert json.loads((twinkle_dir / "twinkles.json").read_text())[0]["content"] == "Note body"
    assert json.loads((twinkle_dir / "twinkles.json").read_text())[0]["related"] == ["post:older"]
    for _, output, current_page in build_site.PAGES:
        html = (tmp_path / output).read_text()
        assert html.startswith(current_page + '|')
        assert 'Notebook &lt;title&gt;:with%20space;Older:older;' in html
        assert 'Existing project|Short note|' in html
    post_html = (source / "index.html").read_text()
    assert '|../../|' in post_html
    assert 'https://ahrism10m501.github.io/pages/posts/with%20space/' in post_html
    assert '|Notebook &lt;title&gt;|True' in post_html
    mtime = posts_path.stat().st_mtime_ns
    build_site.main()
    assert posts_path.stat().st_mtime_ns == mtime


def test_graph_keeps_isolated_records_and_merges_shared_tags_with_explicit_links():
    posts = [
        {"slug": "same slug", "title": "Post", "date": "2026-01-01", "tags": ["AI"],
         "related": ["twinkle:same slug"]},
        {"slug": "isolated", "title": "No links", "date": "2026-01-02", "tags": []},
    ]
    notes = [{"slug": "same slug", "title": "Note", "date": "2026-01-01", "tags": ["AI"],
              "content": "A short note", "related": ["post:same slug"]}]
    graph = build_site.build_graph(posts, notes)
    assert len(graph["nodes"]) == 3
    assert len({node["id"] for node in graph["nodes"]}) == 3
    assert graph["nodes"][0]["url"] == "posts/same%20slug/"
    assert graph["nodes"][2]["url"] == "twinkle/#same%20slug"
    assert graph["nodes"][2]["summary"] == "A short note"
    assert graph["edges"] == [{
        "source": "post:same slug", "target": "twinkle:same slug",
        "tags": ["AI"], "manual": True,
    }]
    assert build_site.build_graph([], []) == {"nodes": [], "edges": []}


@pytest.mark.parametrize("related", ["post:missing", [42], ["post:missing"], ["post:self"]])
def test_graph_rejects_invalid_explicit_references(related):
    with pytest.raises(ValueError, match="post:self"):
        build_site.build_graph([{
            "slug": "self", "title": "Title", "date": "2026-01-01",
            "tags": [], "related": related,
        }], [])
