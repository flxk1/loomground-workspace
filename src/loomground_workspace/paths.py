# SPDX-License-Identifier: AGPL-3.0-only
# Copyright 2026 flxk1
"""Where a workspace keeps what it accumulates, by default."""
from __future__ import annotations

from pathlib import Path

#: Default root for per-workspace logs. A caller may override it everywhere it
#: is used; this is the fallback, not a policy.
LOG_ROOT_DEFAULT = Path.home() / ".workspace" / "log"

#: Where workspaces are looked for when nothing says otherwise.
DEFAULT_WORKSPACE_DIR = Path.home() / "Documents" / "Workspaces"
