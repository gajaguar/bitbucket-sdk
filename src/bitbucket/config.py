from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from os import environ
from typing import TYPE_CHECKING
from typing import Final
from warnings import warn

from bitbucket._version import __version__
from bitbucket.errors import ConfigurationError
from bitbucket.errors import MissingCredentialsError
from bitbucket.retry import RetryPolicy

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

EMAIL_ENV_VAR: Final = "ATLASSIAN_USER_EMAIL"
API_TOKEN_ENV_VAR: Final = "ATLASSIAN_API_TOKEN"  # ruff: ignore[hardcoded-password-string]
LEGACY_API_TOKEN_ENV_VAR: Final = "ATLASSIAN_API_KEY"  # ruff: ignore[hardcoded-password-string]
WORKSPACE_ENV_VAR: Final = "BITBUCKET_WORKSPACE"

DEFAULT_BASE_URL: Final = "https://api.bitbucket.org/2.0"

_CREATE_HINT: Final = "Create one under Atlassian account settings > Security > API tokens, with Bitbucket scopes."

# A caller-supplied callback invoked lazily on every request instead of a fixed string,
# so a rotating or externally-managed token never has to be baked into the client at
# construction time. The SDK never calls this itself outside the auth flow.
type ApiTokenProvider = Callable[[], str]  # pylint: disable=app-module-const-naming


@dataclass(frozen=True, slots=True)
class ClientConfig:
    email: str
    # repr=False: a dataclass repr would otherwise print the raw token into any traceback
    # or log line that captures this object.
    api_token: str | ApiTokenProvider = field(repr=False)
    base_url: str
    timeout: float = 30.0
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    user_agent: str = f"bitbucket-unofficial-sdk/{__version__}"
    event_hooks: dict[str, list[Callable[..., Any]]] | None = None


@dataclass(frozen=True, slots=True)
class ClientOptions:
    base_url: str | None = None
    timeout: float = 30.0
    retry: RetryPolicy | None = None
    event_hooks: dict[str, list[Callable[..., Any]]] | None = None


def resolve_email(explicit: str | None) -> str:
    resolved = explicit or environ.get(EMAIL_ENV_VAR)
    if not resolved:
        message = (
            f"No email provided. Pass email=... or set the {EMAIL_ENV_VAR} environment variable. "
            "Use the email of your Atlassian account."
        )
        raise MissingCredentialsError(message)
    return resolved


def resolve_api_token(explicit: str | ApiTokenProvider | None) -> str | ApiTokenProvider:
    # A provider is returned as-is; it is only invoked later, per request, by BasicAuth.
    if callable(explicit):
        return explicit
    if explicit:
        return explicit
    from_env = environ.get(API_TOKEN_ENV_VAR)
    if from_env:
        return from_env
    legacy = environ.get(LEGACY_API_TOKEN_ENV_VAR)
    if legacy:
        message = f"{LEGACY_API_TOKEN_ENV_VAR} is deprecated; set {API_TOKEN_ENV_VAR} instead."
        # Level 4 points at the caller of BitbucketClient(...): warn <- resolve_api_token <-
        # resolve_credentials <- BitbucketClient.__init__ <- caller.
        warn(message, DeprecationWarning, stacklevel=4)
        return legacy
    message = (
        f"No API token provided. Pass api_token=... or set the {API_TOKEN_ENV_VAR} environment variable. "
        f"{_CREATE_HINT}"
    )
    raise MissingCredentialsError(message)


def resolve_credentials(
    email: str | None,
    api_token: str | ApiTokenProvider | None,
) -> tuple[str, str | ApiTokenProvider]:
    return resolve_email(email), resolve_api_token(api_token)


def resolve_workspace(workspace: str | None) -> str:
    resolved = workspace or environ.get(WORKSPACE_ENV_VAR)
    if not resolved:
        message = f"No workspace provided. Pass workspace=... or set the {WORKSPACE_ENV_VAR} environment variable."
        raise ConfigurationError(message)
    return resolved
