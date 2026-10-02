---
type: playbook
title: Roadmap to full API coverage
description: The phased plan from the current endpoint coverage to full Bitbucket Cloud API parity.
tags: [api, release]
status: stable
---

# Roadmap to full API coverage

This SDK targets **Bitbucket Cloud REST API `2.0`**, checked against
`https://dac-static.atlassian.com/cloud/bitbucket/swagger.v3.json`,
`x-revision: 6856b45887d7` (2026-10-01). Regenerate the numbers below against
a newer revision whenever [endpoint coverage](endpoint-coverage.md) is re-verified.

**Where we are today:** `1.0.0` is released with 291 / 294 operations
(99%), every callable one in the checked spec revision — see the coverage summary
table in [endpoint coverage](endpoint-coverage.md) for the full breakdown by resource
group. This document lays out the path from there to full parity, in phases
tied to version milestones, plus two cross-cutting phases (0a and 0b) that
don't move the coverage number. Phase 0b unblocks consumers — such as an MCP
server — that need to act on behalf of other Bitbucket users with a bearer
token rather than a single operator credential.

## Non-goals

Per the original technical specification (§1.2, not published), none of the
phases below change these:

- No local caching, no ORM, no persistence.
- No business logic layered on top of Bitbucket semantics — the SDK maps the
  API; aggregation is the caller's concern.

## Cross-cutting work every phase inherits

Per the [adding an endpoint](../architecture/adding-an-endpoint.md) checklist,
every operation added in any phase needs:

1. Read/write pydantic models in `src/bitbucket/models/` (write models
   separate from read models, e.g. `PullRequestCreate` vs. `PullRequest`).
2. A method on the relevant resource in `src/bitbucket/resources/`, reusing
   `resources.base.NestedResource` (+ `DeletableResourceMixin` where a
   DELETE-by-id exists) whenever the endpoint fits the
   `{base_path}{_path}[/{id}]` shape, and `resources.base.page_from_payload`
   for anything paginated but irregular.
3. A `# METHOD /path` comment above the method (this repo has no
   docstring-based reference; see `gajaguar-no-docstrings`).
4. A declared `CqsKind` (query / idempotent command / non-idempotent command).
5. A `endpoint-coverage.md` row moved from `planned` to `done`.
6. An async mirror of the method in `src/bitbucket/aio/resources/` (same
   name with an `Async` prefix; auto-paginating methods return
   `AsyncIterator` via `apaginate`) and a matching test in
   `tests/unit/aio/`. The async mirror is in lock-step with the sync
   resource tree — see [async-client](../architecture/async-client.md) for
   the rule and the [layering](../architecture/layering.md) note for the
   shape.

## Phase 0a — async client (`0.5.0`)

Cross-cutting infrastructure, not an endpoint group — this phase adds no
`endpoint-coverage.md` rows and does not move the coverage percentage. It
adds a second transport flavour, `AsyncBitbucketClient` (an
`httpx.AsyncClient`-based mirror of `BitbucketClient`), so consumers can
embed the SDK in an asyncio application without spinning a thread per
request.

In scope:

- A new `bitbucket.aio` subpackage: `AsyncBitbucketClient`,
  `AsyncWorkspaceClient`, `AsyncRepositoryClient`, and one async resource
  per sync resource under `bitbucket/aio/resources/`. Single-shot methods
  are `async def`; auto-paginating methods return `AsyncIterator`.
- Reused as-is: `models/`, `errors.py`, `retry.py`, `config.py`,
  `_auth.BasicAuth` (its `auth_flow` already drives
  `httpx.Auth.async_auth_flow`, so the credential contract applies
  unchanged to the async client), and `resources.base.page_from_payload`.
- New I/O-layer modules: `aio/_transport.AsyncTransport`,
  `aio/_retry_transport.AsyncRetryTransport`,
  `_pagination.apaginate`, and `_polling.apoll_until_terminal`.
- Tests in `tests/unit/aio/` mirroring the sync suites — including the
  credential tests from [`docs/sdk/credential-tests.md`][sdk-credential-tests]
  for both clients.

Out of scope:

- New endpoint coverage — the async mirror maps the surface that already
  exists; it does not add new endpoints.
- A second credential contract. The async client honours the same rules
  (`ATLASSIAN_USER_EMAIL` + `ATLASSIAN_API_TOKEN`, the `ApiTokenProvider`
  callable, the no-credentials-in-logs guarantee).

The full rationale, including the rule that every new endpoint ships in
both clients, is in
[`docs/architecture/async-client.md`](../architecture/async-client.md).

## Phase 1 — complete the pull-request surface — shipped in `0.4.0`

The surface the SDK already claims to cover. Closed every remaining `planned`
row under Pull requests / Pull request comments / Pull request statuses /
Default reviewers in `endpoint-coverage.md` (28 operations, including the `Commit
statuses` spillover called out below — 24 in the `Pullrequests` tag group
plus 4 in the separate `Commit statuses` tag group):

