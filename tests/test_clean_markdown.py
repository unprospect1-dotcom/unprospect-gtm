import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / ".claude" / "skills" / "gtm-web-crawler" / "clean_markdown.py"
SPEC = importlib.util.spec_from_file_location("clean_markdown_v2", MODULE_PATH)
CLEANER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLEANER)


SAMPLE = """# /
Inicio
[Servicios](https://example.com/servicios)
Ayudamos a empresas manufactureras con software de logística B2B.
-15%
AI
S.A.
![Logo Cliente Norte](https://cdn.example.com/logo-norte.png)
[Ver caso de éxito](https://example.com/casos/norte.pdf)
ISO 9001
Nombre
Mensaje
Enviar
# /legal
ISO 9001
"""


class CleanMarkdownV2Test(unittest.TestCase):
    def test_clean_text_retains_short_and_structured_facts(self):
        result = CLEANER.analyze_markdown(SAMPLE)
        clean = result["clean_text"]
        for expected in ("-15%", "AI", "S.A.", "ISO 9001", "Logo Cliente Norte"):
            with self.subTest(expected=expected):
                self.assertIn(expected, clean)

    def test_navigation_and_form_noise_are_removed(self):
        clean = CLEANER.clean_markdown(SAMPLE)
        for noise in ("Inicio", "Nombre", "Mensaje", "Enviar"):
            with self.subTest(noise=noise):
                self.assertNotIn(f"\n{noise}\n", f"\n{clean}\n")

    def test_privacy_page_does_not_take_over_segmentation_context(self):
        privacy = " ".join([
            "Aviso de privacidad para clientes, empleados y proveedores. "
            "Tratamos datos personales para prestar nuestros servicios."
        ] * 80)
        sample = ("# /\nSoftware de inventarios para fabricantes B2B.\n"
                  "# /aviso-de-privacidad\nRazón social: Demo S.A. de C.V.\n" + privacy)
        context = CLEANER.build_segmentation_context(sample, 10_000)["text"]
        self.assertIn("Software de inventarios", context)
        self.assertLess(len(context), 2_500)

    def test_visual_and_case_evidence_are_kept_as_metadata(self):
        meta = CLEANER.analyze_markdown(SAMPLE)["meta"]
        self.assertTrue(any(item["alt"] == "Logo Cliente Norte" for item in meta["visual_assets"]))
        self.assertTrue(any("casos/norte.pdf" in item["url"] for item in meta["evidence_links"]))

    def test_legacy_pages_receive_visual_and_case_metadata(self):
        meta = CLEANER.analyze_markdown(SAMPLE)["meta"]
        original = [{"path": "/", "url": "https://example.com"},
                    {"path": "/legal", "url": "https://example.com/legal"}]
        enriched = CLEANER.attach_evidence_to_pages(original, meta)
        self.assertNotIn("visual_assets", original[0])
        self.assertTrue(any(item["alt"] == "Logo Cliente Norte"
                            for item in enriched[0]["visual_assets"]))
        self.assertTrue(any("casos/norte.pdf" in item["url"]
                            for item in enriched[0]["evidence_links"]))

    def test_segmentation_context_covers_gtm_questions_and_budget(self):
        result = CLEANER.analyze_markdown(SAMPLE, max_context_chars=500)
        context = result["segmentation_context"]
        self.assertLessEqual(len(context), 500)
        self.assertIn("software de logística B2B", context)
        self.assertIn("caso de éxito", context)
        self.assertTrue({"offer", "audience", "industry", "proof", "b2b"}.issubset(
            set(result["meta"]["context_categories"])
        ))

    def test_tel_and_mailto_keep_visible_values(self):
        source = """# /contacto
Teléfono: [777 804 4933](tel:7778044933)
[Escríbenos](mailto:ventas@example.com)
"""
        clean = CLEANER.clean_markdown(source)
        self.assertIn("777 804 4933", clean)
        self.assertIn("ventas@example.com", clean)

    def test_visible_phone_wins_over_placeholder_tel_target(self):
        source = "# /contacto\n[55 3644 9828](tel:123-456-7890)"
        clean = CLEANER.clean_markdown(source)
        self.assertIn("55 3644 9828", clean)
        self.assertNotIn("1234567890", clean)

    def test_malformed_url_does_not_abort_the_site(self):
        clean = CLEANER.clean_markdown("# /\nProducto https://[broken-ipv6")
        self.assertIn("Producto", clean)

    def test_b2c_audience_evidence_is_prioritized(self):
        source = "# /\nCrédito educativo diseñado para estudiantes y sus familias."
        result = CLEANER.analyze_markdown(source, max_context_chars=300)
        self.assertIn("estudiantes y sus familias", result["segmentation_context"])
        self.assertIn("audience", result["meta"]["context_categories"])

    def test_spanish_organization_language_is_a_b2b_signal(self):
        sample = ("# /\nConectamos talento C-level con organizaciones que están "
                  "redefiniendo industrias. Ofrecemos servicios de executive search.")
        result = CLEANER.build_segmentation_context(sample)
        self.assertIn("b2b", result["meta"]["context_categories"])

    def test_context_limits_visual_lines_but_metadata_keeps_assets(self):
        images = "\n".join(
            f"![Logo Cliente {index}](https://cdn.example.com/cliente-{index}.png)"
            for index in range(12)
        )
        result = CLEANER.analyze_markdown("# /clientes\n" + images, max_context_chars=1000)
        self.assertLessEqual(result["segmentation_context"].count("Imagen:"), 5)
        self.assertEqual(12, len(result["meta"]["visual_assets"]))


if __name__ == "__main__":
    unittest.main()
