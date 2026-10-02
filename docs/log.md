# Directory Update Log

## 2026-10-02

* **Change**: the first `make docs-retag` run re-assigned the tags of several
  notes.
* **Addition**: `conventions/help-check.md` and `conventions/claude-md-check.md`,
  which the Makefile targets of the same names already enforce.
* **Addition**: `okf-base.yaml`, `make docs-lint`, `tools/docs-retag.py`,
  `conventions/tag-vocabulary.md` and `toolchain/retag-notes.md`.
* **Updated**: the version files for release `1.0.2`, a patch release that
  leaves the API alone: `Links.clone` is a list of links (issue 54).
  `x-revision` `6856b45887d7` is unchanged.
* **Updated**: the `Links` model for issue 54: `clone` is a list of links, one
  per protocol, as Bitbucket Cloud returns it, so a repository from the real API
  validates. `x-revision` `6856b45887d7` is unchanged.
* **Addition**: `conventions/versioning.md` sets the SemVer bump criteria, tags
  only minor and major bumps, and leaves releases on demand.
* **Addition**: `AGENTS.md` links to `conventions/versioning.md`.
* **Change**: `conventions/tag-vocabulary.md` states the tag form: lowercase, one
  word by default, no parent prefix.
* **Addition**: `make release-tag` (`mk/python.mk`) tags the base branch as
  `v<project.version>` after a minor or major bump merges.
* **Change**: `conventions/versioning.md` names `make release-tag` as the way to
  tag where the `Makefile` defines it.

## 2026-10-01

* **Updated**: the version files for release `1.0.1`, a patch release that
  leaves the API alone: `downloads.get` and `source.read` follow the redirect
  the spec describes (issue 43). `x-revision` `6856b45887d7` is unchanged.
* **Updated**: `api/endpoint-coverage.md`, `sdk/credential-contract.md` and
  `sdk/credential-tests.md` for the fix to `downloads.get` (issue 43): the
  `Downloads` note records the `302` the spec declares in place of a `200`,
  the `Source` note records the `301` of an LFS file, and the credential notes
  say a redirect followed to another origin carries no authentication header.
  `x-revision` `6856b45887d7` is unchanged and the summary still adds up to
  294.
* **Updated**: `api/roadmap.md`, `release/release-checklist.md` and the
  version files for release `1.0.0`: Phase 5 is shipped (291 of 294
  operations; the three `Addon` ones stay `unsupported`), the milestone table
  and "Where we are today" name the release, and the checklist gives the
  semantic-versioning rule from `1.0.0`. `x-revision` `6856b45887d7` is
  unchanged.
* **Added**: `architecture/public-api-conventions.md`, the rules the public
  surface follows from `1.0.0`: a `*_page` for every paginated iterator, `None`
  for a `204`, and `put` as create-or-replace. It lists the asymmetries that
  stay on purpose.
* **Updated**: `api/endpoint-coverage.md` and `README.md` for the public
  surface review before `1.0.0`: the properties `put` returns `None`, because
  the spec declares only `204`, and the 18 iterators that had no page method
  now have one. `x-revision` `6856b45887d7` is unchanged and the summary still
  adds up to 294.
* **Updated**: `api/endpoint-coverage.md`, `api/roadmap.md` and `README.md` for
  the rest of the `Snippets` group (291 of 294 operations): commits,
  revisions, raw files, diff and patch. The new notes record the `405` on a
  revision that is not the latest, the `302` that the HEAD file follows, the
  responses with no schema and the `patch` that takes no `path`; the three
  `Addon` operations stay `unsupported`; `x-revision` `6856b45887d7` is
  unchanged.
* **Updated**: `api/endpoint-coverage.md`, `api/roadmap.md` and `README.md` for
  the first part of the `Snippets` group (282 of 294 operations): snippet CRUD
  for a workspace and for the authenticated user, comments, watch and
  watchers. The new section records the bodies the spec leaves out (JSON for
  metadata, `multipart/form-data` for files, no `multipart/related`), the
  integer `id` the samples contradict, the `links` and `files` fields only the
  samples show, the `404` that `is_watching` reads as `False` and the CQS kind
  of each write; `x-revision` `6856b45887d7` is unchanged.
* **Updated**: `api/endpoint-coverage.md`, `api/roadmap.md` and `README.md` for
  the `properties` group (267 of 294 operations): application properties on
  repositories, commits and users, reusing `PropertiesResource`. The summary
  now counts the three pull-request property operations, which already shipped
  but were left out (it said 255 when the tables held 258). The new `Addon`
  section marks its three operations `unsupported`: they need JWT or a Forge
  app. `x-revision` `6856b45887d7` is unchanged.
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
