---
type: reference
title: Bitbucket credential
description: The names the SDK uses for the Bitbucket email and API token, and where the token is created.
tags: [sdk, auth]
status: stable
---

# Bitbucket credential

The SDK follows the [credential contract](credential-contract.md). This note
holds the values that belong to Bitbucket Cloud.

* **Credential:** the email of an Atlassian account and an API token.
* **Arguments:** `BitbucketClient(email=..., api_token=...)`. The token is a
  string or a provider.
* **Environment variables:** `ATLASSIAN_USER_EMAIL` and
  `ATLASSIAN_API_TOKEN`, exported as `EMAIL_ENV_VAR` and `API_TOKEN_ENV_VAR`.
  `ATLASSIAN_API_KEY` is the former name of the token variable. It still
  works with a `DeprecationWarning`, and `ATLASSIAN_API_TOKEN` wins when both
  are set.
* **Provider type:** `ApiTokenProvider`.
* **Resolvers:** `resolve_email` and `resolve_api_token` in
  `src/bitbucket/config.py`, composed by `resolve_credentials`.
* **Header:** `Authorization: Basic`, built by `BasicAuth` in
  `src/bitbucket/_auth.py` from the email and the token.
* **Where it is created:** Account settings → Security → Create and manage API
  tokens → Create API token with scopes. Choose Bitbucket and the scopes the
  code needs. Atlassian shows the token once and it expires on the date chosen
  at creation.
* **App passwords:** removed by Atlassian on 2026-07-28. They no longer work.
* **Errors:** `MissingCredentialsError` when no source has a value,
  `AuthenticationError` for a `401` and `ForbiddenError` for a `403`.
