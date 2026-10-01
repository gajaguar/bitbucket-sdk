from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

from bitbucket._pagination import apaginate
from bitbucket.aio.resources.base import AsyncDeletableResourceMixin
from bitbucket.aio.resources.base import AsyncNestedResource
from bitbucket.aio.resources.pipeline_variables import AsyncPipelineVariablesResource
from bitbucket.aio.resources.runners import AsyncRunnersResource
from bitbucket.models.pipeline import PipelineScheduleExecution
from bitbucket.models.pipeline_config import PipelineBuildNumber
from bitbucket.models.pipeline_config import PipelineBuildNumberUpdate
from bitbucket.models.pipeline_config import PipelineCache
from bitbucket.models.pipeline_config import PipelineCacheContentUri
from bitbucket.models.pipeline_config import PipelineKnownHost
from bitbucket.models.pipeline_config import PipelineKnownHostCreate
from bitbucket.models.pipeline_config import PipelineKnownHostUpdate
from bitbucket.models.pipeline_config import PipelineSchedule
from bitbucket.models.pipeline_config import PipelineScheduleCreate
from bitbucket.models.pipeline_config import PipelineScheduleUpdate
from bitbucket.models.pipeline_config import PipelineSshKeyPair
from bitbucket.models.pipeline_config import PipelineSshKeyPairUpdate
from bitbucket.models.pipeline_config import PipelinesConfig
from bitbucket.models.pipeline_config import PipelinesConfigUpdate
from bitbucket.resources.base import page_from_payload
from bitbucket.retry import CqsKind

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from typing import Any

    from bitbucket._pagination import Page
    from bitbucket._transport import JSONValue
    from bitbucket.aio._transport import AsyncTransport


class AsyncSchedulesResource(
    AsyncNestedResource[PipelineSchedule, PipelineScheduleCreate, PipelineScheduleUpdate],
    AsyncDeletableResourceMixin,
):
    _path = "/schedules"
    _read_model = PipelineSchedule

    # GET {path}/{schedule_uuid}/executions (auto-paginating)
    def executions(self, schedule_uuid: object) -> AsyncIterator[PipelineScheduleExecution]:
        return apaginate(lambda cursor: self.executions_page(schedule_uuid, cursor=cursor))

    # GET {path}/{schedule_uuid}/executions
    async def executions_page(
        self, schedule_uuid: object, *, cursor: str | None = None
    ) -> Page[PipelineScheduleExecution]:
        data = await self._transport.request(
            "GET", cursor or f"{self._item_path(schedule_uuid)}/executions", kind=CqsKind.QUERY
        )
        return page_from_payload(cast("dict[str, Any]", data), PipelineScheduleExecution)


class AsyncKnownHostsResource(
    AsyncNestedResource[PipelineKnownHost, PipelineKnownHostCreate, PipelineKnownHostUpdate],
    AsyncDeletableResourceMixin,
):
    _path = "/known_hosts"
    _read_model = PipelineKnownHost


class AsyncSshKeyPairResource:
    # A singleton under the repository, not a collection: no id in the path.
    def __init__(self, transport: AsyncTransport, base_path: str) -> None:
        self._transport = transport
        self._path = f"{base_path}/key_pair"

    # DELETE {path}
    async def delete(self) -> None:
        await self._transport.request("DELETE", self._path, kind=CqsKind.IDEMPOTENT_COMMAND)

    # GET {path}
    async def get(self) -> PipelineSshKeyPair:
        data = await self._transport.request("GET", self._path, kind=CqsKind.QUERY)
        return PipelineSshKeyPair.model_validate(data)

    # PUT {path}
    async def update(self, payload: PipelineSshKeyPairUpdate) -> PipelineSshKeyPair:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = await self._transport.request("PUT", self._path, kind=CqsKind.IDEMPOTENT_COMMAND, json=body)
        return PipelineSshKeyPair.model_validate(data)


