import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / ".claude" / "skills" / "gtm-classify-b2b" / "validate_evidence.py"
SPEC = importlib.util.spec_from_file_location("validate_evidence", MODULE_PATH)
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class B2BEvidenceTests(unittest.TestCase):
    def test_exact_quote_passes(self):
        self.assertTrue(VALIDATOR.evidence_is_exact("crédito para PyMEs", "Ofrecemos crédito para PyMEs.", "b2b"))

    def test_nonliteral_encoding_variant_fails(self):
        self.assertFalse(VALIDATOR.evidence_is_exact("crédito vía nómina", "crÃ©dito vÃ­a nÃ³mina", "b2c"))

    def test_all_array_quotes_must_be_exact(self):
        self.assertFalse(VALIDATOR.evidence_is_exact(["PyMEs", "consumidores"], "Financiamiento para PyMEs", "mixed"))

    def test_unclear_may_describe_missing_content(self):
        self.assertTrue(VALIDATOR.evidence_is_exact("sitio vacío", "", "unclear"))

    def test_failure_names_layer(self):
        classifications = {"example.com": {"label": "b2b", "evidence": "empresas"}}
        verifications = {"example.com": {"verify_label": "b2b", "evidence": "negocios"}}
        failures = VALIDATOR.find_evidence_failures(classifications, verifications, {"example.com": "empresas"})
        self.assertEqual(failures, ["example.com:verify"])


if __name__ == "__main__":
    unittest.main()
