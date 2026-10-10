"""Regression tests for parsing the scalar keff summary from OpenMC stdout."""
import unittest

from cbpfr.openmc import OpenMCIntegrationError, parse_openmc_stdout_keff


class ParseOpenMCStdoutKeffTests(unittest.TestCase):
    def test_parses_standard_decimal_summary(self):
        self.assertEqual(
            parse_openmc_stdout_keff(
                "  Combined k-effective = 1.1863941447 +/- 0.0000561134"
            ),
            (1.1863941447, 0.0000561134),
        )

    def test_parses_scientific_notation_and_signs(self):
        self.assertEqual(
            parse_openmc_stdout_keff("Combined k-effective = +1.2E+00 +/- 5.6e-05"),
            (1.2, 5.6e-05),
        )

    def test_rejects_missing_or_malformed_summary(self):
        for text in (
            "",
            "k-effective = 1.0 +/- 0.1",
            "Combined k-effective = not-a-number +/- 0.1",
            "Combined k-effective = 1.0",
        ):
            with self.subTest(text=text):
                with self.assertRaises(OpenMCIntegrationError):
                    parse_openmc_stdout_keff(text)


if __name__ == "__main__":
    unittest.main()
