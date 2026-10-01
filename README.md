# Bitbucket Unofficial SDK

[![CI](https://img.shields.io/github/actions/workflow/status/gajaguar/bitbucket-sdk/ci.yml?branch=main&label=ci)](https://github.com/gajaguar/bitbucket-sdk/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/bitbucket-unofficial-sdk?label=pypi)](https://pypi.org/project/bitbucket-unofficial-sdk/)
[![Python 3.14+](https://img.shields.io/badge/python-3.14%2B-blue)](https://github.com/gajaguar/bitbucket-sdk/blob/main/pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](https://github.com/gajaguar/bitbucket-sdk/blob/main/LICENSE)
[![Topics](https://img.shields.io/badge/topics-api--client%20%7C%20bitbucket%20%7C%20httpx%20%7C%20pydantic%20%7C%20python%20%7C%20sdk-informational)](https://github.com/gajaguar/bitbucket-sdk)

> **Unofficial.** This project is not affiliated with, endorsed by, or
> supported by Atlassian. "Bitbucket" is a trademark of Atlassian. Use at your
> own risk against the
> [Bitbucket Cloud REST API](https://developer.atlassian.com/cloud/bitbucket/rest/intro/).

Typed Python SDK for the Bitbucket Cloud REST API: repository
core (CRUD, forks, hooks, permissions), refs (branches/tags), source, commits,
downloads, and the full pull-request surface (comments, statuses, tasks,
merging, default reviewers). Ships in two flavours — a sync client
(`BitbucketClient`) backed by `httpx.Client` and an async client
(`AsyncBitbucketClient`) backed by `httpx.AsyncClient` — with the same
features and credential contract in both. Every response is a validated,
frozen [pydantic](https://docs.pydantic.dev/) model with attribute access
and real Python types — not a raw `dict`.

See [`docs/architecture/`][architecture] for how the client is
layered.

## Table of contents

- [About](#about)
- [Key features](#key-features)
- [Installation](#installation)
- [Requirements](#requirements)
- [Usage](#usage)
- [Configuration](#configuration)
- [Origin](#origin)
- [Contributing](#contributing)
- [Open items](#open-items)
- [License](#license)

## About

Bitbucket Cloud's REST API returns loosely shaped JSON and paginates by
following `next` URLs. This SDK wraps it so a caller works with typed
objects instead: one client per workspace or repository, lazy pagination,
and a single credential contract shared by the sync and async clients.

## Key features

- Sync (`BitbucketClient`) and async (`AsyncBitbucketClient`) clients with
  the same endpoints.
- Validated, frozen pydantic models for every response.
- Lazy pagination through `Page` and `paginate()`.
- Retry and error mapping built into the transport.
- Credentials read from arguments or environment and kept out of logs.

## Installation

Install it from [PyPI](https://pypi.org/project/bitbucket-unofficial-sdk/):

```bash
uv add bitbucket-unofficial-sdk
```

or with `pip install bitbucket-unofficial-sdk`. To try an unreleased commit,
install it from git instead:

```bash
uv add "bitbucket-unofficial-sdk @ git+https://github.com/gajaguar/bitbucket-sdk"
```

## Requirements

- Python 3.14 or later. The floor is deliberate and can change.
- Either an Atlassian email and API token, or a Bitbucket access token — see
  [Authentication](#authentication)

## Usage

List a repository's open pull requests:

```python
from bitbucket import BitbucketClient

with BitbucketClient() as client:
    repository = client.default_workspace().repository("my-repo")

    for pull_request in repository.pull_requests.list(state="OPEN"):
        print(pull_request.id, pull_request.title)
```

Every `list()` method returns a lazy iterator that follows Bitbucket's `next`
cursor; iterate it directly, wrap it in `list(...)`, or call
`list_page(cursor=...)` to manage pagination yourself. More examples — commenting,
merging and waiting for the result, creating a repository — are in
[`docs/api/recipes.md`][api-recipes]. The layout of the repository is in
[`docs/architecture/project-layout.md`][architecture-project-layout].

### Authentication

```python
from bitbucket import BitbucketClient

# reads ATLASSIAN_USER_EMAIL and ATLASSIAN_API_TOKEN from the environment
client = BitbucketClient()

# or pass the email and API token explicitly
client = BitbucketClient(email="...", api_token="...")

# api_token accepts a zero-argument callable, invoked lazily on every request
client = BitbucketClient(email="...", api_token=lambda: keychain.current_token())

# access_token sends Authorization: Bearer and does not require an email
client = BitbucketClient(access_token="...")

# access_token also accepts a rotating or externally-managed provider
client = BitbucketClient(access_token=lambda: token_store.current_token())
```

The SDK accepts either basic credentials (email plus API token) or a bearer
access token. Within each credential kind, the first source that has a value
wins:

1. A provider callable.
2. An explicit string argument.
3. An environment variable.

Between the two kinds, an explicit argument or provider beats the other kind's
environment variable. If both kinds are explicit, or both are available only
through the environment, the SDK raises `ConfigurationError` because the
request is ambiguous. The resolver only reads or warns for the kind that wins.

`ATLASSIAN_API_KEY` is the former name of `ATLASSIAN_API_TOKEN`. It still
works, with a `DeprecationWarning`, when `ATLASSIAN_API_TOKEN` is not set and
basic credentials win.

#### Getting a credential

For an API token, open your profile menu and choose **Account settings**.
Open the **Security** tab and choose **Create and manage API tokens**. Choose
**Create API token with scopes**, select **Bitbucket** and the scopes your code
needs, then copy the token. Atlassian shows it only once. API tokens are bound
to your account and expire on the date you choose. Atlassian removed app
passwords on 2026-07-28, so they no longer work.

For a bearer token, create a repository, project, or workspace access token in
its **Access tokens** settings, or obtain an OAuth access token through the
application's OAuth flow. The SDK uses the resulting token but does not obtain
or refresh it.

#### What the SDK does not do

The SDK only reads the sources listed above. It has no OS keyring or keychain
integration, no password-manager support, no OAuth flow, and no interactive
prompts — those are application-level concerns for whatever consumes this SDK.
The application is responsible for obtaining, refreshing and storing bearer
tokens.

#### Protecting the token

A Bitbucket token grants the access of its scopes to everything it can reach.
Never commit one, and rotate it immediately if it is exposed. The SDK never
logs headers or its configuration, and credential values are excluded from
`repr(ClientConfig)`.

The full contract is in
[`docs/sdk/credential-contract.md`][sdk-credential-contract], and the
values that belong to Bitbucket are in
[`docs/sdk/credentials.md`][sdk-credentials].

### Users, SSH keys and GPG keys

`client.user` acts for the authenticated user (`me()`, `emails()`,
`email(address)`), while `client.users(selected_user)` returns a handle for
any user, by Atlassian account id or `{uuid}`:

```python
user = client.users("{ed08f5e1-605b-4f4a-aee4-6c97628a673e}")
profile = user.get()

for key in user.ssh_keys.list():
    print(key.label, key.fingerprint)

user.ssh_keys.create(SshKeyCreate(key="ssh-ed25519 AAAA...", label="Work"), expires_on="2027-01-01")
user.gpg_keys.delete("A1B2C3D4E5F6A7B8")
```

### Code search

`ws.search`, `client.users(selected_user).search` and
`client.teams(username).search` search code across an account's repositories.
The query is required and uses the UI's syntax; code search must be turned on
at <https://bitbucket.org/search>, and Bitbucket deprecates these routes on
2026-11-01:

```python
for result in client.workspace("acme").search.code("foo repo:demo", pagelen=50):
    print(result.file.path if result.file else None, result.content_match_count)
```

### Async client

`AsyncBitbucketClient` mirrors the sync client one-for-one — same
`email`/`api_token`/`access_token`/`options`, same `workspace()`, `default_workspace()`,
`users()`, `teams()`, `.user`, same resource tree (`.pull_requests`, `.refs`, `.source`,
`.commits`, ...), and the same `merge_and_wait` polling helper. Single-shot
methods are `async def`; auto-paginating methods return `AsyncIterator`.

```python
from bitbucket import AsyncBitbucketClient
from bitbucket import MergeParameters

async with AsyncBitbucketClient() as client:
    repository = client.default_workspace().repository("my-repo")

    async for pull_request in repository.pull_requests.list(state="OPEN"):
        print(pull_request.id, pull_request.title)

    diff = await repository.pull_requests.diff(pull_request.id)

    status = await repository.pull_requests.merge_and_wait(
        pull_request.id,
        MergeParameters(merge_strategy="squash"),
    )
    print(status.task_status)
```

`BasicAuth`, `BearerAuth` and the credential-resolution rules (provider, env
vars, deprecated `ATLASSIAN_API_KEY`) are shared between the sync and async
clients, so the credential tests in [`docs/sdk/credential-tests.md`][sdk-credential-tests]
apply to both.

## Configuration

| Variable                 | Where it's read                       | Default        | Description                                                      |
| ------------------------ | ------------------------------------- | -------------- | ---------------------------------------------------------------- |
| `ATLASSIAN_USER_EMAIL`   | `BitbucketClient()`                   | none           | Email of the Atlassian account, used for basic auth.             |
| `ATLASSIAN_API_TOKEN`    | `BitbucketClient()`                   | none           | API token, used for basic auth.                                  |
| `ATLASSIAN_API_KEY`      | `BitbucketClient()`                   | none           | Deprecated name of `ATLASSIAN_API_TOKEN`; emits a warning.       |
| `BITBUCKET_ACCESS_TOKEN` | `BitbucketClient()`                   | none           | Bearer access token; no email is required.                       |
| `BITBUCKET_WORKSPACE`    | `BitbucketClient.default_workspace()` | none           | Workspace slug used by `default_workspace()`.                    |

The names are exported as `EMAIL_ENV_VAR`, `API_TOKEN_ENV_VAR`,
`ACCESS_TOKEN_ENV_VAR` and `WORKSPACE_ENV_VAR`, so an application does not
have to repeat the strings.

## Origin

Extracted from a larger internal toolkit's Bitbucket provider module, which
had grown the whole project's maintenance surface. That toolkit keeps the
provider-neutral pull-request seam (models, protocol, registry) and
review-workflow logic (comment filtering and threading, reviewer-queue
aggregation); this SDK carries only the Bitbucket wire client.

## Contributing

See [`CONTRIBUTING.md`][contributing].

## Open items

- Snippets are not yet modeled, and the three Connect `Addon` operations
  cannot be called with Basic or Bearer credentials (they need JWT or a Forge
  app) — see [`docs/api/endpoint-coverage.md`][api-endpoint-coverage] for
  the full endpoint matrix and [`docs/api/roadmap.md`][api-roadmap] for the
  phased plan to full API parity.

## License

MIT — see [`LICENSE`][license].

[architecture]: https://github.com/gajaguar/bitbucket-sdk/blob/main/docs/architecture/index.md
[api-recipes]: https://github.com/gajaguar/bitbucket-sdk/blob/main/docs/api/recipes.md
[architecture-project-layout]: https://github.com/gajaguar/bitbucket-sdk/blob/main/docs/architecture/project-layout.md
[api-roadmap]: https://github.com/gajaguar/bitbucket-sdk/blob/main/docs/api/roadmap.md
[sdk-credential-contract]: https://github.com/gajaguar/bitbucket-sdk/blob/main/docs/sdk/credential-contract.md
[sdk-credential-tests]: https://github.com/gajaguar/bitbucket-sdk/blob/main/docs/sdk/credential-tests.md
[sdk-credentials]: https://github.com/gajaguar/bitbucket-sdk/blob/main/docs/sdk/credentials.md
[api-endpoint-coverage]: https://github.com/gajaguar/bitbucket-sdk/blob/main/docs/api/endpoint-coverage.md
[contributing]: https://github.com/gajaguar/bitbucket-sdk/blob/main/CONTRIBUTING.md
[license]: https://github.com/gajaguar/bitbucket-sdk/blob/main/LICENSE
