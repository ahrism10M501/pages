from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_style_defines_semantic_theme_tokens():
    css = read("style.css")
    for token in [
        "--color-bg",
        "--color-surface",
        "--color-surface-raised",
        "--color-border",
        "--color-text",
        "--color-muted",
        "--color-accent",
        "--color-accent-strong",
        "--color-info",
        "--color-danger",
        "--color-success",
    ]:
        assert token in css


def test_pink_is_not_used_as_general_state_color():
    css = read("style.css")
    assert css.count("#dc00c9") <= 4


def test_semantic_color_tokens_use_valid_hex_values():
    css = read("style.css")
    root_match = re.search(r":root\s*\{(?P<body>.*?)\n\}", css, re.DOTALL)
    assert root_match is not None

    declarations = re.findall(
        r"(--color-[\w-]+)\s*:\s*(#[0-9a-fA-F]+)\s*;",
        root_match.group("body"),
    )
    assert declarations

    for token, value in declarations:
        assert re.fullmatch(r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?", value), (
            f"{token} uses invalid hex color {value}"
        )
        assert value.lower() != "#6d4ef0", f"{token} uses rejected hover typo {value}"
