import importlib.util
from pathlib import Path
import sys
import types
import unittest


ROOT = Path(__file__).resolve().parents[1]
CRAWLER_DIR = ROOT / ".claude" / "skills" / "gtm-web-crawler"


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, CRAWLER_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class CrawlSupervisorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(CRAWLER_DIR))
        cls.crawl = load_module("crawler_for_supervisor_tests", "crawl.py")
        cls.supervisor = load_module("crawl_supervisor_for_tests", "crawl_supervisor.py")

    def test_shards_are_disjoint_and_complete(self):
        domains = [f"site-{index}.mx" for index in range(11)]
        shards = [self.crawl.select_shard(domains, 2, index) for index in range(2)]
        self.assertEqual(set(shards[0]) & set(shards[1]), set())
        self.assertEqual(set(shards[0]) | set(shards[1]), set(domains))

    def test_browser_closed_is_restartable(self):
        result = {"error": "Target page, context or browser has been closed"}
        self.assertTrue(self.crawl.browser_is_unavailable(result))
        self.assertFalse(self.crawl.browser_is_unavailable({"error": "ERR_NAME_NOT_RESOLVED"}))

    def test_worker_command_has_unique_shard(self):
        args = types.SimpleNamespace(
            python="python", input="domains.txt", out="crawl_out", max_pages=2,
            depth=1, concurrency_per_worker=3, domain_timeout=45, workers=2,
            cycle_size=20, supabase=True,
        )
        command = self.supervisor.build_worker_command(args, 1)
        self.assertEqual(command[command.index("--shard-count") + 1], "2")
        self.assertEqual(command[command.index("--shard-index") + 1], "1")
        self.assertEqual(command[command.index("--cycle-size") + 1], "20")
        self.assertIn("--supabase", command)
        self.assertIn("--skip-ensure-table", command)


if __name__ == "__main__":
    unittest.main()
