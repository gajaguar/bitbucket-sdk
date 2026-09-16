from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from os import environ
from typing import TYPE_CHECKING
from typing import Final

from bitbucket._version import __version__
from bitbucket.errors import ConfigurationError
from bitbucket.errors import MissingCredentialsError
from bitbucket.retry import RetryPolicy

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

EMAIL_ENV_VAR: Final = "ATLASSIAN_USER_EMAIL"
API_KEY_ENV_VAR: Final = "ATLASSIAN_API_KEY"
WORKSPACE_ENV_VAR: Final = "BITBUCKET_WORKSPACE"

DEFAULT_BASE_URL: Final = "https://api.bitbucket.org/2.0"


@dataclass(frozen=True, slots=True)
class ClientConfig:
    email: str
    api_token: str
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


def resolve_credentials(email: str | None, api_token: str | None) -> tuple[str, str]:
    resolved_email = email or environ.get(EMAIL_ENV_VAR)
    if not resolved_email:
        message = f"No email provided. Pass email=... or set the {EMAIL_ENV_VAR} environment variable."
        raise MissingCredentialsError(message)
    resolved_token = api_token or environ.get(API_KEY_ENV_VAR)
    if not resolved_token:
        message = f"No API token provided. Pass api_token=... or set the {API_KEY_ENV_VAR} environment variable."
        raise MissingCredentialsError(message)
    return resolved_email, resolved_token


def resolve_workspace(workspace: str | None) -> str:
    resolved = workspace or environ.get(WORKSPACE_ENV_VAR)
    if not resolved:
        message = f"No workspace provided. Pass workspace=... or set the {WORKSPACE_ENV_VAR} environment variable."
        raise ConfigurationError(message)
    return resolved
