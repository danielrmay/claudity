"""Shared fixtures for Claudity tests.

Adapted from microsoft/clarity-agent@6b32c43 tests/conftest.py (MIT License,
Copyright (c) Microsoft Corporation). The keyring/Settings fixtures are
dropped (Claudity has no credential store); the scripts/ directory is put on
sys.path so the vendored standalone scripts import as plain modules.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from protocol_init import init_protocol  # noqa: E402


@pytest.fixture
def project_path(tmp_path: Path) -> Path:
    """Return a temporary git project directory (has a .git folder)."""
    (tmp_path / ".git").mkdir()
    return tmp_path


@pytest.fixture
def protocol_dir(project_path: Path) -> Path:
    """Create a .clarity-protocol/ directory with real (non-template) content.

    Returns the path to the .clarity-protocol/ directory.
    """
    init_protocol(project_path)
    pd = project_path / ".clarity-protocol"

    # Write non-template content into the standard documents so that
    # hashing, staleness, and trigger logic have something to work with.
    docs = {
        "summary.md": "# CoffeeFast\n\nA faster coffee brewing system for engineers who can't wait.\n",
        "goal/problem.md": "# Problem\n\nWe need to make coffee faster.\n",
        "goal/stakeholders.md": "# Stakeholders\n\n- Engineers who drink coffee\n",
        "goal/requirements.md": "# Requirements\n\n1. Brew in under 2 minutes\n",
        "goal/open-questions.md": "# Open Questions\n\nNo fundamental unknowns identified.\n",
        "goal/resolved-questions.md": "# Resolved Questions\n\n## Q1: Can we brew under 2 minutes?\n\n**Status:** resolved\n**Resolution:** Yes, with the modular system.\n",
        "solution/solution.md": "# Solution\n\nUse a better coffee machine.\n",
        "solution/architecture.md": "# Architecture\n\nPlug-in modular brewing system.\n",
        "solution/solution-summary.md": "# Solution Summary\n\nA modular brewing system that makes coffee in under 2 minutes.\n",
        "failures/failures.md": "# Failures\n\n- Could run out of beans.\n",
        "decisions/decisions.md": "# Decisions\n\n- Chose pour-over method.\n",
        "notes.md": "# Notes\n\n- Use modular components for maintainability.\n",
        "observations.md": "# Observations\n\nCoverage: Security thinker examined auth and injection surfaces.\n",
    }
    for rel_path, content in docs.items():
        (pd / rel_path).write_text(content)

    return pd
