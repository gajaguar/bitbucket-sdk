from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

from bitbucket._transport import JSONValue
from bitbucket._transport import _bytes_or_error
from bitbucket._transport import _json_or_error
from bitbucket._transport import _log
from bitbucket._transport import _resolved_params
from bitbucket._transport import _text_or_error
from bitbucket.aio._retry_transport import AsyncRetryTransport
from bitbucket.errors import TransportError

if TYPE_CHECKING:
    from collections.abc import Mapping

    from bitbucket.config import ClientConfig
    from bitbucket.retry import CqsKind


class AsyncTransport:
    def __init__(self, config: ClientConfig, auth: httpx.Auth) -> None:
        self._config = config
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            auth=auth,
            timeout=config.timeout,
            transport=AsyncRetryTransport(httpx.AsyncHTTPTransport(), policy=config.retry),
            headers={"User-Agent": config.user_agent},
            event_hooks=config.event_hooks or {},
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def request(
        self,
        method: str,
        path: str,
        *,
        kind: CqsKind,
        params: Mapping[str, str | float | bool | list[str] | None] | None = None,
        json: JSONValue = None,
    ) -> JSONValue:
        response = await self._send(method, path, kind=kind, params=params, json=json)
        return _json_or_error(response)

    async def request_text(
        self,
        method: str,
        path: str,
        *,
        kind: CqsKind,
        params: Mapping[str, str | float | bool | list[str] | None] | None = None,
    ) -> str:
        response = await self._send(method, path, kind=kind, params=params, json=None)
        return _text_or_error(response)

    async def request_bytes(
        self,
        method: str,
        path: str,
        *,
        kind: CqsKind,
        params: Mapping[str, str | float | bool | list[str] | None] | None = None,
    ) -> bytes:
        response = await self._send(method, path, kind=kind, params=params, json=None)
        return _bytes_or_error(response)

    async def request_multipart(
        self,
        method: str,
        path: str,
        *,
        kind: CqsKind,
        files: Mapping[str, tuple[str, bytes, str] | bytes],
        data: Mapping[str, str] | None = None,
    ) -> JSONValue:
        response = await self._send_multipart(method, path, kind=kind, files=files, data=data)
        return _json_or_error(response)

    async def _send(
        self,
        method: str,
        path: str,
        *,
        kind: CqsKind,
        params: Mapping[str, str | float | bool | list[str] | None] | None,
        json: JSONValue,
    ) -> httpx.Response:
        try:
            response = await self._client.request(
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

    async def _send_multipart(
        self,
        method: str,
        path: str,
        *,
        kind: CqsKind,
        files: Mapping[str, tuple[str, bytes, str] | bytes],
        data: Mapping[str, str] | None,
    ) -> httpx.Response:
        try:
            response = await self._client.request(
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
