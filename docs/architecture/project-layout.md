---
type: reference
title: Project layout
description: What each top-level file and directory of the repository holds, and where the sync and async code and tests live.
tags: [architecture]
status: stable
---

# Project layout

```text
.
├── pyproject.toml       # deps, ruff/mypy/pyright/pytest/coverage config
├── Makefile             # check/fix command surface (root: shared targets)
├── mk/python.mk         # Python-specific targets, wired into the Makefile
├── mise.toml            # pinned toolchain versions
├── docs/                # OKF notes: architecture, endpoint coverage, SDK
├── src/bitbucket/       # SDK package (client, models/, resources/)
│   └── aio/             # async mirror: AsyncBitbucketClient + Async resources
└── tests/
    ├── unit/            # respx-backed, offline, deterministic
    │   └── aio/         # async mirror tests
    └── live/            # marker-gated (`-m live`), hits a real workspace
```
