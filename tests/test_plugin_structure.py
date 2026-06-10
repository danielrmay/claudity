"""Structural tests for the Claudity plugin (Tier 1 — no inference cost).

Guards the invariants that hold the plugin together: manifest validity,
skill/agent/command frontmatter, cross-reference integrity between the
router, process guides, thinker agents, and the status script, the
PORTING.md vendoring rules, and the template-marker coupling between
protocol_init.py and protocol_status.py.

Tests that shell out to the `claude` CLI are skipped when it isn't on PATH.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from protocol_init import init_protocol  # via conftest sys.path
from protocol_status import DEFAULT_DEPENDENCIES, DOCUMENT_PROCESS, check_packet_status

REPO = Path(__file__).resolve().parent.parent
PROCESSES_DIR = REPO / "skills" / "start" / "processes"
AGENTS_DIR = REPO / "agents"
SKILLS_DIR = REPO / "skills"
SKILL_MD = REPO / "skills" / "start" / "SKILL.md"

# Surface skills: user-invocable entries. The router lives in skills/start/
# but is named "start"; the others embed their content directly (no commands).
EXPECTED_SURFACE_SKILLS = {"embed", "status", "decide", "risks", "message"}
# Guides that moved into surface-skill bodies (1:1 user entries).
GUIDE_SKILLS = {
    "decide": "decision-guidance",
    "risks": "failure-brainstorming",
    "message": "message-clarification",
}
EXPECTED_AGENTS = {
    "general-thinker",
    "security-thinker",
    "human-factors-thinker",
    "adversarial-analysis-thinker",
    "codebase-scanner-thinker",
    "security-catalog-thinker",
}
# Shared reference material in processes/, not a routable process.
NON_PROCESS_GUIDES = {"failure-reasoning-guidelines"}

VENDOR_HEADER = "Vendored from microsoft/clarity-agent@6b32c43"
FORBIDDEN_RESIDUE = ["python -m clarity_agent", "`read_thinker_guide`", "pool_add", "failures/pool"]


def parse_frontmatter(path: Path) -> dict[str, str]:
    """Naive single-level YAML frontmatter parser (no dependencies)."""
    lines = path.read_text().splitlines()
    assert lines and lines[0] == "---", f"{path} has no frontmatter"
    end = lines[1:].index("---") + 1
    fm: dict[str, str] = {}
    for line in lines[1:end]:
        m = re.match(r"^([\w-]+):\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"')
    return fm


def frontmatter_block(path: Path) -> str:
    lines = path.read_text().splitlines()
    end = lines[1:].index("---") + 1
    return "\n".join(lines[1:end])


def repo_markdown_files() -> list[Path]:
    skip_parts = {".venv", ".git", "node_modules"}
    return [
        p for p in REPO.rglob("*.md")
        if not (set(p.parts) & skip_parts)
    ]


# -----------------------------------------------------------------------
# Manifests
# -----------------------------------------------------------------------

class TestManifests:
    def test_plugin_json(self) -> None:
        data = json.loads((REPO / ".claude-plugin" / "plugin.json").read_text())
        assert data["name"] == "claudity"
        assert data["version"]
        assert data["description"]

    def test_marketplace_json(self) -> None:
        data = json.loads((REPO / ".claude-plugin" / "marketplace.json").read_text())
        assert data["name"] == "claudity"
        plugins = data["plugins"]
        assert len(plugins) == 1
        source = plugins[0]["source"]
        assert (REPO / source / ".claude-plugin" / "plugin.json").exists()

    def test_versions_agree(self) -> None:
        plugin = json.loads((REPO / ".claude-plugin" / "plugin.json").read_text())
        market = json.loads((REPO / ".claude-plugin" / "marketplace.json").read_text())
        assert plugin["version"] == market["plugins"][0]["version"]


# -----------------------------------------------------------------------
# Frontmatter
# -----------------------------------------------------------------------

class TestFrontmatter:
    def test_skill(self) -> None:
        fm = parse_frontmatter(SKILL_MD)
        assert fm["name"] == "start"
        assert len(fm["description"]) > 100, "skill description is the ambient trigger — keep it substantive"

    def test_agents(self) -> None:
        files = sorted(AGENTS_DIR.glob("*.md"))
        assert {f.stem for f in files} == EXPECTED_AGENTS
        for f in files:
            fm = parse_frontmatter(f)
            assert fm["name"] == f.stem, f"{f.name}: frontmatter name must match filename"
            assert fm["description"], f"{f.name}: missing description"
            tools = {t.strip() for t in fm["tools"].split(",")}
            assert tools <= {"Read", "Grep", "Glob"}, f"{f.name}: thinkers must be read-only, got {tools}"

    def test_surface_skills(self) -> None:
        dirs = {d.name for d in SKILLS_DIR.iterdir() if d.is_dir()} - {"start"}
        assert dirs == EXPECTED_SURFACE_SKILLS
        for name in sorted(EXPECTED_SURFACE_SKILLS):
            fm = parse_frontmatter(SKILLS_DIR / name / "SKILL.md")
            assert fm["name"] == name
            assert fm["description"], f"{name}: missing description"
            assert fm.get("disable-model-invocation") == "true", (
                f"{name}: surface skills are user-invoked only (router handles ambient)"
            )

    def test_guide_skills_carry_vendor_headers(self) -> None:
        for skill, process in GUIDE_SKILLS.items():
            text = (SKILLS_DIR / skill / "SKILL.md").read_text()
            assert f"processes/{process}.md" in text.splitlines()[5], (
                f"{skill}: vendor header for {process} missing under frontmatter"
            )

    def test_frontmatter_is_strict_yaml(self) -> None:
        """Strict parsers silently drop ALL fields on invalid YAML (e.g. an
        unquoted description containing ': '). Caught in the wild by
        `claude plugin tag`; guarded here for every frontmatter file."""
        yaml = pytest.importorskip("yaml")
        files = sorted(SKILLS_DIR.glob("*/SKILL.md")) + sorted(AGENTS_DIR.glob("*.md"))
        bad: list[str] = []
        for f in files:
            try:
                parsed = yaml.safe_load(frontmatter_block(f))
                if not isinstance(parsed, dict):
                    bad.append(f"{f.relative_to(REPO)}: parsed to {type(parsed).__name__}")
            except yaml.YAMLError as e:
                bad.append(f"{f.relative_to(REPO)}: {str(e).splitlines()[0]}")
        assert not bad, f"invalid YAML frontmatter: {bad}"


# -----------------------------------------------------------------------
# Cross-reference integrity
# -----------------------------------------------------------------------

class TestCrossReferences:
    def test_plugin_root_paths_exist(self) -> None:
        """Every ${CLAUDE_PLUGIN_ROOT}/<path> mentioned in repo markdown exists."""
        pattern = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w\-./]+)")
        missing: list[str] = []
        for md in repo_markdown_files():
            for ref in pattern.findall(md.read_text()):
                if not (REPO / ref).exists():
                    missing.append(f"{md.relative_to(REPO)} -> {ref}")
        assert not missing, f"dangling plugin-root references: {missing}"

    def test_process_map_matches_files(self) -> None:
        """SKILL.md's Process Map and the processes/ directory agree."""
        body = SKILL_MD.read_text()
        map_section = body.split("## Process Map")[1].split("##")[0]
        mapped = set(re.findall(r"- \*\*([\w-]+)\*\*", map_section))
        on_disk = {f.stem for f in PROCESSES_DIR.glob("*.md")} | set(GUIDE_SKILLS.values())
        assert mapped <= on_disk, f"process map names without guide files: {mapped - on_disk}"
        assert on_disk - mapped == NON_PROCESS_GUIDES, (
            f"guide files not in process map (and not known references): "
            f"{on_disk - mapped - NON_PROCESS_GUIDES}"
        )

    def test_thinker_table_matches_agents(self) -> None:
        """failure-brainstorming.md's thinker table names real agents."""
        body = (SKILLS_DIR / "risks" / "SKILL.md").read_text()
        table_section = body.split("## Specialist Thinkers")[1].split("## When")[0]
        listed = set(re.findall(r"^\| `([\w-]+)`", table_section, re.MULTILINE))
        assert listed == EXPECTED_AGENTS

    def test_document_process_names_have_guides(self) -> None:
        """Every process the status script can recommend has a guide file."""
        on_disk = {f.stem for f in PROCESSES_DIR.glob("*.md")} | set(GUIDE_SKILLS.values())
        # _resolve_process can also return the dynamic failure phases.
        recommendable = {p for p in DOCUMENT_PROCESS.values() if p} | {
            "failure-brainstorming", "failure-management",
        }
        assert recommendable <= on_disk, f"recommendable without guide: {recommendable - on_disk}"


