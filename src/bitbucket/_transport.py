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

type JSONValue = (  # pylint: disable=app-module-const-naming
    bool | int | float | str | list[JSONValue] | dict[str, JSONValue] | None
)


def _elapsed_ms(response: httpx.Response) -> float:
    try:
        return response.elapsed.total_seconds() * 1000
    except RuntimeError:
        # Timing is unavailable when the response never went through a real network
        # transport (mocked transports in tests). Logging must not fail because of it.
        return 0.0


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
        if response.status_code == _NO_CONTENT:
            return None
        if not response.is_success:
            raise error_for_response(response)
        return self._decode_json(response)

    def request_text(
        self,
        method: str,
        path: str,
        *,
        kind: CqsKind,
        params: Mapping[str, str | float | bool | list[str] | None] | None = None,
    ) -> str:
        response = self._send(method, path, kind=kind, params=params, json=None)
        if not response.is_success:
            raise error_for_response(response)
        return response.text

    def _send(
        self,
        method: str,
        path: str,
        *,
        kind: CqsKind,
        params: Mapping[str, str | float | bool | list[str] | None] | None,
        json: JSONValue,
    ) -> httpx.Response:
        resolved_params = {key: value for key, value in (params or {}).items() if value is not None} or None
        try:
            response = self._client.request(
                method,
                path,
                params=resolved_params,
                json=json,
                extensions={"bitbucket_cqs": kind},
            )
        except httpx.TransportError as error:
            raise TransportError(str(error)) from error
        # Only primitives are logged; headers and the config object are never logged so the
        # basic-auth credentials cannot leak into a caller's log sink.
        elapsed_ms = _elapsed_ms(response)
        LOGGER.debug("%s %s -> %s (%.1fms)", method, path, response.status_code, elapsed_ms)
        return response

    @staticmethod
    def _decode_json(response: httpx.Response) -> JSONValue:
        if not response.content:
            return {}
        try:
            return cast("JSONValue", response.json())
        except ValueError as error:
            message = f"Invalid JSON in response from {response.url}"
            raise TransportError(message, response=response, cause=error) from error
