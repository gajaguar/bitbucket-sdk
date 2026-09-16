from __future__ import annotations

import httpx
import pytest

from bitbucket.errors import AuthenticationError
from bitbucket.errors import BitbucketAPIError
from bitbucket.errors import ConflictError
from bitbucket.errors import ErrorBody
from bitbucket.errors import ForbiddenError
from bitbucket.errors import NotFoundError
from bitbucket.errors import RateLimitError
from bitbucket.errors import ServerError
from bitbucket.errors import ValidationError
from bitbucket.errors import error_for_response


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (400, ValidationError),
        (401, AuthenticationError),
        (403, ForbiddenError),
        (404, NotFoundError),
        (409, ConflictError),
        (422, ValidationError),
        (429, RateLimitError),
        (500, ServerError),
        (503, ServerError),
        (418, BitbucketAPIError),
    ],
)
def test_error_for_response_maps_status_to_class(status: int, expected: type[BitbucketAPIError]) -> None:
    # Arrange
    request = httpx.Request("GET", "https://api.bitbucket.org/2.0/thing")
    response = httpx.Response(status, request=request, json={"error": {"message": "boom"}})
    # Act
    error = error_for_response(response)
    # Assert
    assert isinstance(error, expected)
    assert error.status_code == status
    assert error.message == "boom"


def test_error_for_response_parses_nested_bitbucket_envelope() -> None:
    # Arrange
    request = httpx.Request("GET", "https://api.bitbucket.org/2.0/thing")
    response = httpx.Response(404, request=request, json={"type": "error", "error": {"message": "no", "detail": "d"}})
    # Act
    error = error_for_response(response)
    # Assert
    assert error.message == "no"
    assert error.detail == "d"


def test_error_for_response_falls_back_to_raw_text_on_unrecognized_body() -> None:
    # Arrange
    request = httpx.Request("GET", "https://api.bitbucket.org/2.0/thing")
    response = httpx.Response(400, request=request, text="not json")
    # Act
    error = error_for_response(response)
    # Assert
    assert error.message is None
    assert error.raw == "not json"


def test_error_for_response_captures_retry_after() -> None:
    # Arrange
    request = httpx.Request("GET", "https://api.bitbucket.org/2.0/thing")
    response = httpx.Response(429, request=request, headers={"Retry-After": "12"}, json={"error": {}})
    # Act
    error = error_for_response(response)
    # Assert
    assert isinstance(error, RateLimitError)
    assert error.retry_after == pytest.approx(12.0)


def test_error_for_response_ignores_unparseable_retry_after() -> None:
    # Arrange
    request = httpx.Request("GET", "https://api.bitbucket.org/2.0/thing")
    response = httpx.Response(429, request=request, headers={"Retry-After": "soon"}, json={"error": {}})
    # Act
    error = error_for_response(response)
    # Assert
    assert isinstance(error, RateLimitError)
    assert error.retry_after is None


def test_error_body_defaults_are_none() -> None:
    # Arrange
    # Act
    body = ErrorBody()
    # Assert
    assert body.code is None
    assert body.message is None
    assert body.detail is None
    assert body.raw is None


def test_bitbucket_api_error_uses_default_body_when_none_given() -> None:
    # Arrange
    # Act
    error = BitbucketAPIError(500)
    # Assert
    assert error.status_code == 500
    assert error.message is None
    assert error.code is None