# -----------------------------------------------------------------------
# Porting invariants
# -----------------------------------------------------------------------

class TestPortingInvariants:
    def vendored_files(self) -> list[Path]:
        guide_skills = [SKILLS_DIR / s / "SKILL.md" for s in GUIDE_SKILLS]
        return sorted(PROCESSES_DIR.glob("*.md")) + sorted(AGENTS_DIR.glob("*.md")) + guide_skills

    def test_vendor_headers_present(self) -> None:
        missing = [
            str(f.relative_to(REPO)) for f in self.vendored_files()
            if VENDOR_HEADER not in f.read_text()
        ]
        assert not missing, f"vendored files without upstream header: {missing}"

    def test_no_harness_residue(self) -> None:
        hits: list[str] = []
        for f in self.vendored_files() + [SKILL_MD]:
            text = f.read_text()
            for bad in FORBIDDEN_RESIDUE:
                if bad in text:
                    hits.append(f"{f.relative_to(REPO)}: {bad}")
        assert not hits, f"upstream harness residue found: {hits}"


# -----------------------------------------------------------------------
# Init <-> status coupling and snippet
# -----------------------------------------------------------------------

class TestProtocolScaffolding:
    def test_init_yields_all_empty(self, tmp_path: Path) -> None:
        """A fresh packet must read 'empty' (not 'untracked') for every tracked doc.

        Guards the documented invariant that protocol_init.py template text
        keeps matching protocol_status.py's TEMPLATE_MARKERS.
        """
        (tmp_path / ".git").mkdir()
        pd = init_protocol(tmp_path)
        report = check_packet_status(pd)
        assert set(report["summary"]["empty"]) == set(DEFAULT_DEPENDENCIES)

    def snippet_template(self) -> str:
        body = (REPO / "skills" / "embed" / "SKILL.md").read_text()
        start = body.index("SNIPPET-TEMPLATE-BEGIN")
        end = body.index("SNIPPET-TEMPLATE-END")
        return body[start:end]

    def test_snippet_markers(self) -> None:
        snippet = self.snippet_template()
        assert "<!-- claudity-begin -->" in snippet
        assert "<!-- claudity-end -->" in snippet
        assert snippet.count("{{PROTOCOL_DIR_NAME}}") >= 2

    def test_snippet_is_portable(self) -> None:
        """The snippet is copied into user projects' CLAUDE.md, where
        ${CLAUDE_PLUGIN_ROOT} is not defined — it must route through the
        plugin's commands/skill instead of invoking script paths."""
        assert "CLAUDE_PLUGIN_ROOT" not in self.snippet_template()

    def test_init_version_matches_plugin(self, tmp_path: Path) -> None:
        """Packets record which Claudity version scaffolded them."""
        (tmp_path / ".git").mkdir()
        pd = init_protocol(tmp_path)
        cfg = json.loads((pd / "config.json").read_text())
        plugin = json.loads((REPO / ".claude-plugin" / "plugin.json").read_text())
        assert cfg["claudity"]["version"] == plugin["version"]


