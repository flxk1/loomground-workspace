# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 flxk1
"""Tests for loomground_workspace — the workspace concept, engine-free."""
from __future__ import annotations

import ast
import os
import pathlib
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import loomground_workspace as w  # noqa: E402

SRC = pathlib.Path(__file__).resolve().parents[1] / "src" / "loomground_workspace"


class TestBoundary(unittest.TestCase):
    """The property the whole split rests on: engines import THIS."""

    def test_no_module_imports_an_engine(self):
        """Reports WHICH import broke the rule — a bare assertion that the
        package is clean tells the next person nothing about what to fix.

        `workspace_registry.list_known_workspaces` used to reach into an
        engine module for the request principal. That is why this test exists
        and why it names offenders."""
        engines = {"rvnd", "workspaces", "mcp_serving", "mutation_log", "memory",
                   "loomground_solver", "loomground_governance"}
        offenders = []
        for path in SRC.glob("*.py"):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                mods = []
                if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                    mods = [node.module]
                elif isinstance(node, ast.Import):
                    mods = [a.name for a in node.names]
                for m in mods:
                    if m.split(".")[0] in engines:
                        offenders.append(f"{path.name}: {m}")
        self.assertEqual(offenders, [])

    def test_the_package_declares_no_dependencies(self):
        import tomllib
        toml = tomllib.loads((SRC.parents[1] / "pyproject.toml").read_text())
        self.assertEqual(toml["project"]["dependencies"], [])


class TestIdentity(unittest.TestCase):
    def test_the_legacy_hash_survives(self):
        """Logs written before #162 live under the case-SENSITIVE hash. A
        reader falls back to it when a fresh lookup misses. Dropping it does
        not fail loudly — it silently stops finding history."""
        self.assertTrue(callable(w.legacy_folder_hash))
        h = w.legacy_folder_hash("/tmp/Some/Folder")
        self.assertEqual(len(h), 32)
        self.assertEqual(h, w.legacy_folder_hash("/tmp/Some/Folder"))

    def test_legacy_and_current_differ_on_case(self):
        """The legacy hash is case-sensitive; that difference IS the fix, and
        it is why old logs need the old function to be found at all."""
        self.assertNotEqual(w.legacy_folder_hash("/tmp/AAA"),
                            w.legacy_folder_hash("/tmp/aaa"))

    def test_a_hash_is_stable_and_bounded(self):
        h = w.folder_hash("/tmp/x")
        self.assertEqual(len(h), 32)
        self.assertEqual(h, w.folder_hash("/tmp/x"))


class TestScopeIsInjected(unittest.TestCase):
    """Access control belongs to the host, not to the concept."""

    def _registry(self, tmp):
        w.add_known_workspace(str(tmp / "a"), log_root=tmp / "log")
        w.add_known_workspace(str(tmp / "b"), log_root=tmp / "log")
        return tmp / "log"

    def test_no_scope_returns_everything(self):
        import tempfile
        tmp = pathlib.Path(tempfile.mkdtemp())
        lr = self._registry(tmp)
        self.assertEqual(len(w.list_known_workspaces(log_root=lr)), 2)

    def test_a_host_filter_is_applied(self):
        import tempfile
        tmp = pathlib.Path(tempfile.mkdtemp())
        lr = self._registry(tmp)
        only_a = w.list_known_workspaces(
            log_root=lr, scope=lambda ws: [x for x in ws if x["path"].endswith("a")])
        self.assertEqual(len(only_a), 1)

    def test_a_filter_matching_nothing_returns_nothing(self):
        """Fail-closed is preserved through injection: a host filter that
        matches nobody yields an empty list, never the full registry."""
        import tempfile
        tmp = pathlib.Path(tempfile.mkdtemp())
        lr = self._registry(tmp)
        self.assertEqual(w.list_known_workspaces(log_root=lr, scope=lambda ws: []), [])


class TestScope(unittest.TestCase):
    def test_no_context_raises_rather_than_guessing(self):
        with self.assertRaises(w.NoFolderContextError):
            w.resolve_folder_context(None)

    def test_an_unregistered_folder_is_refused(self):
        """Resolution is not merely path arithmetic: an explicit folder must
        still be a registered workspace. The opt-out is explicit and named,
        so "any path works" can never be the accidental default."""
        with self.assertRaises(w.FolderContextNotAllowed):
            w.resolve_folder_context("/tmp")

    def test_the_optout_is_explicit(self):
        import os
        os.environ[w.ALLOW_UNREGISTERED_ENV] = "1"
        try:
            self.assertTrue(w.resolve_folder_context("/tmp").endswith("tmp"))
        finally:
            os.environ.pop(w.ALLOW_UNREGISTERED_ENV, None)


class TestPackaging(unittest.TestCase):
    def test_version_matches_packaging(self):
        import re
        toml = (SRC.parents[1] / "pyproject.toml").read_text()
        self.assertEqual(w.__version__,
                         re.search(r'^version = "([^"]+)"', toml, re.M).group(1))


if __name__ == "__main__":
    unittest.main()
