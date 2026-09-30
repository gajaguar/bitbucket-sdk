---
type: concept
title: Pagination
description: How Page and paginate() follow Bitbucket next URLs lazily.
tags: [architecture]
status: stable
---

# Pagination

Bitbucket collection endpoints return a `next` URL alongside `values` (and,
on the first page, `size`). `Page[T]` (`_pagination.py`) carries that as
`items`/`next_cursor`/`size`; `paginate()` wraps repeated `list_page(cursor=...)`
calls into a lazy `Iterator[T]`, re-requesting the literal `next` URL until it
is absent.

```mermaid
flowchart LR
    A["repo.pull_requests.list(...)"] --> B["paginate() (lazy)"]
    B --> C["list_page(cursor)"]
    C --> D["yield items"]
    D --> E{"next_cursor present?"}
    E -- yes --> C
    E -- no --> F["StopIteration"]
```
