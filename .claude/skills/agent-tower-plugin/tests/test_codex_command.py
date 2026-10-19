#!/usr/bin/env python3
"""The codex command line must stay headless-safe.

Cross-platform compatible (Windows, macOS, Linux).
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "lib"))

from codex_backend import CodexBackend


def _captured_command(monkeypatch):
    """Build the command without launching anything."""
    captured = {}

    async def fake_exec(*args, **kwargs):
        captured["argv"] = list(args)
        raise FileNotFoundError("not launched")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)
    asyncio.run(CodexBackend(timeout=1).invoke("anything"))
    return captured["argv"]


def test_sandbox_mode_is_explicit(monkeypatch):
    """--full-auto was removed in Codex CLI v0.147.0 (openai/codex#36054)."""
    argv = _captured_command(monkeypatch)

    assert argv[:2] == ["codex", "exec"]
    assert "--full-auto" not in argv
    assert argv[argv.index("--sandbox") + 1] == "workspace-write"


def test_approval_policy_is_pinned(monkeypatch):
    """--full-auto also forced `approval: never`; --sandbox alone does not.

    With `approvals_reviewer = "auto_review"` in the user config, an unpinned
    run reports `approval: on-request` and can escalate outside the workspace.
    """
    argv = _captured_command(monkeypatch)

    assert 'approval_policy="never"' in argv
    assert argv[argv.index('approval_policy="never"') - 1] == "-c"
