import unittest
from unittest.mock import patch

from app.market.order import OrderSide
from app.simulation.order_flow import OrderFlowGenerator


class MarketConditionsTests(unittest.TestCase):
    def test_extreme_pressure_controls_side_and_zero_volatility_keeps_reference(self):
        for pressure, side in ((0, OrderSide.SELL), (1, OrderSide.BUY)):
            flow = OrderFlowGenerator(volatility=0, buy_pressure=pressure, seed=42)
            for _ in range(30):
                order = flow.generate_order()
                self.assertEqual(order.side, side)
                self.assertEqual(flow.reference_price, 100)
                self.assertGreaterEqual(order.price, 99.95)
                self.assertLessEqual(order.price, 100.05)

    def test_reference_move_and_order_offset_are_separate(self):
        flow = OrderFlowGenerator(starting_price=100, volatility=3, seed=42)
        with patch.object(flow.rng, "random", return_value=0.2), patch.object(flow.rng, "randint", side_effect=[3, -5, 7]):
            order = flow.generate_order()
        self.assertEqual(flow.reference_price, 100.03)
        self.assertEqual(order.price, 99.98)
        self.assertEqual(order.quantity, 7)
        self.assertEqual(order.side, OrderSide.BUY)
