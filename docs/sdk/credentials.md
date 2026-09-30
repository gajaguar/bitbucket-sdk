---
type: reference
title: Bitbucket credentials
description: The basic and bearer credentials the SDK accepts, their environment variables, and where tokens are created.
tags: [sdk, auth]
status: stable
---

# Bitbucket credentials

The SDK follows the [credential contract](credential-contract.md). This note
holds the values and authentication schemes that belong to Bitbucket Cloud.

## Basic credentials

* **Credential:** the email of an Atlassian account and an API token.
* **Arguments:** `BitbucketClient(email=..., api_token=...)`. The token is a
  string or an `ApiTokenProvider` callable.
* **Environment variables:** `ATLASSIAN_USER_EMAIL` and
  `ATLASSIAN_API_TOKEN`, exported as `EMAIL_ENV_VAR` and `API_TOKEN_ENV_VAR`.
  `ATLASSIAN_API_KEY` is the former name of the token variable. It still works
  with a `DeprecationWarning`, and `ATLASSIAN_API_TOKEN` wins when both are
  set.
* **Header:** `Authorization: Basic`, built by `BasicAuth` in
  `src/bitbucket/_auth.py` from the email and the token.
* **Where it is created:** Account settings → Security → Create and manage API
  tokens → Create API token with scopes. Choose Bitbucket and the scopes the
  code needs. Atlassian shows the token once and it expires on the date chosen
  at creation.

## Bearer credentials

* **Credential:** a repository, project, or workspace access token, or an OAuth
  access token. The application obtains the token; the SDK only sends it.
* **Argument:** `BitbucketClient(access_token=...)`. The value is a string or
  an `AccessTokenProvider` callable, invoked on every request.
* **Environment variable:** `BITBUCKET_ACCESS_TOKEN`, exported as
  `ACCESS_TOKEN_ENV_VAR`.
* **Resolver:** `resolve_access_token` in `src/bitbucket/config.py`, composed by
  `resolve_credentials`.
* **Header:** `Authorization: Bearer`, built by `BearerAuth` in
  `src/bitbucket/_auth.py`.
* **Where it is created:** repository, project, or workspace settings → Access
  tokens, or the application's OAuth flow.

When both credential kinds are available, the kind with the strongest source
wins: a provider (3), an explicit string argument (2), then an environment
variable (1). Two kinds at the same explicit rank are ambiguous and raise
`ConfigurationError`. When both kinds are available only through the
environment, the bearer token wins. The resolver only reads or warns for the
kind that wins.

## Shared behavior

* **App passwords:** removed by Atlassian on 2026-07-28. They no longer work.
* **Errors:** `MissingCredentialsError` when no source has a value,
  `AuthenticationError` for a `401` and `ForbiddenError` for a `403`.
* **Protection:** providers are called for each request, empty provider values
  raise `MissingCredentialsError`, and credential values are excluded from
  client configuration representations and debug logs.
