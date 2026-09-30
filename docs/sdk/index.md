# SDK

How this SDK reads, protects and tests the credentials its callers give it.

* [Bitbucket credentials](credentials.md) - The basic and bearer credentials
  the SDK accepts, their environment variables, and where tokens are created.
* [Credential contract](credential-contract.md) - The SDK reads a credential
  from a provider, an argument or an environment variable, in that order, and
  keeps it out of logs and output.
* [Why the SDK does not acquire credentials](credential-sources.md) - The SDK
  reads credentials from an argument, a provider or the environment, and
  leaves obtaining and storing them to the application.
* [Differences between the SDKs](sdk-differences.md) - Where this SDK and
  `clockify-sdk` intentionally differ in credentials and surface.
* [Credential tests](credential-tests.md) - Every SDK carries a fixed set of
  tests for how it resolves, sends and hides a credential.
