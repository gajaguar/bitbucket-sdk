# Roadmap to full API coverage

This SDK targets **Bitbucket Cloud REST API `2.0`**, checked against
`https://dac-static.atlassian.com/cloud/bitbucket/swagger.v3.json`,
`x-revision: 167b2dc51ec8` (2026-09-16). Regenerate the numbers below against
a newer revision whenever [`coverage.md`](coverage.md) is re-verified.

**Where we are today:** 97 / 294 operations (33%) — see the coverage summary
table in [`coverage.md`](coverage.md) for the full breakdown by resource
group. This document lays out the path from there to full parity, in phases
tied to version milestones, plus one auth-capability phase (Phase 0) that
doesn't move the coverage number but unblocks consumers — such as an MCP
server — that need to act on behalf of other Bitbucket users via OAuth 2.0
rather than a single operator credential.

## Non-goals (carried from the tech spec)

Per [`TECH_SPEC.local.md`](TECH_SPEC.local.md) §1.2, none of the phases below
change these:

- No local caching, no ORM, no persistence.
- No business logic layered on top of Bitbucket semantics — the SDK maps the
  API; aggregation is the caller's concern.
- No async client. Sync-only (`httpx.Client`) remains correct for the target
  use (scripts, jobs, CI integrations).

## Cross-cutting work every phase inherits

Per [`ARCHITECTURE.md`](ARCHITECTURE.md)'s "Adding a new endpoint" checklist,
every operation added in any phase needs:

1. Read/write pydantic models in `src/bitbucket/models/` (write models
   separate from read models, e.g. `PullRequestCreate` vs. `PullRequest`).
2. A method on the relevant resource in `src/bitbucket/resources/`, reusing
   `resources.base.NestedResource` (+ `DeletableResourceMixin` where a
   DELETE-by-id exists) whenever the endpoint fits the
   `{base_path}{_path}[/{id}]` shape, and `resources.base.page_from_payload`
   for anything paginated but irregular.
3. A `# METHOD /path` comment above the method (this repo has no
   docstring-based reference; see `app-no-docstrings`).
4. A declared `CqsKind` (query / idempotent command / non-idempotent command).
5. A `coverage.md` row moved from `planned` to `done`.

## Phase 0 — OAuth 2.0 bearer auth (`0.1.1`)

Cross-cutting infrastructure, not an endpoint group — this phase adds no
`coverage.md` rows and does not move the coverage percentage. It exists to
unblock any consumer that must act on behalf of *another* Bitbucket user
rather than its own operator credential — concretely, an MCP server
exposing Bitbucket tools to per-user connections. Scoped strictly to the
SDK's side of that split (see the "OAuth Auth Playbook" artifact's §06,
"Where the SDK's job ends"): the SDK becomes able to *use* a bearer token,
not to *obtain* one.

In scope:

- `BearerAuth` (`src/bitbucket/_auth.py`): an `httpx.Auth` sibling to the
  existing `BasicAuth`, attaching `Authorization: Bearer <token>`. The
  seam is already named in `_auth.py`'s own comment.
- A generic refresh mechanism: `auth_flow` yields a request, inspects a
  `401` response, calls a refresh callback, and re-yields — the same
  generator shape `BasicAuth.auth_flow` already returns via
  `httpx.BasicAuth`.
- A `TokenProvider` protocol/callable: "give me a token," with the SDK
  holding no opinion on where it came from.
- `ClientConfig`/`resolve_credentials` (`src/bitbucket/config.py`) widened
  to accept a `TokenProvider` as an alternative to the existing
  email/API-token pair, without making either required unconditionally.
- Restate the no-credentials-in-logs guarantee in `_transport.py`'s
  `_send` explicitly for the `Authorization: Bearer` header — today's
  comment only names Basic Auth.

Out of scope, and deliberately left to whatever delegates to the SDK (an
MCP server, a web app's OAuth callback handler, ...):

- The authorization-code flow itself — building the `/authorize` URL,
  hosting the redirect/callback, exchanging the code at the token URL,
  holding `client_id`/`client_secret`.
- Per-user token storage and lookup — which stored token belongs to which
  connected user.
- Scope selection and consent-screen concerns.

This mirrors the SDK's existing non-goals (no persistence, no policy
beyond mapping the API) rather than expanding them.

## Phase 1 — complete the pull-request surface (`0.2.0`) — shipped

