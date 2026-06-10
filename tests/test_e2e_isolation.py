"""The e2e plugin-isolation guarantee, tested without spending a token.

Sessions in the Tier 2 harness only ever receive a frozen snapshot of the
plugin as --plugin-dir, and the suite hash-verifies the snapshot at exit
(tests/e2e/lib.sh). These tests drive those bash functions directly:
snapshot creation carries the runtime payload and excludes repo junk,
verification passes on an untouched snapshot, any mutation (edit, add,
delete) is detected and fails, and fanout children adopt the parent's
snapshot instead of creating their own.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="the e2e harness is POSIX-only (bash, rsync, shasum); see TESTING.md",
)

REPO = Path(__file__).resolve().parent.parent
LIB = REPO / "tests" / "e2e" / "lib.sh"


def run_lib(script: str, **env: str) -> subprocess.CompletedProcess:
    """Run a bash snippet with lib.sh sourced; returns the completed process."""
    full_env = {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "HOME": str(REPO),  # never the real home
        "CLAUDITY_E2E_ART_DIR": "/tmp/claudity-e2e-art-test",
        **env,
    }
    return subprocess.run(
        ["bash", "-c", f'source "{LIB}"\n{script}'],
        capture_output=True,
        text=True,
        timeout=120,
        env=full_env,
    )


@pytest.fixture()
def snapshot(tmp_path: Path):
    """A real snapshot of this repo; yields its path, removes it after."""
    marker = tmp_path / "plugin_dir"
    proc = run_lib(f'ensure_plugin_snapshot && printf "%s" "$PLUGIN_DIR" > "{marker}"')
    assert proc.returncode == 0, proc.stderr
    snap = Path(marker.read_text())
    assert snap.is_dir()
    yield snap
    subprocess.run(["rm", "-rf", str(snap), f"{snap}.manifest"], check=False)


class TestSnapshotContents:
    def test_runtime_payload_present(self, snapshot: Path) -> None:
        for rel in (
            ".claude-plugin/plugin.json",
            ".mcp.json",
            "skills/start/SKILL.md",
            "agents/general-thinker.md",
            "scripts/mcp_server.py",
            "scripts/protocol_status.py",
        ):
            assert (snapshot / rel).is_file(), f"snapshot missing {rel}"

    def test_repo_junk_excluded(self, snapshot: Path) -> None:
        assert not (snapshot / ".git").exists()
        assert not (snapshot / ".venv").exists()

    def test_manifest_written_outside_snapshot(self, snapshot: Path) -> None:
        manifest = Path(f"{snapshot}.manifest")
        assert manifest.is_file()
        assert "scripts/mcp_server.py" in manifest.read_text()


class TestVerification:
    def _verify(self, snapshot: Path) -> subprocess.CompletedProcess:
        return run_lib(
            'PLUGIN_DIR="$CLAUDITY_E2E_PLUGIN_DIR"; '
            'PLUGIN_MANIFEST="$PLUGIN_DIR.manifest"; '
            "PLUGIN_SNAPSHOT_OWNED=1; verify_plugin_snapshot",
            CLAUDITY_E2E_PLUGIN_DIR=str(snapshot),
        )

    def test_untouched_snapshot_verifies(self, snapshot: Path) -> None:
        proc = self._verify(snapshot)
        assert proc.returncode == 0, proc.stderr

    def test_edit_detected(self, snapshot: Path) -> None:
        target = snapshot / "skills" / "start" / "SKILL.md"
        target.write_text(target.read_text() + "\ntampered\n")
        proc = self._verify(snapshot)
        assert proc.returncode != 0
        assert "MUTATED" in proc.stderr
        assert "skills/start/SKILL.md" in proc.stderr

    def test_added_file_detected(self, snapshot: Path) -> None:
        (snapshot / "stray-packet.md").write_text("a session wrote this\n")
        proc = self._verify(snapshot)
        assert proc.returncode != 0
        assert "stray-packet.md" in proc.stderr

    def test_deleted_file_detected(self, snapshot: Path) -> None:
        (snapshot / "scripts" / "mailbox.py").unlink()
        proc = self._verify(snapshot)
        assert proc.returncode != 0
        assert "scripts/mailbox.py" in proc.stderr


class TestFanoutAdoption:
    def test_child_adopts_parent_snapshot(self, snapshot: Path) -> None:
        """With CLAUDITY_E2E_PLUGIN_DIR set, no new snapshot is created and
        the adopter is not the owner (it must neither verify nor remove)."""
        proc = run_lib(
            'ensure_plugin_snapshot && printf "%s %s" "$PLUGIN_DIR" "$PLUGIN_SNAPSHOT_OWNED"',
            CLAUDITY_E2E_PLUGIN_DIR=str(snapshot),
        )
        assert proc.returncode == 0, proc.stderr
        assert proc.stdout == f"{snapshot} 0"
