---
type: decision
title: Why the SDK does not acquire credentials
description: The SDK reads credentials from an argument, a provider or the environment, and leaves obtaining and storing them to the application.
tags: [sdk, auth]
status: stable
generated: { by: claude-code/claude-sonnet-5-5, at: 2026-09-29T00:00:00Z }
sources:
  - id: python-gitlab-config
    resource: https://python-gitlab.readthedocs.io/en/stable/cli-usage.html
    title: python-gitlab configuration
    author: team:python-gitlab
  - id: boto3-credentials
    resource: https://docs.aws.amazon.com/boto3/latest/guide/credentials.html
    title: Boto3 credentials
    author: team:aws
  - id: workos-cli-auth
    resource: https://workos.com/blog/best-practices-for-cli-authentication-a-technical-guide
    title: Best practices for CLI authentication
    author: team:workos
---

# Why the SDK does not acquire credentials

The SDK reads a credential from a provider, an argument or an environment
variable, and nothing else. The application that uses the SDK asks the
person for the credential, checks it, and decides where to keep it.

## Alternatives

* **Keyring or keychain inside the SDK.** Ties a library to an operating
  system service. A server or a container has no keyring.
* **A credentials file inside the SDK.** Fits a library that ships its own
  command-line tool, as python-gitlab does.[^python-gitlab-config] It does
  not fit a library that does not.
* **A long chain of sources, as boto3 has.** The chain covers cloud
  environments that these services do not have.[^boto3-credentials]
* **An OAuth flow or prompts inside the SDK.** Needs a browser or a
  terminal, and a redirect address the SDK cannot know.

## What the application does

A command-line tool keeps the secret in the operating system keychain,
falls back to a file with owner-only permissions, and lets an environment
variable override both for continuous integration.[^workos-cli-auth] It
passes the resolved value to the SDK as an argument or a provider.

## Consequences

* The SDK has one job: turn what it receives into request headers.
* Adding a credential type means adding an authentication class.
* Two SDKs behave the same way, because neither has a source the other
  lacks.

[^python-gitlab-config]: python-gitlab configuration
[^boto3-credentials]: Boto3 credentials
[^workos-cli-auth]: Best practices for CLI authentication
