# Directory Update Log

## 2026-10-01

* **Updated**: `api/roadmap.md` and the version files for release `0.9.0`: the
  rows `3c`, `4a` and `4b` (255 of 294 operations) now name the release that
  ships them, and the phase sections say `shipped in 0.9.0` instead of
  `shipped on main`.
* **Updated**: `api/endpoint-coverage.md`, `api/roadmap.md` and `README.md` for
  Phase 4b, the `Deployments` and `Reports` groups (255 of 294 operations):
  environments, deployments, repository and project deploy keys, and
  code-insight reports with their annotations. The new sections record the
  request bodies the spec leaves out (deploy keys, environment `changes`), the
  deploy-key schema gaps, the `202` and `204` responses, the read-only scopes
  declared by the report writes and the CQS kind of each write; `x-revision`
  `6856b45887d7` is unchanged.
* **Updated**: `api/endpoint-coverage.md`, `api/roadmap.md` and `README.md` for
  Phase 4a, the `Pipelines` group (230 of 294 operations): pipelines, steps,
  logs, test reports, pipelines-config, variables for four scopes, runners,
  OIDC and the four environment variables. The roadmap now splits Phase 4 into
  4a and 4b (`Deployments` and `Reports`). The new section records the spec's
  `pipelines_config` and `pipelines-config` spellings, the runner operations
  with no request body, the responses with no schema, the `307` and `Range`
  handling of the logs and the `SecretStr` fields; `x-revision`
  `6856b45887d7` is unchanged.
* **Updated**: `api/endpoint-coverage.md`, `api/roadmap.md` and `README.md` for
  the rest of row `3c` (162 of 294 operations): `mergeability/checks`,
  `file-conflicts` and the two `POST` commit listings, with the spec's notes on
  their form body and paging; `x-revision` `6856b45887d7` is unchanged.
* **Updated**: `api/endpoint-coverage.md`, `api/roadmap.md` and `README.md` for
  the `Search` group (158 of 294 operations), with notes on its deprecation on
  2026-11-01 and on turning code search on; re-checked against spec
  `x-revision` `6856b45887d7`, which is unchanged.

## 2026-09-30

* **Updated**: `api/endpoint-coverage.md`, `api/roadmap.md` and `README.md` for
  the `Users`, `SSH` and `GPG` groups (155 of 294 operations); re-checked
  against spec `x-revision` `6856b45887d7`, which is unchanged. The roadmap now
  says `Projects` and `Workspaces` shipped in `0.8.0`.
* **Updated**: `api/endpoint-coverage.md`, `api/roadmap.md` and `README.md` for
  the `Workspaces` group (143 of 294 operations): members, permissions, the
  caller's own workspaces and the GPG public key.
* **Updated**: `api/endpoint-coverage.md` and `api/roadmap.md` for the
  `Projects` group (133 of 294 operations); re-checked against spec
  `x-revision` `6856b45887d7`, which is unchanged.
* **Updated**: `api/endpoint-coverage.md` and `api/roadmap.md`, re-verified
  against spec `x-revision` `6856b45887d7`: corrected the per-tag counts,
  the override-settings path, the `Commits` rows and the milestone totals.
* **Updated**: `api/endpoint-coverage.md` and `api/roadmap.md` for the
  hook-event catalogue and the workspace webhooks (104 of 294 operations),
  and the roadmap's note on the newer spec revision.
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
