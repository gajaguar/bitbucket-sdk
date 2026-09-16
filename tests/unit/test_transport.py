from __future__ import annotations

from typing import Final

import httpx
import pytest
import respx
from httpx import Response

from bitbucket._auth import BasicAuth  # ruff: ignore[import-private-name]
from bitbucket._transport import Transport  # ruff: ignore[import-private-name]
from bitbucket.config import ClientConfig
from bitbucket.errors import NotFoundError
from bitbucket.errors import ServerError
from bitbucket.errors import TransportError
from bitbucket.retry import NO_RETRY
from bitbucket.retry import CqsKind

BASE_URL: Final = "https://api.bitbucket.org/2.0"


def _transport(**overrides: object) -> Transport:
    defaults = {
        "email": "a@b.com",
        "api_token": "tok",
        "base_url": BASE_URL,
        "retry": NO_RETRY,
    }
    config = ClientConfig(**(defaults | overrides))  # type: ignore[arg-type]
    return Transport(config, BasicAuth(config.email, config.api_token))


@respx.mock
def test_request_sends_user_agent_header() -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/user").mock(return_value=Response(200, json={"ok": True}))
    transport = _transport(user_agent="test-agent/0.1")
    # Act
    data = transport.request("GET", "/user", kind=CqsKind.QUERY)
    # Assert
    assert data == {"ok": True}
    assert route.calls[0].request.headers["User-Agent"] == "test-agent/0.1"
    transport.close()


@respx.mock
def test_request_drops_none_valued_params() -> None:
    # Arrange
    route = respx.get(f"{BASE_URL}/thing").mock(return_value=Response(200, json={}))
    transport = _transport()
    # Act
    transport.request("GET", "/thing", kind=CqsKind.QUERY, params={"q": None, "pagelen": 10})
    # Assert
    assert "q" not in route.calls[0].request.url.params
    assert route.calls[0].request.url.params["pagelen"] == "10"
    transport.close()


@respx.mock
def test_request_returns_none_for_no_content_body() -> None:
    # Arrange
    respx.delete(f"{BASE_URL}/thing/1").mock(return_value=Response(204))
    transport = _transport()
    # Act
    result = transport.request("DELETE", "/thing/1", kind=CqsKind.IDEMPOTENT_COMMAND)
    # Assert
    assert result is None
    transport.close()


@respx.mock
def test_request_returns_empty_dict_for_empty_body() -> None:
    # Arrange
    respx.get(f"{BASE_URL}/thing").mock(return_value=Response(200, content=b""))
    transport = _transport()
    # Act
    result = transport.request("GET", "/thing", kind=CqsKind.QUERY)
    # Assert
    assert result == {}
    transport.close()


@respx.mock
def test_request_text_returns_raw_body() -> None:
    # Arrange
    respx.get(f"{BASE_URL}/diff").mock(return_value=Response(200, text="diff --git a b"))
    transport = _transport()
    # Act
    result = transport.request_text("GET", "/diff", kind=CqsKind.QUERY)
    # Assert
    assert result == "diff --git a b"
    transport.close()


@respx.mock
def test_not_found_status_raises_not_found_error() -> None:
    # Arrange
    respx.get(f"{BASE_URL}/missing").mock(return_value=Response(404, json={"error": {"message": "nope"}}))
    transport = _transport()
    # Act
    # Assert
    with pytest.raises(NotFoundError):
        transport.request("GET", "/missing", kind=CqsKind.QUERY)
    transport.close()


@respx.mock
def test_server_error_status_raises_server_error() -> None:
    # Arrange
    respx.get(f"{BASE_URL}/broken").mock(return_value=Response(500, text="boom"))
    transport = _transport()
    # Act
    # Assert
    with pytest.raises(ServerError):
        transport.request("GET", "/broken", kind=CqsKind.QUERY)
    transport.close()


@respx.mock
def test_invalid_json_body_raises_transport_error() -> None:
    # Arrange
    respx.get(f"{BASE_URL}/bad-json").mock(
        return_value=Response(200, content=b"not json", headers={"content-type": "application/json"}),
    )
    transport = _transport()
    # Act
    # Assert
    with pytest.raises(TransportError, match="Invalid JSON"):
        transport.request("GET", "/bad-json", kind=CqsKind.QUERY)
    transport.close()


@respx.mock
def test_network_failure_raises_transport_error() -> None:
    # Arrange
    respx.get(f"{BASE_URL}/thing").mock(side_effect=httpx.ConnectError("boom"))
    transport = _transport()
    # Act
    # Assert
    with pytest.raises(TransportError):
        transport.request("GET", "/thing", kind=CqsKind.QUERY)
    transport.close()
