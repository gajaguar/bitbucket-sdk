from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Final

import pytest

from bitbucket._auth import auth_for  # ruff: ignore[import-private-name]
from bitbucket._transport import Transport  # ruff: ignore[import-private-name]
from bitbucket.aio._transport import AsyncTransport  # ruff: ignore[import-private-name]
from bitbucket.aio.client import AsyncBitbucketClient
from bitbucket.client import BitbucketClient
from bitbucket.config import BasicCredentials
from bitbucket.config import ClientConfig
from bitbucket.config import ClientOptions
from bitbucket.retry import NO_RETRY

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from collections.abc import Iterator

BASE_URL: Final = "https://api.bitbucket.org/2.0"


@pytest.fixture
def client() -> Iterator[BitbucketClient]:
    with BitbucketClient(
        email="a@b.com",
        api_token="tok",  # ruff: ignore[hardcoded-password-func-arg]
        options=ClientOptions(retry=NO_RETRY),
    ) as bitbucket_client:
        yield bitbucket_client


@pytest.fixture
def transport() -> Iterator[Transport]:
    config = ClientConfig(
        credentials=BasicCredentials(
            email="a@b.com",
            api_token="tok",  # ruff: ignore[hardcoded-password-func-arg]
        ),
        base_url=BASE_URL,
        retry=NO_RETRY,
    )
    built_transport = Transport(config, auth_for(config.credentials))
    try:
        yield built_transport
    finally:
        built_transport.close()


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def aclient() -> AsyncIterator[AsyncBitbucketClient]:
    async with AsyncBitbucketClient(
        email="a@b.com",
        api_token="tok",  # ruff: ignore[hardcoded-password-func-arg]
        options=ClientOptions(retry=NO_RETRY),
    ) as bitbucket_client:
        yield bitbucket_client


@pytest.fixture
async def atransport() -> AsyncIterator[AsyncTransport]:
    config = ClientConfig(
        credentials=BasicCredentials(
            email="a@b.com",
            api_token="tok",  # ruff: ignore[hardcoded-password-func-arg]
        ),
        base_url=BASE_URL,
        retry=NO_RETRY,
    )
    built_transport = AsyncTransport(config, auth_for(config.credentials))
    try:
        yield built_transport
    finally:
        await built_transport.aclose()
