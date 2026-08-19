# loomground-workspace

What a workspace is — how it is scoped, identified and registered — independent
of any engine that governs one.

A workspace is a folder on an operator's disk. It exists before any engine
governs it and outlives any that does. This package holds the concept and
nothing about what may be done inside one.

## Install

```
pip install git+https://github.com/flxk1/loomground-workspace
```

Python 3.10+. No dependencies.

## Use

```python
from loomground_workspace import (
    add_known_workspace, folder_hash, legacy_folder_hash, list_known_workspaces,
)

add_known_workspace("~/Workspaces/alpha", log_root=lr)
add_known_workspace("~/Workspaces/beta", log_root=lr)

list_known_workspaces(log_root=lr)
# a host with per-principal access control passes its own filter:
list_known_workspaces(log_root=lr, scope=lambda ws: [w for w in ws if mine(w)])
```

```
known           : ['alpha', 'beta']
host-scoped     : ['alpha']
identity        : 7890a2219e880b4c
legacy identity : fa231ca27ce1dd0d
```

## What is here

| | |
|---|---|
| `folder_context` | scope: explicit argument → contextvar → `WORKSPACE_FOLDER_CONTEXT`; absent all three it **raises** rather than guessing. Symlink policy lives here. |
| `identity` | `folder_hash`, `legacy_folder_hash` — are these two paths the same workspace? |
| `workspace_registry` | which workspaces are known; `scope` is injected by the caller |
| `paths` | where a workspace keeps what it accumulates, by default |

## Semantics

**Identity is not string comparison.** `~/Workspaces` and `~/workspaces` are one
folder on APFS or NTFS and two on ext4, and a symlink may merge two paths onto
one directory or be exactly the boundary you meant to keep. Everything that
accumulates per workspace hangs off the answer, so the rule is stated once and
applied everywhere.

**`legacy_folder_hash` is load-bearing.** Logs written before the
case-normalisation fix live under a case-*sensitive* hash. A reader falls back
to it when a fresh lookup misses. Dropping it does not fail loudly — it silently
stops finding history, which is the worst failure a lookup can have.

**Scope is refused, not guessed.** With no folder context, resolution raises
`NoFolderContextError`. An explicit folder that is not a registered workspace
raises `FolderContextNotAllowed`; the opt-out is a named environment variable,
so "any path works" can never become the accidental default.

**Access control is the host's.** `list_known_workspaces` takes an optional
`scope` filter. This package has no opinion about who may see which workspace —
a host that scopes per principal passes its filter, one that does not passes
nothing. Fail-closed survives injection: a filter matching nobody yields an
empty list, never the full registry.

## The direction is the point

This package imports **no engine**; engines import it. A boundary test walks
every module's AST and names any import that reaches an engine, because the
moment that direction reverses the split has failed and nothing else would say
so. It caught a real one during extraction: the registry reached into an engine
module for the request principal, which is why `scope` is injected today.

## Tests

```
pytest -q
```

## Licence

AGPL-3.0-only.
