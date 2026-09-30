---
type: concept
title: Request lifecycle
description: The auth, retry, error-mapping, and validation pipeline every request goes through.
tags: [architecture]
status: stable
---

# Request lifecycle

Every request passes through the same auth → retry → error-mapping →
validation pipeline, regardless of which resource issued it.

```mermaid
sequenceDiagram
    participant Caller
    participant Resource
    participant Transport as Transport
    participant API as Bitbucket API

    Caller->>Resource: repo.pull_requests.list(state="OPEN")
    Resource->>Transport: request("GET", path, kind=QUERY, params)
    Transport->>API: GET .../pullrequests?state=OPEN
    API-->>Transport: 429 + Retry-After
    Transport->>Transport: wait, retry (bounded by max_attempts)
    Transport->>API: GET .../pullrequests?state=OPEN (retry)
    API-->>Transport: 200 + JSON page
    Transport->>Transport: map status to exception (2xx: none)
    Transport-->>Resource: raw JSON
    Resource->>Resource: validate into PullRequest model(s)
    Resource-->>Caller: Iterator[PullRequest]
```

Errors map through `errors.error_for_response`
(`AuthenticationError`/`ForbiddenError`/`NotFoundError`/`ConflictError`/
`ValidationError`/`RateLimitError`/`ServerError`) with `BitbucketAPIError` as
the fallback for any other non-2xx status.
