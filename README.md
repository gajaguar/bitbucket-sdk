# Bitbucket Unofficial SDK

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Topics](https://img.shields.io/badge/topics-python%20%7C%20sdk%20%7C%20api--client%20%7C%20bitbucket%20%7C%20httpx-informational)](https://github.com/gajaguar/bitbucket-sdk)

> **Unofficial.** This project is not affiliated with, endorsed by, or
> supported by Atlassian. "Bitbucket" is a trademark of Atlassian. Use at your
> own risk against the
> [Bitbucket Cloud REST API](https://developer.atlassian.com/cloud/bitbucket/rest/intro/).

Typed, synchronous Python SDK for the Bitbucket Cloud REST API's pull-request
surface: repositories, pull requests, comments, statuses, and default
reviewers. Every response is a validated, frozen [pydantic](https://docs.pydantic.dev/)
model with attribute access and real Python types — not a raw `dict`.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for how the client is
layered.

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

#### Custom pylint checkers (`pylint-plugin`)

A standalone pylint plugin encoding personal code-review preferences beyond
ruff's rule set, installed as a `uv` git dependency pinned in
`pyproject.toml`'s `[tool.uv.sources]` — see
[the plugin's README](https://github.com/gajaguar/pylint-plugin) for the full
checker list.

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

- **No CI pipeline.** `make check && make test` is the gate; run it before
  every commit and always before tagging a release.
- **`requires-python = ">=3.14"`** excludes most current Python installations
  (3.11–3.13); this is a deliberate, revisitable floor, matching
  [`clockify-sdk`](https://github.com/gajaguar/clockify-sdk) and
  [`pylint-plugin`](https://github.com/gajaguar/pylint-plugin).
- `mise.toml` forces `uv` onto the mise-provided interpreter
  (`python-preference = "only-system"`, `python-downloads = "never"` in
  `pyproject.toml`'s `[tool.uv]`), so `.python-version` is intentionally
  absent — mise is the single source of truth for the pinned Python version.

## Origin

Extracted from [`agent-kit`](https://github.com/gajaguar/agent-kit)'s
`vcs_providers/bitbucket/` module, which had grown the whole project's
maintenance surface. `agent-kit` keeps the provider-neutral pull-request seam
(models, protocol, registry) and review-workflow logic (comment filtering and
threading, reviewer-queue aggregation); this SDK carries only the Bitbucket
wire client. `agent-kit` consumes it as a pinned `uv` git dependency, the same
mechanism it already uses for `pylint-plugin`.

## Open items

- Repository create/update/delete, branch restrictions, and webhooks are not
  yet modeled — see [`docs/coverage.md`](docs/coverage.md) for the full
  endpoint matrix.
- `RepositoryClient.default_reviewers` is read-only; adding/removing a
  default reviewer is deferred.
- No GitHub Actions CI yet.
