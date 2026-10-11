import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "config" / "benchmarks" / "public_qubo_benchmark_summary.csv"


class PublicQuboBenchmarkSummaryTests(unittest.TestCase):
    def test_family_counts_sum_to_published_aggregate(self):
        with SUMMARY.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 5)
        family_rows = [row for row in rows if row["instance_family"] != "ALL"]
        aggregate = next(row for row in rows if row["instance_family"] == "ALL")
        for field in (
            "total_instances",
            "classical_lower_objective",
            "equal_objective",
            "dwave_lower_objective",
            "dwave_result_missing",
            "matched_results",
        ):
            self.assertEqual(
                sum(int(row[field]) for row in family_rows),
                int(aggregate[field]),
                msg=f"family rows do not sum to ALL for {field}",
            )

    def test_outcomes_partition_each_family(self):
        with SUMMARY.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        for row in rows:
            self.assertEqual(
                int(row["total_instances"]),
                int(row["classical_lower_objective"])
                + int(row["equal_objective"])
                + int(row["dwave_lower_objective"])
                + int(row["dwave_result_missing"]),
                msg=f"outcome counts do not partition {row['instance_family']}",
            )
            self.assertEqual(
                int(row["matched_results"]),
                int(row["classical_lower_objective"])
                + int(row["equal_objective"])
                + int(row["dwave_lower_objective"]),
                msg=f"matched count mismatch for {row['instance_family']}",
            )
            self.assertEqual(row["source_type"], "published aggregate summary")
            self.assertEqual(row["independent_reanalysis"], "no")
            self.assertTrue(row["source_commit"])


if __name__ == "__main__":
    unittest.main()
