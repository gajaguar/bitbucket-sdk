# Technical Specification — Bitbucket Unofficial Python SDK

- **Status:** Adopted (0.2.0)
- **Date:** 2026-09-15
- **Owner:** <dev@gajaguar.com>
- **Repository:** `gajaguar/bitbucket-sdk`
- **Distribution name:** `bitbucket-unofficial-sdk`
- **Import name:** `bitbucket`

This document supersedes the informal design of `0.1.0` (`TypedDict` response
shapes over a flat `BitbucketClient`). It records the modeling pattern adopted
in `0.2.0` and the reasoning behind it, ported from the sibling
[`clockify-sdk`](https://github.com/gajaguar/clockify-sdk) project and adapted
where Bitbucket's API genuinely differs. See [`ARCHITECTURE.md`](ARCHITECTURE.md)
for how the client is layered and [`coverage.md`](coverage.md) for the
endpoint-to-method mapping.

---

## 1. Goal

Provide a typed, synchronous Python client over the Bitbucket Cloud REST API's
pull-request surface (repositories, pull requests, comments, statuses, default
reviewers) where every response is a validated model with attribute access and
real Python types — not a `dict` the caller has to trust.

### 1.1 Why this changed

`0.1.0` typed every response as a `total=False` `TypedDict`. Nothing checked
that annotation at runtime: every response-returning method on the old
`BitbucketClient` ended in `# type: ignore[return-value]`, because
`BaseRestClient.request` actually returned `dict[str, Any]`. A Bitbucket field
rename shipped silently and failed at the caller's `pull_request["title"]`,
not at the SDK boundary where it belonged. `total=False` also erased the
"absent vs. present" distinction that `| None` fields give for free, made
reserved wire names (`links["self"]`, `comment["inline"]["from"]`) awkward to
read, and left write payloads (`create_pull_request`, `create_pr_comment`) as
unvalidated `dict[str, Any]`.

### 1.2 Non-goals

- No local caching, no ORM, no persistence.
- No business logic on top of Bitbucket semantics — the SDK maps the API;
  aggregation is the caller's concern.
- No async client. Sync-only remains correct for the target use (scripts,
  jobs, CI integrations); an async client can be added later without breaking
  the sync surface.

---

## 2. Decisions

| #   | Decision                 | Choice                                                                                                 | Rationale                                                                                                                                                                                         |
| --- | ------------------------ | ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D1  | Concurrency model        | **Sync only** (`httpx.Client`)                                                                         | Unchanged from `0.1.0`; see §1.2.                                                                                                                                                                 |
| D2  | Model layer              | **Pydantic v2**, replacing `TypedDict`                                                                 | Runtime validation, attribute access, good errors, first-class mypy/pyright support. See §4.                                                                                                      |
| D3  | Wire naming              | **No `alias_generator`**                                                                               | Bitbucket's field names are already snake_case (`display_name`, `created_on`). Unlike Clockify's camelCase API, there is nothing to translate — see §4.1.                                         |
| D4  | Public shape             | **Workspace- and repository-bound sub-clients**                                                        | `client.workspace(slug).repository(slug).pull_requests…` removes the repeated `repo`/`workspace` arguments the flat `0.1.0` client required on nearly every method.                               |
| D5  | Validation strictness    | **Lenient: every field optional, `extra="allow"`**                                                     | Bitbucket's `fields=` query parameter can omit any field from any response, and Bitbucket adds fields without notice. A model that requires a field breaks on the first `fields=`-projected call. |
| D6  | Write payloads           | **Typed write models** (`PullRequestCreate`, `CommentCreate`, ...)                                     | Replaces bare `dict[str, Any]` bodies. Validated, completable, and self-documenting.                                                                                                              |
| D7  | Identifiers              | **Value Object types** (`RepositorySlug`, `WorkspaceSlug`, `PullRequestId`, ...), not bare `str`/`int` | Transposing `workspace` and `repo` — both bare strings today — is the most likely user-facing bug in a client this shape-heavy.                                                                   |
| D8  | Architecture style       | **Not DDD.** Generic resource base + Strategy + transport Decorator                                    | The domain is Bitbucket's, not ours; see §5.1.                                                                                                                                                    |
| D9  | Retries                  | Built in for `429` and `5xx`, keyed off CQS classification, not verb                                   | See §7.3.                                                                                                                                                                                         |
| D10 | Command-Query Separation | **Adopted for side effects; commands still return their result**                                       | See §5.5.                                                                                                                                                                                         |
| D11 | Pagination               | **Cursor-based** (`next` URL + `values`), not offset-based                                             | Bitbucket's collection endpoints work this way; see §7.2 and the Divergences note below.                                                                                                          |
| D12 | Python floor             | **`>=3.14`**, unchanged                                                                                | Inherited from the template.                                                                                                                                                                      |
| D13 | Build backend / tooling  | **uv + hatchling**, ruff `ALL`, mypy `strict`, pyright, pytest                                         | Unchanged from `0.1.0`.                                                                                                                                                                           |

### Divergences from the Clockify pattern

This SDK's model layer is a direct port of `clockify-sdk`'s pattern (§5), not
a rewrite from scratch. Four places are deliberately different because the two
APIs differ, not by oversight:

1. **No `to_camel` alias generator** (D3) — only reserved-word fields
   (`Links.self_`, `CommentInline.from_`) get an explicit `Field(alias=...)`.
2. **Cursor pagination, not offset pagination** (D11) — `Page[T]` carries a
   `next_cursor: str | None` rather than a `page`/`page_size` pair, and
   `list_page()` re-requests the literal `next` URL Bitbucket returns instead
   of incrementing a page number.
3. **Nested error envelope** — Bitbucket emits
   `{"type": "error", "error": {"message", "detail"}}`, not Clockify's flat
   `{"code", "message"}`; `errors._decode_body` is written for that shape.
4. **No ISO-8601 duration type** — Bitbucket has no duration-valued fields, so
   `_time.py` carries only the instant codec, not Clockify's
   `ClockifyDuration`.

---

## 3. Public API

### 3.1 Construction

```python
from bitbucket import BitbucketClient, ClientOptions

client = BitbucketClient(email="...", api_token="...")
# or: reads ATLASSIAN_USER_EMAIL / ATLASSIAN_API_KEY from the environment
client = BitbucketClient()

client = BitbucketClient(options=ClientOptions(retry=NO_RETRY))
```

### 3.2 Workspace- and repository-bound sub-clients

```python
workspace = client.workspace("my-workspace")  # or client.default_workspace()
workspace.repositories.list()  # Iterator[Repository]
workspace.pull_requests_by_author("alice")  # Iterator[PullRequest]

repository = workspace.repository("my-repo")
repository.pull_requests.list(state="OPEN")  # Iterator[PullRequest]
repository.pull_requests.get(42)  # PullRequest
repository.pull_requests.create(PullRequestCreate(...))
repository.pull_requests.approve(42)
repository.pull_requests.diff(42)  # str
repository.pull_requests.comments(42).list()  # Iterator[PullRequestComment]
repository.pull_requests.statuses(42).list()  # Iterator[PullRequestStatus]
repository.default_reviewers.list()
```

### 3.3 Method naming contract

Every resource follows the same five verbs where the underlying endpoint
supports them: `create`, `get`, `list` (lazy iterator), `list_page` (one page,
explicit `cursor`), `update`. `delete` is added only where Bitbucket actually
exposes a DELETE-by-id endpoint (comments; not pull requests — see §5.2).
Non-CRUD actions (`approve`, `diff`) are plain methods named after the
Bitbucket verb they call.

---

## 4. Models

### 4.1 Conventions

- Every model derives from a shared `BitbucketModel(BaseModel)` base with
  `populate_by_name=True`, `extra="allow"`, `frozen=True` — **no
  `alias_generator`** (D3): Bitbucket's wire names are already the Python
  attribute names.
- Every field is `T | None = None` (D5). There is no required field on any
  read model; a `fields=`-projected response or a not-yet-observed Bitbucket
  addition must never raise `ValidationError`.
- Read models (`PullRequest`) and write models (`PullRequestCreate`,
  `PullRequestUpdate`) are separate types. Write models carry no
  server-assigned fields and serialize with
  `model_dump(mode="json", by_alias=True, exclude_unset=True)`.
- Read models are frozen; the server owns the truth and local objects are
  snapshots. Mutation is expressed only by sending a write model.
- Identifier fields are Value Object types from `ids.py` (§5.3).
- Reserved Python keywords collide with two Bitbucket field names —
  `links.self` and `comment.inline.from` — both get an explicit
  `Field(alias=...)` and a trailing underscore on the Python side
  (`links.self_`, `inline.from_`).
- Enumerated Bitbucket values (`UserType`, `PullRequestState`'s sibling
  `Scm`/`ForkPolicy`/`MergeStrategy`/`Markup`/`ParticipantRole`/
  `ParticipantState`) are `StrEnum` with an `UNKNOWN` fallback member via
  `_missing_` — Bitbucket adds enum values without notice.

### 4.2 Time handling

| Wire                          | Python                     |
| ----------------------------- | -------------------------- |
| `"2024-01-01T10:00:00+00:00"` | `datetime` (tz-aware, UTC) |

One reusable annotated type, `BitbucketInstant` (`bitbucket._time`), carries
the validator/serializer pair, normalizing naive or offset datetimes to UTC.
Bitbucket has no duration-valued fields, so there is no `BitbucketDuration`
counterpart to Clockify's `ClockifyDuration`.

---

## 5. Design patterns

### 5.1 Why not Domain-Driven Design

Unchanged from the Clockify rationale, restated for Bitbucket: the domain is
Bitbucket's, not ours. Bitbucket's server is the sole authority on every
invariant that matters (merge conflicts, branch protection, review
requirements); any invariant encoded locally is a guess that drifts silently.
There is no domain logic to model — the risk here is surface area and
transport correctness, not business rules.

`repository.pull_requests` resembles a Repository pattern; it is not one — see
the Clockify TECH_SPEC §5.1 for why collection semantics (identity map, unit
of work) are wrong over HTTP. It is the Resource pattern; the shared name is
coincidence.

### 5.2 Patterns adopted

| Pattern                       | Applied to                                | Why                                                                                |
| ----------------------------- | ----------------------------------------- | ---------------------------------------------------------------------------------- |
| Generic resource base         | `resources/base.py`'s `NestedResource`    | Writes the CRUD shape once for pull requests and comments instead of twice         |
| Strategy                      | `RetryPolicy`, `BasicAuth`                | A future OAuth/`X-Addon-Token` scheme is a new strategy, not a rewritten transport |
| Decorator (transport wrapper) | retry/backoff as an `httpx.BaseTransport` | Composes, tests standalone, keeps `Transport.request()` linear                     |
| Facade                        | `BitbucketClient`                         | One entry point over httpx, auth, retries, pagination                              |
| Iterator                      | `list()` → `Iterator[T]`                  | Lazy pagination without materializing whole workspaces                             |
| Value Object                  | `ids.py` types, `BitbucketInstant`        | Prevents `workspace`/`repo` transposition; see §5.3                                |
| Parameter Object              | `ClientOptions`, `ErrorBody`              | Collapses a long keyword list into one typed object                                |

**Guard against over-abstraction.** `NestedResource` covers only the two
resources whose shape is genuinely uniform: pull requests (no `delete` — see
below) and comments (full CRUD). These are hand-written instead, because
contorting them into the generic shape would misrepresent what Bitbucket
actually exposes:

- `RepositoriesResource` — read-only, workspace-scoped, no create/update/delete
- `StatusesResource` — read-only, nested under a pull request
- `DefaultReviewersResource` — read-only, no `{id}` item path at all
- `UserResource` — root-level `/user`, not workspace- or repo-scoped
- `PullRequestsResource.approve` / `.diff` — non-CRUD verbs on the item path

**Pull requests have no `delete`.** Bitbucket has no DELETE-by-id endpoint for
pull requests — they are merged, declined, or superseded, never removed — but
comments do support DELETE. Rather than inherit a `delete` method that would
always 404, `delete` lives on a separate `DeletableResourceMixin` that only
`CommentsResource` composes in. `NestedResource` itself defines `create`,
`get`, `list`, `list_page`, `update`.

### 5.3 Value Objects for identifiers

`WorkspaceSlug`, `RepositorySlug`, `PullRequestId`, `CommentId`, `AccountId`,
`Uuid`, `CommitHash` are distinct `NewType`s, not bare `str`/`int`. With
workspace- and repository-bound sub-clients (D4), `workspace` and `repo` are
no longer threaded through every method signature as they were in `0.1.0`'s
flat client — but they are still both bare strings at the call site
(`client.workspace("ws").repository("repo")`), and transposing them is exactly
the class of bug typed IDs exist to catch statically.

Read models are frozen; mutation is expressed only by sending a write model to
the server (§4.1).

### 5.4 Patterns explicitly rejected

| Pattern                                | Verdict                                                                                                                      |
| -------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Domain-Driven Design (as architecture) | See §5.1                                                                                                                     |
| Repository, Unit of Work, identity map | Wrong over HTTP; collection semantics the transport cannot honor                                                             |
| Circuit breaker                        | Right pattern, wrong scale. A `RateLimitError`/`ServerError` after bounded retries is more debuggable for a script/CI client |
| `Result`/`Either` return types         | Non-idiomatic in Python, fights mypy ergonomics; §7.4 already specifies a typed exception hierarchy                          |
| Plugin/registry for resources          | Nothing needs runtime discovery; static attributes are more discoverable and typecheck                                       |

### 5.5 Command-Query Separation

Unchanged in substance from Clockify's §5.5. Every method is classified as a
**query** (`get`, `list`, `list_page`, `diff`) or a **command**
(`create`, `update`, `delete`, `approve`), and that classification — not the
HTTP verb — decides `5xx` retry eligibility (§7.3). `approve` is a `POST` but
classified `IDEMPOTENT_COMMAND`: approving an already-approved pull request is
a no-op on Bitbucket's side, so retrying it after a `5xx` is safe.

Commands return their result (`create`/`update`/`approve` return the server's
representation; `delete` returns `None`), for the same reason Clockify gives:
discarding the created resource would force a second, unreliable request to
find what was just created.

---

## 6. Package layout

```text
src/bitbucket/
    __init__.py            # public re-exports
    _version.py
    client.py               # BitbucketClient — facade: .user, .workspace(slug)
    workspace.py             # WorkspaceClient — .repositories, .repository(slug)
    repository.py            # RepositoryClient — .pull_requests, .default_reviewers
    config.py                # ClientOptions, ClientConfig, env resolution
    errors.py                # exception hierarchy
    ids.py                   # WorkspaceSlug, RepositorySlug, PullRequestId, ...
    retry.py                 # CqsKind, RetryPolicy, NO_RETRY
    _auth.py                 # BasicAuth strategy
    _transport.py            # httpx wiring, logging
    _retry_transport.py      # httpx.BaseTransport decorator applying RetryPolicy
    _pagination.py           # Page[T], paginate() — cursor-based
    _time.py                 # BitbucketInstant codec
    models/
        __init__.py  base.py  link.py  account.py  project.py  branch.py
        repository.py  commit.py  pull_request.py  comment.py  status.py
    resources/
        __init__.py  base.py  repositories.py  pull_requests.py  comments.py
        statuses.py  default_reviewers.py  user.py
tests/
    unit/                   # respx-backed, offline, deterministic
    live/                   # marker-gated, real workspace
    conftest.py
docs/
    TECH_SPEC.md  ARCHITECTURE.md  coverage.md
```

Everything prefixed with `_` is private and may change without a major version
bump. `resources/` is private in practice — instances are reached only through
`BitbucketClient`/`WorkspaceClient`/`RepositoryClient` attributes.

---

## 7. Transport

### 7.1 Authentication

HTTP Basic auth (email + API token) applied by `BasicAuth`
(`_auth.py`, wrapping `httpx.BasicAuth`) — an auth strategy object rather than
a call hardcoded in the transport, so a future OAuth bearer scheme is a new
strategy, not a `_transport.py` change.

### 7.2 Pagination

Bitbucket collection endpoints return a `next` URL alongside `values` and,
on the first page, `size`. `Page[T]` (`_pagination.py`) carries
`items`, `next_cursor`, and `size`; `paginate()` wraps repeated
`list_page(cursor=...)` calls into a lazy `Iterator[T]`, re-requesting the
literal `next` URL (not a derived page number) until it is absent.

- `list()` returns the lazy iterator; `list_page()` exposes one page for
  callers managing their own cursor.
- Iteration is lazy: no request is issued until the iterator is advanced.

### 7.3 Retries and rate limits

Policy is carried by a `RetryPolicy` strategy object (§5.2), applied by an
`httpx.BaseTransport` decorator in `_retry_transport.py`:

- Retry on `429` and on `500`, `502`, `503`, `504`.
- Honor `Retry-After` when present; otherwise exponential backoff with full
  jitter, base 0.5 s.
- `max_attempts` default **3**; `NO_RETRY` disables retries entirely.
- After exhausting retries, the caller sees the final `RateLimitError` or
  `ServerError`.

**Retry eligibility is keyed off the CQS classification (§5.5), not the HTTP
verb:**

| Call kind                                          | Retry on `429` | Retry on `5xx` |
| -------------------------------------------------- | -------------- | -------------- |
| Query (`get`, `list`, `list_page`, `diff`)         | yes            | yes            |
| Idempotent command (`update`, `delete`, `approve`) | yes            | yes            |
| Non-idempotent command (`create`)                  | yes            | **no**         |

`429` is always retryable because the request provably did not execute; `5xx`
is withheld only where a retry could duplicate a write (`create_pull_request`,
`create_pr_comment`).

### 7.4 Errors

```text
BitbucketError                      # base; carries request + response context
├── ConfigurationError
│   └── MissingCredentialsError
├── BitbucketAPIError               # any non-2xx; .status_code, .code, .raw
│   ├── AuthenticationError         # 401
│   ├── ForbiddenError              # 403
│   ├── NotFoundError               # 404
│   ├── ValidationError             # 400, 422 (also raised on a malformed instant)
│   ├── ConflictError               # 409
│   ├── RateLimitError              # 429; .retry_after
│   └── ServerError                 # 5xx
└── TransportError                  # connect/read failures, invalid JSON
```

Bitbucket's error body — `{"type": "error", "error": {"message", "detail"}}`
— is parsed when present and preserved verbatim in `.raw` when it is not
(Divergences §3). `message`/`detail`/`code`/`raw` travel into the exception
constructors as one `ErrorBody` (a Parameter Object) but remain flat
attributes on the raised exception.

### 7.5 Logging

- Logger name `bitbucket`, `NullHandler` attached at import.
- `DEBUG`: method, path, status, elapsed ms — primitives only.
- The Basic-auth credentials are **never** logged.

---

## 8. Testing

| Layer      | Tooling            | Runs                              |
| ---------- | ------------------ | --------------------------------- |
| Unit       | `pytest` + `respx` | Always. Offline, deterministic.   |
| Live smoke | `pytest -m live`   | Manual, against a real workspace. |

- Every resource method has a unit test asserting the exact HTTP method,
  path, query parameters, and request body it produces.
- Pagination, retry/backoff, and error mapping each have dedicated unit tests
  independent of any resource (`test_pagination.py`, `test_retry_transport.py`,
  `test_errors.py`).
- Model tests cover reserved-word aliasing, `extra="allow"`, `frozen=True`,
  the `_missing_` enum fallback, and `exclude_unset` write serialization
  (`test_models.py`).
- Coverage gate: **90%** on `src/bitbucket`, enforced by `make test`.

---

## 9. Documentation deliverables

| File                      | Content                                                                                      |
| ------------------------- | -------------------------------------------------------------------------------------------- |
| `README.md`               | Install, auth, quickstart recipes, link to the coverage matrix                               |
| `docs/ARCHITECTURE.md`    | Layering, request lifecycle, pagination, how to add an endpoint                              |
| `docs/coverage.md`        | Table: Bitbucket documented endpoint → SDK method → status                                   |
| `# METHOD /path` comments | Docstrings are banned (`app-no-docstrings`); every resource method names its endpoint inline |

---

## 10. Risks and accepted trade-offs

| #   | Risk                                               | Impact                                                                | Position                                                                                                                       |
| --- | -------------------------------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| R1  | Breaking change from `0.1.0`                       | Every caller of the flat `BitbucketClient` must migrate.              | Accepted: the package is `0.x` alpha; a breaking `0.2.0` is cheaper now than carrying a dead TypedDict API forward.            |
| R2  | No CI                                              | Nothing enforces `make check` on a PR.                                | Accepted for now, same as `0.1.0`; release checklist in `ARCHITECTURE.md` requires `make check && make test` before tagging.   |
| R3  | Hand-written endpoints drift from Bitbucket's docs | Silent breakage when Bitbucket changes a payload.                     | `extra="allow"` + all-optional fields (D5) absorb additions and removals without raising; live smoke detects real regressions. |
| R4  | `requires-python = ">=3.14"`                       | Excludes nearly every current installation.                           | Accepted by owner, unchanged from `0.1.0`.                                                                                     |
| R5  | Generic resource base over-abstracts               | Endpoints with no CRUD analogue get contorted into the generic shape. | Guarded explicitly in §5.2; four resources are hand-written by rule, not by oversight.                                         |

---

## 11. Open items

1. Repository create/update/delete, branch restrictions, and webhooks are not
   yet modeled — the SDK covers pull requests, comments, statuses, default
   reviewers, and repository listing only. Extend `docs/coverage.md` as these
   are added.
2. `RepositoryClient.default_reviewers` is read-only; adding/removing a
   default reviewer (`PUT`/`DELETE .../default-reviewers/{account_id}`) is
   deferred.
