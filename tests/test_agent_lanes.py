import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_agent_compat import frontmatter, validate_agent_lanes  # noqa: E402

CHEAP_LANES = {"gtm-classifier", "gtm-profiler"}


class AgentLanesTest(unittest.TestCase):
    def test_lanes_are_valid(self):
        self.assertEqual([], validate_agent_lanes())

    def test_claude_md_imports_agents_md(self):
        claude_md = ROOT / "CLAUDE.md"
        self.assertTrue(claude_md.is_file(), "Claude Code no lee AGENTS.md; falta CLAUDE.md")
        self.assertIn("@AGENTS.md", claude_md.read_text(encoding="utf-8"))

    def test_required_claude_lanes_exist(self):
        names = {
            frontmatter(path).get("name")
            for path in (ROOT / ".claude" / "agents").glob("*.md")
        }
        self.assertLessEqual({"gtm-classifier", "gtm-verifier", "gtm-profiler"}, names)

    def test_cheap_lanes_use_cheap_model(self):
        for path in (ROOT / ".claude" / "agents").glob("*.md"):
            meta = frontmatter(path)
            if meta.get("name") in CHEAP_LANES:
                self.assertEqual("haiku", meta.get("model"), path.name)

    def test_worker_lanes_do_not_inherit_all_tools(self):
        for path in (ROOT / ".claude" / "agents").glob("*.md"):
            tools = frontmatter(path).get("tools", "")
            self.assertNotIn("Bash", tools, f"{path.name}: los workers no necesitan Bash")
            self.assertIn("Read", tools, path.name)


if __name__ == "__main__":
    unittest.main()
