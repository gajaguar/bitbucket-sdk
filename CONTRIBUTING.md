# Contributing

Thanks for considering a contribution. Bug reports, feature ideas,
documentation fixes, and code are all welcome.

## Ways to contribute

- Report a bug or propose a feature by opening a GitHub issue. For a bug,
  include the steps to reproduce it and what you expected to happen.
- Fix or extend documentation under `docs/`.
- Submit a pull request for a bug fix or a new feature. For anything larger
  than a small fix, open an issue first so the approach can be agreed before
  you invest time in it.

## Set up

[mise](https://mise.jdx.dev) pins the toolchain in `mise.toml`: Python 3.14,
uv, node, pnpm, pre-commit and checkmake. Install it, then run:

```bash
mise install
make install
```

`make install` syncs the Python dependencies, installs the node tooling and
registers the pre-commit hook. Run `make help` for the full list of targets.

`mise.toml` forces `uv` onto the mise-provided interpreter, so
`.python-version` is intentionally absent; see
[`docs/python/interpreter-source.md`](docs/python/interpreter-source.md).

## Before opening a pull request

Run the gate and the tests; both MUST pass:

```bash
make check
make test
```

`make fix` applies the safe automatic fixes for what `make check` reports.
[`python.yml`](.github/workflows/python.yml) runs the same targets on every
push to `main` and every pull request, and blocks the merge when either
fails.

To add a Bitbucket endpoint, follow
[`docs/architecture/adding-an-endpoint.md`](docs/architecture/adding-an-endpoint.md).

## Commits and branches

- Commit messages follow
  [Conventional Commits](https://www.conventionalcommits.org/).
- Branch names follow
  [Conventional Branch](https://conventionalbranch.org/):
  `<type>/<description>`, for example `feat/add-login` or
  `fix/normalize-description-grammar`. The branch type is one of `feat`,
  `fix`, `hotfix`, `release`, or `chore`; documentation work uses `chore/`.

A pre-commit hook and `make commits-check` enforce both; see
[`docs/conventions/commits-check.md`](docs/conventions/commits-check.md).

## Documentation

`docs/` is a bundle of atomic notes: one concept per file. A new note is
added to its directory's `index.md` and to [`docs/log.md`](docs/log.md) in
the same pull request. Read [`AGENTS.md`](AGENTS.md) for the rules that apply
to both people and coding agents working in this repository.

## License

By contributing, you agree that your contribution is licensed under the
project's license; see [LICENSE](LICENSE).
