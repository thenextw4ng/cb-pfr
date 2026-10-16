import importlib.util
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load_script(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/"scripts"/(name+".py"))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
class ResearchExperimentTests(unittest.TestCase):
    def test_convergence_slope_and_defaults(self):
        m=load_script("analyze_c5g7_convergence_study")
        self.assertAlmostEqual(m.slope_per_1000([0,1,2,3]),1000.0)
        self.assertEqual(m.DEFAULTS["minimum_active_batches"],100)
    def test_incremental_qubo_energy(self):
        m=load_script("run_classical_vs_qubo_benchmark");ins=m.Instance(10,1234)
        x=[1,0,1,0,1,0,1,0,1,0];count=sum(x);delta,_,dc=ins.flip_delta(x,2,count)
        y=x.copy();y[2]=1-y[2]
        self.assertAlmostEqual(ins.energy(x)+delta,ins.energy(y));self.assertEqual(dc,-1)
    def test_equal_budget_protocol(self):
        m=load_script("run_equal_budget_c5g7_selection")
        self.assertEqual(m.BUDGET,18);self.assertEqual(len(m.SIGS),6);self.assertAlmostEqual(m.T95_DF4,2.132)
if __name__=="__main__":unittest.main()
