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
  (OpenAPI 3.0.0), `x-revision: 167b2dc51ec8`, checked 2026-09-16.
- **SDK base URL:** `https://api.bitbucket.org/2.0` — see
  `src/bitbucket/config.py`'s `DEFAULT_BASE_URL`.

When re-verifying this file, re-download the spec above, confirm `x-revision`,
and re-check every path/parameter name against `paths` verbatim.

## Coverage summary

294 operations across the spec's tags, grouped by each operation's first tag
(an operation can carry more than one tag — e.g. a repository's webhook
endpoints are also tagged `Webhooks` — so this table counts each operation
once, under its first tag, to sum to 294 without double-counting).

| Group               | Operations |   Done |       % |
| ------------------- | ---------: | -----: | ------: |
| Pipelines           |         68 |      0 |      0% |
| Pullrequests        |         37 |     37 |    100% |
| Repositories        |         25 |      2 |      8% |
| Snippets            |         24 |      0 |      0% |
| Commits             |         17 |      0 |      0% |
| Deployments         |         16 |      0 |      0% |
| Workspaces          |         16 |      1 |      6% |
| Projects            |         16 |      0 |      0% |
| properties          |         12 |      0 |      0% |
| Reports             |          9 |      0 |      0% |
| Refs                |          9 |      0 |      0% |
| Branching model     |          7 |      0 |      0% |
| Branch restrictions |          5 |      0 |      0% |
| SSH                 |          5 |      0 |      0% |
| Commit statuses     |          4 |      4 |    100% |
| Downloads           |          4 |      0 |      0% |
| Source              |          4 |      0 |      0% |
| Users               |          4 |      1 |     25% |
| GPG                 |          4 |      0 |      0% |
| Addon               |          3 |      0 |      0% |
| Search              |          3 |      0 |      0% |
| Webhooks            |          2 |      0 |      0% |
| **Total**           |    **294** | **45** | **15%** |

The spec also declares `Issue tracker` and `Wiki` tags with zero operations
attached to any path — Bitbucket's issue-tracker and wiki REST endpoints are
not in this machine-readable spec even though Atlassian's HTML docs still
describe them, so the 294 total above is the spec's surface, not necessarily
the full historical API. See [`ROADMAP.md`](ROADMAP.md) for the phased plan
to close this gap.

## User

| Endpoint    | SDK method         | Status |
| ----------- | ------------------ | ------ |
| `GET /user` | `client.user.me()` | done   |

## Repositories

| Endpoint                                       | SDK method                              | Status  |
| ---------------------------------------------- | --------------------------------------- | ------- |
| `GET /repositories/{workspace}`                | `ws.repositories.list(q=..., sort=...)` | done    |
| `GET /repositories/{workspace}/{repo_slug}`    | `ws.repositories.get(slug)`             | done    |
| `POST /repositories/{workspace}/{repo_slug}`   | —                                       | planned |
| `PUT /repositories/{workspace}/{repo_slug}`    | —                                       | planned |
| `DELETE /repositories/{workspace}/{repo_slug}` | —                                       | planned |

Note: repository creation is `POST /repositories/{workspace}/{repo_slug}` —
the slug is part of the path, not a body-only field.

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
| `GET /workspaces/{workspace}/pullrequests/{selected_user}`                       | `ws.pull_requests_by_author(user, states=..., fields=...)` | done    |

## Pull request comments

| Endpoint                                                                  | SDK method                                                    | Status  |
| ------------------------------------------------------------------------- | ------------------------------------------------------------- | ------- |
| `GET .../pullrequests/{pull_request_id}/comments`                         | `repo.pull_requests.comments(id).list(sort=...)`              | done    |
| `GET .../pullrequests/{pull_request_id}/comments/{comment_id}`            | `repo.pull_requests.comments(id).get(comment_id)`             | done    |
| `POST .../pullrequests/{pull_request_id}/comments`                        | `repo.pull_requests.comments(id).create(payload)`             | done    |
| `PUT .../pullrequests/{pull_request_id}/comments/{comment_id}`            | `repo.pull_requests.comments(id).update(comment_id, payload)` | done    |
| `DELETE .../pullrequests/{pull_request_id}/comments/{comment_id}`         | `repo.pull_requests.comments(id).delete(comment_id)`          | done    |
| `POST .../pullrequests/{pull_request_id}/comments/{comment_id}/resolve`   | `repo.pull_requests.comments(id).resolve(comment_id)`         | done    |
| `DELETE .../pullrequests/{pull_request_id}/comments/{comment_id}/resolve` | `repo.pull_requests.comments(id).unresolve(comment_id)`       | done    |

## Pull request statuses

| Endpoint                                           | SDK method                                            | Status |
| -------------------------------------------------- | ----------------------------------------------------- | ------ |
| `GET .../pullrequests/{pull_request_id}/statuses`  | `repo.pull_requests.statuses(id).list()`              | done   |
| `GET .../commit/{commit}/statuses`                 | `repo.commit_statuses.list(commit)`                   | done   |
| `POST .../commit/{commit}/statuses/build`          | `repo.commit_statuses.create(commit, payload)`        | done   |
| `GET .../commit/{commit}/statuses/build/{key}`     | `repo.commit_statuses.get(commit, key)`               | done   |
| `PUT .../commit/{commit}/statuses/build/{key}`     | `repo.commit_statuses.update(commit, key, payload)`   | done   |

## Default reviewers

| Endpoint                                          | SDK method                                          | Status |
| ------------------------------------------------- | --------------------------------------------------- | ------ |
| `GET .../default-reviewers`                       | `repo.default_reviewers.list()`                     | done   |
| `GET .../default-reviewers/{target_username}`     | `repo.default_reviewers.get(target_username)`       | done   |
| `PUT .../default-reviewers/{target_username}`     | `repo.default_reviewers.add(target_username)`       | done   |
| `DELETE .../default-reviewers/{target_username}`  | `repo.default_reviewers.remove(target_username)`    | done   |
| `GET .../effective-default-reviewers`             | `repo.default_reviewers.effective()`                | done   |

Note: the endpoint uses `{target_username}`, not `{account_id}`.
