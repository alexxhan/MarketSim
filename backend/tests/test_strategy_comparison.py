import unittest

from app.simulation.engine import SimulationEngine


class StrategyComparisonTests(unittest.TestCase):
    def test_paired_marks_and_external_orders_are_independent_of_strategy(self):
        observations = []
        books = []
        for strategy in ("basic", "inventory"):
            engine = SimulationEngine(strategy=strategy, seed=42, volatility=3, order_arrival_rate=3)
            generate = engine.order_flow.generate_order
            flow = []

            def capture():
                order = generate()
                flow.append((order.side, order.price, order.quantity, engine.order_flow.reference_price))
                return order

            engine.order_flow.generate_order = capture
            marks, midprices = [], []
            for _ in range(100):
                state = engine.step()
                marks.append(state["mark_price"])
                midprices.append(state["midprice"])
                self.assertEqual(state["reference_price"], state["mark_price"])
                self.assertAlmostEqual(state["portfolio_value"], state["cash"] + state["inventory"] * state["mark_price"])
                self.assertAlmostEqual(state["pnl"], state["portfolio_value"] - 100000)
            observations.append((flow, marks))
            books.append(midprices)
        self.assertEqual(observations[0], observations[1])
        self.assertNotEqual(books[0], books[1])
