from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Final

import pytest

from bitbucket.client import BitbucketClient
from bitbucket.config import ClientOptions
from bitbucket.retry import NO_RETRY

if TYPE_CHECKING:
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
