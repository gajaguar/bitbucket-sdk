---
type: reference
title: Endpoint coverage
description: Every Bitbucket Cloud REST API endpoint the SDK supports, mapped to its method and status.
tags: [api]
status: stable
---

# Endpoint coverage

Authoritative mapping of every Bitbucket Cloud REST API endpoint this SDK
supports to its method and implementation status. This table is the
verifiable definition of "covers the pull-request surface" — an endpoint with
no row, or a row not marked `done`, is not yet supported.

Every operation marked auto-paginating in the notes also has a
`<method>_page(..., cursor=None)` that returns one `Page`; the table lists only
the iterator. See
[Public API conventions](../architecture/public-api-conventions.md).

Status values: `planned`, `in-progress`, `done`, `unsupported` (the spec
declares the operation but the SDK cannot call it; the row says why).

## Target API version

- **API version:** `2.0` — Bitbucket Cloud publishes a single, undated major
  version at `/2.0`; there is no header-negotiated or dated version scheme to
  pin beyond that.
- **Spec checked:** `https://dac-static.atlassian.com/cloud/bitbucket/swagger.v3.json`
  (OpenAPI 3.0.0), `x-revision: 6856b45887d7`, checked 2026-10-01.
- **SDK base URL:** `https://api.bitbucket.org/2.0` — see
  `src/bitbucket/config.py`'s `DEFAULT_BASE_URL`.

When re-verifying this file, re-download the spec above, confirm `x-revision`,
and re-check every path/parameter name against `paths` verbatim.

## Coverage summary

294 operations across the spec's tags, grouped by each operation's first tag
(an operation can carry more than one tag — e.g. a repository's webhook
endpoints are also tagged `Webhooks` — so this table counts each operation
once, under its first tag, to sum to 294 without double-counting).

| Group               | Operations |    Done |       % |
| ------------------- | ---------: | ------: | ------: |
| Pipelines           |         68 |      68 |    100% |
| Pullrequests        |         38 |      38 |    100% |
| Repositories        |         24 |      24 |    100% |
| Snippets            |         24 |      24 |    100% |
| Commits             |         17 |      17 |    100% |
| Deployments         |         16 |      16 |    100% |
| Workspaces          |         16 |      16 |    100% |
| Projects            |         16 |      16 |    100% |
| properties          |         12 |      12 |    100% |
| Reports             |          9 |       9 |    100% |
| Refs                |          9 |       9 |    100% |
| Branching model     |          7 |       7 |    100% |
| Branch restrictions |          5 |       5 |    100% |
| SSH                 |          5 |       5 |    100% |
| Commit statuses     |          4 |       4 |    100% |
| Downloads           |          4 |       4 |    100% |
| Source              |          4 |       4 |    100% |
| Users               |          4 |       4 |    100% |
| GPG                 |          4 |       4 |    100% |
| Addon               |          3 |       0 |      0% |
| Search              |          3 |       3 |    100% |
| Webhooks            |          2 |       2 |    100% |
| **Total**           |    **294** | **291** | **99%** |

The spec also declares `Issue tracker` and `Wiki` tags with zero operations
attached to any path — Bitbucket's issue-tracker and wiki REST endpoints are
not in this machine-readable spec even though Atlassian's HTML docs still
describe them, so the 294 total above is the spec's surface, not necessarily
the full historical API. See the [roadmap](roadmap.md) for the phased plan
to close this gap.

The three pull-request property operations were `done` before this count was
last corrected: their first tag is `properties`, but the summary kept them
out, so it said 255 when the tables held 258 `done` rows. The summary now
counts them under `properties`.

## Users

| Endpoint                     | SDK method                   | Status |
| ---------------------------- | ---------------------------- | ------ |
| `GET /user`                  | `client.user.me()`           | done   |
| `GET /user/emails`           | `client.user.emails()`       | done   |
| `GET /user/emails/{email}`   | `client.user.email(address)` | done   |
| `GET /users/{selected_user}` | `user.get()`                 | done   |

Note: the `/user` operations act on the authenticated user and live on
`client.user`; everything under `/users/{selected_user}` hangs off the
`user = client.users(selected_user)` handle (the SSH and GPG tables use the
same `user`), which sends no request until a method is called.
`{selected_user}` is an Atlassian account id or a `{uuid}`.

Note: the spec types `GET /user` and `GET /users/{selected_user}` as `account`
although it defines a richer `user` schema, so both return `User` (an
`Account` plus `account_status`, `has_2fa_enabled` and `is_staff`).
`account_status` maps an unrecognized value to `UNKNOWN`, since the spec says
more values may follow. The two email operations declare no success response,
only a default error, so `UserEmail` follows their descriptions: `email`,
`is_primary`, `is_confirmed`.

## SSH

| Endpoint                               | SDK method                                      | Status |
| -------------------------------------- | ----------------------------------------------- | ------ |
| `GET /users/{selected_user}/ssh-keys`  | `user.ssh_keys.list()`                          | done   |
| `POST /users/{selected_user}/ssh-keys` | `user.ssh_keys.create(payload, expires_on=...)` | done   |
| `GET .../ssh-keys/{key_id}`            | `user.ssh_keys.get(key_id)`                     | done   |
| `PUT .../ssh-keys/{key_id}`            | `user.ssh_keys.update(key_id, payload)`         | done   |
| `DELETE .../ssh-keys/{key_id}`         | `user.ssh_keys.delete(key_id)`                  | done   |

Note: `{key_id}` is the key's UUID. `expires_on` is a query parameter on the
`POST`, in ISO-8601, and is sent only when given. The spec declares no write
schema, so the `POST` and `PUT` bodies are `SshKeyCreate` (`key`, `label`) and
`SshKeyUpdate` (`label`), the fields its examples send. Its `PUT` description
says only `comment` can change, yet the example sends `label`; the SDK follows
the example.

## GPG

| Endpoint                               | SDK method                          | Status |
| -------------------------------------- | ----------------------------------- | ------ |
| `GET /users/{selected_user}/gpg-keys`  | `user.gpg_keys.list()`              | done   |
| `POST /users/{selected_user}/gpg-keys` | `user.gpg_keys.create(payload)`     | done   |
| `GET .../gpg-keys/{fingerprint}`       | `user.gpg_keys.get(fingerprint)`    | done   |
| `DELETE .../gpg-keys/{fingerprint}`    | `user.gpg_keys.delete(fingerprint)` | done   |

Note: a GPG key is addressed by its fingerprint, and there is no `PUT`, so
`gpg_keys` has no `update`. Deleting a subkey answers `403`. `key` and
`subkeys` are only returned when requested through `fields`, so every `GpgKey`
field is optional. `GpgKeyCreate` sends `key` and `name`; the spec reuses the
read schema for the body.

## Search

| Endpoint                                  | SDK method                | Status |
| ----------------------------------------- | ------------------------- | ------ |
| `GET /workspaces/{workspace}/search/code` | `ws.search.code(query)`   | done   |
| `GET /users/{selected_user}/search/code`  | `user.search.code(query)` | done   |
| `GET /teams/{username}/search/code`       | `team.search.code(query)` | done   |

Note: the spec marks all three operations `deprecated: true` and says "This
API will be deprecated on November 1, 2026." The SDK keeps them and raises no
runtime warning.

Note: `team = client.teams(username)` is a handle whose only resource is
`search`; `{username}` is the team's name or a `{uuid}`. Each route answers
`404` (`NotFoundError`) until code search is turned on for the account at
<https://bitbucket.org/search>. A `429` is retried like on any other request,
honouring `Retry-After`, and raises `RateLimitError` once the retries run out.

