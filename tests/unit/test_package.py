from __future__ import annotations

import bitbucket


def test_version_is_exported() -> None:
    # Arrange
    # Act
    version = bitbucket.__version__
    # Assert
    assert isinstance(version, str)
    assert version


def test_credential_surface_is_public() -> None:
    # Arrange
    names = {
        "ACCESS_TOKEN_ENV_VAR",
        "API_TOKEN_ENV_VAR",
        "EMAIL_ENV_VAR",
        "WORKSPACE_ENV_VAR",
        "AccessTokenProvider",
        "ApiTokenProvider",
        "BitbucketClient",
        "ClientOptions",
        "MissingCredentialsError",
        "AuthenticationError",
        "ForbiddenError",
    }
    # Act
    missing = names - set(bitbucket.__all__)
    # Assert
    assert not missing


def test_search_surface_is_public() -> None:
    # Arrange
    names = {"TeamClient", "CodeSearchResult", "SearchContentMatch", "SearchLine", "SearchSegment"}
    # Act
    missing = names - set(bitbucket.__all__)
    # Assert
    assert not missing


def test_mergeability_surface_is_public() -> None:
    # Arrange
    names = {
        "FileConflictScenario",
        "GitMergeabilityReason",
        "MergeCheckDefinition",
        "MergeQueue",
        "MergeabilityCheck",
        "MergeabilityCheckStatus",
        "MergeabilityCheckType",
        "MergeabilityPullRequestState",
    }
    # Act
    missing = names - set(bitbucket.__all__)
    # Assert
    assert not missing


def test_pipelines_surface_is_public() -> None:
    # Arrange
    names = {
        "Pipeline",
        "PipelineBuildNumber",
        "PipelineBuildNumberUpdate",
        "PipelineCache",
        "PipelineCacheContentUri",
        "PipelineCommand",
        "PipelineCommitRef",
        "PipelineCommitTargetCreate",
        "PipelineConfigurationSource",
        "PipelineCreate",
        "PipelineError",
        "PipelineImage",
        "PipelineKnownHost",
        "PipelineKnownHostCreate",
        "PipelineKnownHostUpdate",
        "PipelineLinks",
        "PipelineRefTargetCreate",
        "PipelineRefType",
        "PipelineResultName",
        "PipelineSchedule",
        "PipelineScheduleCreate",
        "PipelineScheduleExecution",
        "PipelineScheduleTargetCreate",
        "PipelineScheduleUpdate",
        "PipelineSelector",
        "PipelineSelectorType",
        "PipelineSshKeyPair",
        "PipelineSshKeyPairUpdate",
        "PipelineSshPublicKey",
        "PipelineStageName",
        "PipelineState",
        "PipelineStateName",
        "PipelineStateResult",
        "PipelineStateStage",
        "PipelineStep",
        "PipelineStepResult",
        "PipelineStepResultName",
        "PipelineStepState",
        "PipelineStepStateName",
        "PipelineTarget",
        "PipelineTrigger",
        "PipelineVariable",
        "PipelineVariableCreate",
        "PipelineVariableUpdate",
        "PipelinesConfig",
        "PipelinesConfigUpdate",
        "Runner",
        "RunnerCreate",
        "RunnerOAuthClient",
        "RunnerState",
        "RunnerStatus",
        "RunnerUpdate",
        "RunnerVersion",
    }
    # Act
    missing = names - set(bitbucket.__all__)
    # Assert
    assert not missing


def test_deployments_and_reports_surface_is_public() -> None:
    # Arrange
    names = {
        "AnnotationResult",
        "AnnotationSeverity",
        "AnnotationType",
        "DeployKey",
        "DeployKeyCreate",
        "DeployKeyUpdate",
        "Deployment",
        "DeploymentRelease",
        "DeploymentState",
        "DeploymentStateName",
        "DeploymentStatus",
        "DeploymentStatusName",
        "Environment",
        "EnvironmentCreate",
        "EnvironmentUpdate",
        "ProjectDeployKey",
        "Report",
        "ReportAnnotation",
        "ReportAnnotationWrite",
        "ReportData",
        "ReportDataType",
        "ReportResult",
        "ReportType",
        "ReportWrite",
    }
    # Act
    missing = names - set(bitbucket.__all__)
    # Assert
    assert not missing
