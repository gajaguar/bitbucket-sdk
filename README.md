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

See [`docs/architecture/`](docs/architecture/index.md) for how the client is
layered.

## Table of contents

- [Installation](#installation)
- [Requirements](#requirements)
- [Usage](#usage)
- [Configuration](#configuration)
- [Security](#security)
- [Platform notes](#platform-notes)
- [Origin](#origin)
- [Open items](#open-items)
- [Contributing](#contributing)

## Installation

Not published to PyPI. Add it as a `uv` git dependency pinned to a tag:

```bash
uv add "bitbucket-unofficial-sdk @ git+https://github.com/gajaguar/bitbucket-sdk@v0.4.0"
```

or add the source directly in `pyproject.toml`:

```toml
[project]
dependencies = ["bitbucket-unofficial-sdk"]

[tool.uv.sources.bitbucket-unofficial-sdk]
git = "https://github.com/gajaguar/bitbucket-sdk"
tag = "v0.4.0"
```

## Requirements

- [mise](https://mise.jdx.dev) — pins the toolchain (`mise.toml`: Python 3.14,
  uv, node, pnpm, pre-commit, checkmake); run `mise install`, then
  `make install`
- A Bitbucket Cloud API token and the email of its Atlassian account — see
  [Authentication](#authentication)

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

# reads ATLASSIAN_USER_EMAIL and ATLASSIAN_API_TOKEN from the environment
client = BitbucketClient()

# or pass them explicitly; an explicit argument takes precedence
client = BitbucketClient(email="...", api_token="...")

# api_token also accepts a zero-argument callable, invoked lazily on every
# request instead of once at construction time — useful for a rotating or
# externally-managed token (e.g. one read from an OS keyring by the calling
# application).
client = BitbucketClient(email="...", api_token=lambda: keychain.current_token())
```

The credential sources, in order of precedence, are:

1. The `api_token` argument as a provider (a callable).
2. The `email` and `api_token` arguments as strings.
3. The `ATLASSIAN_USER_EMAIL` and `ATLASSIAN_API_TOKEN` environment variables.

`ATLASSIAN_API_KEY` is the former name of `ATLASSIAN_API_TOKEN`. It still
works, with a `DeprecationWarning`, when `ATLASSIAN_API_TOKEN` is not set.

#### Getting a credential

Bitbucket Cloud authenticates with the email of your Atlassian account and an
API token. Atlassian removed app passwords on 2026-07-28, so they no longer
work.

1. Open your profile menu and choose **Account settings**.
2. Open the **Security** tab and choose **Create and manage API tokens**.
3. Choose **Create API token with scopes**, then set a name and an expiry date.
4. Choose **Bitbucket** as the app and select the scopes your code needs.
   Bitbucket rejects a token that has no Bitbucket scopes.
5. Copy the token. Atlassian shows it only once.

The token is bound to your account and expires on the date you chose, so
rotate it before then.

#### What the SDK does not do

The SDK only reads the sources listed above. It has no OS keyring or keychain
integration, no password-manager support, no OAuth flow, and no interactive
prompts — that is an application-level concern for whatever consumes this SDK.
Bearer (OAuth 2.0) support is planned; see [`docs/api/roadmap.md`](docs/api/roadmap.md).

The full contract is in
[`docs/sdk/credential-contract.md`](docs/sdk/credential-contract.md), and the
values that belong to Bitbucket are in
[`docs/sdk/credentials.md`](docs/sdk/credentials.md).

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

### Project layout

```text
.
├── pyproject.toml       # deps, ruff/mypy/pyright/pytest/coverage config
├── Makefile             # check/fix command surface (root: shared targets)
├── mk/python.mk         # Python-specific targets, wired into the Makefile
├── mise.toml            # pinned toolchain versions
├── docs/                # OKF notes: architecture, endpoint coverage, SDK
├── src/bitbucket/       # SDK package (client, models/, resources/)
└── tests/
    ├── unit/            # respx-backed, offline, deterministic
    └── live/            # marker-gated (`-m live`), hits a real workspace
```

## Configuration

| Variable               | Where it's read                       | Default        | Description                                                      |
| ---------------------- | ------------------------------------- | -------------- | ---------------------------------------------------------------- |
| `ATLASSIAN_USER_EMAIL` | `BitbucketClient()`                   | none, required | Email of the Atlassian account, used when `email` is not passed. |
| `ATLASSIAN_API_TOKEN`  | `BitbucketClient()`                   | none, required | API token, used when `api_token` is not passed.                  |
| `ATLASSIAN_API_KEY`    | `BitbucketClient()`                   | none           | Deprecated name of `ATLASSIAN_API_TOKEN`; emits a warning.       |
| `BITBUCKET_WORKSPACE`  | `BitbucketClient.default_workspace()` | none           | Workspace slug used by `default_workspace()`.                    |

The names are exported as `EMAIL_ENV_VAR`, `API_TOKEN_ENV_VAR` and
`WORKSPACE_ENV_VAR`, so an application does not have to repeat the strings.

## Security

A Bitbucket API token grants the access of its scopes to everything your
account can reach — never commit one, and rotate it immediately if it is
exposed. The SDK never logs headers or its configuration, and the token is
excluded from `repr(ClientConfig)`.

## Platform notes

- **CI runs the full gate.** [`python.yml`](.github/workflows/python.yml)
  runs `make check` and `make test` on every push to `main` and every pull
  request.
- **`requires-python = ">=3.14"`** excludes most current Python installations
  (3.11–3.13); this is a deliberate, revisitable floor.
- `mise.toml` forces `uv` onto the mise-provided interpreter through its
  `[env]` (`UV_PYTHON_PREFERENCE=only-system`, `UV_PYTHON_DOWNLOADS=never`),
  so `.python-version` is intentionally absent — mise is the single source of
  truth for the pinned Python version.

## Origin

Extracted from a larger internal toolkit's Bitbucket provider module, which
had grown the whole project's maintenance surface. That toolkit keeps the
provider-neutral pull-request seam (models, protocol, registry) and
review-workflow logic (comment filtering and threading, reviewer-queue
aggregation); this SDK carries only the Bitbucket wire client.

## Open items

- Branch restrictions, branching model, projects, workspaces, and pipelines
  are not yet modeled — see
  [`docs/api/endpoint-coverage.md`](docs/api/endpoint-coverage.md) for the
  full endpoint matrix and [`docs/api/roadmap.md`](docs/api/roadmap.md) for
  the phased plan to full API parity.
- A handful of `Commits` operations from the original Phase 2 estimate
  (a "file-conflicts" endpoint and up to 2 others) couldn't be confidently
  mapped to a real spec path without re-checking the live spec — see the
  note in `docs/api/endpoint-coverage.md`'s `Commits` section.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md).