- PR lifecycle: `DELETE .../approve`, `POST .../merge`,
  `GET .../merge/task-status/{task_id}`, `POST .../decline`,
  `POST`/`DELETE .../request-changes`.
- PR content: `commits`, `conflicts`, `diffstat`, `patch`,
  `GET .../commit/{commit}/pullrequests`.
- Activity: `GET .../pullrequests/activity`,
  `GET .../pullrequests/{pull_request_id}/activity`.
- Tasks: full CRUD on `.../tasks` and `.../tasks/{task_id}`.
- Comment resolution: `POST`/`DELETE .../comments/{comment_id}/resolve`.
- PR properties: `GET`/`PUT`/`DELETE .../properties/{app_key}/{property_name}`.
- Default reviewers: `GET`/`PUT`/`DELETE .../default-reviewers/{target_username}`,
  `GET .../effective-default-reviewers`.
- Commit statuses: `GET .../commit/{commit}/statuses`,
  `POST .../commit/{commit}/statuses/build`,
  `GET`/`PUT .../commit/{commit}/statuses/build/{key}` — pulled forward from
  Phase 2's spillover note below, since the PR-content work here already
  needed `CommitStatusCreate`/`CommitStatusUpdate` models.

**Architecture note:** `POST .../merge` returns `202 Accepted` with a
task-status URL to poll, not the merged PR directly — this needs a small
async-task-polling helper (poll `GET .../merge/task-status/{task_id}` until
terminal), the first pattern of its kind in the SDK.

## Phase 2 — repository core — shipped in `0.4.0` (52 of 55 operations)

25 `Repositories` operations, plus the directly-related content endpoints
(`Commit statuses` below was already `done`, see Phase 1):

- Repository CRUD: `POST`/`PUT`/`DELETE /repositories/{workspace}/{repo_slug}`
  (create takes the slug in the path — see the note in
  `endpoint-coverage.md`), forks, hooks, watchers, permissions-config
  (groups/users), override-settings. All 23 operations shipped.
- `Refs` (9): branches and tags — create/get/list/delete (no `update`;
  Bitbucket has no PUT-by-name endpoint for either). All 9 shipped.
- `Source` (4): `GET`/`POST .../src`, `GET .../src/{commit}/{path}`
  (exposed as two SDK methods — `list_path`/`read` — since the endpoint is
  polymorphic between a directory listing and raw file content),
  `GET .../filehistory/{commit}/{path}`. All 4 shipped.
