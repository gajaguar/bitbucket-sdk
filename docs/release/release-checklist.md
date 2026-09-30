---
type: playbook
title: Release checklist
description: What to verify before tagging a release.
tags: [release]
status: stable
---

# Release checklist

CI ([`python.yml`](../../.github/workflows/python.yml)) runs `make check` and
`make test` on every push to `main` and every pull request. Before tagging a
release:

1. Bump the version in `pyproject.toml` and `src/bitbucket/_version.py`
   following [Semantic Versioning](https://semver.org/): while the SDK is
   `0.y.z`, a new feature or a breaking change bumps the minor version, and a
   fix or a change that leaves the API alone bumps the patch.
2. `make check` and `make test` — both must exit 0, and the 90% coverage gate
   must pass.
3. `make build` — must produce a valid sdist and wheel, and
   `uvx twine check dist/*` must accept the README.
4. Confirm [endpoint coverage](../api/endpoint-coverage.md) reflects the
   endpoints actually shipped in this version.
5. Publish a GitHub Release from tag `vX.Y.Z`, then approve the `pypi`
   environment so [`publish.yml`](../../.github/workflows/publish.yml)
   uploads it — see
   [PyPI Trusted Publishing](../release/pypi-trusted-publishing.md).