The surface the SDK already claims to cover. Closed every remaining `planned`
row under Pull requests / Pull request comments / Pull request statuses /
Default reviewers in `coverage.md` (28 operations, including the `Commit
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

## Phase 2 — repository core (`0.3.0`) — shipped (52 of 55 operations)

25 `Repositories` operations, plus the directly-related content endpoints
(`Commit statuses` below was already `done`, see Phase 1):

- Repository CRUD: `POST`/`PUT`/`DELETE /repositories/{workspace}/{repo_slug}`
  (create takes the slug in the path — see the note in `coverage.md`), forks,
  hooks, watchers, permissions-config (groups/users), override-settings. All
  23 operations shipped.
- `Refs` (9): branches and tags — create/get/list/delete (no `update`;
  Bitbucket has no PUT-by-name endpoint for either). All 9 shipped.
- `Source` (4): `GET`/`POST .../src`, `GET .../src/{commit}/{path}`
  (exposed as two SDK methods — `list_path`/`read` — since the endpoint is
  polymorphic between a directory listing and raw file content),
  `GET .../filehistory/{commit}/{path}`. All 4 shipped.
- `Commits` (17, 14 shipped): commit list/get, commit comments, commit
  approve, diff, diffstat, patch, merge-base all shipped; a "file-conflicts"
  endpoint from this phase's original estimate could not be confidently
  mapped to a real, documented Bitbucket Cloud path without re-checking the
  live spec (see `coverage.md`'s note on this group) and is left `planned`,
  along with up to 2 further unverified operations against the original
  17-op estimate.
- `Commit statuses` (4) — delivered as part of Phase 1's spillover; no
  remaining work here beyond `coverage.md` bookkeeping.
- `Downloads` (4): repository downloads CRUD. All 4 shipped.

**Architecture note:** `POST .../src` is a multipart file upload, and
`diff`/`patch`/`filehistory` return plain text, not JSON — `Transport` grew
`request_multipart` and `request_bytes` seams alongside the existing
`request_text` to cover both.

**Follow-up:** re-verify the `Commits` group's exact operation list against
the live spec (`x-revision` in `coverage.md`) and close the remaining
`planned` rows there before treating Phase 2 as fully closed.

## Phase 3 — governance (`0.4.0`)

Also closes Phase 2's 3 `planned` `Commits` rows (see that phase's
follow-up note) once the live spec confirms their exact shape.

Workspace- and project-level administration surface:

- `Webhooks` (2, repo-level; workspace-level hooks live under `Workspaces`).
- `Branch restrictions` (5), `Branching model` (7).
- `Projects` (16): project CRUD, default reviewers, permissions-config.
- `Workspaces` (16): members, permissions, hooks, GPG public key.
- `Users` (4), `SSH` (5), `GPG` (4), `Search` (3).

No new architectural seams — all fit `NestedResource` or hand-written methods
following the existing pattern.

## Phase 4 — CI/CD (`0.5.0`)

- `Pipelines` (68): pipeline trigger/list/get/stop, steps, logs, test reports,
  pipelines-config (caches, runners, variables, schedules, SSH key pair,
  known hosts, OIDC discovery).
- `Deployments` (16): deploy keys, deployments, environments,
  environment variables.
- `Reports` (9): code-insight reports and annotations on commits.

**Architecture note:** step logs (`GET .../steps/{step_uuid}/log`) are
streamed/large text bodies, closer to `request_text` than `request`; test
reports and schedule executions are ordinary paginated JSON and fit the
existing `NestedResource` pattern.

## Phase 5 — remainder (`1.0.0`)

- `Snippets` (24): full snippet CRUD, comments, commits, watch, files.
- `properties` (12): app-key/property-name CRUD on commits, repos, PRs, users
  (Connect-app storage — narrow but mechanical, reuses `NestedResource`).
- `Addon` (3): Connect-app lifecycle (`PUT`/`DELETE /addon`,
  `GET /addon/{addon_key}/client-key}`).

At the end of Phase 5 the SDK covers all 294 operations in the checked spec
revision. `Issue tracker` and `Wiki` (declared as spec tags but carrying no
operations in this revision) are out of scope until Atlassian publishes them
in the machine-readable spec — see the footnote in `coverage.md`.

## Milestone summary

| Phase | Version | Adds                     |  Cumulative coverage |
| ----- | ------- | ------------------------ | -------------------: |
| —     | 0.1.0   | (shipped)                |              17 (6%) |
| 0     | 0.1.1   | +0 (OAuth bearer auth)   |              17 (6%) |
| 1     | 0.2.0   | +28 (shipped)            |             45 (15%) |
| 2     | 0.3.0   | +52 (shipped, 3 planned) |             97 (33%) |
| 3     | 0.4.0   | +49 (46 + the 3 above)   |            146 (50%) |
| 4     | 0.5.0   | +93                      |            239 (81%) |
| 5     | 1.0.0   | +55                      |           294 (100%) |

Phase 0 is listed first because it unblocks delegated-access consumers
independently of endpoint coverage, not because later phases depend on it —
Phases 1–5 proceed the same whether or not Phase 0 has landed.