class AsyncCachesResource:
    # Keyed by cache uuid for one cache, by `name` (a query parameter) for all
    # caches of that name; neither fits NestedResource.
    def __init__(self, transport: AsyncTransport, base_path: str) -> None:
        self._transport = transport
        self._path = f"{base_path}/caches"

    # GET {path}/{cache_uuid}/content-uri
    async def content_uri(self, cache_uuid: object) -> PipelineCacheContentUri:
        data = await self._transport.request("GET", f"{self._path}/{cache_uuid}/content-uri", kind=CqsKind.QUERY)
        return PipelineCacheContentUri.model_validate(data)

    # DELETE {path}/{cache_uuid}
    async def delete(self, cache_uuid: object) -> None:
        await self._transport.request("DELETE", f"{self._path}/{cache_uuid}", kind=CqsKind.IDEMPOTENT_COMMAND)

    # DELETE {path}?name={name}
    async def delete_by_name(self, name: str) -> None:
        await self._transport.request("DELETE", self._path, kind=CqsKind.IDEMPOTENT_COMMAND, params={"name": name})

    # GET {path} (auto-paginating)
    def list(self) -> AsyncIterator[PipelineCache]:
        return apaginate(lambda cursor: self.list_page(cursor=cursor))

    # GET {path}
    async def list_page(self, *, cursor: str | None = None) -> Page[PipelineCache]:
        data = await self._transport.request("GET", cursor or self._path, kind=CqsKind.QUERY)
        return page_from_payload(cast("dict[str, Any]", data), PipelineCache)


class AsyncRepositoryPipelinesConfig:  # pylint: disable=too-many-instance-attributes
    # The spec spells the segment two ways: `pipelines_config` (settings,
    # schedules, SSH, variables) and `pipelines-config` (caches, runners);
    # each sub-resource gets the base path it needs.
    def __init__(self, transport: AsyncTransport, base_path: str) -> None:
        self._transport = transport
        self._path = f"{base_path}/pipelines_config"
        self.variables = AsyncPipelineVariablesResource(transport, self._path)
        self.schedules = AsyncSchedulesResource(transport, self._path)
        self.known_hosts = AsyncKnownHostsResource(transport, f"{self._path}/ssh")
        self.ssh_key_pair = AsyncSshKeyPairResource(transport, f"{self._path}/ssh")
        self.caches = AsyncCachesResource(transport, f"{base_path}/pipelines-config")
        self.runners = AsyncRunnersResource(transport, f"{base_path}/pipelines-config")

    # GET .../pipelines_config
    async def get(self) -> PipelinesConfig:
        data = await self._transport.request("GET", self._path, kind=CqsKind.QUERY)
        return PipelinesConfig.model_validate(data)

    # PUT .../pipelines_config
    async def update(self, payload: PipelinesConfigUpdate) -> PipelinesConfig:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = await self._transport.request("PUT", self._path, kind=CqsKind.IDEMPOTENT_COMMAND, json=body)
        return PipelinesConfig.model_validate(data)

    # PUT .../pipelines_config/build_number
    async def update_build_number(self, payload: PipelineBuildNumberUpdate) -> PipelineBuildNumber:
        body = payload.model_dump(mode="json", by_alias=True, exclude_unset=True)
        data = await self._transport.request(
            "PUT", f"{self._path}/build_number", kind=CqsKind.IDEMPOTENT_COMMAND, json=body
        )
        return PipelineBuildNumber.model_validate(data)


class AsyncWorkspacePipelinesConfig:
    def __init__(self, transport: AsyncTransport, base_path: str) -> None:
        self._transport = transport
        self._path = f"{base_path}/pipelines-config"
        self.variables = AsyncPipelineVariablesResource(transport, self._path)
        self.runners = AsyncRunnersResource(transport, self._path)

    # GET .../pipelines-config/identity/oidc/.well-known/openid-configuration
    async def oidc_configuration(self) -> JSONValue:
        # The spec declares no schema for either OIDC response, so the JSON is returned as is.
        path = f"{self._path}/identity/oidc/.well-known/openid-configuration"
        return await self._transport.request("GET", path, kind=CqsKind.QUERY)

    # GET .../pipelines-config/identity/oidc/keys.json
    async def oidc_keys(self) -> JSONValue:
        return await self._transport.request("GET", f"{self._path}/identity/oidc/keys.json", kind=CqsKind.QUERY)


class AsyncAccountPipelinesConfig:
    # Team and user scopes expose only variables, under `pipelines_config`.
    def __init__(self, transport: AsyncTransport, base_path: str) -> None:
        self.variables = AsyncPipelineVariablesResource(transport, f"{base_path}/pipelines_config")
