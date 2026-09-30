from __future__ import annotations

from base64 import b64encode
from logging import DEBUG
from typing import TYPE_CHECKING

import pytest
import respx
from httpx import Response

from bitbucket.aio.client import AsyncBitbucketClient
from bitbucket.config import ClientOptions
from bitbucket.errors import AuthenticationError
from bitbucket.errors import ConfigurationError
from bitbucket.errors import MissingCredentialsError
from bitbucket.retry import NO_RETRY
from bitbucket.retry import CqsKind
from tests.conftest import BASE_URL

if TYPE_CHECKING:
    from bitbucket.aio._transport import AsyncTransport


def _basic_auth_header(email: str, api_token: str) -> str:
    return "Basic " + b64encode(f"{email}:{api_token}".encode()).decode()


@respx.mock
async def test_async_client_prefers_explicit_credentials_over_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "env@b.com")
    monkeypatch.setenv("ATLASSIAN_API_TOKEN", "env-tok")
    route = respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json={}))
    # Act
    async with AsyncBitbucketClient(
        email="explicit@b.com",
        api_token="explicit-tok",  # ruff: ignore[hardcoded-password-func-arg]
        options=ClientOptions(retry=NO_RETRY),
    ) as client:
        await client.user.me()
    # Assert
    assert route.calls[0].request.headers["Authorization"] == _basic_auth_header("explicit@b.com", "explicit-tok")


@respx.mock
async def test_async_client_falls_back_to_environment_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.setenv("ATLASSIAN_USER_EMAIL", "env@b.com")
    monkeypatch.setenv("ATLASSIAN_API_TOKEN", "env-tok")
    route = respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json={}))
    # Act
    async with AsyncBitbucketClient(options=ClientOptions(retry=NO_RETRY)) as client:
        await client.user.me()
    # Assert
    assert route.calls[0].request.headers["Authorization"] == _basic_auth_header("env@b.com", "env-tok")


def test_async_client_without_credentials_raises_missing_credentials_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.delenv("ATLASSIAN_USER_EMAIL", raising=False)
    monkeypatch.delenv("ATLASSIAN_API_TOKEN", raising=False)
    monkeypatch.delenv("ATLASSIAN_API_KEY", raising=False)
    monkeypatch.delenv("BITBUCKET_ACCESS_TOKEN", raising=False)
    # Act
    # Assert
    with pytest.raises(MissingCredentialsError, match="ATLASSIAN_USER_EMAIL"):
        AsyncBitbucketClient()


@respx.mock
async def test_async_client_sends_a_bearer_token() -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json={}))
    # Act
    async with AsyncBitbucketClient(
        access_token="access-token",  # ruff: ignore[hardcoded-password-func-arg]
        options=ClientOptions(retry=NO_RETRY),
    ) as client:
        await client.user.me()
    # Assert
    assert route.calls[0].request.headers["Authorization"] == "Bearer access-token"


@respx.mock
async def test_async_client_does_not_retry_a_bearer_authentication_failure() -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/user").mock(return_value=Response(401, json={"type": "error"}))
    # Act
    # Assert
    with pytest.raises(AuthenticationError):
        async with AsyncBitbucketClient(
            access_token="access-token",  # ruff: ignore[hardcoded-password-func-arg]
            options=ClientOptions(retry=NO_RETRY),
        ) as client:
            await client.user.me()
    assert route.call_count == 1


@respx.mock
async def test_async_client_sends_the_default_user_agent(aclient: AsyncBitbucketClient) -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json={}))
    # Act
    await aclient.user.me()
    # Assert
    assert route.calls[0].request.headers["User-Agent"].startswith("bitbucket-unofficial-sdk/")


@respx.mock
async def test_async_client_uses_the_base_url_option_for_every_request() -> None:
    # Arrange
    custom_base_url = "https://bitbucket.example.com/2.0"
    route = respx.get(f"{custom_base_url}/user").mock(return_value=Response(200, json={"uuid": "{abc}"}))
    # Act
    async with AsyncBitbucketClient(
        email="a@b.com",
        api_token="tok",  # ruff: ignore[hardcoded-password-func-arg]
        options=ClientOptions(base_url=custom_base_url, retry=NO_RETRY),
    ) as client:
        user = await client.user.me()
    # Assert
    assert user.uuid == "{abc}"
    assert route.called


