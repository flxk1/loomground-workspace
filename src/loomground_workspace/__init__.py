# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""loomground-workspace — what a workspace is, independent of any engine.

A workspace is a folder on an operator's disk. It exists before any engine
governs it and outlives any that does. This package is the concept: how a
workspace is **scoped**, how it is **identified**, and how it is **registered**
— nothing about what may be done inside one.

  * :mod:`.folder_context` — scope. Explicit argument, then contextvar, then
    ``WORKSPACE_FOLDER_CONTEXT``; absent all three it raises rather than
    guessing. Symlink policy lives here too, because whether a symlink is a
    boundary is part of what a workspace *is*.
  * :mod:`.identity` — the question that has to be answered once and applied
    everywhere: are these two paths the same workspace? Case-insensitive
    filesystems and symlinks both make the naive answer wrong.
  * :mod:`.workspace_registry` — which workspaces are known.
  * :mod:`.paths` — where a workspace keeps what it accumulates, by default.

**The direction is the point.** This package imports no engine; engines import
it. A boundary test asserts that, because the moment it reverses the split has
failed and nothing else would say so.

Stdlib only.
"""
from __future__ import annotations

from . import folder_context, identity, paths, workspace_registry
from .folder_context import (
    ALLOW_UNREGISTERED_ENV, UNSCOPED_SENTINEL, FolderContextNotAllowed,
    NoFolderContextError, current_folder, folder_context as folder_scope,
    reset_folder, resolve_folder_context, set_folder, symlink_mode,
    with_folder_context,
)
from .identity import folder_hash, legacy_folder_hash
from .paths import DEFAULT_WORKSPACE_DIR, LOG_ROOT_DEFAULT
from .workspace_registry import (
    REGISTRY_FILE, REGISTRY_VERSION, add_known_workspace,
    bootstrap_default_workspace, list_known_workspaces, load_registry,
    remove_known_workspace,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "folder_context", "identity", "paths", "workspace_registry",
    # scope
    "NoFolderContextError", "FolderContextNotAllowed", "UNSCOPED_SENTINEL",
    "ALLOW_UNREGISTERED_ENV", "current_folder", "set_folder", "reset_folder",
    "folder_scope", "with_folder_context", "resolve_folder_context",
    "symlink_mode",
    # identity
    "folder_hash", "legacy_folder_hash",
    # registration
    "load_registry", "add_known_workspace", "remove_known_workspace",
    "list_known_workspaces", "bootstrap_default_workspace",
    "REGISTRY_FILE", "REGISTRY_VERSION",
    # defaults
    "LOG_ROOT_DEFAULT", "DEFAULT_WORKSPACE_DIR",
]
