# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Workspace identity — when are two paths the same workspace?

The question is not rhetorical. `~/Workspaces` and `~/workspaces`
are one folder on APFS and two on ext4; a symlink may merge two paths onto one
physical directory, or may be exactly the boundary you meant to keep. Everything
that accumulates per workspace — a log, a registry entry, a memory — hangs off
the answer, so the rule has to be stated once and applied everywhere.

Pure stdlib. No engine, no I/O beyond a filesystem probe.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

def _filesystem_is_case_insensitive(path: Path) -> bool:
    """Best-effort detection: does the filesystem at this path treat
    'Foo' and 'foo' as the same entry?

    macOS APFS (default) and Windows NTFS are case-insensitive.
    Linux ext4/xfs are case-sensitive. On detection failure defaults to
    True (over-normalising is safer than under-normalising).
    """
    try:
        import os
        if not path.exists():
            path = path.parent if path.parent.exists() else Path.home()
        s = os.path.dirname(str(path))
        n = os.path.basename(str(path))
        if not n or not s:
            return True
        flipped = n.swapcase()
        if flipped == n:
            return True   # no alphabetic chars to probe with
        try:
            orig_stat = path.stat()
            flipped_path = Path(s) / flipped
            flipped_stat = flipped_path.stat()
            return orig_stat.st_ino == flipped_stat.st_ino
        except (OSError, FileNotFoundError):
            return False
    except Exception:
        return True


def folder_hash(folder_path: str | Path) -> str:
    """Stable identifier for a folder.

    Phase 2 (post-#162): on case-insensitive filesystems (APFS, NTFS),
    the resolved absolute path is lower-cased before hashing. This way
    "~/Workspaces" and "~/workspaces" — same physical folder
    on macOS — produce the same hash. Workspace identity follows the
    inode, not the path-string case.

    B6.3 (0.6.8): symlink resolution honours :envvar:`WORKSPACE_SYMLINK_MODE`.
    Default ``follow`` keeps pre-0.6.8 behaviour (symlinks dereferenced;
    same physical folder via two paths shares one log). ``isolate`` keeps
    the symlink path distinct (one log per path; intentionally breaks
    symlink-merged workspaces).

    Returns a 32-char prefix of the SHA-256 hex digest.
    """
    try:
        from .folder_context import _resolve_with_symlink_policy
        p = _resolve_with_symlink_policy(folder_path)
    except Exception:
        p = Path(folder_path).expanduser().resolve()
    absolute = str(p)
    if _filesystem_is_case_insensitive(p):
        absolute = absolute.lower()
    return hashlib.sha256(absolute.encode("utf-8")).hexdigest()[:32]


def legacy_folder_hash(folder_path: str | Path) -> str:
    """The pre-#162 hash — case-SENSITIVE on the resolved path string.

    Kept because logs written before the fix live under this hash. A reader
    falls back to it when a fresh :func:`folder_hash` lookup misses, so old
    data still resolves. Dropping it does not fail loudly; it silently stops
    finding history, which is the worst failure a lookup can have.
    """
    absolute = str(Path(folder_path).expanduser().resolve())
    return hashlib.sha256(absolute.encode("utf-8")).hexdigest()[:32]
