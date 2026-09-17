import unittest

from app.simulation.order_flow import OrderFlowGenerator


class SeedTests(unittest.TestCase):
    def test_same_seed_produces_identical_order_flow_and_reference_path(self):
        def sample(seed):
            flow = OrderFlowGenerator(seed=seed)
            observations = []
            for _ in range(50):
                order = flow.generate_order()
                observations.append((order.identity, order.side, order.price, order.quantity, flow.reference_price))
            return observations

        self.assertEqual(sample(42), sample(42))
        self.assertNotEqual(sample(42), sample(43))
