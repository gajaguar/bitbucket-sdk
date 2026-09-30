---
type: reference
title: Differences between the SDKs
description: Where this SDK and clockify-sdk intentionally differ in credentials and surface, after aligning the credential contract, selection rule and tests.
tags: [sdk, auth]
status: stable
---

# Differences between the SDKs

`bitbucket-sdk` and `clockify-sdk` share the
[credential contract](credential-contract.md), the
[credential tests](credential-tests.md), the error names and the rule for
[choosing between credential kinds](credential-contract.md#choosing-between-credential-kinds).
These differences remain because the services differ.

* **Credential kinds:** `bitbucket-sdk` takes basic credentials (email plus
  API token) or a bearer access token; `clockify-sdk` takes an API key or an
  add-on token.
* **Parts of a kind:** basic has two parts and both must be available; each
  `clockify-sdk` kind is one value.
* **Header:** `Authorization: Basic` or `Authorization: Bearer`, against
  `X-Api-Key` or `X-Addon-Token`.
* **Credential object:** `bitbucket-sdk` returns `BasicCredentials` or
  `BearerCredentials` and `auth_for` turns it into an `httpx.Auth`;
  `clockify-sdk` returns a tuple of the two optional values.
* **Renamed variable:** `ATLASSIAN_API_KEY` still works with a
  `DeprecationWarning`; `clockify-sdk` has none.
* **Async client:** `AsyncBitbucketClient` in `bitbucket.aio`; `clockify-sdk`
  has none yet (its issue 19).
* **Scope of a client:** a workspace slug, against a region and a workspace
  ID.
