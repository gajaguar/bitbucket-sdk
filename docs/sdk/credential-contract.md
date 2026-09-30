---
type: convention
title: Credential contract
description: The SDK reads a credential from a provider, an argument or an environment variable, in that order, and keeps it out of logs and output.
tags: [sdk, auth]
status: stable
sources:
  - id: openai-python-client
    resource: https://www.mintlify.com/openai/openai-python/concepts/client
    title: openai-python client
    author: team:openai
  - id: boto3-credentials
    resource: https://docs.aws.amazon.com/boto3/latest/guide/credentials.html
    title: Boto3 credentials
    author: team:aws
---

# Credential contract

An SDK resolves the credentials its caller supplies and does not obtain or
store them — see [`credential-sources.md`](credential-sources.md). This
note fixes how the SDK resolves them, so every SDK behaves the same way.

## Sources and precedence

For each secret value, the SDK returns the first source that has a
value:[^openai-python-client]

1. A provider: a zero-argument function passed in place of the value.
2. An explicit argument.
3. An environment variable.

When no source has a value, the SDK raises a `MissingCredentialsError`. A
documented, fixed order matters more than the number of sources: the
caller can predict which value wins.[^boto3-credentials]

## Choosing between credential kinds

An SDK that accepts more than one kind of credential, such as a key and a
token, uses exactly one kind per client. A kind is available when the caller
supplied all its parts, explicitly or through the environment. An
explicit argument or provider is stronger than an environment variable.

* An explicit kind beats the other kind's environment variable.
* Two explicit kinds raise `ConfigurationError`.
* Two kinds available only through the environment raise `ConfigurationError`.
* No available kind raises `MissingCredentialsError`.

The SDK never guesses between two kinds of the same strength: acting as the
wrong identity is worse than an error. It reads or warns only about the
environment variables of the kind it picks.

## The provider

A provider is called on every request, inside the authentication step, and
its result is never cached. A rotating or externally managed secret is
therefore always current. A provider that returns an empty value raises
`MissingCredentialsError`.

## The missing-credential error

The message states three things: the argument to pass, the environment
variable to set, and where in the service's web interface the credential is
created.

## Configuration object

The configuration object is immutable. Each secret field is excluded from
its text representation, with a comment that says why, so a traceback or a
log line that captures the object does not print the secret.

## Environment variable names

Each variable name is a constant exported from the package, together with
the provider type. An application reads the constant instead of repeating
the string. When a variable is renamed, the old name keeps working, emits a
deprecation warning, and loses to the new name when both are set.

## Authentication is injected

The client builds one authentication object and passes it to the transport.
A new credential type arrives as another authentication class, and the
transport does not change.

## Logging

The transport logs only the method, the path, the status and the elapsed
time. It never logs headers or the configuration object.

## README

The README's Authentication section carries:

* An example for the environment variable, the explicit argument and the
  provider.
* The sources in order of precedence.
* A "Getting a credential" list with the steps in the service's web
  interface.
* A "What the SDK does not do" paragraph: no keyring, no password manager,
  no OAuth flow and no prompts.

The Configuration section lists every environment variable, and the
Security section says to rotate a credential that is exposed.

[^openai-python-client]: openai-python client
[^boto3-credentials]: Boto3 credentials

## Python

The Python names for the contract, with `<secret>` standing for the name of
the credential, such as `api_key` or `api_token`:

* `resolve_<secret>` in `config.py` returns the provider, the argument or the
  environment value, in that order.
* `<SECRET>_ENV_VAR` and `<Secret>Provider` are exported from the package.
* The configuration is a `dataclass(frozen=True, slots=True)`, and each secret
  field uses `field(repr=False)`.
* The authentication class in `_auth.py` is an `httpx.Auth` subclass. The
  client builds it and passes it to `Transport`.
* The tests live in `tests/`, in files named after the module they cover, and
  carry the cases in [`credential-tests.md`](credential-tests.md).
