---
type: decision
title: PyPI releases use Trusted Publishing
description: The publish workflow uploads to PyPI via OIDC trusted publishing triggered by a GitHub Release, not a long-lived API token.
tags: [release, ci]
status: stable
---

# PyPI releases use Trusted Publishing

Publishing a GitHub Release (`published` event) runs
[`.github/workflows/publish.yml`](../../.github/workflows/publish.yml): it
builds the sdist and wheel with `make build`, then uploads them with
[`pypa/gh-action-pypi-publish`](https://github.com/pypa/gh-action-pypi-publish)
under the `pypi` environment. The publish job authenticates with a
short-lived OIDC token instead of a stored `PYPI_API_TOKEN`, so no PyPI
secret exists anywhere in this repository.

## One-time PyPI-side setup

The PyPI project is `bitbucket-unofficial-sdk`, the `name` in
`pyproject.toml`, which differs from the repository name `bitbucket-sdk`.
Register this workflow as its trusted publisher
(`https://pypi.org/manage/project/bitbucket-unofficial-sdk/publishing/`, or
the "pending publisher" form under
`https://pypi.org/manage/account/publishing/` before the first upload):

* PyPI project name: `bitbucket-unofficial-sdk`
* Owner: `gajaguar`
* Repository name: `bitbucket-sdk`
* Workflow name: `publish.yml`
* Environment name: `pypi`

The repository's `pypi` environment deploys only from `v*` tags and requires
a reviewer, so a release only uploads after an explicit approval.
