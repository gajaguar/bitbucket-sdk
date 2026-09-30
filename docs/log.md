# Directory Update Log

## 2026-09-30

* **Added**: `sdk/sdk-differences.md` — the differences from `clockify-sdk`
  that remain by design.
* **Updated**: `sdk/credential-contract.md` (new "Choosing between credential
  kinds" section), `sdk/credential-tests.md` (new "Selection" group),
  `sdk/credentials.md` and `README.md` for the stricter rule: two credential
  kinds of the same strength raise `ConfigurationError`.

* **Updated**: `sdk/credentials.md`, `architecture/async-client.md`,
  `architecture/layering.md`, `README.md` and `api/roadmap.md` for shipped
  bearer-token authentication and its sync/async credential contract.
* **Added**: `api/recipes.md` and `architecture/project-layout.md`, moved out
  of the README's Usage section.
* **Restructure**: Moved `architecture/release-checklist.md` to
  `release/release-checklist.md`; aligned the `architecture/`, `api/` and
  `sdk/` index entries with each note's `description`, and gave every note
  a type from the vocabulary.
* **Updated**: `api/roadmap.md` — Phase 0b is "bearer token auth"; drops the
  refresh-on-401 mechanism and the reference to an artifact outside the
  repository, and states that the authorization-code flow, token renewal and
  storage belong to the application.
* **Updated**: `api/roadmap.md` — phases renumbered after the 0.4.x
  releases; Phase 0a is the async client.
* **Updated**: `architecture/adding-an-endpoint.md` lists the async mirror
  as a required step; `architecture/layering.md` gained the async-mirror
  paragraph.
* **Added**: `architecture/async-client.md` — the `bitbucket.aio` mirror,
  what is shared and the rule that every new endpoint ships in both
  clients.
* **Added**: `release/` with `pypi-trusted-publishing.md`.
* **Restructure**: Split `ARCHITECTURE.md` into atomic notes under
  `architecture/`: `layering.md`, `request-lifecycle.md`, `pagination.md`,
  `modeling.md`, `endpoint-comments.md`, `adding-an-endpoint.md` and
  `release-checklist.md`.
* **Restructure**: Moved `coverage.md` and `ROADMAP.md` to
  `api/endpoint-coverage.md` and `api/roadmap.md`, with frontmatter.
* **Added**: `conventions/commits-check.md`,
  `toolchain/layering-rule.md`, `toolchain/rejected-install-backends.md`,
  `python/interpreter-source.md` and `python/pyproject-defaults.md`, and this
  bundle's `index.md`.

## 2026-09-29

* **Added**: `sdk/credential-contract.md`, `sdk/credential-sources.md`,
  `sdk/credential-tests.md` and `sdk/credentials.md` — the credential
  contract, the decision not to acquire credentials, the credential tests
  and the Bitbucket credential note.
* **Updated**: `README.md` and `sdk/credentials.md` describe planned bearer
  support without calling it OAuth.

## 2026-09-16

* **Added**: `README.md` installation steps and project overview.
* **Added**: the architecture guide, the endpoint coverage matrix and the
  usage recipes.
