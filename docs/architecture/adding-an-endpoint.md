---
type: playbook
title: Adding an endpoint
description: The steps to add a new Bitbucket endpoint to the SDK.
tags: [architecture]
status: stable
---

# Adding an endpoint

1. Add or extend the pydantic model(s) in `src/bitbucket/models/`. Read
   models and write models (`XCreate`/`XUpdate`) are separate types.
2. Add the method to the relevant resource in `src/bitbucket/resources/`. If
   the resource is reachable as `{base_path}{_path}[/{id}]` and needs
   `create`/`get`/`list`/`update`, subclass `resources.base.NestedResource`;
   otherwise write it by hand and reuse `resources.base.page_from_payload`
   for pagination. Prefix the method with a `# METHOD /path` comment.
3. Declare the method's CQS kind — query, idempotent command, or
   non-idempotent command. The retry transport reads it to decide `5xx`
   eligibility, so getting it wrong either strips retry protection from a
   read or risks duplicating a write.
4. Add a unit test in `tests/unit/` asserting the exact HTTP method, path,
   query parameters, and body the method produces (respx).
5. Mirror the method in the async resource at
   `src/bitbucket/aio/resources/` (same name with an `Async` prefix, same
   path comment, same CQS kind; auto-paginating methods return
   `AsyncIterator` via `apaginate`). Add a matching unit test in
   `tests/unit/aio/`. The async mirror must stay in lock-step — every new
   endpoint ships in both clients; see
   [`async-client.md`](async-client.md).
6. Update [endpoint coverage](../api/endpoint-coverage.md): flip the
   endpoint's status to `done` and link the method.
7. Run `make check && make test` before committing.
