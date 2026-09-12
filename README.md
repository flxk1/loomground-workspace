# loomground-workspace

Workspace identity and boundary contract: how a workspace folder is scoped, identified, and registered.

## Problem
Every engine identifies "this folder" differently; records cannot be joined. One folder identity and registry contract.

## Install

```
pip install git+https://github.com/flxk1/loomground-workspace
```

## Usage

```python
from loomground_workspace import add_known_workspace, folder_hash, list_known_workspaces

add_known_workspace("~/Workspaces/alpha", log_root=lr)
list_known_workspaces(log_root=lr)                    # ['alpha']
list_known_workspaces(log_root=lr, scope=my_filter)   # host-scoped subset
folder_hash("~/Workspaces/alpha")                     # hex identity
```

## Example
```
in : folder_hash("/Users/me/Documents/Contracts")
out: 4c26f206a19b38f8be65a3d37f81169f
```

## Contracts

| Module | Contract |
|---|---|
| `folder_context` | resolution order: explicit argument → contextvar → `WORKSPACE_FOLDER_CONTEXT`; all three absent raises `NoFolderContextError`; an unregistered folder raises `FolderContextNotAllowed` unless `WORKSPACES_ALLOW_UNREGISTERED=1`; symlink policy from `WORKSPACE_SYMLINK_MODE` |
| `identity` | `folder_hash` (case-normalised), `legacy_folder_hash` (case-sensitive, for logs written before the fix; readers fall back to it) |
| `workspace_registry` | `known-workspaces.json` (version 1) under `log_root`; `scope` filter injected by the host; a filter matching nobody yields an empty list |
| `paths` | `LOG_ROOT_DEFAULT` = `~/.workspace/log` · `DEFAULT_WORKSPACE_DIR` = `~/Documents/Workspaces` |

Semantics and the boundary test: `docs/semantics.md`.

## Family

Workspace identity and boundary contract — a shared contract, not an engine component. Consumes: stdlib only · consumed by any host that scopes work to a folder · pipeline position: outside the reasoning pipeline; supplies the identity every per-workspace record hangs off. Engines import this package; a boundary test walks every module's AST for the reverse direction.

## Status

Version 0.1.0 · 12 tests · 0 dependencies · Python >=3.10.

## License

Apache-2.0 · `LICENSES/Apache-2.0.txt` · `NOTICE`