- `Commits` (17, all shipped): commit list/get, commit comments, commit
  approve, diff, diffstat, patch and merge-base shipped here; the last 3
  (`file-conflicts` and the two `POST` listings) shipped in Phase 3 once the
  live spec confirmed them (see `endpoint-coverage.md`'s note on this group).
- `Commit statuses` (4) — delivered as part of Phase 1's spillover; no
  remaining work here beyond `endpoint-coverage.md` bookkeeping.
- `Downloads` (4): repository downloads CRUD. All 4 shipped.

**Architecture note:** `POST .../src` is a multipart file upload, and
`diff`/`patch`/`filehistory` return plain text, not JSON — `Transport` grew
`request_multipart` and `request_bytes` seams alongside the existing
`request_text` to cover both.

**Follow-up (resolved):** the live spec confirms the 3 remaining `Commits`
operations — `GET .../file-conflicts/{spec}`, `POST .../commits` and
`POST .../commits/{revision}` — and they ship in Phase 3 (`0.8.0`).

## Phase 0b — bearer token auth (`0.6.0`) — shipped

Cross-cutting infrastructure, not an endpoint group — this shipped phase adds no
`endpoint-coverage.md` rows and does not move the coverage percentage. It
lets a consumer authenticate with a bearer token instead of the operator's
email and API token. Bitbucket Cloud accepts `Authorization: Bearer` for
repository, project and workspace access tokens, and for an OAuth 2.0 access
token; the SDK does not care which one it receives.

The SDK's side of the split is to *use* a bearer token, not to *obtain* or
renew it — see
[why the SDK does not acquire credentials](../sdk/credential-sources.md). A
consumer that acts for other Bitbucket users, such as an MCP server, builds
one client per user, or passes a provider that looks the token up for that
user.

In scope:

- `BearerAuth` (`src/bitbucket/_auth.py`): an `httpx.Auth` sibling to the
  existing `BasicAuth`, attaching `Authorization: Bearer <token>`. The
  seam is already named in `_auth.py`'s own comment.
- A bearer-token provider, `AccessTokenProvider`, with the same rules as
  `ApiTokenProvider` (`src/bitbucket/config.py`): called on every request,
  never cached, an empty value raises `MissingCredentialsError`. Renewing an
  expiring token is the provider's job; the SDK has no refresh callback.
- `ClientConfig`/`resolve_credentials` (`src/bitbucket/config.py`) are widened
  so a bearer token is an alternative to the email/API-token pair, without
  making either required unconditionally.
- The no-credentials-in-logs guarantee in `_transport.py`'s logging comment
  covers both the `Authorization: Basic` and `Authorization: Bearer` headers.
- Async parity: the same classes and tests apply to `AsyncBitbucketClient`,
  per the lock-step rule in
  [async-client](../architecture/async-client.md).

Out of scope, and left to the application that calls the SDK (a
command-line tool, an MCP server, a web app's OAuth callback handler, ...):

- The OAuth authorization-code flow — building the `/authorize` URL,
  hosting the redirect/callback, exchanging the code at the token URL,
  holding `client_id`/`client_secret`.
- Refreshing an expired access token. It needs the `refresh_token` and the
  client secret, so it belongs inside the provider the application passes.
- Per-user token storage and lookup, including any keyring or file store.
- Scope selection and consent-screen concerns.

The interactive login is a job for a separate command-line tool, structured
the way `clockify-cli` is: credential stores, a resolver, and a factory that
hands the SDK a token or a provider. Such a tool is not part of this
roadmap.

The decisions for this phase (how the configuration models the two
credential kinds, which one wins when both are supplied, the new environment
variable) were settled before the code landed, following the
[credential contract](../sdk/credential-contract.md).

## Phase 3 — governance (`0.7.0` and `0.8.0`)

Also closed Phase 2's 3 `Commits` rows (see that phase's follow-up note),
whose shape the live spec confirmed.

Workspace- and project-level administration surface:

- `Webhooks` (2) — **shipped in `0.7.0`**: the hook-event catalogue
  (`GET /hook_events`, `GET /hook_events/{subject_type}`). Repository-level
  hooks shipped in `0.4.0`.
- `Branch restrictions` (5), `Branching model` (7) — **shipped in `0.7.0`**.
  The 3 project-level branching-model operations introduced `ProjectClient`
  (`ws.project(key)`), which the rest of `Projects` extends.
- `Projects` (16) — **shipped in `0.8.0`**: project CRUD,
  default reviewers and permissions-config, plus the project listing that the
  spec first-tags `Workspaces`.
- `Workspaces` (16) — **shipped in `0.8.0`**: members,
  permissions, hooks, GPG public key, plus the caller's own workspaces and
  permissions under `/user`. The 5 workspace hook operations
  (`/workspaces/{workspace}/hooks[/{uid}]`) shipped in `0.7.0`, pulled forward
  with `Webhooks` because they reuse `HooksResource` as-is.
- `Users` (4), `SSH` (5), `GPG` (4) — **shipped in `0.9.0`**: the caller's
  profile and emails under `/user`, and a `client.users(selected_user)` handle
  for the profile, SSH keys and GPG keys of any user.
- `Search` (3) — **shipped in `0.9.0`**: code search under workspaces, users
  and a new `client.teams(username)` handle, through one `SearchResource`; the
  result's file reuses `TreeEntry`. The spec deprecates all three operations
  on 2026-11-01.
- Two operations the spec added since the first check:
  `GET .../pullrequests/{pull_request_id}/mergeability/checks` (a
  `Pullrequests` read, **shipped in `0.9.0`**) and
  `GET /user/workspaces/{workspace}/permissions/repositories` (counted under
  `Repositories`, shipped with `Workspaces`).

No new architectural seams — verified against `x-revision` `6856b45887d7`:
every remaining operation fits `NestedResource` or a hand-written method
following the existing pattern. The one non-JSON response,
`GET /workspaces/{workspace}/settings/gpg/public-key`, is plain text and uses
the existing `Transport.request_text`.

The one exception is the two `POST .../commits` listings: they send
`include`/`exclude` as a form body, so `Transport` and `AsyncTransport` grew a
`request_form` seam beside `request_multipart`.

The table was re-verified against that revision: the total is still 294, and
the per-first-tag counts are `Repositories` 24 and `Pullrequests` 38.
Re-verifying also found the repository override-settings path wrong in the
SDK; the fix is noted in [endpoint coverage](endpoint-coverage.md).

## Phase 4 — CI/CD (`4a` and `4b`)

Phase 4 is split in two, counting each operation under its first tag. The four
`.../deployments_config/environments/{environment_uuid}/variables` operations
are first-tagged `Pipelines`, so they count in 4a although they are about
deployment environments.

### 4a — `Pipelines` (68) — shipped in `0.9.0`

Pipelines trigger, list, get and stop; steps, step and container logs, test
reports; pipelines-config (settings, build number, schedules, SSH key pair,
known hosts, caches, runners, variables for the repository, workspace, team
and user scopes); the two OIDC operations; and the four environment variables,
reached through `repo.environments.variables(environment_uuid)`. Coverage goes
from 162 to 230 (78%).

**Architecture note:** one new seam. Step logs are bytes, can be large, accept
a `Range` header and answer `307` to long-term storage when a step finishes,
so `request_bytes` now takes per-request `headers` and `follow_redirects`.
Test reports, test cases, test-case reasons and the OIDC operations declare no
response schema and return the JSON as is. Everything else fits
`NestedResource` (one `PipelineVariablesResource` for four scopes, one
`RunnersResource` for two) or a hand-written method. Secrets (variable values,
the SSH private key, a runner's OAuth secret) are `SecretStr`.

### 4b — `Deployments` (16) and `Reports` (9) — shipped in `0.9.0`

- `Deployments` (16): deploy keys, deployments, environments. 4b extends the
  `EnvironmentsResource` that 4a introduced for the environment variables.
- `Reports` (9): code-insight reports and annotations on commits.

Coverage goes from 230 to 255 (87%).

**Architecture note:** no new seam. Environments extend the 4a resource (the
`changes` call answers `202` with no content, so `update` returns `None`).
Deploy keys use `NestedResource` for repositories and a small hand-written
resource for projects, which have no `PUT`. Reports and annotations are keyed
by an id the caller picks, so `put` is an `IDEMPOTENT_COMMAND`, and the bulk
annotation upload posts a JSON array. None of the 25 operations carries a
secret, and none declares a `429`. Several bodies are undeclared in the spec
(deploy keys, environment `changes`); the models carry the fields the spec's
examples show and accept extras. See [endpoint coverage](endpoint-coverage.md).

## Phase 5 — remainder (shipped in `1.0.0`)

- `Snippets` (24): full snippet CRUD, comments, commits, watch, files. Done.
- `properties` (12): app-key/property-name CRUD on commits, repos, PRs, users
  (Connect-app storage). Done: the 3 pull-request operations shipped in Phase
  1 and the other 9 reuse the same `PropertiesResource`. All 12 are deprecated
  in the spec (Connect end of support, 2027-01-31).
- `Addon` (3): Connect-app lifecycle (`PUT`/`DELETE /addon`,
  `GET /addon/{addon_key}/client-key}`). Not implemented: the first two accept
  only JWT and the third only a Forge app, and the SDK sends only Basic or
  Bearer. They stay in the 294 as `unsupported`, so the SDK calls 291 of 294.

At the end of Phase 5 the SDK covers all 294 operations in the checked spec
revision. `Issue tracker` and `Wiki` (declared as spec tags but carrying no
operations in this revision) are out of scope until Atlassian publishes them
in the machine-readable spec — see the footnote in `endpoint-coverage.md`.

## Milestone summary

| Phase | Version  | Adds                            | Cumulative coverage |
| ----- | -------- | ------------------------------- | ------------------- |
| —     | 0.1.0    | (shipped)                       | 17 (6%)             |
| 1, 2  | 0.4.0    | +80 (shipped, 3 planned)        | 97 (33%)            |
| 0a    | 0.5.0    | +0 (async client)               | 97 (33%)            |
| 0b    | 0.6.0    | +0 (bearer token auth, shipped) | 97 (33%)            |
| 3a    | 0.7.0    | +19 (shipped)                   | 116 (39%)           |
| 3b    | 0.8.0    | +27 (shipped)                   | 143 (49%)           |
| 3c    | 0.9.0    | +19 (shipped)                   | 162 (55%)           |
| 4a    | 0.9.0    | +68 (shipped)                   | 230 (78%)           |
| 4b    | 0.9.0    | +25 (shipped)                   | 255 (87%)           |
| 5     | 1.0.0    | +39 (shipped, 3 unsupported)    | 294 (100%)          |

Phase 3 is split across two releases. `0.7.0` carries the 19 operations
already done (the webhook groups, `Branch restrictions` and `Branching model`);
`0.8.0` adds 27 more, and `0.9.0` closes the phase together with Phase 4.
Each bump follows the [release checklist](../release/release-checklist.md).

Phases 1 and 2 were planned as `0.2.0` and `0.3.0` but never tagged; they
shipped together in `0.4.0` with the credential contract. `0.4.1` changed
tooling and distribution only. Phases 3 and 4 added features without breaking
the API, so each bumped the minor version. `1.0.0` freezes the public names
after a review of the surface (see
[public API conventions](../architecture/public-api-conventions.md)); its one
breaking change is that the properties `put` returns `None`.

Phases 0a and 0b are listed first because they unblock their respective
consumers (async callers in Phase 0a; delegated-access consumers in Phase 0b)
independently of endpoint coverage, not because later phases depend on
either — Phases 3–5 proceed the same whether or not they have landed.
