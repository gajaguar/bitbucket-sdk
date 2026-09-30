from __future__ import annotations

from typing import TYPE_CHECKING

from bitbucket._pagination import Page  # ruff: ignore[import-private-name]
from bitbucket._pagination import apaginate  # ruff: ignore[import-private-name]

if TYPE_CHECKING:
    from collections.abc import Awaitable
    from collections.abc import Callable


async def _fetch_from(pages: list[Page[int]], cursor: str | None) -> Page[int]:  # ruff: ignore[unused-async]
    return pages[0] if cursor is None else pages[1]


async def test_apaginate_follows_next_cursor_until_absent() -> None:
    # Arrange
    pages = [
        Page(items=[1, 2], next_cursor="https://api.bitbucket.org/2.0/things?page=2", size=4),
        Page(items=[3, 4], next_cursor=None),
    ]
    # Act
    items = [item async for item in apaginate(lambda cursor: _fetch_from(pages, cursor))]
    # Assert
    assert items == [1, 2, 3, 4]


async def _single(page: Page[str]) -> Callable[[str | None], Awaitable[Page[str]]]:  # ruff: ignore[unused-async]
    async def _fetch(_: str | None) -> Page[str]:  # ruff: ignore[unused-async]
        return page

    return _fetch


async def test_apaginate_single_page_stops_without_next_cursor() -> None:
    # Arrange
    page = Page(items=["a", "b"], next_cursor=None)
    # Act
    items = [item async for item in apaginate(await _single(page))]
    # Assert
    assert items == ["a", "b"]


async def test_apaginate_empty_page_yields_nothing() -> None:
    # Arrange
    page: Page[str] = Page(items=[], next_cursor=None)
    # Act
    items = [item async for item in apaginate(await _single(page))]
    # Assert
    assert not items
