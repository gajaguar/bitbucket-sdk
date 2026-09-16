# Bitbucket Unofficial SDK

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> **Unofficial.** This project is not affiliated with, endorsed by, or
> supported by Atlassian. "Bitbucket" is a trademark of Atlassian. Use at your
> own risk against the
> [Bitbucket Cloud REST API](https://developer.atlassian.com/cloud/bitbucket/rest/intro/).

Typed, synchronous Python SDK for the Bitbucket Cloud REST API's pull-request
surface.

## Requirements

- [mise](https://mise.jdx.dev) — pins the toolchain (`mise.toml`: Python 3.14,
  uv, node, pnpm, pre-commit, checkmake); run `mise install`, then
  `make install`

## Usage

```bash
make install   # sync Python deps, install node tooling, install pre-commit hook
make check     # read-only gate: lint, format-check, mypy, pyright,
               # md-lint, spell, pylint
make fix       # apply safe auto-fixes (format, ruff --fix, markdownlint --fix)
make test      # run the test suite
```

Run `make help` for the full target list.
