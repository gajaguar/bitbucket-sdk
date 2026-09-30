---
type: playbook
title: Release checklist
description: What to verify before tagging a release.
tags: [architecture, release]
status: stable
---

# Release checklist

CI ([`python.yml`](../../.github/workflows/python.yml)) runs `make check` and
`make test` on every push to `main` and every pull request. Before tagging a
release:

1. Bump the version in `pyproject.toml` and `src/bitbucket/_version.py`
   following [Semantic Versioning](https://semver.org/): while the SDK is
   `0.y.z`, a breaking change bumps the minor version and anything else bumps
   the patch.
2. `make check` and `make test` — both must exit 0, and the 90% coverage gate
   must pass.
3. `make build` — must produce a valid sdist and wheel.
4. Confirm [endpoint coverage](../api/endpoint-coverage.md) reflects the
   endpoints actually shipped in this version.
5. Tag `vX.Y.Z` and publish the GitHub release.
