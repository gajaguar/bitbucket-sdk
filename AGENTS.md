# AGENTS.md

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## Command surface

The agent MUST use the `Makefile` targets (`make check`, `make fix`,
`make test`, ...) instead of invoking the underlying tools directly, and
MUST NOT add a target without its `##` help line.

## Branch model

Anything language-agnostic MUST be changed on `main` and brought down into a
language branch with `git merge main`. A language branch MUST NOT edit a
file it shares with `main` except by *appending to the end* — see
[`docs/adding-a-language.md`](docs/adding-a-language.md).

## Commits and branches

Commit messages MUST follow
[Conventional Commits](https://www.conventionalcommits.org/); branch names
MUST follow [Conventional Branch](https://conventional-branch.github.io/)
(`<type>/<description>`, e.g. `feat/add-python-branch`,
`fix/makefile-phony-scoping`). Both share the same `type` vocabulary
(`feat`, `fix`, `docs`, `build`, `ci`, `refactor`, `test`, `chore`, ...).

## Gate

`make check` MUST pass before any commit. Findings SHOULD be fixed with
`make fix` before editing by hand.

## Repository metadata

The agent MUST populate the GitHub repository metadata before the first
release, and SHOULD do so in the first commit that follows instantiation of
this template:

- The repository description MUST be set to a single sentence, in English,
  without a trailing period.
- Repository topics MUST include the primary language and the project kind,
  and SHOULD include the main framework or runtime.
- The homepage URL MUST be set when the project is deployed or published,
  and MAY be left empty otherwise.
- `README.md` MUST NOT be the only place where the purpose of the project is
  stated; the description and the README first paragraph MUST agree.

The agent SHOULD apply these with `gh`:

```bash
gh repo edit --description "..." --add-topic <topic> --homepage "..."
```

The agent MUST NOT leave the description empty, and MUST NOT copy the
description of this template verbatim.

## Template instantiation

When starting a project from this template, the agent MUST:

1. Rename the placeholder package to the project's real name.
2. Update every reference to the placeholder name across config files
   (build backend package list, coverage source, CLI entry points).
3. Update this repository's metadata per the section above.
4. Run `make install && make check && make test` to confirm everything
   still passes after the rename.

## Python

The Python-specific rules below extend the sections above; they apply only
on this branch.

- The agent MUST rename the placeholder package `src/app/` to the project's
  real name and update `[project].name`, `[project.scripts]`, and
  `[tool.hatch.build.targets.wheel].packages` in `pyproject.toml`
  accordingly, plus `[tool.coverage.run].source`.
- The agent MUST NOT add docstrings to functions, methods, or classes; use a
  comment only where the *why* is not obvious from the code. The
  `pylint-plugin` `app-no-docstrings` checker enforces this and fails
  `make check`/`make pylint` otherwise.
- The agent MUST run `make check` and `make test` before committing Python
  changes, and SHOULD run `make fix` first for anything auto-fixable.
