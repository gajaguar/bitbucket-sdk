# Architecture

* [Layering](layering.md) - How BitbucketClient, the workspace and repository
  clients, resources, and the transport stack on each other.
* [Async client](async-client.md) - Why the SDK now ships an
  `AsyncBitbucketClient` mirror under `bitbucket.aio`, what is shared with the
  sync client, and the rule that every new endpoint ships in both.
* [Request lifecycle](request-lifecycle.md) - The auth, retry, error-mapping,
  and validation pipeline every request goes through.
* [Pagination](pagination.md) - How Page and paginate() follow Bitbucket next
  URLs lazily.
* [Modeling](modeling.md) - How read and write payloads map to frozen pydantic
  models.
* [Endpoint comments](endpoint-comments.md) - Every resource method names the
  Bitbucket endpoint it calls in a comment, since docstrings are not allowed.
* [Adding an endpoint](adding-an-endpoint.md) - The steps to add a new
  Bitbucket endpoint to the SDK.
