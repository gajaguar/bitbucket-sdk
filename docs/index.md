---
okf_version: "0.2"
---

# Documentation

This is an [Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
(OKF) bundle: one Markdown concept per file, each with YAML frontmatter, laid
out under this directory.

## Reference

* [Conventions](conventions/index.md) - commit and branch naming, and how
  they're enforced.
* [Toolchain](toolchain/index.md) - which layer (mise or an ecosystem
  package manager) installs which tool, and why.

See [`log.md`](log.md) for the bundle's change history.

## SDK

* [SDK](sdk/index.md) - the credential contract the SDK follows and the
  tests that prove it.
* [Architecture](architecture/index.md) - how the client is layered and how
  an endpoint is added.
* [API](api/index.md) - endpoint coverage and the roadmap to full parity.

## Release

* [Release](release/index.md) - how this project ships new versions to
  PyPI.

## Python

* [Python](python/index.md) - the interpreter source and the
  `pyproject.toml` settings left out on purpose.
