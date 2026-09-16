# Endpoint coverage

Authoritative mapping of every Bitbucket Cloud REST API endpoint this SDK
supports to its method and implementation status. This table is the
verifiable definition of "covers the pull-request surface" — an endpoint with
no row, or a row not marked `done`, is not yet supported.

Status values: `planned`, `in-progress`, `done`.

## User

| Endpoint    | SDK method         | Status |
| ----------- | ------------------ | ------ |
| `GET /user` | `client.user.me()` | done   |

## Repositories

| Endpoint                                       | SDK method                              | Status  |
| ---------------------------------------------- | --------------------------------------- | ------- |
| `GET /repositories/{workspace}`                | `ws.repositories.list(q=..., sort=...)` | done    |
| `GET /repositories/{workspace}/{repo_slug}`    | `ws.repositories.get(slug)`             | done    |
| `POST /repositories/{workspace}`               | —                                       | planned |
| `PUT /repositories/{workspace}/{repo_slug}`    | —                                       | planned |
| `DELETE /repositories/{workspace}/{repo_slug}` | —                                       | planned |

## Pull requests

| Endpoint                                             | SDK method                                                 | Status  |
| ---------------------------------------------------- | ---------------------------------------------------------- | ------- |
| `GET .../pullrequests`                               | `repo.pull_requests.list(state=..., q=..., fields=...)`    | done    |
| `GET .../pullrequests/{id}`                          | `repo.pull_requests.get(id)`                               | done    |
| `POST .../pullrequests`                              | `repo.pull_requests.create(payload)`                       | done    |
| `PUT .../pullrequests/{id}`                          | `repo.pull_requests.update(id, payload)`                   | done    |
| `POST .../pullrequests/{id}/approve`                 | `repo.pull_requests.approve(id)`                           | done    |
| `DELETE .../pullrequests/{id}/approve`               | —                                                          | planned |
| `GET .../pullrequests/{id}/diff`                     | `repo.pull_requests.diff(id)`                              | done    |
| `POST .../pullrequests/{id}/merge`                   | —                                                          | planned |
| `POST .../pullrequests/{id}/decline`                 | —                                                          | planned |
| `GET .../workspaces/{workspace}/pullrequests/{user}` | `ws.pull_requests_by_author(user, states=..., fields=...)` | done    |

## Pull request comments

| Endpoint                                             | SDK method                                                    | Status |
| ---------------------------------------------------- | ------------------------------------------------------------- | ------ |
| `GET .../pullrequests/{id}/comments`                 | `repo.pull_requests.comments(id).list(sort=...)`              | done   |
| `GET .../pullrequests/{id}/comments/{comment_id}`    | `repo.pull_requests.comments(id).get(comment_id)`             | done   |
| `POST .../pullrequests/{id}/comments`                | `repo.pull_requests.comments(id).create(payload)`             | done   |
| `PUT .../pullrequests/{id}/comments/{comment_id}`    | `repo.pull_requests.comments(id).update(comment_id, payload)` | done   |
| `DELETE .../pullrequests/{id}/comments/{comment_id}` | `repo.pull_requests.comments(id).delete(comment_id)`          | done   |

## Pull request statuses

| Endpoint                                | SDK method                               | Status  |
| --------------------------------------- | ---------------------------------------- | ------- |
| `GET .../pullrequests/{id}/statuses`    | `repo.pull_requests.statuses(id).list()` | done    |
| `POST .../commit/{hash}/statuses/build` | —                                        | planned |

## Default reviewers

| Endpoint                                    | SDK method                      | Status  |
| ------------------------------------------- | ------------------------------- | ------- |
| `GET .../default-reviewers`                 | `repo.default_reviewers.list()` | done    |
| `PUT .../default-reviewers/{account_id}`    | —                               | planned |
| `DELETE .../default-reviewers/{account_id}` | —                               | planned |
