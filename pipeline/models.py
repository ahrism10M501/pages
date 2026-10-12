"""Content metadata shared by the scanner and writer."""

from typing import TypedDict


class FrontMatter(TypedDict, total=False):
    title: str
    date: str
    tags: list[str]
    summary: str
    related: list[str]


class PostRecord(TypedDict, total=False):
    slug: str
    title: str
    date: str
    tags: list[str]
    summary: str
    notebook: bool
    related: list[str]
