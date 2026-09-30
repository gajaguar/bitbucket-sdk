---
type: concept
title: Layering
description: How BitbucketClient, the workspace and repository clients, resources, and the transport stack on each other.
tags: [architecture]
status: stable
---

# Layering

`BitbucketClient` owns one `httpx.Client` and exposes `.user` (root-level) and
`.workspace(slug)`, which returns a `WorkspaceClient` bound to that workspace.
`WorkspaceClient.repository(slug)` returns a `RepositoryClient` bound to that
repository, exposing `.pull_requests` and `.default_reviewers`. Resource
objects never touch `httpx` directly — every request goes through
`_transport.Transport`, which owns auth, retries, and error mapping.
`models/` (pydantic) is used by every layer above transport to validate and
serialize payloads.

```mermaid
flowchart TD
    Caller["Caller code"] --> Client["BitbucketClient"]
    Client --> WSClient["WorkspaceClient"]
    WSClient --> RepoClient["RepositoryClient"]
    Client --> UserRes["UserResource"]
    WSClient --> ReposRes["RepositoriesResource"]
    RepoClient --> PRRes["PullRequestsResource"]
    PRRes --> CommentsRes["CommentsResource"]
    PRRes --> StatusesRes["StatusesResource"]
    RepoClient --> ReviewersRes["DefaultReviewersResource"]
    UserRes --> Transport["Transport (_transport.py)"]
    ReposRes --> Transport
    PRRes --> Transport
    CommentsRes --> Transport
    StatusesRes --> Transport
    ReviewersRes --> Transport
    Transport --> Retry["RetryTransport"]
    Retry --> Httpx["httpx.HTTPTransport"]
    Httpx --> API["Bitbucket Cloud API"]
    Models["models/ (pydantic)"] -.validates/serializes.-> PRRes
    Models -.validates/serializes.-> CommentsRes
```
