from __future__ import annotations

from dataclasses import dataclass
from json import loads
from typing import TYPE_CHECKING
from typing import Final

if TYPE_CHECKING:
    from httpx import Response


@dataclass(frozen=True, slots=True)
class ErrorBody:
    code: str | None = None
    message: str | None = None
    detail: str | None = None
    raw: str | None = None


class BitbucketError(Exception):
    def __init__(
        self,
        message: str | None = None,
        *,
        request: object | None = None,
        response: object | None = None,
    ) -> None:
        super().__init__(message or self.__class__.__name__)
        self.message = message
        self.request = request
        self.response = response


class ConfigurationError(BitbucketError):
    pass


class MissingCredentialsError(ConfigurationError):
    pass


class PollTimeoutError(BitbucketError):
    pass


class TransportError(BitbucketError):
    def __init__(
        self,
        message: str | None = None,
        *,
        request: object | None = None,
        response: object | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message, request=request, response=response)
        self.cause = cause


class BitbucketAPIError(BitbucketError):
    def __init__(
        self,
        status_code: int = 0,
        *,
        body: ErrorBody | None = None,
        request: object | None = None,
        response: object | None = None,
    ) -> None:
        resolved_body = body or ErrorBody()
        super().__init__(resolved_body.message, request=request, response=response)
        self.status_code = status_code
        self.code = resolved_body.code
        self.message = resolved_body.message
        self.detail = resolved_body.detail
        self.raw = resolved_body.raw


class AuthenticationError(BitbucketAPIError):
    pass


class ForbiddenError(BitbucketAPIError):
    pass


class NotFoundError(BitbucketAPIError):
    pass


class ValidationError(BitbucketAPIError):
    pass


class ConflictError(BitbucketAPIError):
    pass


class RateLimitError(BitbucketAPIError):
    def __init__(
        self,
        status_code: int = 0,
        *,
        body: ErrorBody | None = None,
        request: object | None = None,
        response: object | None = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(status_code, body=body, request=request, response=response)
        self.retry_after = retry_after


class ServerError(BitbucketAPIError):
    pass


_STATUS_MAP: Final[dict[int, type[BitbucketAPIError]]] = {
    400: ValidationError,
    401: AuthenticationError,
    403: ForbiddenError,
    404: NotFoundError,
    409: ConflictError,
    422: ValidationError,
    429: RateLimitError,
}

_SERVER_ERROR_FLOOR: Final = 500


def _error_class(status_code: int) -> type[BitbucketAPIError]:
    mapped = _STATUS_MAP.get(status_code)
    if mapped is not None:
        return mapped
    if status_code >= _SERVER_ERROR_FLOOR:
        return ServerError
    return BitbucketAPIError


def _decode_body(text: str) -> ErrorBody:
    # Bitbucket's error envelope is {"type": "error", "error": {"message", "detail"}},
    # nested under an "error" key rather than a flat {"code", "message"} shape.
    try:
        payload: object = loads(text)
    except ValueError, TypeError:
        return ErrorBody(raw=text)
    if not isinstance(payload, dict):
        return ErrorBody(raw=text)
    error = payload.get("error")
    if not isinstance(error, dict):
        return ErrorBody(raw=text)
    message = error.get("message")
    detail = error.get("detail")
    if message is None and detail is None:
        return ErrorBody(raw=text)
    return ErrorBody(
        message=str(message) if message is not None else None,
        detail=str(detail) if detail is not None else None,
    )


def _retry_after(response: Response) -> float | None:
    header = response.headers.get("Retry-After")
    if header is None:
        return None
    try:
        return float(header)
    except ValueError:
        return None


def error_for_response(response: Response) -> BitbucketAPIError:
    try:
        text = response.text
    except ValueError, UnicodeDecodeError:
        text = ""
    body = _decode_body(text)
    error_class = _error_class(response.status_code)
    if error_class is RateLimitError:
        return RateLimitError(
            response.status_code,
            body=body,
            request=response.request,
            response=response,
            retry_after=_retry_after(response),
        )
    return error_class(
        response.status_code,
        body=body,
        request=response.request,
        response=response,
    )
