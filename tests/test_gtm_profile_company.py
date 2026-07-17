import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".claude" / "skills" / "gtm-profile-company" / "scripts" / "validate_profiles.py"
SPEC = importlib.util.spec_from_file_location("validate_profiles", SCRIPT)
VALIDATE_PROFILES = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(VALIDATE_PROFILES)


def valid_profile(domain="example.com"):
    return {
        "domain": domain,
        "entity_type": "company",
        "business_model": "b2b",
        "confidence": "high",
        "b2b_line_present": True,
        "sells": "Software empresarial",
        "primary_customer": "Empresas manufactureras",
        "probable_icp": {
            "company_type": "Plantas industriales",
            "industries": ["Manufactura"],
            "buyer": "Operaciones",
            "geography": [],
        },
        "sales_economics": "plausible",
        "outbound_fit": "high",
        "outbound_scope": "companywide",
        "outbound_reason": "ICP claro y solución empresarial consultiva.",
        "evidence": ["Software empresarial para plantas industriales"],
    }


class ValidateProfilesTests(unittest.TestCase):
    def write_json(self, directory, name, payload):
        path = Path(directory) / name
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def test_accepts_valid_profile_with_literal_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            source = self.write_json(
                directory,
                "source.json",
                {"companies": [{"domain": "example.com", "clean_text": "Software empresarial para plantas industriales"}]},
            )
            results = self.write_json(directory, "results.json", [valid_profile()])
            self.assertEqual([], VALIDATE_PROFILES.validate(source, results))

    def test_rejects_nonliteral_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            source = self.write_json(
                directory,
                "source.json",
                {"companies": [{"domain": "example.com", "clean_text": "Software empresarial para plantas industriales"}]},
            )
            profile = valid_profile()
            profile["evidence"] = ["cita inventada"]
            results = self.write_json(directory, "results.json", [profile])
            errors = VALIDATE_PROFILES.validate(source, results)
            self.assertTrue(any("not a literal" in error for error in errors))

    def test_noncommercial_requires_not_applicable_and_no_outbound(self):
        with tempfile.TemporaryDirectory() as directory:
            source = self.write_json(
                directory,
                "source.json",
                {"companies": [{"domain": "example.com", "clean_text": "Organismo público"}]},
            )
            profile = valid_profile()
            profile.update(
                {
                    "entity_type": "government",
                    "business_model": "noncommercial",
                    "b2b_line_present": False,
                    "sales_economics": "weak",
                    "outbound_fit": "medium",
                    "outbound_scope": "unclear",
                    "evidence": ["Organismo público"],
                }
            )
            results = self.write_json(directory, "results.json", [profile])
            errors = VALIDATE_PROFILES.validate(source, results)
            self.assertTrue(any("sales_economics=not_applicable" in error for error in errors))
            self.assertTrue(any("outbound_fit=low" in error for error in errors))

    def test_prospectable_scope_requires_b2b_line(self):
        with tempfile.TemporaryDirectory() as directory:
            source = self.write_json(
                directory,
                "source.json",
                {"companies": [{"domain": "example.com", "clean_text": "Guía informativa"}]},
            )
            profile = valid_profile()
            profile.update(
                {
                    "entity_type": "media_or_directory",
                    "business_model": "unclear",
                    "b2b_line_present": False,
                    "sales_economics": "unclear",
                    "outbound_fit": "medium",
                    "outbound_scope": "b2b_line_only",
                    "evidence": ["Guía informativa"],
                }
            )
            results = self.write_json(directory, "results.json", [profile])
            errors = VALIDATE_PROFILES.validate(source, results)
            self.assertTrue(any("high/medium outbound_fit" in error for error in errors))
            self.assertTrue(any("prospectable outbound_scope" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
