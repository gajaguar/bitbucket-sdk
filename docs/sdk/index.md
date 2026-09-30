# SDK

How this SDK reads, protects and tests the credentials its callers give it.

* [Bitbucket credential](credentials.md) - the names the SDK uses for the
  email and the API token, and where the token is created.
* [Credential contract](credential-contract.md) - the sources the SDK reads
  a credential from, their order, and how the credential stays out of logs
  and output.
* [Why the SDK does not acquire credentials](credential-sources.md) - the
  decision to read credentials, not to obtain or store them, with the
  alternatives it rejected.
* [Credential tests](credential-tests.md) - the tests every SDK carries to
  prove the contract.
