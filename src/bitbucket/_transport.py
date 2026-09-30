from __future__ import annotations

from logging import NullHandler
from logging import getLogger
from typing import TYPE_CHECKING
from typing import Final
from typing import cast

import httpx

from bitbucket._retry_transport import RetryTransport
from bitbucket.errors import TransportError
from bitbucket.errors import error_for_response

if TYPE_CHECKING:
    from collections.abc import Mapping

    from bitbucket._auth import BasicAuth
    from bitbucket.config import ClientConfig
    from bitbucket.retry import CqsKind

LOGGER: Final = getLogger("bitbucket")
LOGGER.addHandler(NullHandler())

_NO_CONTENT: Final = 204

type JSONValue = (  # pylint: disable=gajaguar-module-const-naming
    bool | int | float | str | list[JSONValue] | dict[str, JSONValue] | None
)


def _elapsed_ms(response: httpx.Response) -> float:
    try:
        return response.elapsed.total_seconds() * 1000
    except RuntimeError:
        # Timing is unavailable when the response never went through a real network
        # transport (mocked transports in tests). Logging must not fail because of it.
        return 0.0


def _resolved_params(
    params: Mapping[str, str | float | bool | list[str] | None] | None,
) -> Mapping[str, str | float | bool | list[str]] | None:
    if params is None:
        return None
    return {key: value for key, value in params.items() if value is not None} or None


def _log(method: str, path: str, response: httpx.Response) -> None:
    # Only primitives are logged; headers and the config object are never logged so the
    # basic-auth credentials cannot leak into a caller's log sink.
    elapsed_ms = _elapsed_ms(response)
    LOGGER.debug("%s %s -> %s (%.1fms)", method, path, response.status_code, elapsed_ms)


def _decode_json(response: httpx.Response) -> JSONValue:
    if not response.content:
        return {}
    try:
        return cast("JSONValue", response.json())
    except ValueError as error:
        message = f"Invalid JSON in response from {response.url}"
        raise TransportError(message, response=response, cause=error) from error


def _json_or_error(response: httpx.Response) -> JSONValue:
    if response.status_code == _NO_CONTENT:
        return None
    if not response.is_success:
        raise error_for_response(response)
    return _decode_json(response)


def _text_or_error(response: httpx.Response) -> str:
    if not response.is_success:
        raise error_for_response(response)
    return response.text


def _bytes_or_error(response: httpx.Response) -> bytes:
    if not response.is_success:
        raise error_for_response(response)
    return response.content


class Transport:
    def __init__(self, config: ClientConfig, auth: BasicAuth) -> None:
        self._config = config
        self._client = httpx.Client(
            base_url=config.base_url,
            auth=auth,
            timeout=config.timeout,
            transport=RetryTransport(httpx.HTTPTransport(), policy=config.retry),
            headers={"User-Agent": config.user_agent},
            event_hooks=config.event_hooks or {},
        )

    def close(self) -> None:
        self._client.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        kind: CqsKind,
        params: Mapping[str, str | float | bool | list[str] | None] | None = None,
        json: JSONValue = None,
    ) -> JSONValue:
        response = self._send(method, path, kind=kind, params=params, json=json)
        return _json_or_error(response)

    def request_text(
        self,
        method: str,
        path: str,
        *,
        kind: CqsKind,
        params: Mapping[str, str | float | bool | list[str] | None] | None = None,
    ) -> str:
        response = self._send(method, path, kind=kind, params=params, json=None)
        return _text_or_error(response)

    def request_bytes(
        self,
        method: str,
        path: str,
        *,
        kind: CqsKind,
        params: Mapping[str, str | float | bool | list[str] | None] | None = None,
    ) -> bytes:
        response = self._send(method, path, kind=kind, params=params, json=None)
        return _bytes_or_error(response)

    def request_multipart(
        self,
        method: str,
        path: str,
        *,
        kind: CqsKind,
        files: Mapping[str, tuple[str, bytes, str] | bytes],
        data: Mapping[str, str] | None = None,
    ) -> JSONValue:
        response = self._send_multipart(method, path, kind=kind, files=files, data=data)
        return _json_or_error(response)

    def _send(
        self,
        method: str,
        path: str,
        *,
        kind: CqsKind,
        params: Mapping[str, str | float | bool | list[str] | None] | None,
        json: JSONValue,
    ) -> httpx.Response:
        try:
            response = self._client.request(
                method,
                path,
                params=_resolved_params(params),
                json=json,
                extensions={"bitbucket_cqs": kind},
            )
        except httpx.TransportError as error:
            raise TransportError(str(error)) from error
        _log(method, path, response)
        return response

    def _send_multipart(
        self,
        method: str,
        path: str,
        *,
        kind: CqsKind,
        files: Mapping[str, tuple[str, bytes, str] | bytes],
        data: Mapping[str, str] | None,
    ) -> httpx.Response:
        try:
            response = self._client.request(
                method,
                path,
                files=files,
                data=data,
                extensions={"bitbucket_cqs": kind},
            )
        except httpx.TransportError as error:
            raise TransportError(str(error)) from error
        _log(method, path, response)
        return response
