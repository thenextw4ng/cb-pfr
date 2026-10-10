import unittest

from cbpfr.openmc import OpenMCIntegrationError, parse_openmc_stdout_keff


class OpenMCStdoutParserTests(unittest.TestCase):
    def test_parses_combined_keff_mean_and_uncertainty(self):
        mean, uncertainty = parse_openmc_stdout_keff(
            "Some output\nCombined k-effective = 1.00234 +/- 0.00056\n"
        )
        self.assertAlmostEqual(mean, 1.00234)
        self.assertAlmostEqual(uncertainty, 0.00056)

    def test_parses_scientific_notation(self):
        mean, uncertainty = parse_openmc_stdout_keff(
            "Combined k-effective = 9.99E-1 +/- 1.2e-04"
        )
        self.assertAlmostEqual(mean, 0.999)
        self.assertAlmostEqual(uncertainty, 0.00012)

    def test_rejects_missing_keff_line(self):
        with self.assertRaises(OpenMCIntegrationError):
            parse_openmc_stdout_keff("OpenMC completed without a keff summary")


if __name__ == "__main__":
    unittest.main()
