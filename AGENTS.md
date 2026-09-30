# AGENTS.md

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## Agent instructions

`AGENTS.md` is the only agent instructions file. The repository MUST NOT
contain a `CLAUDE.md` or any other tool-specific copy; project rules go here.

## Command surface

The agent MUST use the `Makefile` targets (`make check`, `make fix`,
`make test`, ...) instead of invoking the underlying tools directly, and
MUST NOT add a target without its `##` help line. Run `make help` for the
full list.

## Gate

`make check` MUST pass before any commit. Findings SHOULD be fixed with
`make fix` before editing by hand.

## Commits and branches

Commit messages MUST follow
[Conventional Commits](https://www.conventionalcommits.org/); branch names
MUST follow [Conventional Branch](https://conventionalbranch.org/)
(`<type>/<description>`, e.g. `feat/add-login`). Documentation and
dependency work uses `chore/`, not `docs/`: a branch type is not a commit
type. A pre-commit hook and `make commits-check` enforce both — see
[`docs/conventions/commits-check.md`](docs/conventions/commits-check.md).

## Documentation

Documentation MUST be an OKF bundle of atomic notes under `docs/`: one
Markdown concept per file, with YAML frontmatter (`type`, `title`,
`description`). A new note MUST be added to its directory's `index.md` and
to [`docs/log.md`](docs/log.md). A note MUST cover exactly one concept, and
only when it explains something a reader can't already get from `make
help`, a linter's own message, or the configuration it comes from.

## Dependencies

A new tool MUST be added to the ecosystem manager that owns it and MUST
only go in `mise.toml` when it bootstraps an ecosystem or has none in this
repository — see
[`docs/toolchain/layering-rule.md`](docs/toolchain/layering-rule.md).

## Python

- The agent MUST NOT add docstrings to functions, methods, or classes; use a
  comment only where the *why* is not obvious from the code. The
  `pylint-gajaguar` `gajaguar-no-docstrings` checker enforces this and fails
  `make check`/`make pylint` otherwise.
- pylint MUST enable the plugin with `enable = ["gajaguar"]` in
  `pyproject.toml`'s `[tool.pylint."messages control"]`, not with a list of
  rules, so a rule added by a `pylint-gajaguar` upgrade is never left off.
- `conventional-git` MUST be the latest PyPI release; `make
  conventional-git-latest` (part of `make check`) fails otherwise, and `make
  install` upgrades it.
- The agent MUST NOT add a `pyproject.toml` setting that equals the tool's
  default, and every `lint.per-file-ignores` entry MUST match a current
  violation — see
  [`docs/python/pyproject-defaults.md`](docs/python/pyproject-defaults.md).
- The agent MUST run `make check` and `make test` before committing Python
  changes, and SHOULD run `make fix` first for anything auto-fixable.

## SDK

- The agent MUST follow
  [`docs/sdk/credential-contract.md`](docs/sdk/credential-contract.md) when it
  changes how the SDK reads, sends or hides a credential, and MUST keep the
  tests listed in
  [`docs/sdk/credential-tests.md`](docs/sdk/credential-tests.md) passing.
- The agent MUST follow
  [`docs/architecture/adding-an-endpoint.md`](docs/architecture/adding-an-endpoint.md)
  when it adds a Bitbucket endpoint, and MUST keep
  [`docs/api/endpoint-coverage.md`](docs/api/endpoint-coverage.md) in sync
  with the resources that ship.
- The agent MUST bump the version per
  [`docs/release/release-checklist.md`](docs/release/release-checklist.md)
  before tagging a release.
