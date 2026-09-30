---
type: decision
title: Async client
description: Why the SDK now ships an `AsyncBitbucketClient` mirror under `bitbucket.aio`, what is shared with the sync client, and the rule that every new endpoint ships in both.
tags: [architecture]
status: stable
---

# Async client

Issue #10 asked whether to add an async transport or stay sync-only. This
note records the decision to ship both, the seam between them, and the rule
that keeps them in lock-step going forward.

## Decision

`AsyncBitbucketClient` is a hand-written mirror of `BitbucketClient` under
`bitbucket.aio`. The two clients share the credential contract, the
endpoint surface, and every piece that has no I/O; only the I/O layer is
duplicated. `0.5.0` ships the mirror; future endpoints ship in both.

## What is shared

These modules have no I/O and are reused unchanged by both clients:

- `bitbucket.models.*` — frozen pydantic models for read and write
  payloads.
- `bitbucket.errors` — `MissingCredentialsError`, `ConfigurationError`,
  the HTTP-status-mapped error classes (`AuthenticationError`,
  `ForbiddenError`, `NotFoundError`, `ServerError`, `TransportError`,
  etc.).
- `bitbucket.retry` — `RetryPolicy`, `should_retry`, `compute_delay`, and
  `CqsKind`. The retry transport is the only consumer; the rule lives
  here, the implementation is per-client.
- `bitbucket.config` — `ClientConfig`, `ClientOptions`,
  `resolve_credentials`, `resolve_workspace`, the `ApiTokenProvider` and
  `AccessTokenProvider` callables. `BitbucketClient.__init__` and
  `AsyncBitbucketClient.__init__` both call the shared `_build_config` helper.
- `bitbucket._auth.BasicAuth` and `bitbucket._auth.BearerAuth` — their
  `auth_flow` generators drive `httpx.Auth.async_auth_flow` for the async
  transport unchanged, so both auth schemes and their per-request providers
  behave identically in both clients.
- `bitbucket.resources.base.page_from_payload` — the async pagination
  helper reuses it.

## What is mirrored

The I/O layer is duplicated under `bitbucket.aio`:

- `aio/_transport.AsyncTransport` mirrors `_transport.Transport`,
  delegating to a shared set of pure helpers (`_resolved_params`,
  `_log`, `_decode_json`, and the 204 → `None` / non-success →
  `error_for_response` status-handling). The same pure helpers back
  `Transport.request` on the sync side.
- `aio/_retry_transport.AsyncRetryTransport` mirrors
  `_retry_transport.RetryTransport`, swapping the sync `sleep` for an
  `asyncio`-aware one and `response.read()` for `await
  response.aread()`. `_parse_retry_after` is module-level in both files.
- `_pagination.apaginate` mirrors `_pagination.paginate`, returning an
  `AsyncIterator` that follows `next` cursors via an `await`-able fetch.
- `_polling.apoll_until_terminal` mirrors `_polling.poll_until_terminal`,
  with an `asyncio.sleep` default and an `Awaitable` sleep callback.
- `aio/resources/*.py` mirrors `resources/*.py` one-for-one, with the
  same class name plus an `Async` prefix, the same `# METHOD /path`
  comments, the same `CqsKind`s, and the same sub-resource factories
  (`comments()`, `tasks()`, ...) — those remain synchronous, returning
  the async resource.

## The rule

Every endpoint that ships in the sync client ships in the async client
too. The
[`adding an endpoint` playbook](adding-an-endpoint.md) makes the rule
explicit: when a method lands under `bitbucket/resources/`, mirror it
under `bitbucket/aio/resources/` (same name, `Async` prefix) and add a
matching test in `tests/unit/aio/`. The cross-cutting-work list in the
[roadmap](../api/roadmap.md) carries the same step.

## Credential contract

The credential contract from [`docs/sdk/credential-contract.md`](../sdk/credential-contract.md)
applies to both clients. The
[`docs/sdk/credential-tests.md`](../sdk/credential-tests.md) tests are
split: the "Sending" and "Hiding" groups run for both `BitbucketClient`
and `AsyncBitbucketClient` because the same `_build_config` resolves the
credentials in both, and the same `BasicAuth` or `BearerAuth` attaches the
`Authorization` header.
