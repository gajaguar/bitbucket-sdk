# Architecture

* [Layering](layering.md) - how the clients, resources, and transport stack
  on each other.
* [Request lifecycle](request-lifecycle.md) - the auth, retry,
  error-mapping, and validation pipeline.
* [Pagination](pagination.md) - how `Page` and `paginate()` follow `next`
  URLs.
* [Modeling](modeling.md) - read and write payloads as frozen pydantic
  models.
* [Endpoint comments](endpoint-comments.md) - the `# METHOD /path` comment
  every resource method carries.
* [Adding an endpoint](adding-an-endpoint.md) - the steps to add a new
  Bitbucket endpoint.
* [Release checklist](release-checklist.md) - what to verify before tagging
  a release.
