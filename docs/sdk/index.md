# SDK

How this SDK reads, protects and tests the credentials its callers give it.

* [Bitbucket credential](credentials.md) - The names the SDK uses for the
  Bitbucket email and API token, and where the token is created.
* [Credential contract](credential-contract.md) - The SDK reads a credential
  from a provider, an argument or an environment variable, in that order, and
  keeps it out of logs and output.
* [Why the SDK does not acquire credentials](credential-sources.md) - The SDK
  reads credentials from an argument, a provider or the environment, and
  leaves obtaining and storing them to the application.
* [Credential tests](credential-tests.md) - Every SDK carries a fixed set of
  tests for how it resolves, sends and hides a credential.