# -----------------------------------------------------------------------
# MCP server declaration and tool surface
# -----------------------------------------------------------------------

class TestMcpServer:
    EXPECTED_TOOLS = {
        "run_clarity", "check_decision", "get_packet_status",
        "read_protocol_document", "write_protocol_document",
        "record_decision", "record_failure", "record_suggestion",
    }

    def test_mcp_json_declares_clarity_agent(self) -> None:
        cfg = json.loads((REPO / ".mcp.json").read_text())
        assert set(cfg["mcpServers"]) == {"clarity-agent"}
        server = cfg["mcpServers"]["clarity-agent"]
        assert server["command"] == "python3"
        script = server["args"][0].replace("${CLAUDE_PLUGIN_ROOT}", str(REPO))
        assert Path(script).exists(), f"server script missing: {script}"
        assert server["env"]["CLAUDITY_PLUGIN_ROOT"] == "${CLAUDE_PLUGIN_ROOT}"

    def test_tool_surface_matches_upstream(self) -> None:
        from mcp_server import TOOLS
        assert {t["name"] for t in TOOLS} == self.EXPECTED_TOOLS

    def test_guide_map_targets_exist(self) -> None:
        from mcp_server import GUIDE_MAP
        for process, rel in GUIDE_MAP.items():
            assert (REPO / rel).exists(), f"GUIDE_MAP[{process}] -> missing {rel}"


