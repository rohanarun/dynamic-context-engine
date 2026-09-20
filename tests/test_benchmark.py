import unittest
from benchmarks.website_replay import costs

class BenchmarkAccountingTests(unittest.TestCase):
    def test_counts_selector_cost_and_preserves_request_cost(self):
        rates={'jev_input_per_million':.042,'generation_input_per_million':.75,'generation_cached_input_per_million':.075}
        result=costs(100000,20000,1000,150000,rates)
        cold=result['comparisons']['uncached']
        self.assertAlmostEqual(result['jev_usd'],.0063)
        self.assertAlmostEqual(cold['baseline_usd'],.07575)
        self.assertAlmostEqual(cold['dynamic_usd'],.02205)
        self.assertAlmostEqual(cold['net_saved_usd'],.0537)
        self.assertLess(result['comparisons']['baseline_cached_dynamic_uncached']['net_saved_usd'],0)
    def test_no_compression_cannot_claim_savings(self):
        rates={'jev_input_per_million':.042,'generation_input_per_million':.75,'generation_cached_input_per_million':.075}
        result=costs(1000,1000,100,1000,rates)
        for comparison in result['comparisons'].values():
            self.assertLess(comparison['net_saved_usd'],0)