async def test_async_default_workspace_reads_the_workspace_environment_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.setenv("BITBUCKET_WORKSPACE", "env-ws")
    client = AsyncBitbucketClient(
        email="a@b.com",
        api_token="tok",  # ruff: ignore[hardcoded-password-func-arg]
        options=ClientOptions(retry=NO_RETRY),
    )
    # Act
    workspace = client.default_workspace()
    # Assert
    assert workspace.slug == "env-ws"
    await client.aclose()


async def test_async_default_workspace_without_environment_variable_raises_configuration_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.delenv("BITBUCKET_WORKSPACE", raising=False)
    client = AsyncBitbucketClient(
        email="a@b.com",
        api_token="tok",  # ruff: ignore[hardcoded-password-func-arg]
        options=ClientOptions(retry=NO_RETRY),
    )
    # Act
    # Assert
    with pytest.raises(ConfigurationError, match="BITBUCKET_WORKSPACE"):
        client.default_workspace()
    await client.aclose()


async def test_async_workspace_returns_a_client_for_the_given_slug(aclient: AsyncBitbucketClient) -> None:  # ruff: ignore[unused-async]
    # Arrange
    slug = "my-ws"
    # Act
    workspace = aclient.workspace(slug)
    # Assert
    assert workspace.slug == slug


@respx.mock
async def test_async_provider_yields_a_fresh_token_per_request() -> None:
    # Arrange
    tokens = iter(["first", "second"])
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json={}))
    # Act
    async with AsyncBitbucketClient(
        email="a@b.com",
        api_token=lambda: next(tokens),  # type: ignore[arg-type,return-value]
        options=ClientOptions(retry=NO_RETRY),
    ) as client:
        await client.user.me()
        await client.user.me()
    # Assert
    headers = [call.request.headers["Authorization"] for call in respx.calls]
    assert headers == [
        _basic_auth_header("a@b.com", "first"),
        _basic_auth_header("a@b.com", "second"),
    ]


@respx.mock
async def test_async_provider_is_deferred_until_the_first_request() -> None:  # pylint: disable=gajaguar-test-no-blank-lines
    # fmt: off
    # Arrange
    state = {"calls": 0}
    def _provider() -> str:  # ruff: ignore[blank-lines-before-nested-definition]
        state["calls"] += 1
        return "tok"
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json={}))
    # Act
    async with AsyncBitbucketClient(
        email="a@b.com",
        api_token=_provider,  # type: ignore[arg-type]
        options=ClientOptions(retry=NO_RETRY),
    ) as client:
        pre_call = dict(state)
        await client.user.me()
        post_call = dict(state)
    # Assert
    assert pre_call == {"calls": 0}
    assert post_call == {"calls": 1}
    # fmt: on


@respx.mock
async def test_async_empty_provider_raises_missing_credentials_error() -> None:
    # Arrange
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json={}))
    # Act
    # Assert
    async with AsyncBitbucketClient(
        email="a@b.com",
        api_token=lambda: "",  # type: ignore[arg-type,return-value]
        options=ClientOptions(retry=NO_RETRY),
    ) as client:
        with pytest.raises(MissingCredentialsError, match="empty value"):
            await client.user.me()


@respx.mock
async def test_async_context_manager_exit_stops_requests_from_being_sent() -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json={}))
    entered: AsyncBitbucketClient | None = None
    async with AsyncBitbucketClient(
        email="a@b.com",
        api_token="tok",  # ruff: ignore[hardcoded-password-func-arg]
        options=ClientOptions(retry=NO_RETRY),
    ) as client:
        entered = client
    # Act
    # Assert
    assert entered is not None
    with pytest.raises(RuntimeError, match="has been closed"):
        await entered.user.me()
    assert not route.called


@respx.mock
async def test_async_debug_log_never_contains_the_bearer_token(caplog: pytest.LogCaptureFixture) -> None:
    # Arrange
    secret = "bearer-secret"  # ruff: ignore[hardcoded-password-string]
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json={}))
    # Act
    with caplog.at_level(DEBUG, logger="bitbucket"):
        async with AsyncBitbucketClient(
            access_token=secret,
            options=ClientOptions(retry=NO_RETRY),
        ) as client:
            await client.user.me()
    # Assert
    assert caplog.records
    assert secret not in caplog.text


@respx.mock
async def test_async_debug_log_never_contains_the_api_token(
    atransport: AsyncTransport,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Arrange
    respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json={}))
    # Act
    with caplog.at_level(DEBUG, logger="bitbucket"):
        await atransport.request("GET", "/user", kind=CqsKind.QUERY)
    # Assert
    assert caplog.records
    assert "tok" not in caplog.text
    assert "a@b.com" not in caplog.text
