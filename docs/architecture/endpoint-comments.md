---
type: rule
title: Endpoint comments
description: Every resource method names the Bitbucket endpoint it calls in a comment, since docstrings are not allowed.
tags: [architecture]
status: stable
---

# Endpoint comments

`pylint-gajaguar`'s `gajaguar-no-docstrings` checker fails `make check` on any
docstring, so there is no docstring-based endpoint reference. Every resource
method carries a `# METHOD /path` comment directly above its `def` naming the
exact Bitbucket endpoint it calls.
