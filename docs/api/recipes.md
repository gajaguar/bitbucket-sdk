---
type: playbook
title: Usage recipes
description: Runnable examples that list and comment on pull requests, merge one and wait for the result, and create a repository, branch and file read.
tags: [api]
status: stable
---

# Usage recipes

Each recipe assumes the credential setup in the
[README](../../README.md#authentication).

List a repository's open pull requests, fetch one's diff, and post a comment:

```python
from bitbucket import BitbucketClient
from bitbucket import CommentContentCreate
from bitbucket import CommentCreate

with BitbucketClient() as client:
    # workspace() takes an explicit slug; default_workspace() reads
    # BITBUCKET_WORKSPACE from the environment instead.
    repository = client.default_workspace().repository("my-repo")

    open_prs = list(repository.pull_requests.list(state="OPEN"))
    for pull_request in open_prs:
        print(pull_request.id, pull_request.title)

    diff = repository.pull_requests.diff(open_prs[0].id)

    repository.pull_requests.comments(open_prs[0].id).create(
        CommentCreate(content=CommentContentCreate(raw="Looks good.")),
    )
```

Merge a pull request and wait for the result — `POST .../merge` returns
`202 Accepted` with an async task to poll, not the merged PR directly:

```python
from bitbucket import MergeParameters

status = repository.pull_requests.merge_and_wait(
    open_prs[0].id,
    MergeParameters(merge_strategy="squash"),
)
print(status.task_status)
```

`merge()` returns the task immediately without waiting; poll it yourself with
`merge_task_status(pull_request_id, task_id)` if you need finer control.

Create a repository, push a branch, and read a file from it:

```python
from bitbucket import BranchCreate
from bitbucket import RefTargetSpec
from bitbucket import RepositoryCreate

with BitbucketClient() as client:
    workspace = client.default_workspace()

    repository = workspace.repositories.create("new-repo", RepositoryCreate(is_private=True))
    main = next(iter(workspace.repository("new-repo").refs.branches.list()))

    workspace.repository("new-repo").refs.branches.create(
        BranchCreate(name="feature", target=RefTargetSpec(hash=main.target.hash)),
    )

    readme = workspace.repository("new-repo").source.read(main.target.hash, "README.md")
```
