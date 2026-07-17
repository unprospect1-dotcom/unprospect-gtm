import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import job_signals


class JobSignalsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = job_signals.load_config()

    def test_keywords_ignore_comments_and_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "keywords.txt"
            path.write_text("# tier\nSDR\n\nsdr\nprospección\n", encoding="utf-8")
            self.assertEqual(job_signals.load_keywords(path), ["SDR", "prospección"])

    def test_urls_apply_mexico_and_weekly_freshness(self):
        url = job_signals.build_search_urls(
            ["desarrollo de negocios"], "Mexico", 604800
        )[0]
        parsed = __import__("urllib.parse").parse.urlparse(url)
        query = __import__("urllib.parse").parse.parse_qs(parsed.query)
        self.assertEqual(query["keywords"], ["desarrollo de negocios"])
        self.assertEqual(query["location"], ["Mexico"])
        self.assertEqual(query["f_TPR"], ["r604800"])

    def test_actor_input_uses_current_mexico_search_market(self):
        payload = job_signals.actor_input(self.config, 25)
        locations = {
            __import__("urllib.parse").parse.parse_qs(
                __import__("urllib.parse").parse.urlparse(url).query
            )["location"][0]
            for url in payload["urls"]
        }
        self.assertEqual(locations, {"Mexico"})

    def test_normalize_retains_full_source_and_leaves_copy_empty(self):
        description = (
            "Buscamos abrir cuentas nuevas. La persona construirá listas, hará prospección "
            "outbound y generará pipeline para México."
        )
        item = {
            "id": "job-1",
            "link": "https://www.linkedin.com/jobs/view/job-1",
            "title": "Business Development Representative",
            "companyName": "Ejemplo",
            "companyWebsite": "https://www.ejemplo.com/about",
            "companyEmployeesCount": "18 employees",
            "descriptionText": description,
            "companyLogo": "https://cdn.example/logo.png",
            "companyAddress": {"addressCountry": "MX"},
        }
        row = job_signals.normalize_job(item, self.config)
        self.assertEqual(row["description_text"], description)
        self.assertEqual(row["raw_payload"], item)
        self.assertEqual(row["company_domain"], "ejemplo.com")
        self.assertEqual(row["company_employee_count"], 18)
        self.assertEqual(row["company_address_country_code"], "MX")
        self.assertEqual(row["company_region_fit"], "unreviewed")
        self.assertEqual(row["prefilter_priority"], "high")
        self.assertEqual(row["fit"], "unreviewed")
        self.assertEqual(row["signal_fit"], "unreviewed")
        self.assertEqual(row["account_fit"], "unreviewed")
        self.assertEqual(row["prospecting_scope"], "unknown")
        self.assertEqual(row["campaign_action"], "review")
        self.assertIsNone(row["email_1_body"])
        self.assertIsNone(row["email_2_body"])
        packet = job_signals.review_packet(row)
        self.assertEqual(packet["company_website"], "https://www.ejemplo.com/about")
        self.assertIn("signal_fit", packet["required_output"])
        self.assertIn("prospecting_scope", packet["required_output"])

    def test_prefilter_never_makes_final_fit_decision(self):
        row = job_signals.normalize_job(
            {
                "id": "retail-1",
                "title": "Asesor de ventas de piso",
                "descriptionText": "Atención en mostrador dentro de tienda departamental.",
            },
            self.config,
        )
        self.assertEqual(row["prefilter_priority"], "low")
        self.assertEqual(row["fit"], "unreviewed")
        self.assertEqual(row["pipeline_status"], "ready_for_analysis")

    def test_evidence_is_exact_source_text(self):
        description = (
            "Responsabilidades generales.\n"
            "Abrir cuentas nuevas mediante prospección outbound.\n"
            "Preparar reportes semanales."
        )
        evidence = job_signals.extract_evidence(description)
        self.assertIn("Abrir cuentas nuevas mediante prospección outbound.", evidence)
        self.assertTrue(all(fragment in description for fragment in evidence))

    def test_dedupe_keeps_richer_description(self):
        base = {
            "workspace": "unprospect",
            "source": "linkedin_jobs",
            "source_job_id": "same",
        }
        rows = job_signals.dedupe_jobs(
            [{**base, "description_text": "corta"}, {**base, "description_text": "mucho más completa"}]
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["description_text"], "mucho más completa")

    def test_verified_email_is_preferred_over_linkedin_only(self):
        contacts = [
            {
                "id": "a",
                "title": "Director Comercial",
                "email": None,
                "email_status": None,
                "linkedin_url": "https://linkedin.com/in/a",
                "do_not_contact": False,
            },
            {
                "id": "b",
                "title": "Gerente de Ventas",
                "email": "b@example.com",
                "email_status": "VERIFIED",
                "linkedin_url": "https://linkedin.com/in/b",
                "do_not_contact": False,
            },
        ]
        contact, channel = job_signals.choose_contact(contacts, 80, ["VERIFIED"], 90)
        self.assertEqual(contact["id"], "b")
        self.assertEqual(channel, "email")

    def test_recently_contacted_and_do_not_contact_are_excluded(self):
        recent = dt.datetime.now(dt.timezone.utc).isoformat()
        contacts = [
            {
                "id": "a",
                "title": "CEO",
                "email": "a@example.com",
                "email_status": "VERIFIED",
                "do_not_contact": False,
                "last_contacted_at": recent,
            },
            {
                "id": "b",
                "title": "CEO",
                "email": "b@example.com",
                "email_status": "VERIFIED",
                "do_not_contact": True,
            },
        ]
        contact, channel = job_signals.choose_contact(contacts, 10, ["VERIFIED"], 90)
        self.assertIsNone(contact)
        self.assertIsNone(channel)

    def test_plan_is_offline_and_within_configured_budget(self):
        estimate = job_signals.estimate_cost(self.config)
        self.assertLessEqual(estimate, self.config["harvest"]["hard_budget_usd"])
        with mock.patch.object(job_signals, "run_apify") as run:
            code = job_signals.main(["plan", "--max-results", "25"])
        self.assertEqual(code, 0)
        run.assert_not_called()

    def test_copy_module_cannot_be_silently_enabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            config = json.loads(json.dumps(self.config))
            config["analysis"]["copy_module"] = "legacy-copy"
            path.write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaises(ValueError):
                job_signals.load_config(path)

    def test_positive_fit_waits_for_human_before_contact_matching(self):
        self.assertEqual(
            job_signals.analysis_pipeline_status("high", needs_human_review=True),
            "qualified",
        )
        self.assertEqual(
            job_signals.analysis_pipeline_status("high", needs_human_review=False),
            "ready_for_contact",
        )
        self.assertEqual(
            job_signals.analysis_pipeline_status("no_fit", needs_human_review=False),
            "not_fit",
        )

    def test_dimensional_gate_keeps_signal_separate_from_market_fit(self):
        self.assertEqual(
            job_signals.dimensional_pipeline_status(
                "no_fit", "high", "unreviewed", "unreviewed", "likely", "review", True
            ),
            "qualified",
        )
        self.assertEqual(
            job_signals.dimensional_pipeline_status(
                "high", "high", "high", "latam", "verified", "contact", False
            ),
            "ready_for_contact",
        )
        self.assertEqual(
            job_signals.dimensional_pipeline_status(
                "high", "high", "high", "non_latam", "verified", "exclude", False
            ),
            "not_fit",
        )

    def test_job_country_requirement_is_informational_and_hidden_employer_is_warning(self):
        geo = job_signals.normalize_job(
            {
                "id": "geo",
                "title": "BDR",
                "descriptionText": "Outbound role. Based in Colombia (required).",
            },
            self.config,
        )
        hidden = job_signals.normalize_job(
            {
                "id": "hidden",
                "title": "BDR",
                "descriptionText": "Our client is looking for a Business Development Representative.",
            },
            self.config,
        )
        self.assertEqual(geo["prefilter_priority"], "high")
        self.assertEqual(geo["job_location_requirement"], "Colombia")
        self.assertNotIn("geo_mismatch:Colombia", geo["prefilter_reasons"])
        self.assertEqual(geo["company_region_fit"], "unreviewed")
        self.assertEqual(hidden["prefilter_priority"], "low")
        self.assertIn("hidden_employer", hidden["prefilter_reasons"])
        self.assertEqual(hidden["employer_confidence"], "hidden")
        self.assertEqual(hidden["campaign_action"], "hold")

    def test_company_review_consolidates_jobs_without_paraphrasing(self):
        rows = []
        descriptions = [
            "The SDR will build target-account lists and prospect B2B companies in Mexico.",
            "You will run cold calling and outbound email to generate qualified pipeline.",
        ]
        for index, description in enumerate(descriptions, start=1):
            rows.append(
                {
                    "source_job_id": f"job-{index}",
                    "company_name": "Empresa Ejemplo",
                    "company_domain": "ejemplo.com",
                    "role_title": "SDR",
                    "description_text": description,
                    "description_hash": job_signals.description_hash(description),
                    "prefilter_priority": "high",
                    "prefilter_reasons": ["positive:outbound", "positive:pipeline"],
                    "raw_payload": {"companyDescription": "Software B2B para logística."},
                }
            )
        review = job_signals.build_company_review_rows(rows)
        self.assertEqual(len(review), 1)
        self.assertEqual(review[0]["job_count"], 2)
        self.assertIn("build target-account lists", review[0]["description_brief_exact"])
        self.assertIn("cold calling", review[0]["description_brief_exact"])
        for description in descriptions:
            fragment = job_signals.review_description_fragments(description, 1)[0]
            self.assertIn(fragment, review[0]["description_brief_exact"])

    def test_company_review_flags_us_market_without_calling_it_hq(self):
        description = (
            "The BDR will prospect US-based businesses and generate pipeline for the US market."
        )
        rows = [
            {
                "source_job_id": "job-us",
                "company_name": "Empresa LATAM por verificar",
                "role_title": "BDR",
                "description_text": description,
                "prefilter_priority": "high",
                "prefilter_reasons": ["positive:bdr", "positive:pipeline"],
                "raw_payload": {},
            }
        ]
        review = job_signals.build_company_review_rows(rows)[0]
        self.assertIn("United States", review["market_mentions"])
        self.assertIn("Posible venta hacia USA", review["automatic_warnings"])
        self.assertEqual(review["manual_company_base"], "Sin revisar")


if __name__ == "__main__":
    unittest.main()
