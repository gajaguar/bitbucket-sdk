# Directory Update Log

## 2026-09-30

* **Added**: `release/` with the PyPI Trusted Publishing decision.
* **Restructure**: Split `ARCHITECTURE.md` into atomic notes under
  `architecture/`.
* **Restructure**: Moved `coverage.md` and `ROADMAP.md` to
  `api/endpoint-coverage.md` and `api/roadmap.md`, with frontmatter.
* **Added**: `conventions/`, `toolchain/`, and `python/` notes, and this
  bundle's `index.md`.
* **Added**: SDK credential notes and the Bitbucket credential note.
* **Added**: `architecture/async-client.md` — decision note for the
  `bitbucket.aio` mirror (`AsyncBitbucketClient`), recording what is
  shared vs. mirrored and the rule that every new endpoint ships in both
  clients (closes #10).
* **Restructure**: Pulled shared response helpers
  (`_resolved_params`, `_log`, `_decode_json`, 204 → `None` and
  non-success → `error_for_response` status handling) out of
  `_transport.Transport` so the sync and async transports use the same
  pure code; the sync `Transport.request` now delegates to the same
  `_json_or_error` helper that `AsyncTransport.request` uses.
* **Added**: `bitbucket.aio` subpackage — `AsyncBitbucketClient`,
  `AsyncWorkspaceClient`, `AsyncRepositoryClient`, `AsyncTransport`,
  `AsyncRetryTransport`, and one async resource per sync resource under
  `bitbucket/aio/resources/`; `apaginate` and `apoll_until_terminal`
  join `_pagination.py` and `_polling.py` as the async-side siblings of
  `paginate` and `poll_until_terminal`. Reused unchanged: `models/`,
  `errors.py`, `retry.py`, `config.py`, `_auth.BasicAuth`,
  `resources.base.page_from_payload`.
* **Added**: `tests/unit/aio/` — async test mirrors of every sync suite
  (credential tests for both clients, transport, retry, pagination,
  polling, and one resource suite per sync resource), wired through the
  anyio pytest plugin (`anyio_mode = "auto"`).
* **Updated**: `docs/architecture/adding-an-endpoint.md` now lists the
  async mirror as a required step (mirror under
  `bitbucket/aio/resources/`, add a test in `tests/unit/aio/`).
* **Updated**: `docs/architecture/layering.md` gained the async-mirror
  paragraph.
* **Updated**: `docs/api/roadmap.md` — Phase 0a is the async client
  in `0.5.0`; OAuth is Phase 0b in `0.6.0`; governance is `0.7.0`;
  CI/CD is `0.8.0`; 1.0.0 is unchanged. The "No async client"
  non-goal is removed.
* **Updated**: `README.md` — tagline drops "synchronous"; new "Async
  client" section under Usage.
* **Updated**: version → `0.5.0` in `pyproject.toml` and
  `src/bitbucket/_version.py`. Not tagged and not published to PyPI yet.
