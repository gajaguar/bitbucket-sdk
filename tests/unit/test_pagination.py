from __future__ import annotations

from bitbucket._pagination import Page  # ruff: ignore[import-private-name]
from bitbucket._pagination import paginate  # ruff: ignore[import-private-name]


def _fetch_from(pages: list[Page[int]], cursor: str | None) -> Page[int]:
    return pages[0] if cursor is None else pages[1]


def test_paginate_follows_next_cursor_until_absent() -> None:
    # Arrange
    pages = [
        Page(items=[1, 2], next_cursor="https://api.bitbucket.org/2.0/things?page=2", size=4),
        Page(items=[3, 4], next_cursor=None),
    ]
    # Act
    items = list(paginate(lambda cursor: _fetch_from(pages, cursor)))
    # Assert
    assert items == [1, 2, 3, 4]


def test_paginate_single_page_stops_without_next_cursor() -> None:
    # Arrange
    page = Page(items=["a", "b"], next_cursor=None)
    # Act
    items = list(paginate(lambda _: page))
    # Assert
    assert items == ["a", "b"]


def test_paginate_empty_page_yields_nothing() -> None:
    # Arrange
    page: Page[str] = Page(items=[], next_cursor=None)
    # Act
    items = list(paginate(lambda _: page))
    # Assert
    assert not items
