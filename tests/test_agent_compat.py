import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_agent_compat import skill_names, validate  # noqa: E402


class AgentCompatibilityTest(unittest.TestCase):
    def test_every_canonical_skill_has_one_codex_adapter(self):
        self.assertEqual(
            skill_names(ROOT / ".claude" / "skills"),
            skill_names(ROOT / ".agents" / "skills"),
        )

    def test_adapters_are_valid(self):
        self.assertEqual([], validate())


if __name__ == "__main__":
    unittest.main()
