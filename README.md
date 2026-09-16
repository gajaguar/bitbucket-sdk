# Bitbucket Unofficial SDK

[![CI](https://github.com/gajaguar/bitbucket-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/gajaguar/bitbucket-sdk/actions/workflows/ci.yml)
[![Python 3.14+](https://img.shields.io/badge/python-3.14%2B-blue.svg)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Topics](https://img.shields.io/badge/topics-python%20%7C%20sdk%20%7C%20api--client%20%7C%20bitbucket%20%7C%20httpx-informational)](https://github.com/gajaguar/bitbucket-sdk)

> **Unofficial.** This project is not affiliated with, endorsed by, or
> supported by Atlassian. "Bitbucket" is a trademark of Atlassian. Use at your
> own risk against the
> [Bitbucket Cloud REST API](https://developer.atlassian.com/cloud/bitbucket/rest/intro/).

Typed, synchronous Python SDK for the Bitbucket Cloud REST API: repository
core (CRUD, forks, hooks, permissions), refs (branches/tags), source, commits,
downloads, and the full pull-request surface (comments, statuses, tasks,
merging, default reviewers). Every response is a validated, frozen
[pydantic](https://docs.pydantic.dev/) model with attribute access and real
Python types — not a raw `dict`.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for how the client is
layered.

## Table of contents

- [Installation](#installation)
- [Requirements](#requirements)
- [Usage](#usage)
- [Platform notes](#platform-notes)
- [Origin](#origin)
- [Open items](#open-items)

## Installation

Not published to PyPI. Add it as a `uv` git dependency pinned to a tag:

```bash
uv add "bitbucket-unofficial-sdk @ git+https://github.com/gajaguar/bitbucket-sdk@v0.3.0"
```

or add the source directly in `pyproject.toml`:

```toml
[project]
dependencies = ["bitbucket-unofficial-sdk"]

[tool.uv.sources.bitbucket-unofficial-sdk]
git = "https://github.com/gajaguar/bitbucket-sdk"
tag = "v0.3.0"
```

## Requirements

- [mise](https://mise.jdx.dev) — pins the toolchain (`mise.toml`: Python 3.14,
  uv, node, pnpm, pre-commit, checkmake); run `mise install`, then
  `make install`
- A Bitbucket app password/API token — see [Authentication](#authentication)

## Usage

```bash
make install   # sync Python deps, install node tooling, install pre-commit hook
make check     # read-only gate: lint, format-check, mypy, pyright,
               # md-lint, spell, pylint
make fix       # apply safe auto-fixes (format, ruff --fix, markdownlint --fix)
make test      # run the test suite
```

Run `make help` for the full target list.

### Authentication

```python
from bitbucket import BitbucketClient

# reads ATLASSIAN_USER_EMAIL and ATLASSIAN_API_KEY from the environment
client = BitbucketClient()

# or pass them explicitly
client = BitbucketClient(email="...", api_token="...")
```

### Recipes

List a repository's open pull requests, fetch one's diff, and post a comment:

```python
from bitbucket import BitbucketClient
from bitbucket import CommentContentCreate
from bitbucket import CommentCreate

with BitbucketClient() as client:
    # workspace() takes an explicit slug; default_workspace() reads
    # BITBUCKET_WORKSPACE from the environment instead.
    repository = client.default_workspace().repository("my-repo")

    open_prs = list(repository.pull_requests.list(state="OPEN"))
    for pull_request in open_prs:
        print(pull_request.id, pull_request.title)

    diff = repository.pull_requests.diff(open_prs[0].id)

    repository.pull_requests.comments(open_prs[0].id).create(
        CommentCreate(content=CommentContentCreate(raw="Looks good.")),
    )
```

Every `list()` method returns a lazy iterator that follows Bitbucket's `next`
cursor; iterate it directly, wrap in `list(...)`, or call `list_page(cursor=...)`
to manage pagination yourself.

Merge a pull request and wait for the result — `POST .../merge` returns
`202 Accepted` with an async task to poll, not the merged PR directly:

```python
from bitbucket import MergeParameters

status = repository.pull_requests.merge_and_wait(
    open_prs[0].id,
    MergeParameters(merge_strategy="squash"),
)
print(status.task_status)
```

`merge()` returns the task immediately without waiting; poll it yourself with
`merge_task_status(pull_request_id, task_id)` if you need finer control.

Create a repository, push a branch, and read a file from it:

```python
from bitbucket import BranchCreate
from bitbucket import RefTargetSpec
from bitbucket import RepositoryCreate

with BitbucketClient() as client:
    workspace = client.default_workspace()

    repository = workspace.repositories.create("new-repo", RepositoryCreate(is_private=True))
    main = next(iter(workspace.repository("new-repo").refs.branches.list()))

    workspace.repository("new-repo").refs.branches.create(
        BranchCreate(name="feature", target=RefTargetSpec(hash=main.target.hash)),
    )

    readme = workspace.repository("new-repo").source.read(main.target.hash, "README.md")
```

### Command convention: `check` vs `fix`

Targets are split by whether they mutate files:

| Prefix / umbrella   | Behavior                                                             | Example targets                                                                               |
| ------------------- | -------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `check` (read-only) | Reports problems, exits non-zero, never writes. This is the CI gate. | `lint`, `format-check`, `mypy`, `pyright`, `typecheck`, `md-lint`, `spell`, `pylint`, `check` |
| `fix` (writable)    | Mutates files in place.                                              | `format`, `lint-fix`, `lint-fix-unsafe`, `md-fix`, `fix`, `fix-unsafe`                        |

All targets accept `FILES="..."` to scope to specific paths/globs, e.g.
`make lint FILES="src/bitbucket/client.py"`.

### Toolchain

- **uv** — dependency management and virtualenvs (`hatchling` build backend)
- **httpx** — HTTP transport
- **pydantic** — response/request models (validation, aliasing, `frozen=True`)
- **ruff** — linting and formatting (`lint.select = ["ALL"]`, curated ignores)
- **mypy** + **pyright** — static type checking
- **pytest** + **pytest-cov** + **respx** — testing, coverage, HTTP mocking
- **markdownlint-cli2** + **cspell** (pnpm, dev-only) — Markdown lint & spell check
- **checkmake** — lints the `Makefile` itself (`make makefile-lint`)
- **pylint** + [`pylint-plugin`](https://github.com/gajaguar/pylint-plugin)
  (uv git dependency) — custom checkers for personal-preference rules ruff
  doesn't cover (e.g. no docstrings — see below)
- **pre-commit** — git hook running the generic hygiene hooks
  (trailing-whitespace, end-of-file-fixer, check-yaml, check-toml,
  check-merge-conflict, check-added-large-files, mixed-line-ending),
  markdownlint-cli2, cspell, checkmake, ruff, ruff-format, mypy, and pylint
  before each commit
- **mise** — pins the whole toolchain version (Python, uv, node, pnpm,
  pre-commit, checkmake) in `mise.toml`

#### Docstring policy

This project does not use docstrings — use comments only where the *why*
isn't obvious from the code. `pylint-plugin`'s `app-no-docstrings` (W9001)
checker fails `make check`/`make pylint` if any function, method, or class
has one.

### Project layout

```text
.
├── pyproject.toml       # deps, ruff/mypy/pyright/pytest/coverage config
├── Makefile             # check/fix command surface (root: shared targets)
├── mk/python.mk         # Python-specific targets, wired into the Makefile
├── mise.toml            # pinned toolchain versions
├── docs/                # ARCHITECTURE, endpoint coverage matrix
├── src/bitbucket/       # SDK package (client, models/, resources/)
└── tests/
    ├── unit/            # respx-backed, offline, deterministic
    └── live/            # marker-gated (`-m live`), hits a real workspace
```

## Platform notes

- **CI enforces lint, formatting, and spelling, not tests.**
  [`ci.yml`](.github/workflows/ci.yml) runs `make makefile-lint`,
  `make md-lint`, `make spell`, and the pre-commit hooks (ruff, ruff-format,
  mypy, pylint) on every push and pull request. It does not run `pytest` or
  `pyright`. `make check && make test` remains the full local gate; run it
  before every commit and always before tagging a release.
- **`requires-python = ">=3.14"`** excludes most current Python installations
  (3.11–3.13); this is a deliberate, revisitable floor.
- `mise.toml` forces `uv` onto the mise-provided interpreter
  (`python-preference = "only-system"`, `python-downloads = "never"` in
  `pyproject.toml`'s `[tool.uv]`), so `.python-version` is intentionally
  absent — mise is the single source of truth for the pinned Python version.

## Origin

Extracted from a larger internal toolkit's Bitbucket provider module, which
had grown the whole project's maintenance surface. That toolkit keeps the
provider-neutral pull-request seam (models, protocol, registry) and
review-workflow logic (comment filtering and threading, reviewer-queue
aggregation); this SDK carries only the Bitbucket wire client.

## Open items

- Branch restrictions, branching model, projects, workspaces, and pipelines
  are not yet modeled — see [`docs/coverage.md`](docs/coverage.md) for the
  full endpoint matrix and [`docs/ROADMAP.md`](docs/ROADMAP.md) for the
  phased plan to full API parity.
- A handful of `Commits` operations from the original Phase 2 estimate
  (a "file-conflicts" endpoint and up to 2 others) couldn't be confidently
  mapped to a real spec path without re-checking the live spec — see the
  note in `docs/coverage.md`'s `Commits` section.
- [`python.yml`](.github/workflows/python.yml) targets a `python` branch
  that doesn't exist and never runs; inherited from the template repo this
  project was extracted from, it needs retargeting to `main` or removal.
- CI does not run `pytest` or `pyright` — see [Platform notes](#platform-notes).
