import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SchemaContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = "\n".join(
            path.read_text(encoding="utf-8").lower()
            for path in sorted((ROOT / "supabase" / "migrations").glob("*.sql"))
        )

    def test_site_crawls_has_clean_text(self):
        self.assertIn("clean_text text", self.sql)

    def test_operational_list_company_columns_are_migrated(self):
        for column in (
            "ads_checked",
            "ads_runs",
            "ads_last_shown",
            "ads_formats",
            "subcat",
            "subcat_confidence",
            "subcat_evidence",
            "subcat_model",
            "subcat_verify",
            "subcat_agree",
        ):
            with self.subTest(column=column):
                self.assertIn(f"add column if not exists {column} ", self.sql)

    def test_job_signal_foreign_keys_are_indexed(self):
        self.assertIn("on public.job_signals (run_id)", self.sql)
        self.assertIn("on public.job_signals (company_id)", self.sql)

    def test_job_signal_market_dimensions_are_separate(self):
        for column in (
            "signal_fit",
            "account_fit",
            "company_region_fit",
            "prospecting_scope",
            "employer_confidence",
            "campaign_action",
        ):
            with self.subTest(column=column):
                self.assertIn(f"add column if not exists {column} ", self.sql)
        self.assertIn("job location alone is never sufficient evidence", self.sql)


if __name__ == "__main__":
    unittest.main()
