---
type: reference
title: Modeling
description: How read and write payloads map to frozen pydantic models.
tags: [architecture]
status: stable
---

# Modeling

Every response is a frozen pydantic model (`BitbucketModel` base:
`populate_by_name=True`, `extra="allow"`, every field optional). There is
**no `alias_generator`** — Bitbucket's wire names are already snake_case —
so only the two reserved-word fields (`Links.self_`, `CommentInline.from_`)
carry an explicit `Field(alias=...)`.
Every field is optional because Bitbucket's `fields=` query parameter can
omit anything from any response.

Write payloads (`PullRequestCreate`, `CommentCreate`, ...) are separate models
from their read counterparts and serialize with
`model_dump(mode="json", by_alias=True, exclude_unset=True)`.
