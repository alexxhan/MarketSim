import unittest

from app.simulation.engine import SimulationEngine


class LiquidityTests(unittest.TestCase):
    def test_activity_is_fixed_arrivals_per_tick(self):
        for activity in (1, 3, 10):
            with self.subTest(activity=activity):
                engine = SimulationEngine(order_arrival_rate=activity, seed=42)
                for _ in range(20):
                    state = engine.step()
                    self.assertEqual(len(state["orders"]), activity)
                self.assertEqual(engine.order_flow.next_order_id, 20 * activity + 1)
