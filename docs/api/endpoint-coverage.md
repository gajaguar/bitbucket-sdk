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

Status values: `planned`, `in-progress`, `done`.

## Target API version

- **API version:** `2.0` — Bitbucket Cloud publishes a single, undated major
  version at `/2.0`; there is no header-negotiated or dated version scheme to
  pin beyond that.
- **Spec checked:** `https://dac-static.atlassian.com/cloud/bitbucket/swagger.v3.json`
  (OpenAPI 3.0.0), `x-revision: 6856b45887d7`, checked 2026-09-30.
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
| Pipelines           |         68 |       0 |      0% |
| Pullrequests        |         38 |      37 |     97% |
| Repositories        |         24 |      24 |    100% |
| Snippets            |         24 |       0 |      0% |
| Commits             |         17 |      14 |     82% |
| Deployments         |         16 |       0 |      0% |
| Workspaces          |         16 |      16 |    100% |
| Projects            |         16 |      16 |    100% |
| properties          |         12 |       0 |      0% |
| Reports             |          9 |       0 |      0% |
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
| Search              |          3 |       0 |      0% |
| Webhooks            |          2 |       2 |    100% |
| **Total**           |    **294** | **155** | **53%** |

The spec also declares `Issue tracker` and `Wiki` tags with zero operations
attached to any path — Bitbucket's issue-tracker and wiki REST endpoints are
not in this machine-readable spec even though Atlassian's HTML docs still
describe them, so the 294 total above is the spec's surface, not necessarily
the full historical API. See the [roadmap](roadmap.md) for the phased plan
to close this gap.

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

| Endpoint                                                                         | SDK method                                                 | Status  |
| -------------------------------------------------------------------------------- | ---------------------------------------------------------- | ------- |
| `GET .../pullrequests`                                                           | `repo.pull_requests.list(state=..., q=..., fields=...)`    | done    |
| `GET .../pullrequests/{pull_request_id}`                                         | `repo.pull_requests.get(id)`                               | done    |
| `POST .../pullrequests`                                                          | `repo.pull_requests.create(payload)`                       | done    |
| `PUT .../pullrequests/{pull_request_id}`                                         | `repo.pull_requests.update(id, payload)`                   | done    |
| `GET .../pullrequests/activity`                                                  | `ws.repositories.pull_request_activity(slug)`              | done    |
| `GET .../pullrequests/{pull_request_id}/activity`                                | `repo.pull_requests.activity(id)`                          | done    |
| `POST .../pullrequests/{pull_request_id}/approve`                                | `repo.pull_requests.approve(id)`                           | done    |
| `DELETE .../pullrequests/{pull_request_id}/approve`                              | `repo.pull_requests.unapprove(id)`                         | done    |
| `GET .../pullrequests/{pull_request_id}/commits`                                 | `repo.pull_requests.commits(id)`                           | done    |
| `GET .../pullrequests/{pull_request_id}/conflicts`                               | `repo.pull_requests.conflicts(id)`                         | done    |
| `POST .../pullrequests/{pull_request_id}/decline`                                | `repo.pull_requests.decline(id)`                           | done    |
| `GET .../pullrequests/{pull_request_id}/diff`                                    | `repo.pull_requests.diff(id)`                              | done    |
| `GET .../pullrequests/{pull_request_id}/diffstat`                                | `repo.pull_requests.diffstat(id)`                          | done    |
| `POST .../pullrequests/{pull_request_id}/merge`                                  | `repo.pull_requests.merge(id, payload)`                    | done    |
| `GET .../pullrequests/{pull_request_id}/merge/task-status/{task_id}`             | `repo.pull_requests.merge_task_status(id, task_id)`        | done    |
| `GET .../pullrequests/{pull_request_id}/patch`                                   | `repo.pull_requests.patch(id)`                             | done    |
| `POST .../pullrequests/{pull_request_id}/request-changes`                        | `repo.pull_requests.request_changes(id)`                   | done    |
| `DELETE .../pullrequests/{pull_request_id}/request-changes`                      | `repo.pull_requests.unrequest_changes(id)`                 | done    |
| `GET .../pullrequests/{pull_request_id}/tasks`                                   | `repo.pull_requests.tasks(id).list()`                      | done    |
| `POST .../pullrequests/{pull_request_id}/tasks`                                  | `repo.pull_requests.tasks(id).create(payload)`             | done    |
| `GET .../pullrequests/{pull_request_id}/tasks/{task_id}`                         | `repo.pull_requests.tasks(id).get(task_id)`                | done    |
| `PUT .../pullrequests/{pull_request_id}/tasks/{task_id}`                         | `repo.pull_requests.tasks(id).update(task_id, payload)`    | done    |
| `DELETE .../pullrequests/{pull_request_id}/tasks/{task_id}`                      | `repo.pull_requests.tasks(id).delete(task_id)`             | done    |
| `GET .../pullrequests/{pull_request_id}/properties/{app_key}/{property_name}`    | `repo.pull_requests.properties(id).get(key, name)`         | done    |
| `PUT .../pullrequests/{pull_request_id}/properties/{app_key}/{property_name}`    | `repo.pull_requests.properties(id).put(key, name, value)`  | done    |
| `DELETE .../pullrequests/{pull_request_id}/properties/{app_key}/{property_name}` | `repo.pull_requests.properties(id).delete(key, name)`      | done    |
| `GET .../commit/{commit}/pullrequests`                                           | `ws.repositories.commit_pull_requests(slug, commit)`       | done    |
| `GET .../pullrequests/{pull_request_id}/mergeability/checks`                     | —                                                          | planned |
| `GET /workspaces/{workspace}/pullrequests/{selected_user}`                       | `ws.pull_requests_by_author(user, states=..., fields=...)` | done    |

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
guessing from the response.

