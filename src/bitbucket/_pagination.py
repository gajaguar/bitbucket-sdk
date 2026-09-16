from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Iterator


@dataclass(frozen=True, slots=True)
class Page[T]:
    items: list[T]
    next_cursor: str | None
    size: int | None = None


def paginate[T](fetch: Callable[[str | None], Page[T]]) -> Iterator[T]:
    cursor: str | None = None
    while True:
        page = fetch(cursor)
        yield from page.items
        if not page.next_cursor:
            return
        cursor = page.next_cursor