# -----------------------------------------------------------------------
# Repo hygiene (e2e sessions know the plugin root and can stray into it)
# -----------------------------------------------------------------------

class TestRepoHygiene:
    def test_no_packet_at_repo_root(self) -> None:
        """A stray session once ran protocol_init/decide against the repo
        itself and the packet got swept into a commit. Never again."""
        assert not (REPO / ".clarity-protocol").exists()
        assert not (REPO / "Clarity Protocol").exists()

    def test_example_packet_matches_manifest(self) -> None:
        """The e2e fixture packet is a frozen snapshot whose states the
        scenarios depend on; a stray session once 'analyzed' it in place.
        Any change must be deliberate (update this manifest when curating)."""
        root = REPO / "tests" / "e2e" / "fixtures" / "feature-flags-cli" / ".clarity-protocol"
        actual = {str(f.relative_to(root)) for f in root.rglob("*") if f.is_file()}
        expected = {
            "config.json", "notes.md", "observations.md", "summary.md",
            "goal/problem.md", "goal/stakeholders.md", "goal/requirements.md",
            "goal/open-questions.md", "goal/resolved-questions.md",
            "solution/solution.md", "solution/architecture.md",
            "solution/solution-summary.md",
            "decisions/decisions.md", "decisions/decision-01-go-vs-rust.md",
            "failures/failures.md", "failures/failure-01-token-replay.md",
            "mailboxes/failure-brainstorm/_config.json",
            "mailboxes/suggestions/_config.json",
            "archive/failure-brainstorm/_config.json",
            "archive/failure-brainstorm/snapshot-20260609-000000/20260609-000000-00-token-replay.md",
            "archive/suggestions/_config.json",
        }
        assert actual == expected, (
            f"unexpected: {sorted(actual - expected)}; missing: {sorted(expected - actual)}"
        )

    def test_showcase_example_matches_manifest(self) -> None:
        """examples/dev-db-snap is a frozen real-session packet; protect it
        from stray e2e sessions the same way as the fixture."""
        root = REPO / "examples" / "dev-db-snap" / ".clarity-protocol"
        actual = {str(f.relative_to(root)) for f in root.rglob("*") if f.is_file()}
        expected = {
            "config.json",
            "decisions/decisions.md",
            "failures/failures.md",
            "goal/open-questions.md",
            "goal/problem.md",
            "goal/requirements.md",
            "goal/resolved-questions.md",
            "goal/stakeholders.md",
            "notes.md",
            "observations.md",
            "solution/architecture.md",
            "solution/solution-summary.md",
            "solution/solution.md",
            "summary.md",
        }
        assert actual == expected, (
            f"unexpected: {sorted(actual - expected)}; missing: {sorted(expected - actual)}"
        )

    def test_showcase_goal_docs_are_real(self) -> None:
        root = REPO / "examples" / "dev-db-snap" / ".clarity-protocol"
        for doc in ("goal/problem.md", "goal/stakeholders.md", "goal/requirements.md"):
            text = (root / doc).read_text()
            assert "[To be determined" not in text and len(text) > 300, f"{doc} looks skeletal"


