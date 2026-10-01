---
type: rule
title: Public API conventions
description: The naming and return-type rules the public surface follows from 1.0.0, and the asymmetries that are intentional.
tags: [architecture]
status: stable
---

# Public API conventions

From `1.0.0` the public names are frozen. A change to a rule below needs a new
major version. The async client in `bitbucket.aio` follows every rule, with
`await` and `AsyncIterator` in place of the sync types.

## Rules

- A `GET` that returns a collection has a lazy iterator (`list()`, or the
  noun, such as `commits()`) and a `<name>_page(..., cursor=None)` method
  that returns one `Page`. The iterator calls the page method. `cursor` is the
  literal `next` URL of the previous page. A page method takes `pagelen` only
  where the spec's endpoint accepts it and the SDK already sent it.
- `create`, `get`, `update` and `delete` follow the verb of the request. An
  operation that answers `204` returns `None`; `delete`, `unwatch`, `unapprove`
  and `put` on a property do.
- `put` is create-or-replace under a key the caller chooses: properties,
  reports and annotations, with `put_many` for the annotation upload. It is
  not `update`, which changes a resource the server named. Renaming it would
  hide that a repeat call writes the same state.
- A method takes at most five arguments. The first ones are the path
  parameters, in the order of the path, and the rest are keyword-only.

## Intentional asymmetries

- `client.users(selected_user)` and `client.teams(username)` are plural
  because the argument picks one among many, while `client.user` is the
  authenticated user. `workspace`, `repository` and `project` are singular
  handles that name the one they open.
- `client.snippets` has only `create`: the spec has `POST /snippets` and no
  `GET /snippets`. The rest is under `workspace.snippets` and
  `workspace.snippet(id)`.
- `get()` exists on a handle only when the spec has a `GET` on the handle's own
  path (`WorkspaceClient`, `UserClient`). The repository and the project are
  read with `repositories.get(slug)` and `projects.get(key)`.
- Path parameters keep the spec's name where it differs, such as
  `target_username` on a repository's default reviewers and `selected_user` on
  a project's, so that a reader can find them in the spec.

See [Pagination](pagination.md) for the cursor and
[Endpoint comments](endpoint-comments.md) for the comment above each method.
