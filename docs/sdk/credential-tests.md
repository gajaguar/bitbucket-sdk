---
type: rule
title: Credential tests
description: Every SDK carries a fixed set of tests for how it resolves, sends and hides a credential.
tags: [sdk, auth, testing]
status: stable
---

# Credential tests

Every SDK carries these tests, so a change to credential handling that
breaks the [credential contract](credential-contract.md) fails a test.

## Resolution

* An explicit argument wins over the environment variable.
* The environment variable is the fallback.
* A missing credential raises `MissingCredentialsError`, and the message
  names the environment variable and where to create the credential.
* A provider is returned unchanged.
* A provider wins over the environment variable.
* When a variable was renamed, the old name works and emits a deprecation
  warning, and the new name wins when both are set.

## Selection

Only for an SDK that accepts more than one kind of credential.

* An explicit kind beats the other kind's environment variable.
* Two explicit kinds raise `ConfigurationError`.
* Two kinds available only through the environment raise
  `ConfigurationError`.
* A kind with a missing part does not count as available.

## Sending

* The authentication header reaches the request.
* A redirect followed to another origin does not carry the authentication
  header.
* A provider is not called until the first request.
* A provider is called on every request.
* A provider that returns an empty value raises `MissingCredentialsError`.

## Hiding

* The text representation of the configuration object does not contain the
  secret.
* The debug log of a request does not contain the secret.

## Surface

* The environment variable constants, the provider type,
  `MissingCredentialsError`, `AuthenticationError` and `ForbiddenError` are
  exported from the package.