# -----------------------------------------------------------------------
# Upstream pin consistency (upstream.json is the source of truth)
# -----------------------------------------------------------------------

class TestUpstreamPin:
    # Verbatim vendored files that cannot carry a header comment.
    HEADER_EXEMPT = {
        "skills/risks/security-catalog.csv",
        "skills/start/reference/clarity-agent.upstream.md",
        "skills/embed/SKILL.md",  # snippet inlined as a fenced template; header inside the fence
        "NOTICE.md",  # quotes the upstream license; carries the full pin instead
    }

    def upstream_config(self) -> dict:
        return json.loads((REPO / "upstream.json").read_text())

    def test_watch_locals_exist(self) -> None:
        cfg = self.upstream_config()
        missing = [w["local"] for w in cfg["watch"] if not (REPO / w["local"]).exists()]
        assert not missing, f"watch entries without local files: {missing}"

    def test_vendored_headers_match_pin(self) -> None:
        cfg = self.upstream_config()
        short = cfg["pin"][:7]
        stale: list[str] = []
        for entry in cfg["watch"]:
            local = entry["local"]
            if local in self.HEADER_EXEMPT:
                continue
            if f"clarity-agent@{short}" not in (REPO / local).read_text():
                stale.append(local)
        assert not stale, f"vendored files whose header pin != upstream.json pin: {stale}"

    def test_full_pin_in_docs(self) -> None:
        pin = self.upstream_config()["pin"]
        for doc in ("NOTICE.md", "UPSTREAM.md"):
            assert pin in (REPO / doc).read_text(), f"{doc} missing the full pin {pin}"

    def test_vendored_files_all_watched(self) -> None:
        """Every file carrying a vendor header appears in the watch set."""
        cfg = self.upstream_config()
        watched = {w["local"] for w in cfg["watch"]}
        # SKILL.md and routing.md are rewrites of the watched upstream router.
        rewrites = {"skills/start/SKILL.md", "skills/start/reference/routing.md"}
        unwatched = [
            str(p.relative_to(REPO))
            for p in repo_markdown_files()
            if "clarity-agent@" in p.read_text()
            and str(p.relative_to(REPO)) not in watched | rewrites | self.HEADER_EXEMPT
            # examples/ holds rendered artifacts of watched files (e.g. the
            # embedded CLAUDE.md rendered from the snippet), not vendoring units
            and not str(p.relative_to(REPO)).startswith(("PORTING", "UPSTREAM", "README", "TESTING", "CHANGELOG", "tests/e2e/fixtures/", "examples/"))
        ]
        assert not unwatched, f"files with vendor headers not in upstream.json watch set: {unwatched}"


# -----------------------------------------------------------------------
# Tier 0 via CLI (skipped when claude isn't installed)
# -----------------------------------------------------------------------

needs_claude = pytest.mark.skipif(
    shutil.which("claude") is None, reason="claude CLI not on PATH"
)


@needs_claude
class TestClaudeCli:
    def test_plugin_validate(self) -> None:
        r = subprocess.run(
            ["claude", "plugin", "validate", str(REPO)],
            capture_output=True, text=True, timeout=120,
        )
        assert r.returncode == 0, r.stdout + r.stderr

    def test_component_inventory(self) -> None:
        """Every skill, command, and agent is discovered by the plugin loader."""
        r = subprocess.run(
            ["claude", "--plugin-dir", str(REPO), "plugin", "details", "claudity"],
            capture_output=True, text=True, timeout=120,
        )
        assert r.returncode == 0, r.stdout + r.stderr
        for component in {"start"} | EXPECTED_SURFACE_SKILLS | EXPECTED_AGENTS:
            assert component in r.stdout, f"component not loaded: {component}"