## Commits

| Endpoint                                           | SDK method                                                  | Status  |
| -------------------------------------------------- | ----------------------------------------------------------- | ------- |
| `GET .../commits`                                  | `repo.commits.list(include=..., exclude=...)`               | done    |
| `GET .../commits/{revision}`                       | `repo.commits.list_from(revision)`                          | done    |
| `GET .../commit/{commit}`                          | `repo.commits.get(commit)`                                  | done    |
| `POST .../commit/{commit}/approve`                 | `repo.commits.approve(commit)`                              | done    |
| `DELETE .../commit/{commit}/approve`               | `repo.commits.unapprove(commit)`                            | done    |
| `GET .../commit/{commit}/comments`                 | `repo.commits.comments(commit).list()`                      | done    |
| `POST .../commit/{commit}/comments`                | `repo.commits.comments(commit).create(payload)`             | done    |
| `GET .../commit/{commit}/comments/{comment_id}`    | `repo.commits.comments(commit).get(comment_id)`             | done    |
| `PUT .../commit/{commit}/comments/{comment_id}`    | `repo.commits.comments(commit).update(comment_id, payload)` | done    |
| `DELETE .../commit/{commit}/comments/{comment_id}` | `repo.commits.comments(commit).delete(comment_id)`          | done    |
| `GET .../diff/{spec}`                              | `repo.commits.diff(spec)`                                   | done    |
| `GET .../diffstat/{spec}`                          | `repo.commits.diffstat(spec)`                               | done    |
| `GET .../patch/{spec}`                             | `repo.commits.patch(spec)`                                  | done    |
| `GET .../merge-base/{revspec}`                     | `repo.commits.merge_base(spec)`                             | done    |
| `GET .../file-conflicts/{spec}`                    | —                                                           | planned |
| `POST .../commits`                                 | —                                                           | planned |
| `POST .../commits/{revision}`                      | —                                                           | planned |

Note: the three `planned` rows were confirmed against `x-revision`
`6856b45887d7`; the spec declares no request body for the two `POST`
operations, so check a live response before modelling them.

## Downloads

| Endpoint                          | SDK method                             | Status |
| --------------------------------- | -------------------------------------- | ------ |
| `GET .../downloads`               | `repo.downloads.list()`                | done   |
| `POST .../downloads`              | `repo.downloads.upload(name, content)` | done   |
| `GET .../downloads/{filename}`    | `repo.downloads.get(filename)`         | done   |
| `DELETE .../downloads/{filename}` | `repo.downloads.delete(filename)`      | done   |

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
