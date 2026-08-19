# SPDX-License-Identifier: AGPL-3.0-only
# Copyright 2026 flxk1
"""Workspace registry — persistent list of folders the user has marked as
Workspaces workspaces.

Until now the dashboard kept this list in browser ``localStorage``. That
loses everything when the user switches browser or reinstalls Cowork. This
module persists the same list to ``<log_root>/known-workspaces.json`` so it
survives independently of whatever host is reading it.

Format:

    {
      "version":   1,
      "default":   "~/Documents/Workspaces",
      "added_at":  "2026-05-21T12:00:00.000000Z",
      "workspaces": [
        {"path": "~/Documents/Workspaces", "added_at": "...", "label": ""},
        ...
      ]
    }

The ``default`` field records the bootstrap-created default workspace.
The dashboard falls back to localStorage only when this file is missing
(first run on a new machine).

This module is intentionally side-effect-light: it never writes outside
``log_root``. Bootstrapping the default workspace directory itself is a
separate explicit action (``bootstrap_default_workspace``) so we don't
silently create folders on every read.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Callable, Optional

from .paths import LOG_ROOT_DEFAULT


REGISTRY_FILE = "known-workspaces.json"
REGISTRY_VERSION = 1
DEFAULT_WORKSPACE_DIR = Path.home() / "Documents" / "Workspaces"


def _now_iso() -> str:
    t = time.time()
    secs = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(t))
    micros = int((t - int(t)) * 1_000_000)
    return f"{secs}.{micros:06d}Z"


def _registry_path(log_root: Optional[Path] = None) -> Path:
    return (Path(log_root) if log_root else LOG_ROOT_DEFAULT) / REGISTRY_FILE


def _resolved(p: str | Path) -> str:
    return str(Path(p).expanduser().resolve())


def load_registry(log_root: Optional[Path] = None) -> dict[str, Any]:
    """Load the registry. Missing file returns an empty default-shaped dict."""
    path = _registry_path(log_root)
    if not path.exists():
        return {
            "version":    REGISTRY_VERSION,
            "default":    "",
            "workspaces": [],
        }
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        # Corrupt file → treat as empty; caller can overwrite by adding.
        return {
            "version":    REGISTRY_VERSION,
            "default":    "",
            "workspaces": [],
            "_corrupt":   True,
        }
    # Normalise shape
    data.setdefault("version", REGISTRY_VERSION)
    data.setdefault("default", "")
    data.setdefault("workspaces", [])
    return data


def _save_registry(data: dict[str, Any],
                   log_root: Optional[Path] = None) -> Path:
    path = _registry_path(log_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    os.replace(tmp, path)
    return path


def add_known_workspace(folder_path: str | Path,
                        *,
                        label: str = "",
                        log_root: Optional[Path] = None) -> dict[str, Any]:
    """Register a folder as a known workspace. Idempotent — re-adding the
    same path updates ``label`` and bumps ``added_at`` but does not duplicate.
    """
    resolved = _resolved(folder_path)
    data = load_registry(log_root=log_root)
    ws: list[dict[str, Any]] = data.get("workspaces") or []
    ws = [w for w in ws if w.get("path") != resolved]
    ws.append({
        "path":     resolved,
        "label":    label or "",
        "added_at": _now_iso(),
    })
    data["workspaces"] = ws
    _save_registry(data, log_root=log_root)
    return {"path": resolved, "total": len(ws)}


def remove_known_workspace(folder_path: str | Path,
                           *,
                           log_root: Optional[Path] = None) -> bool:
    """Unregister a folder. Returns True iff it was present."""
    resolved = _resolved(folder_path)
    data = load_registry(log_root=log_root)
    ws: list[dict[str, Any]] = data.get("workspaces") or []
    before = len(ws)
    ws = [w for w in ws if w.get("path") != resolved]
    removed = len(ws) != before
    if removed:
        data["workspaces"] = ws
        # If we removed the default, clear the default pointer too
        if data.get("default") == resolved:
            data["default"] = ""
        _save_registry(data, log_root=log_root)
    return removed


def list_known_workspaces(log_root: Optional[Path] = None, *,
                          scope: Optional[Callable[[list[dict[str, Any]]],
                                                   list[dict[str, Any]]]] = None,
                          ) -> list[dict[str, Any]]:
    """Return the registered workspace list. Sorted by added_at ascending.

    ``scope`` is an optional filter the CALLER supplies. It exists because
    access control is not this package's business: a host that fronts a
    registry with per-principal scoping passes its own filter here, and one
    that does not passes nothing and gets the full list.

    This used to reach into an engine module for the request principal, which
    made the concept depend on the thing consuming it. Inverting it keeps the
    fail-closed behaviour available — a host filter that matches nothing
    returns an empty list, never the full registry — while leaving the policy
    where it belongs, with the host."""
    data = load_registry(log_root=log_root)
    ws = list(data.get("workspaces") or [])
    ws.sort(key=lambda w: w.get("added_at", ""))
    if scope is not None:
        ws = list(scope(ws))
    return ws


# ---------------------------------------------------------------------------
# Default workspace bootstrap (#134)
# ---------------------------------------------------------------------------


def bootstrap_default_workspace(*,
                                target: Optional[str | Path] = None,
                                log_root: Optional[Path] = None) -> dict[str, Any]:
    """Create ``~/Documents/Workspaces/`` (or ``target``) if it doesn't exist,
    register it in the workspace registry, and mark it as the default.

    Safe to call repeatedly: existing directory is preserved; an existing
    default record is preserved unless ``target`` overrides it.

    Returns ``{ok, path, created, was_default}``.
    """
    target_path = Path(target).expanduser() if target else DEFAULT_WORKSPACE_DIR
    target_resolved = _resolved(target_path)
    created = False
    if not target_path.exists():
        target_path.mkdir(parents=True, exist_ok=True)
        created = True

    data = load_registry(log_root=log_root)
    was_default = data.get("default") == target_resolved
    # Register + flag as default
    ws: list[dict[str, Any]] = data.get("workspaces") or []
    if not any(w.get("path") == target_resolved for w in ws):
        ws.append({
            "path":     target_resolved,
            "label":    "default",
            "added_at": _now_iso(),
        })
    data["workspaces"] = ws
    data["default"] = target_resolved
    _save_registry(data, log_root=log_root)

    return {
        "ok":          True,
        "path":        target_resolved,
        "created":     created,
        "was_default": was_default,
    }