Note: `search_query` is required and positional, and uses the UI's syntax
(`foo repo:demo`). `fields` (for example `+values.file.commit.repository`) and
`pagelen` (the spec's default is 10) are sent only when given. Pagination is the
standard `next` link, which already carries the query, so `code()` follows it
and `code_page(..., cursor=...)` takes it; `Page` does not surface the
response's `query_substituted`, `page` or `pagelen`.

Note: the result's `file` is the spec's `commit_file`, parsed as the existing
`TreeEntry`. The spec types `commit_file.attributes` as a single string enum,
while `TreeEntry.attributes` is `list[str]`, as the SDK already models it for
the source listing; this change leaves it as is.

## Repositories

| Endpoint                                                    | SDK method                                            | Status  |
| ----------------------------------------------------------- | ----------------------------------------------------- | ------- |
| `GET /repositories/{workspace}`                             | `ws.repositories.list(q=..., sort=...)`               | done    |
| `GET /repositories/{workspace}/{repo_slug}`                 | `ws.repositories.get(slug)`                           | done    |
| `POST /repositories/{workspace}/{repo_slug}`                | `ws.repositories.create(slug, payload)`               | done    |
| `PUT /repositories/{workspace}/{repo_slug}`                 | `ws.repositories.update(slug, payload)`               | done    |
| `DELETE /repositories/{workspace}/{repo_slug}`              | `ws.repositories.delete(slug)`                        | done    |
| `POST .../repositories/{workspace}/{repo_slug}/forks`       | `ws.repositories.create_fork(slug, payload)`          | done    |
| `GET .../repositories/{workspace}/{repo_slug}/forks`        | `ws.repositories.forks(slug)`                         | done    |
| `GET .../repositories/{workspace}/{repo_slug}/watchers`     | `ws.repositories.watchers(slug)`                      | done    |
| `GET .../hooks`                                             | `repo.hooks.list()`                                   | done    |
| `POST .../hooks`                                            | `repo.hooks.create(payload)`                          | done    |
| `GET .../hooks/{uid}`                                       | `repo.hooks.get(uid)`                                 | done    |
| `PUT .../hooks/{uid}`                                       | `repo.hooks.update(uid, payload)`                     | done    |
| `DELETE .../hooks/{uid}`                                    | `repo.hooks.delete(uid)`                              | done    |
| `GET .../permissions-config/groups`                         | `repo.permissions.groups.list()`                      | done    |
| `GET .../permissions-config/groups/{group_slug}`            | `repo.permissions.groups.get(group_slug)`             | done    |
| `PUT .../permissions-config/groups/{group_slug}`            | `repo.permissions.groups.update(group_slug, payload)` | done    |
| `DELETE .../permissions-config/groups/{group_slug}`         | `repo.permissions.groups.delete(group_slug)`          | done    |
| `GET .../permissions-config/users`                          | `repo.permissions.users.list()`                       | done    |
| `GET .../permissions-config/users/{selected_user_id}`       | `repo.permissions.users.get(account_id)`              | done    |
| `PUT .../permissions-config/users/{selected_user_id}`       | `repo.permissions.users.update(account_id, payload)`  | done    |
| `DELETE .../permissions-config/users/{selected_user_id}`    | `repo.permissions.users.delete(account_id)`           | done    |
| `GET .../override-settings`                                 | `repo.permissions.override_settings()`                | done    |
| `PUT .../override-settings`                                 | `repo.permissions.update_override_settings(payload)`  | done    |
| `GET /user/workspaces/{workspace}/permissions/repositories` | `ws.my_repository_permissions(q=..., sort=...)`       | done    |

Note: override-settings sits beside `permissions-config`, not under it. The
`GET` returns an inheritance state (`type` plus an `override_settings`
object); the `PUT` answers `204` with no body, so `update_override_settings`
returns `None`. The spec does not declare the `PUT` request body, so the SDK
sends `{"override_settings": {...}}`, the shape the `GET` returns. The
`{selected_user_id}` path segment is the SDK's `account_id` argument.

Note: repository creation is `POST /repositories/{workspace}/{repo_slug}` —
the slug is part of the path, not a body-only field. Paths omitting the
`/repositories/{workspace}/{repo_slug}` prefix above are abbreviated the
same way the Pull requests section abbreviates `.../pullrequests`.

## Pull requests

| Endpoint                                                                         | SDK method                                                 | Status |
| -------------------------------------------------------------------------------- | ---------------------------------------------------------- | ------ |
| `GET .../pullrequests`                                                           | `repo.pull_requests.list(state=..., q=..., fields=...)`    | done   |
| `GET .../pullrequests/{pull_request_id}`                                         | `repo.pull_requests.get(id)`                               | done   |
| `POST .../pullrequests`                                                          | `repo.pull_requests.create(payload)`                       | done   |
| `PUT .../pullrequests/{pull_request_id}`                                         | `repo.pull_requests.update(id, payload)`                   | done   |
| `GET .../pullrequests/activity`                                                  | `ws.repositories.pull_request_activity(slug)`              | done   |
| `GET .../pullrequests/{pull_request_id}/activity`                                | `repo.pull_requests.activity(id)`                          | done   |
| `POST .../pullrequests/{pull_request_id}/approve`                                | `repo.pull_requests.approve(id)`                           | done   |
| `DELETE .../pullrequests/{pull_request_id}/approve`                              | `repo.pull_requests.unapprove(id)`                         | done   |
| `GET .../pullrequests/{pull_request_id}/commits`                                 | `repo.pull_requests.commits(id)`                           | done   |
| `GET .../pullrequests/{pull_request_id}/conflicts`                               | `repo.pull_requests.conflicts(id)`                         | done   |
| `POST .../pullrequests/{pull_request_id}/decline`                                | `repo.pull_requests.decline(id)`                           | done   |
| `GET .../pullrequests/{pull_request_id}/diff`                                    | `repo.pull_requests.diff(id)`                              | done   |
| `GET .../pullrequests/{pull_request_id}/diffstat`                                | `repo.pull_requests.diffstat(id)`                          | done   |
| `POST .../pullrequests/{pull_request_id}/merge`                                  | `repo.pull_requests.merge(id, payload)`                    | done   |
| `GET .../pullrequests/{pull_request_id}/merge/task-status/{task_id}`             | `repo.pull_requests.merge_task_status(id, task_id)`        | done   |
| `GET .../pullrequests/{pull_request_id}/patch`                                   | `repo.pull_requests.patch(id)`                             | done   |
| `POST .../pullrequests/{pull_request_id}/request-changes`                        | `repo.pull_requests.request_changes(id)`                   | done   |
| `DELETE .../pullrequests/{pull_request_id}/request-changes`                      | `repo.pull_requests.unrequest_changes(id)`                 | done   |
| `GET .../pullrequests/{pull_request_id}/tasks`                                   | `repo.pull_requests.tasks(id).list()`                      | done   |
| `POST .../pullrequests/{pull_request_id}/tasks`                                  | `repo.pull_requests.tasks(id).create(payload)`             | done   |
| `GET .../pullrequests/{pull_request_id}/tasks/{task_id}`                         | `repo.pull_requests.tasks(id).get(task_id)`                | done   |
| `PUT .../pullrequests/{pull_request_id}/tasks/{task_id}`                         | `repo.pull_requests.tasks(id).update(task_id, payload)`    | done   |
| `DELETE .../pullrequests/{pull_request_id}/tasks/{task_id}`                      | `repo.pull_requests.tasks(id).delete(task_id)`             | done   |
| `GET .../pullrequests/{pullrequest_id}/properties/{app_key}/{property_name}`     | `repo.pull_requests.properties(id).get(key, name)`         | done   |
| `PUT .../pullrequests/{pullrequest_id}/properties/{app_key}/{property_name}`     | `repo.pull_requests.properties(id).put(key, name, value)`  | done   |
| `DELETE .../pullrequests/{pullrequest_id}/properties/{app_key}/{property_name}`  | `repo.pull_requests.properties(id).delete(key, name)`      | done   |
| `GET .../commit/{commit}/pullrequests`                                           | `ws.repositories.commit_pull_requests(slug, commit)`       | done   |
| `GET .../pullrequests/{pull_request_id}/mergeability/checks`                     | `repo.pull_requests.mergeability_checks(id, q=...)`        | done   |
| `GET /workspaces/{workspace}/pullrequests/{selected_user}`                       | `ws.pull_requests_by_author(user, states=..., fields=...)` | done   |

Note: `mergeability/checks` is not paginated (`size` and `values`, no `next`),
so `mergeability_checks` returns a list. `q` takes a small BBQL subset and
anything else is a `400`. A `429` (its own rate limit) is retried like any
other, under the default `RetryPolicy`; a `500` means custom merge checks or
the merge queue could not be read.

## Pull request comments

| Endpoint                                                                  | SDK method                                                    | Status |
| ------------------------------------------------------------------------- | ------------------------------------------------------------- | ------ |
| `GET .../pullrequests/{pull_request_id}/comments`                         | `repo.pull_requests.comments(id).list(sort=...)`              | done   |
| `GET .../pullrequests/{pull_request_id}/comments/{comment_id}`            | `repo.pull_requests.comments(id).get(comment_id)`             | done   |
| `POST .../pullrequests/{pull_request_id}/comments`                        | `repo.pull_requests.comments(id).create(payload)`             | done   |
| `PUT .../pullrequests/{pull_request_id}/comments/{comment_id}`            | `repo.pull_requests.comments(id).update(comment_id, payload)` | done   |
| `DELETE .../pullrequests/{pull_request_id}/comments/{comment_id}`         | `repo.pull_requests.comments(id).delete(comment_id)`          | done   |
| `POST .../pullrequests/{pull_request_id}/comments/{comment_id}/resolve`   | `repo.pull_requests.comments(id).resolve(comment_id)`         | done   |
| `DELETE .../pullrequests/{pull_request_id}/comments/{comment_id}/resolve` | `repo.pull_requests.comments(id).unresolve(comment_id)`       | done   |

## Pull request statuses

| Endpoint                                          | SDK method                                          | Status |
| ------------------------------------------------- | --------------------------------------------------- | ------ |
| `GET .../pullrequests/{pull_request_id}/statuses` | `repo.pull_requests.statuses(id).list()`            | done   |
| `GET .../commit/{commit}/statuses`                | `repo.commit_statuses.list(commit)`                 | done   |
| `POST .../commit/{commit}/statuses/build`         | `repo.commit_statuses.create(commit, payload)`      | done   |
| `GET .../commit/{commit}/statuses/build/{key}`    | `repo.commit_statuses.get(commit, key)`             | done   |
| `PUT .../commit/{commit}/statuses/build/{key}`    | `repo.commit_statuses.update(commit, key, payload)` | done   |

## Default reviewers

| Endpoint                                         | SDK method                                       | Status |
| ------------------------------------------------ | ------------------------------------------------ | ------ |
| `GET .../default-reviewers`                      | `repo.default_reviewers.list()`                  | done   |
| `GET .../default-reviewers/{target_username}`    | `repo.default_reviewers.get(target_username)`    | done   |
| `PUT .../default-reviewers/{target_username}`    | `repo.default_reviewers.add(target_username)`    | done   |
| `DELETE .../default-reviewers/{target_username}` | `repo.default_reviewers.remove(target_username)` | done   |
| `GET .../effective-default-reviewers`            | `repo.default_reviewers.effective()`             | done   |

Note: the endpoint uses `{target_username}`, not `{account_id}`.

## Refs

| Endpoint                          | SDK method                           | Status |
| --------------------------------- | ------------------------------------ | ------ |
| `GET .../refs`                    | `repo.refs.list()`                   | done   |
| `GET .../refs/branches`           | `repo.refs.branches.list()`          | done   |
| `POST .../refs/branches`          | `repo.refs.branches.create(payload)` | done   |
| `GET .../refs/branches/{name}`    | `repo.refs.branches.get(name)`       | done   |
| `DELETE .../refs/branches/{name}` | `repo.refs.branches.delete(name)`    | done   |
| `GET .../refs/tags`               | `repo.refs.tags.list()`              | done   |
| `POST .../refs/tags`              | `repo.refs.tags.create(payload)`     | done   |
| `GET .../refs/tags/{name}`        | `repo.refs.tags.get(name)`           | done   |
| `DELETE .../refs/tags/{name}`     | `repo.refs.tags.delete(name)`        | done   |

Note: no `update` for branches or tags — Bitbucket has no PUT-by-name
endpoint for either.

## Source

| Endpoint                              | SDK method                                                    | Status |
| ------------------------------------- | ------------------------------------------------------------- | ------ |
| `GET .../src`                         | `repo.source.list()`                                          | done   |
| `POST .../src`                        | `repo.source.create_commit(files, ...)`                       | done   |
| `GET .../src/{commit}/{path}`         | `repo.source.list_path(commit, path)` / `.read(commit, path)` | done   |
| `GET .../filehistory/{commit}/{path}` | `repo.source.file_history(commit, path)`                      | done   |

Note: `GET .../src/{commit}/{path}` is polymorphic — a directory or a file,
depending on `path` — so the SDK exposes it as two methods rather than
guessing from the response. A file managed by LFS answers `301` to Atlassian's
media platform, which the spec describes but does not list as a response, so
`read` follows the redirect without sending `Authorization` to the other
origin.

## Commits

| Endpoint                                           | SDK method                                                           | Status |
| -------------------------------------------------- | -------------------------------------------------------------------- | ------ |
| `GET .../commits`                                  | `repo.commits.list(include=..., exclude=...)`                        | done   |
| `GET .../commits/{revision}`                       | `repo.commits.list_from(revision)`                                   | done   |
| `GET .../commit/{commit}`                          | `repo.commits.get(commit)`                                           | done   |
| `POST .../commit/{commit}/approve`                 | `repo.commits.approve(commit)`                                       | done   |
| `DELETE .../commit/{commit}/approve`               | `repo.commits.unapprove(commit)`                                     | done   |
| `GET .../commit/{commit}/comments`                 | `repo.commits.comments(commit).list()`                               | done   |
| `POST .../commit/{commit}/comments`                | `repo.commits.comments(commit).create(payload)`                      | done   |
| `GET .../commit/{commit}/comments/{comment_id}`    | `repo.commits.comments(commit).get(comment_id)`                      | done   |
| `PUT .../commit/{commit}/comments/{comment_id}`    | `repo.commits.comments(commit).update(comment_id, payload)`          | done   |
| `DELETE .../commit/{commit}/comments/{comment_id}` | `repo.commits.comments(commit).delete(comment_id)`                   | done   |
| `GET .../diff/{spec}`                              | `repo.commits.diff(spec)`                                            | done   |
| `GET .../diffstat/{spec}`                          | `repo.commits.diffstat(spec)`                                        | done   |
| `GET .../patch/{spec}`                             | `repo.commits.patch(spec)`                                           | done   |
| `GET .../merge-base/{revspec}`                     | `repo.commits.merge_base(spec)`                                      | done   |
| `GET .../file-conflicts/{spec}`                    | `repo.commits.file_conflicts(spec)`                                  | done   |
| `POST .../commits`                                 | `repo.commits.list_by_post(include=..., exclude=...)`                | done   |
| `POST .../commits/{revision}`                      | `repo.commits.list_from_by_post(revision, include=..., exclude=...)` | done   |

Notes, checked against `x-revision` `6856b45887d7`:

- Both `POST` operations declare no `requestBody` and no parameters. The
  `GET .../commits` description says that include and exclude go in an
  `x-www-form-urlencoded` `POST` when they do not fit in a query string, so
  the SDK sends them as a repeated form body. Each later page is a `POST` to
  the `next` link with the same body, so the filter cannot be lost. They only
  read (scope `read:repository`), so they are `QUERY`.
- The spec lists no `include`, `exclude` or `path` parameters on either `GET`,
  although the SDK sends `include` and `exclude` there.
- `file-conflicts` pages with `next` and `values`. `GET
  .../pullrequests/{pull_request_id}/conflicts` is only a `302` to it, and
  both return `FileConflict` (now with `scenario` and `message`).

## Downloads

| Endpoint                          | SDK method                             | Status |
| --------------------------------- | -------------------------------------- | ------ |
| `GET .../downloads`               | `repo.downloads.list()`                | done   |
| `POST .../downloads`              | `repo.downloads.upload(name, content)` | done   |
| `GET .../downloads/{filename}`    | `repo.downloads.get(filename)`         | done   |
| `DELETE .../downloads/{filename}` | `repo.downloads.delete(filename)`      | done   |

Note: `GET .../downloads/{filename}` declares `302`, `403` and `404` and no
`200`: the file is served from a signed storage URL on another origin. `get`
follows the redirect, and the request to the storage URL carries no
`Authorization` header.

## Webhooks

| Endpoint                          | SDK method                              | Status |
| --------------------------------- | --------------------------------------- | ------ |
| `GET /hook_events`                | `client.hook_events.subject_types()`    | done   |
| `GET /hook_events/{subject_type}` | `client.hook_events.list(subject_type)` | done   |

Note: `subject_type` is `repository` or `workspace`; the spec rejects any other
value with a `404`. Both endpoints are public, but the SDK still sends its
credentials. The repository-level hook endpoints are under
[Repositories](#repositories) — they carry the `Webhooks` tag too, but are
counted once, under `Repositories`.

## Workspaces

| Endpoint                                                  | SDK method                                            | Status |
| --------------------------------------------------------- | ----------------------------------------------------- | ------ |
| `GET /user/workspaces`                                    | `client.user.workspaces(administrator=..., sort=...)` | done   |
| `GET /user/workspaces/{workspace}/permission`             | `ws.my_permission()`                                  | done   |
| `GET /workspaces/{workspace}`                             | `ws.get()`                                            | done   |
| `GET .../workspaces/{workspace}/members`                  | `ws.members.list()`                                   | done   |
| `GET .../workspaces/{workspace}/members/{member}`         | `ws.members.get(member)`                              | done   |
| `GET .../workspaces/{workspace}/permissions`              | `ws.permissions.list(q=...)`                          | done   |
| `GET .../workspaces/{workspace}/permissions/repositories` | `ws.permissions.repositories(q=..., sort=...)`        | done   |
| `GET .../permissions/repositories/{repo_slug}`            | `ws.permissions.repository(slug, q=..., sort=...)`    | done   |
| `GET .../workspaces/{workspace}/settings/gpg/public-key`  | `ws.gpg_public_key()`                                 | done   |

Note: the hooks, the project listing and the pull requests by author are
first-tagged `Workspaces` too, so they count under this group; they are listed
under [Workspace webhooks](#workspace-webhooks), [Projects](#projects) and
[Pull requests](#pull-requests). The caller's repository permissions
(`GET /user/workspaces/{workspace}/permissions/repositories`) count under
`Repositories`; see there.

Note: `{member}` is a member UUID or an Atlassian account id. The two `/user`
operations act on the authenticated user, so `client.user.workspaces()` lives
on the client and `ws.my_permission()` takes the workspace from `ws`.

Note: permissions are effective ones, with no split between direct and group
grants. The `collaborator` role is being removed by Bitbucket but still parses;
`last_accessed` and `added_on` vanish once administration moves to
admin.atlassian.com, so they are optional. The spec does not declare
`permission` on a membership, but its description and examples return it.

Note: the GPG public key is plain text (one key, or two during a rotation), so
`gpg_public_key()` returns a `str` rather than a model.

## Workspace webhooks

| Endpoint                             | SDK method                      | Status |
| ------------------------------------ | ------------------------------- | ------ |
| `GET /workspaces/{workspace}/hooks`  | `ws.hooks.list()`               | done   |
| `POST /workspaces/{workspace}/hooks` | `ws.hooks.create(payload)`      | done   |
| `GET .../hooks/{uid}`                | `ws.hooks.get(uid)`             | done   |
| `PUT .../hooks/{uid}`                | `ws.hooks.update(uid, payload)` | done   |
| `DELETE .../hooks/{uid}`             | `ws.hooks.delete(uid)`          | done   |

Note: these five operations are first-tagged `Workspaces`, so they count under
that group in the summary above, not under `Webhooks`.

## Branch restrictions

| Endpoint                              | SDK method                                             | Status |
| ------------------------------------- | ------------------------------------------------------ | ------ |
| `GET .../branch-restrictions`         | `repo.branch_restrictions.list(kind=..., pattern=...)` | done   |
| `POST .../branch-restrictions`        | `repo.branch_restrictions.create(payload)`             | done   |
| `GET .../branch-restrictions/{id}`    | `repo.branch_restrictions.get(id)`                     | done   |
| `PUT .../branch-restrictions/{id}`    | `repo.branch_restrictions.update(id, payload)`         | done   |
| `DELETE .../branch-restrictions/{id}` | `repo.branch_restrictions.delete(id)`                  | done   |

Note: `{id}` is the integer restriction id. `kind` and `branch_match_kind` are
enums that map an unrecognized value to `UNKNOWN` instead of failing, so a kind
Bitbucket adds later still parses.

## Branching model

| Endpoint                                                  | SDK method                                                 | Status |
| --------------------------------------------------------- | ---------------------------------------------------------- | ------ |
| `GET .../branching-model`                                 | `repo.branching_model.get()`                               | done   |
| `GET .../branching-model/settings`                        | `repo.branching_model.settings()`                          | done   |
| `PUT .../branching-model/settings`                        | `repo.branching_model.update_settings(payload)`            | done   |
| `GET .../effective-branching-model`                       | `repo.branching_model.effective()`                         | done   |
| `GET .../projects/{project_key}/branching-model`          | `ws.project(key).branching_model.get()`                    | done   |
| `GET .../projects/{project_key}/branching-model/settings` | `ws.project(key).branching_model.settings()`               | done   |
| `PUT .../projects/{project_key}/branching-model/settings` | `ws.project(key).branching_model.update_settings(payload)` | done   |

Note: the repository paths are under `/repositories/{workspace}/{repo_slug}`
and the project paths under `/workspaces/{workspace}`. `effective()` exists
only on a repository; a project has no effective model. `ws.project(key)`
returns a `ProjectClient` that will grow as the `Projects` group lands.

## Projects

| Endpoint                                                                        | SDK method                                                       | Status |
| ------------------------------------------------------------------------------- | ---------------------------------------------------------------- | ------ |
| `GET /workspaces/{workspace}/projects`                                          | `ws.projects.list()`                                             | done   |
| `POST /workspaces/{workspace}/projects`                                         | `ws.projects.create(payload)`                                    | done   |
| `GET .../projects/{project_key}`                                                | `ws.projects.get(key)`                                           | done   |
| `PUT .../projects/{project_key}`                                                | `ws.projects.update(key, payload)`                               | done   |
| `DELETE .../projects/{project_key}`                                             | `ws.projects.delete(key)`                                        | done   |
| `GET .../projects/{project_key}/default-reviewers`                              | `ws.project(key).default_reviewers.list()`                       | done   |
| `GET .../projects/{project_key}/default-reviewers/{selected_user}`              | `ws.project(key).default_reviewers.get(selected_user)`           | done   |
| `PUT .../projects/{project_key}/default-reviewers/{selected_user}`              | `ws.project(key).default_reviewers.add(selected_user)`           | done   |
| `DELETE .../projects/{project_key}/default-reviewers/{selected_user}`           | `ws.project(key).default_reviewers.remove(selected_user)`        | done   |
| `GET .../projects/{project_key}/permissions-config/groups`                      | `ws.project(key).permissions.groups.list()`                      | done   |
| `GET .../projects/{project_key}/permissions-config/groups/{group_slug}`         | `ws.project(key).permissions.groups.get(group_slug)`             | done   |
| `PUT .../projects/{project_key}/permissions-config/groups/{group_slug}`         | `ws.project(key).permissions.groups.update(group_slug, payload)` | done   |
| `DELETE .../projects/{project_key}/permissions-config/groups/{group_slug}`      | `ws.project(key).permissions.groups.delete(group_slug)`          | done   |
| `GET .../projects/{project_key}/permissions-config/users`                       | `ws.project(key).permissions.users.list()`                       | done   |
| `GET .../projects/{project_key}/permissions-config/users/{selected_user_id}`    | `ws.project(key).permissions.users.get(account_id)`              | done   |
| `PUT .../projects/{project_key}/permissions-config/users/{selected_user_id}`    | `ws.project(key).permissions.users.update(account_id, payload)`  | done   |
| `DELETE .../projects/{project_key}/permissions-config/users/{selected_user_id}` | `ws.project(key).permissions.users.delete(account_id)`           | done   |

Note: the project listing is first-tagged `Workspaces`, so it counts under
that group in the summary above, not under `Projects`; the project
branching-model operations are under [Branching model](#branching-model).

Note: `PUT .../projects/{project_key}` creates or updates (the spec answers
`200` or `201`), while `POST .../projects` creates only.

Note: project permissions accept and return `read`, `write`, `create-repo`
and `admin` (a response can also carry `none`), so they use their own
`ProjectPermissionLevel` rather than the repository `PermissionLevel`, which
has no `create-repo`. An unrecognized value maps to `UNKNOWN`.

Note: the default-reviewers list returns `{type, reviewer_type, user}`
wrappers (`DefaultReviewerAndType`), while an item path returns a bare user;
a project has no effective-default-reviewers path. The `{selected_user}`
segment is a username or account id, as the spec declares it.

## Pipelines

Note: `Pipelines` is the spec's first tag on 68 operations, so all of them are
counted here, including four under
`.../deployments_config/environments/{environment_uuid}/variables` that are
about deployment environments (see [Environment
variables](#environment-variables)). The handles are `repo =
ws.repository(slug)`, `ws`, `team = client.teams(username)` and `user =
client.users(selected_user)`; `repo.pipelines_config`, `ws.pipelines_config`
and the team and user ones send no request until a method is called. Checked
against `x-revision` `6856b45887d7`, unchanged.

The spec spells the config segment two ways, and each path is copied as is:
`pipelines_config` (underscore) for the repository settings, schedules, SSH
and variables and for the team and user variables, and `pipelines-config`
(hyphen) for caches, runners and everything under `/workspaces/{workspace}`.

### Pipelines and steps

| Endpoint                                                                                                         | SDK method                                                                        | Status |
| ---------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ------ |
| `GET .../pipelines`                                                                                              | `repo.pipelines.list(**filters)`                                                  | done   |
| `POST .../pipelines`                                                                                             | `repo.pipelines.create(payload, merge_defaults=..., target_branch_to_create=...)` | done   |
| `GET .../pipelines/{pipeline_uuid}`                                                                              | `repo.pipelines.get(pipeline_uuid)`                                               | done   |
| `POST .../pipelines/{pipeline_uuid}/stopPipeline`                                                                | `repo.pipelines.stop(pipeline_uuid)`                                              | done   |
| `GET .../pipelines/{pipeline_uuid}/steps`                                                                        | `repo.pipelines.steps(pipeline_uuid)`                                             | done   |
| `GET .../pipelines/{pipeline_uuid}/steps/{step_uuid}`                                                            | `repo.pipelines.step(pipeline_uuid, step_uuid)`                                   | done   |
| `GET .../pipelines/{pipeline_uuid}/steps/{step_uuid}/log`                                                        | `repo.pipelines.step_log(pipeline_uuid, step_uuid, start=..., end=...)`           | done   |
| `GET .../pipelines/{pipeline_uuid}/steps/{step_uuid}/logs/{log_uuid}`                                            | `repo.pipelines.container_log(pipeline_uuid, step_uuid, log_uuid)`                | done   |
| `GET .../pipelines/{pipeline_uuid}/steps/{step_uuid}/test_reports`                                               | `repo.pipelines.test_reports(pipeline_uuid, step_uuid)`                           | done   |
| `GET .../pipelines/{pipeline_uuid}/steps/{step_uuid}/test_reports/test_cases`                                    | `repo.pipelines.test_cases(pipeline_uuid, step_uuid)`                             | done   |
| `GET .../pipelines/{pipeline_uuid}/steps/{step_uuid}/test_reports/test_cases/{test_case_uuid}/test_case_reasons` | `repo.pipelines.test_case_reasons(pipeline_uuid, step_uuid, test_case_uuid)`      | done   |

Note: `list()` follows `next` and takes the spec's filters as keyword
arguments under their own names, for example
`repo.pipelines.list(**{"target.branch": "main"}, status="COMPLETED",
sort="-created_on")`; `pagelen` and `page` are query parameters too. `steps()`
follows `next` as well.

Note: `create` posts `PipelineCreate`: a `target` that is either
`PipelineRefTargetCreate` (`ref_type`, `ref_name`, `selector`, optional
`commit`) or `PipelineCommitTargetCreate` (`commit`, `selector`), plus
optional `variables`. These are the only two subtypes the spec defines for the
polymorphic `pipeline_target`; each sends its fixed `type`. `merge_defaults`
and `target_branch_to_create` are query parameters, sent only when given. A
pipeline's `target`, `state` and step `state` are each one model with the
subtype's fields optional, and `type` tells the subtype apart; `name` values
(`PENDING`, `COMPLETED`, `SUCCESSFUL`, `NOT_RUN` and the rest) are enums that
map an unknown value to `UNKNOWN`.

Note: The step log and the container log answer `application/octet-stream` for
errors and declare no content type on success, so they go through
`request_bytes` and return `bytes`: a log may not be valid UTF-8, and the spec
says it can be very large. The spec says `GET .../log` supports (and
encourages) HTTP Range requests, though it lists no `Range` parameter, only a
`416` response. `step_log(start=..., end=...)` sends `Range: bytes=start-end`
(open-ended when only `start` is given), and `request_bytes` now takes
per-request `headers` to carry it. Both log operations answer `307` once the
step finishes, with a redirect to long-term storage; they are sent with
`follow_redirects=True`, and httpx drops `Authorization` when the redirect
goes to another origin. `container_log` declares no `304`/`416`, and neither
operation is conditional in the SDK (no `If-None-Match`).

Note: `test_reports`, `test_cases` and `test_case_reasons` declare a `200`
with no content and no schema. The SDK returns the decoded JSON as is
(`JSONValue`) and does not page them, since nothing in the spec says they
carry `next`; model them when Atlassian publishes the schemas.

Note: `stop` answers `204`, and `400` when the pipeline already completed.

### Repository pipelines configuration

| Endpoint                                | SDK method                                           | Status |
| --------------------------------------- | ---------------------------------------------------- | ------ |
| `GET .../pipelines_config`              | `repo.pipelines_config.get()`                        | done   |
| `PUT .../pipelines_config`              | `repo.pipelines_config.update(payload)`              | done   |
| `PUT .../pipelines_config/build_number` | `repo.pipelines_config.update_build_number(payload)` | done   |

Note: `PUT .../pipelines_config` takes `pipelines_config` (`enabled`,
`repository`) and the SDK sends only `enabled`, through
`PipelinesConfigUpdate`. `build_number` takes `next`, which must be higher
than the current number (else `400`).

### Schedules

| Endpoint                                                        | SDK method                                                       | Status |
| --------------------------------------------------------------- | ---------------------------------------------------------------- | ------ |
| `POST .../pipelines_config/schedules`                           | `repo.pipelines_config.schedules.create(payload)`                | done   |
| `GET .../pipelines_config/schedules`                            | `repo.pipelines_config.schedules.list()`                         | done   |
| `GET .../pipelines_config/schedules/{schedule_uuid}`            | `repo.pipelines_config.schedules.get(schedule_uuid)`             | done   |
| `PUT .../pipelines_config/schedules/{schedule_uuid}`            | `repo.pipelines_config.schedules.update(schedule_uuid, payload)` | done   |
| `DELETE .../pipelines_config/schedules/{schedule_uuid}`         | `repo.pipelines_config.schedules.delete(schedule_uuid)`          | done   |
| `GET .../pipelines_config/schedules/{schedule_uuid}/executions` | `repo.pipelines_config.schedules.executions(schedule_uuid)`      | done   |

Note: `schedules.list()` and `executions()` follow `next`. The `POST` body is
`pipeline_schedule_post_request_body`: `target` (`ref_type`, `ref_name`,
`selector`), `cron_pattern` and `enabled`, where `target` and `cron_pattern`
are required. The spec's only `ref_type` for it is `branch`. The `PUT` body,
`pipeline_schedule_put_request_body`, has only `enabled`. A schedule execution
is either `executed` (a `pipeline`) or `errored` (an `error` with `key` and
`message`); `PipelineScheduleExecution` holds both. The spec documents a `401`
for the schedule limit, and the SDK raises it as the `AuthenticationError`
that every `401` maps to.

### SSH key pair and known hosts

| Endpoint                                                        | SDK method                                                           | Status |
| --------------------------------------------------------------- | -------------------------------------------------------------------- | ------ |
| `GET .../pipelines_config/ssh/key_pair`                         | `repo.pipelines_config.ssh_key_pair.get()`                           | done   |
| `PUT .../pipelines_config/ssh/key_pair`                         | `repo.pipelines_config.ssh_key_pair.update(payload)`                 | done   |
| `DELETE .../pipelines_config/ssh/key_pair`                      | `repo.pipelines_config.ssh_key_pair.delete()`                        | done   |
| `GET .../pipelines_config/ssh/known_hosts`                      | `repo.pipelines_config.known_hosts.list()`                           | done   |
| `POST .../pipelines_config/ssh/known_hosts`                     | `repo.pipelines_config.known_hosts.create(payload)`                  | done   |
| `GET .../pipelines_config/ssh/known_hosts/{known_host_uuid}`    | `repo.pipelines_config.known_hosts.get(known_host_uuid)`             | done   |
| `PUT .../pipelines_config/ssh/known_hosts/{known_host_uuid}`    | `repo.pipelines_config.known_hosts.update(known_host_uuid, payload)` | done   |
| `DELETE .../pipelines_config/ssh/known_hosts/{known_host_uuid}` | `repo.pipelines_config.known_hosts.delete(known_host_uuid)`          | done   |

Note: `pipeline_ssh_key_pair` has `private_key` and `public_key`; Bitbucket
returns only the public key. `private_key` is a `SecretStr`. A `known_hosts`
entry has a `hostname` and a `public_key` (`key_type`, `key`, and the two
fingerprints). `known_hosts.list()` follows `next`.

### Caches

| Endpoint                                                   | SDK method                                             | Status |
| ---------------------------------------------------------- | ------------------------------------------------------ | ------ |
| `GET .../pipelines-config/caches`                          | `repo.pipelines_config.caches.list()`                  | done   |
| `DELETE .../pipelines-config/caches`                       | `repo.pipelines_config.caches.delete_by_name(name)`    | done   |
| `DELETE .../pipelines-config/caches/{cache_uuid}`          | `repo.pipelines_config.caches.delete(cache_uuid)`      | done   |
| `GET .../pipelines-config/caches/{cache_uuid}/content-uri` | `repo.pipelines_config.caches.content_uri(cache_uuid)` | done   |

Note: `caches.list()` follows `next`. `DELETE .../caches` takes a required
`name` query parameter and deletes every cache with that name; `DELETE
.../caches/{cache_uuid}` deletes one. `content-uri` returns a `uri`.

### Variables

| Endpoint                                                                    | SDK method                                                       | Status |
| --------------------------------------------------------------------------- | ---------------------------------------------------------------- | ------ |
| `GET .../pipelines_config/variables`                                        | `repo.pipelines_config.variables.list()`                         | done   |
| `POST .../pipelines_config/variables`                                       | `repo.pipelines_config.variables.create(payload)`                | done   |
| `GET .../pipelines_config/variables/{variable_uuid}`                        | `repo.pipelines_config.variables.get(variable_uuid)`             | done   |
| `PUT .../pipelines_config/variables/{variable_uuid}`                        | `repo.pipelines_config.variables.update(variable_uuid, payload)` | done   |
| `DELETE .../pipelines_config/variables/{variable_uuid}`                     | `repo.pipelines_config.variables.delete(variable_uuid)`          | done   |
| `GET /workspaces/{workspace}/pipelines-config/variables`                    | `ws.pipelines_config.variables.list()`                           | done   |
| `POST /workspaces/{workspace}/pipelines-config/variables`                   | `ws.pipelines_config.variables.create(payload)`                  | done   |
| `GET /workspaces/{workspace}/pipelines-config/variables/{variable_uuid}`    | `ws.pipelines_config.variables.get(variable_uuid)`               | done   |
| `PUT /workspaces/{workspace}/pipelines-config/variables/{variable_uuid}`    | `ws.pipelines_config.variables.update(variable_uuid, payload)`   | done   |
| `DELETE /workspaces/{workspace}/pipelines-config/variables/{variable_uuid}` | `ws.pipelines_config.variables.delete(variable_uuid)`            | done   |
| `GET /teams/{username}/pipelines_config/variables`                          | `team.pipelines_config.variables.list()`                         | done   |
| `POST /teams/{username}/pipelines_config/variables`                         | `team.pipelines_config.variables.create(payload)`                | done   |
| `GET /teams/{username}/pipelines_config/variables/{variable_uuid}`          | `team.pipelines_config.variables.get(variable_uuid)`             | done   |
| `PUT /teams/{username}/pipelines_config/variables/{variable_uuid}`          | `team.pipelines_config.variables.update(variable_uuid, payload)` | done   |
| `DELETE /teams/{username}/pipelines_config/variables/{variable_uuid}`       | `team.pipelines_config.variables.delete(variable_uuid)`          | done   |
| `GET /users/{selected_user}/pipelines_config/variables`                     | `user.pipelines_config.variables.list()`                         | done   |
| `POST /users/{selected_user}/pipelines_config/variables`                    | `user.pipelines_config.variables.create(payload)`                | done   |
| `GET /users/{selected_user}/pipelines_config/variables/{variable_uuid}`     | `user.pipelines_config.variables.get(variable_uuid)`             | done   |
| `PUT /users/{selected_user}/pipelines_config/variables/{variable_uuid}`     | `user.pipelines_config.variables.update(variable_uuid, payload)` | done   |
| `DELETE /users/{selected_user}/pipelines_config/variables/{variable_uuid}`  | `user.pipelines_config.variables.delete(variable_uuid)`          | done   |

Note: The same `pipeline_variable` (`uuid`, `key`, `value`, `secured`) serves
four scopes through one `PipelineVariablesResource`. Each list follows `next`.
The team, user and workspace `POST` and `PUT` bodies come from
`components/requestBodies` (`pipeline_variable2` for `POST`,
`pipeline_variable` for `PUT`), not from an inline schema, and the `POST` one
is not marked required; the SDK sends `PipelineVariableCreate` (`key`,
`value`, `secured`) and `PipelineVariableUpdate` either way.

Note: A `409` on `POST` means the key already exists. For a secured variable
the spec says the value is empty in every response.

### Runners

| Endpoint                                                                | SDK method                                                   | Status |
| ----------------------------------------------------------------------- | ------------------------------------------------------------ | ------ |
| `GET .../pipelines-config/runners`                                      | `repo.pipelines_config.runners.list()`                       | done   |
| `POST .../pipelines-config/runners`                                     | `repo.pipelines_config.runners.create(payload)`              | done   |
| `GET .../pipelines-config/runners/{runner_uuid}`                        | `repo.pipelines_config.runners.get(runner_uuid)`             | done   |
| `PUT .../pipelines-config/runners/{runner_uuid}`                        | `repo.pipelines_config.runners.update(runner_uuid, payload)` | done   |
| `DELETE .../pipelines-config/runners/{runner_uuid}`                     | `repo.pipelines_config.runners.delete(runner_uuid)`          | done   |
| `GET /workspaces/{workspace}/pipelines-config/runners`                  | `ws.pipelines_config.runners.list()`                         | done   |
| `POST /workspaces/{workspace}/pipelines-config/runners`                 | `ws.pipelines_config.runners.create(payload)`                | done   |
| `GET /workspaces/{workspace}/pipelines-config/runners/{runner_uuid}`    | `ws.pipelines_config.runners.get(runner_uuid)`               | done   |
| `PUT /workspaces/{workspace}/pipelines-config/runners/{runner_uuid}`    | `ws.pipelines_config.runners.update(runner_uuid, payload)`   | done   |
| `DELETE /workspaces/{workspace}/pipelines-config/runners/{runner_uuid}` | `ws.pipelines_config.runners.delete(runner_uuid)`            | done   |

Note: The `POST` and `PUT` of repository and workspace runners declare no
request body, and `POST` answers `200`, not `201`. `RunnerCreate` and
`RunnerUpdate` therefore carry `name` and `labels`, the writable-looking
fields of `pipeline_runner`; nothing else is documented, and the models accept
extra fields. The list follows `next`; the runner list declares `next` and
`previous` as plain strings, not URIs. A runner's `oauth_client.secret` is a
`SecretStr`.

### OpenID Connect

| Endpoint                                                                                      | SDK method                                 | Status |
| --------------------------------------------------------------------------------------------- | ------------------------------------------ | ------ |
| `GET /workspaces/{workspace}/pipelines-config/identity/oidc/.well-known/openid-configuration` | `ws.pipelines_config.oidc_configuration()` | done   |
| `GET /workspaces/{workspace}/pipelines-config/identity/oidc/keys.json`                        | `ws.pipelines_config.oidc_keys()`          | done   |

Note: Both operations declare `200` with no schema, and no scope (`oauth2:
[]`). They return the decoded JSON as is. They are workspace-level and sit
under `ws.pipelines_config`.

### Environment variables

| Endpoint                                                                                  | SDK method                                                                     | Status |
| ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ | ------ |
| `GET .../deployments_config/environments/{environment_uuid}/variables`                    | `repo.environments.variables(environment_uuid).list()`                         | done   |
| `POST .../deployments_config/environments/{environment_uuid}/variables`                   | `repo.environments.variables(environment_uuid).create(payload)`                | done   |
| `PUT .../deployments_config/environments/{environment_uuid}/variables/{variable_uuid}`    | `repo.environments.variables(environment_uuid).update(variable_uuid, payload)` | done   |
| `DELETE .../deployments_config/environments/{environment_uuid}/variables/{variable_uuid}` | `repo.environments.variables(environment_uuid).delete(variable_uuid)`          | done   |

Note: These four operations are first-tagged `Pipelines`, so they count in
this group, but they belong to deployment environments. They live at
`repo.environments.variables(environment_uuid)`, on an `EnvironmentsResource`
that also carries the `Deployments` operations (see below). The spec has no `GET`
for a single deployment variable, so the resource has no `get`. Variables use
the same models as the pipeline ones (the `deployment_variable` schema is the
same shape). `list()` follows `next`.

### Pipelines notes

Note: Pagination, operation by operation: the `next` and `values` envelope is
declared by the pipelines list, steps, schedules, schedule executions, known
hosts, repository, workspace, team, user and environment variables, caches and
the repository and workspace runners lists (all auto-paginating). Every other
operation returns one object, no content (`204`), bytes, or, for test reports,
test cases, test-case reasons and the two OIDC operations, JSON with no
declared schema.

Note: CQS kinds: every `GET` is a `QUERY`. `PUT` and `DELETE` are
`IDEMPOTENT_COMMAND`, since they replace or remove by id and a repeat has no
second effect. `POST` that creates (a pipeline, a variable, a runner, a
schedule, a known host) is `NON_IDEMPOTENT_COMMAND`, so a `5xx` is never
retried and cannot start a second pipeline or hit a `409`. `stopPipeline` is
`IDEMPOTENT_COMMAND`: it only signals a stop, and a repeat answers `400`
already completed. Both `DELETE .../caches` forms are `IDEMPOTENT_COMMAND`.

Note: Secrets: a variable's `value`, the SSH `private_key`, a runner's
`oauth_client.secret` and a step image's `password` are `SecretStr`, so
`repr`, `str`, logs and error messages never show them. The write models send
the real value in the request body, which is the only place it goes. The tests
cover `repr`, the debug log and a `409` error.

Note: Rate limits: none of the 68 operations declares a `429`. The retry
policy is unchanged, so a `429` is retried like on any other request,
honouring `Retry-After`, and raises `RateLimitError` once the retries run out.

Note: Scopes: reads need `pipeline` (runners: `runner`); `stopPipeline`,
schedules, caches and cache deletion need `pipeline:write`; variables, SSH key
pair, known hosts, build number and environment variables need
`pipeline:variable`; runner writes need `runner:write`; the repository
configuration needs `repository:admin`. The OIDC operations declare none.

## Deployments

### Environments

| Endpoint                                           | SDK method                                            | Status |
| -------------------------------------------------- | ----------------------------------------------------- | ------ |
| `GET .../environments`                             | `repo.environments.list()`                            | done   |
| `POST .../environments`                            | `repo.environments.create(payload)`                   | done   |
| `GET .../environments/{environment_uuid}`          | `repo.environments.get(environment_uuid)`             | done   |
| `DELETE .../environments/{environment_uuid}`       | `repo.environments.delete(environment_uuid)`          | done   |
| `POST .../environments/{environment_uuid}/changes` | `repo.environments.update(environment_uuid, payload)` | done   |

Note: `POST .../environments/{environment_uuid}/changes` declares no request
body and answers `202` with no content, so `update` sends `EnvironmentUpdate`
(`name`, the one field `deployment_environment` documents) and returns `None`.
`deployment_environment` declares only `uuid` and `name`; `Environment` accepts
extra fields, and `EnvironmentCreate` always sends `type`
(`deployment_environment`). `POST .../environments` answers `201` and `409`
when the name exists. The four variable operations of an environment are
counted under `Pipelines` (see above) and share the `repo.environments`
resource.

### Deployments

| Endpoint                                | SDK method                              | Status |
| --------------------------------------- | --------------------------------------- | ------ |
| `GET .../deployments`                   | `repo.deployments.list()`               | done   |
| `GET .../deployments/{deployment_uuid}` | `repo.deployments.get(deployment_uuid)` | done   |

Note: The spec has no operation to create or change a deployment. A deployment's
`state` is one of three subtypes (`deployment_state_undeployed`,
`..._in_progress`, `..._completed`) and a completed state carries one of three
status subtypes (`..._successful`, `..._failed`, `..._stopped`). `DeploymentState`
and `DeploymentStatus` are one model each, with a `name` enum that falls back to
`UNKNOWN`, like `PipelineState`.

### Deploy keys

| Endpoint                                                                     | SDK method                                 | Status |
| ---------------------------------------------------------------------------- | ------------------------------------------ | ------ |
| `GET .../deploy-keys`                                                        | `repo.deploy_keys.list()`                  | done   |
| `POST .../deploy-keys`                                                       | `repo.deploy_keys.create(payload)`         | done   |
| `GET .../deploy-keys/{key_id}`                                               | `repo.deploy_keys.get(key_id)`             | done   |
| `PUT .../deploy-keys/{key_id}`                                               | `repo.deploy_keys.update(key_id, payload)` | done   |
| `DELETE .../deploy-keys/{key_id}`                                            | `repo.deploy_keys.delete(key_id)`          | done   |
| `GET /workspaces/{workspace}/projects/{project_key}/deploy-keys`             | `project.deploy_keys.list()`               | done   |
| `POST /workspaces/{workspace}/projects/{project_key}/deploy-keys`            | `project.deploy_keys.create(payload)`      | done   |
| `GET /workspaces/{workspace}/projects/{project_key}/deploy-keys/{key_id}`    | `project.deploy_keys.get(key_id)`          | done   |
| `DELETE /workspaces/{workspace}/projects/{project_key}/deploy-keys/{key_id}` | `project.deploy_keys.delete(key_id)`       | done   |

Note: The spec declares no request body for the `POST` and `PUT` of repository
deploy keys or the `POST` of project deploy keys; their descriptions show `key`
and `label`, which is what `DeployKeyCreate` and `DeployKeyUpdate` carry (the
`PUT` must send the same `key` again). The spec has no `PUT` for a project key,
so `project.deploy_keys` has no `update`. Both `POST` answer `200`, not `201`.
The schemas declare no `id`, though the `{key_id}` path and the examples use
it, and list `added_on` where the examples show `created_on`; the models
declare both. The project `GET` example shows a paginated envelope while its
schema is a single key; the SDK follows the schema. The 9 operations declare no
`operationId`.

### Deployments notes

Note: Pagination: the repository and project deploy-key lists, deployments and
environments declare `next` and `values` (all auto-paginating, with no query
parameters). Every other operation returns one object or no content: the three
`DELETE` operations answer `204` and the environment `changes` answers `202`.

Note: CQS kinds: every `GET` is a `QUERY`. `DELETE` and `PUT` are
`IDEMPOTENT_COMMAND`. `POST` that creates (an environment, a deploy key) is
`NON_IDEMPOTENT_COMMAND`, so a `5xx` is never retried and cannot hit a `409`.
`POST .../changes` is `NON_IDEMPOTENT_COMMAND` as well: it answers `202`, and
the spec does not say whether a repeat has a second effect.

Note: Secrets: none of the 16 operations carries a secret. A deploy key's `key`
is the SSH public key, so it is a plain `str`, like `SshKey.key`; the private
half never reaches the API.

Note: Rate limits: none of the 16 operations declares a `429`. The retry policy
is unchanged, so a `429` is retried like on any other request, honouring
`Retry-After`, and raises `RateLimitError` once the retries run out.

Note: Scopes: environments and deployments need `pipeline` (the new-style
`read:pipeline:bitbucket`, or `admin:pipeline:bitbucket` to create, change or
delete an environment). Repository deploy keys need `repository:admin`
(`admin:repository:bitbucket`, plus `write:ssh-key:bitbucket` or
`delete:ssh-key:bitbucket` to write); project deploy keys need `project:admin`
(`admin:project:bitbucket`, with the same two `ssh-key` scopes).

## Reports

| Endpoint                                                                   | SDK method                                                                        | Status |
| -------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ------ |
| `GET .../commit/{commit}/reports`                                          | `repo.commits.reports(commit).list()`                                             | done   |
| `GET .../commit/{commit}/reports/{reportId}`                               | `repo.commits.reports(commit).get(report_id)`                                     | done   |
| `PUT .../commit/{commit}/reports/{reportId}`                               | `repo.commits.reports(commit).put(report_id, payload)`                            | done   |
| `DELETE .../commit/{commit}/reports/{reportId}`                            | `repo.commits.reports(commit).delete(report_id)`                                  | done   |
| `GET .../commit/{commit}/reports/{reportId}/annotations`                   | `repo.commits.reports(commit).annotations(report_id).list()`                      | done   |
| `POST .../commit/{commit}/reports/{reportId}/annotations`                  | `repo.commits.reports(commit).annotations(report_id).put_many(payloads)`          | done   |
| `GET .../commit/{commit}/reports/{reportId}/annotations/{annotationId}`    | `repo.commits.reports(commit).annotations(report_id).get(annotation_id)`          | done   |
| `PUT .../commit/{commit}/reports/{reportId}/annotations/{annotationId}`    | `repo.commits.reports(commit).annotations(report_id).put(annotation_id, payload)` | done   |
| `DELETE .../commit/{commit}/reports/{reportId}/annotations/{annotationId}` | `repo.commits.reports(commit).annotations(report_id).delete(annotation_id)`       | done   |

Note: A report and an annotation are keyed by an id the caller picks, so `put`
creates or replaces (`IDEMPOTENT_COMMAND`: a repeat writes the same state).
`ReportWrite` and `ReportAnnotationWrite` leave out `type`, as the spec's
sample requests do, and `ReportAnnotationWrite` carries `title` although the
`report_annotation` schema omits it, because the samples send it. The spec
gives `report_data.value` as `object`; its description says a number, string,
boolean or `{text, href}` object depending on `type`, so `ReportData.value` is
untyped.

Note: `put_many` posts a JSON array of 1 to 100 annotations and returns the
array the server answers. It is `IDEMPOTENT_COMMAND`: every annotation must
carry an `external_id`, which makes the upload an upsert, so a repeat has no
second effect. A report holds up to 1000 annotations.

Note: Pagination: the report and annotation lists declare `next` and `values`
(auto-paginating). Every other operation returns one object, the array of the
bulk upload, or no content (`DELETE` answers `204`). Only the two `PUT`
operations declare a `400`; the two single `GET` operations declare a `404`.

Note: Secrets: none. Rate limits: none of the 9 operations declares a `429`;
the retry policy is unchanged.

Note: Scopes: all nine declare only the read scope (`repository`,
`read:repository:bitbucket`), writes included; the spec is likely wrong, so a
write may need more at runtime.

## Properties

| Endpoint                                                             | SDK method                                                  | Status |
| -------------------------------------------------------------------- | ----------------------------------------------------------- | ------ |
| `GET .../properties/{app_key}/{property_name}` (repository)          | `repo.properties.get(app_key, name)`                        | done   |
| `PUT .../properties/{app_key}/{property_name}` (repository)          | `repo.properties.put(app_key, name, value)`                 | done   |
| `DELETE .../properties/{app_key}/{property_name}` (repository)       | `repo.properties.delete(app_key, name)`                     | done   |
| `GET .../commit/{commit}/properties/{app_key}/{property_name}`       | `repo.commits.properties(commit).get(app_key, name)`        | done   |
| `PUT .../commit/{commit}/properties/{app_key}/{property_name}`       | `repo.commits.properties(commit).put(app_key, name, value)` | done   |
| `DELETE .../commit/{commit}/properties/{app_key}/{property_name}`    | `repo.commits.properties(commit).delete(app_key, name)`     | done   |
| `GET /users/{selected_user}/properties/{app_key}/{property_name}`    | `user.properties.get(app_key, name)`                        | done   |
| `PUT /users/{selected_user}/properties/{app_key}/{property_name}`    | `user.properties.put(app_key, name, value)`                 | done   |
| `DELETE /users/{selected_user}/properties/{app_key}/{property_name}` | `user.properties.delete(app_key, name)`                     | done   |

Note: The three pull-request property operations are listed in the
[Pull requests](#pull-requests) table (`repo.pull_requests.properties(id)`);
all 12 operations of the group share one `PropertiesResource`.
The spec names their path parameter `{pullrequest_id}`, unlike the other
pull-request paths, which use `{pull_request_id}`; the table now follows it.

Note: The stored value is whatever JSON the app wrote. The spec's
`application_property` allows any keys and declares only `_attributes`
(`public`, `read_only`), so `get` returns and `put` takes a JSON value, not a
model. The spec declares `204` for every `PUT` and `DELETE`, so both return
`None` (before 1.0.0, `put` returned the body when the server sent one). A
`PUT` is `IDEMPOTENT_COMMAND` (the same value leaves the same state), a
`DELETE` too.

Note: All 12 operations are marked `deprecated: true`: the spec says "This API
will be deprecated on January 31, 2027 as part of end of support for Connect
app". The SDK keeps them and raises no runtime warning. Only the `GET`
operations declare a scope (`admin:workspace:bitbucket`); the `PUT` and
`DELETE` operations declare none. No operation is paginated or declares a
`429`; the retry policy is unchanged.

Note: Secrets: the SDK holds none here. A property value is opaque JSON owned
by the caller, so it is not a `SecretStr`. The transport logs only the method,
path and status, never a body, and a test checks that a `PUT` value does not
reach the log.

## Addon

| Endpoint                            | SDK method | Status      |
| ----------------------------------- | ---------- | ----------- |
| `PUT /addon`                        | —          | unsupported |
| `DELETE /addon`                     | —          | unsupported |
| `GET /addon/{addon_key}/client-key` | —          | unsupported |

Note: Not callable with this SDK's credentials. `PUT /addon` and
`DELETE /addon` say they are for Bitbucket Connect apps and "only support JWT
authentication", which is how Bitbucket identifies the installation; the SDK
sends only Basic or Bearer credentials. `GET /addon/{addon_key}/client-key`
is "intended to be used by a Forge app using `asApp().requestBitbucket()`
only". Connect end of support is announced for 2027, so these three operations
count in the 294 but are `unsupported`, not `done`. The spec lists
`oauth2`, `basic` and `api_key` as accepted schemes for all three, which
contradicts the descriptions; the SDK follows the descriptions. `PUT /addon`
declares no request body, though its description allows `{}`, a
`descriptor` or a `descriptor_url`.

## Snippets

| Endpoint                                                          | SDK method                                                                      | Status |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------- | ------ |
| `POST /snippets`                                                  | `client.snippets.create(payload, files=...)`                                    | done   |
| `GET /snippets/{workspace}`                                       | `ws.snippets.list(role=...)`                                                    | done   |
| `POST /snippets/{workspace}`                                      | `ws.snippets.create(payload, files=...)`                                        | done   |
| `GET /snippets/{workspace}/{encoded_id}`                          | `ws.snippets.get(snippet_id)`                                                   | done   |
| `PUT /snippets/{workspace}/{encoded_id}`                          | `ws.snippets.update(snippet_id, payload, files=..., delete_files=...)`          | done   |
| `DELETE /snippets/{workspace}/{encoded_id}`                       | `ws.snippets.delete(snippet_id)`                                                | done   |
| `GET /snippets/{workspace}/{encoded_id}/comments`                 | `ws.snippet(id).comments.list()`                                                | done   |
| `POST /snippets/{workspace}/{encoded_id}/comments`                | `ws.snippet(id).comments.create(payload)`                                       | done   |
| `GET /snippets/{workspace}/{encoded_id}/comments/{comment_id}`    | `ws.snippet(id).comments.get(comment_id)`                                       | done   |
| `PUT /snippets/{workspace}/{encoded_id}/comments/{comment_id}`    | `ws.snippet(id).comments.update(comment_id, payload)`                           | done   |
| `DELETE /snippets/{workspace}/{encoded_id}/comments/{comment_id}` | `ws.snippet(id).comments.delete(comment_id)`                                    | done   |
| `GET /snippets/{workspace}/{encoded_id}/watch`                    | `ws.snippet(id).is_watching()`                                                  | done   |
| `PUT /snippets/{workspace}/{encoded_id}/watch`                    | `ws.snippet(id).watch()`                                                        | done   |
| `DELETE /snippets/{workspace}/{encoded_id}/watch`                 | `ws.snippet(id).unwatch()`                                                      | done   |
| `GET /snippets/{workspace}/{encoded_id}/watchers`                 | `ws.snippet(id).watchers()`                                                     | done   |
| `GET /snippets/{workspace}/{encoded_id}/commits`                  | `ws.snippet(id).commits()`                                                      | done   |
| `GET /snippets/{workspace}/{encoded_id}/commits/{revision}`       | `ws.snippet(id).commit(revision)`                                               | done   |
| `GET /snippets/{workspace}/{encoded_id}/files/{path}`             | `ws.snippet(id).file(path)`                                                     | done   |
| `GET /snippets/{workspace}/{encoded_id}/{node_id}`                | `ws.snippet(id).revision(node_id).get()`                                        | done   |
| `PUT /snippets/{workspace}/{encoded_id}/{node_id}`                | `ws.snippet(id).revision(node_id).update(payload, files=..., delete_files=...)` | done   |
| `DELETE /snippets/{workspace}/{encoded_id}/{node_id}`             | `ws.snippet(id).revision(node_id).delete()`                                     | done   |
| `GET /snippets/{workspace}/{encoded_id}/{node_id}/files/{path}`   | `ws.snippet(id).revision(node_id).file(path)`                                   | done   |
| `GET /snippets/{workspace}/{encoded_id}/{revision}/diff`          | `ws.snippet(id).diff(revision, path=...)`                                       | done   |
| `GET /snippets/{workspace}/{encoded_id}/{revision}/patch`         | `ws.snippet(id).patch(revision)`                                                | done   |

Note: All 24 operations are done.

Note: `ws.snippets` is the workspace collection and `ws.snippet(id)` a handle
for one snippet, like `ws.repositories` and `ws.repository(slug)`; the handle
sends no request until a method is called. `POST /snippets` creates under the
authenticated user's account and is `client.snippets.create`, which offers no
other method. `{encoded_id}` is the short id such as `abc`, as a string.

Note: Request bodies. `POST` and `PUT` on a snippet declare no body (the `POST`
declares the `snippet` schema as JSON, but its description says snippets "are
created with a multipart POST"). The SDK follows the descriptions:

- `create` always sends `multipart/form-data`: `title`, `is_private` and `scm`
  as flat form fields, and one `file` part per entry of `files` (name to
  bytes).
- `update` sends JSON when it only changes metadata, so `SnippetUpdate(title=None)`
  sends `null`, which the spec uses to delete a title. With `files` or
  `delete_files` it sends `multipart/form-data` instead, where a file to delete
  is a repeated `files` field. A form field cannot carry `null`, so `None`
  fields are left out there.
- `multipart/related` is not supported, and the SDK sends no `Accept` header, so
  the response is the default JSON.

Note: Responses. The spec's `snippet` schema declares `id` as an integer, but
its samples and the `{encoded_id}` path use a string, so `Snippet.id` is text
and an integer is read as text. It leaves out `links` and `files`, which the
samples show; `Snippet` carries both, `files` as a map of file name to
`SnippetFile` (its links). `scm` maps an unlisted value to `UNKNOWN`.
`snippet_comment` does not extend `comment` in the spec; `SnippetComment`
extends `Comment` and adds `snippet`, and `SnippetCommentCreate` takes
`content.raw` and an optional `parent.id`, as the description says.

Note: `GET .../watch` answers `204` when the user watches the snippet and
`404` both when the user does not and when the snippet does not exist, so
`is_watching()` returns `False` for either; any other error is raised.
`watchers` is `deprecated` in the spec; it is kept, with no runtime warning.

Note: Pagination: the snippet, comment and watcher lists declare `next` and
`values` (auto-paginating). `watch`, `unwatch` and the three `DELETE`
operations answer `204` with no body. CQS: `GET` is `QUERY`; `create` and
comment `create` are `NON_IDEMPOTENT_COMMAND`; `update`, `watch`, `unwatch`
and the `DELETE`s are `IDEMPOTENT_COMMAND`, since repeating them leaves the
same state. Secrets: none; snippet contents are not credentials. Rate limits:
none of the 15 declares a `429`; the retry policy is unchanged.

Note: Scopes: the spec lists `snippet` and `snippet:write` for OAuth, and the
`x-atlassian-oauth2-scopes` `read:snippet:bitbucket`, `write:snippet:bitbucket`
and `delete:snippet:bitbucket`. `GET .../watchers` declares none.

Note: History. `{node_id}` and `{revision}` are commit hashes of the snippet's
own repository. `ws.snippet(id).revision(node_id)` addresses
`/snippets/{workspace}/{encoded_id}/{node_id}`: `get` reads that revision,
and `update` and `delete` act only on the latest one, so an older `node_id`
answers `405` (raised as `BitbucketAPIError`). The spec calls this a
compare-and-swap guard. A retry cannot duplicate anything, so both are
`IDEMPOTENT_COMMAND`, like the unversioned `PUT` and `DELETE`, and `update`
takes the same `files` and `delete_files` arguments.

Note: Bodies that are not JSON. `file(path)` on the snippet answers `302` to
the file at the latest revision; the SDK follows it and returns the bytes
(`revision(node_id).file(path)` answers `200` with the bytes directly). The
spec declares no response schema for either, only `Content-Type` and
`Content-Disposition` headers, which the SDK does not surface. `diff` and
`patch` return the raw text; the spec says the character encoding of a diff is
unspecified. `diff` sends `?path=` only when given, and the spec says `patch`
does not support it. `GET .../commits` is paginated with `next` and `values`;
the other eight operations are not.

Note: `snippet_commit` extends `base_commit` with `links` and `snippet`.
`SnippetCommit` keeps `hash` as text and reuses `AuthorRef`, `CommitRef` and
`RenderedField`, like `Commit`. None of the nine declares a `429` or a secret.
Scopes: the reads declare `read:snippet:bitbucket`; the revision `PUT` adds
`write:snippet:bitbucket` and the revision `DELETE` declares only that.
