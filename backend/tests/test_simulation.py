import unittest
from unittest.mock import patch

from app.market.order import Order, OrderSide
from app.simulation.engine import SimulationEngine


class SimulationTests(unittest.TestCase):
    def test_crossing_maker_bid_executes_at_resting_ask_before_external_arrival(self):
        engine = SimulationEngine(strategy="inventory", inventory_risk_factor=0.02, seed=42)
        engine.market_maker.portfolio.inventory = -100
        engine.order_book.add_order(Order(900, OrderSide.BUY, 99, 100))
        engine.order_book.add_order(Order(901, OrderSide.SELL, 101, 100))

        def arrival():
            self.assertEqual(engine.market_maker.portfolio.inventory, -90)
            self.assertEqual(engine.market_maker.portfolio.cash, 98990)
            self.assertEqual(engine.order_book.get_best_ask().quantity, 90)
            return Order(1, OrderSide.SELL, 100, 1)

        with patch.object(engine.order_flow, "generate_order", side_effect=arrival):
            state = engine.step()
        self.assertEqual([(t.price, t.quantity) for t in state["trades"]], [(101, 10)])
        self.assertEqual(state["metrics"]["market_maker_buy_fills"], 1)

    def test_crossing_maker_quote_executes_before_external_arrival(self):
        engine = SimulationEngine(strategy="inventory", inventory_risk_factor=0.02, seed=42)
        engine.market_maker.portfolio.inventory = 100
        engine.order_book.add_order(Order(900, OrderSide.BUY, 99, 100))
        engine.order_book.add_order(Order(901, OrderSide.SELL, 101, 100))

        def arrival():
            self.assertEqual(engine.market_maker.portfolio.inventory, 90)
            self.assertEqual(engine.market_maker.portfolio.cash, 100990)
            self.assertEqual(engine.order_book.get_best_bid().quantity, 90)
            self.assertEqual(engine.order_book.get_best_ask().price, 101)
            return Order(1, OrderSide.BUY, 100, 1)

        with patch.object(engine.order_flow, "generate_order", side_effect=arrival):
            state = engine.step()
        self.assertEqual([(t.price, t.quantity) for t in state["trades"]], [(99, 10)])
        self.assertEqual(state["metrics"]["market_maker_sell_fills"], 1)

    def test_one_cent_spreads_never_self_trade_or_leave_crossed_book(self):
        for strategy in ("basic", "inventory"):
            engine = SimulationEngine(strategy=strategy, spread=0.01, volatility=3, order_arrival_rate=3, seed=42)
            cash, inventory = 100000, 0
            for _ in range(100):
                state = engine.step()
                for trade in state["trades"]:
                    bought = trade.buyer_owner == engine.market_maker.owner
                    sold = trade.seller_owner == engine.market_maker.owner
                    self.assertFalse(bought and sold)
                    if bought:
                        cash -= trade.price * trade.quantity
                        inventory += trade.quantity
                    if sold:
                        cash += trade.price * trade.quantity
                        inventory -= trade.quantity
                self.assertAlmostEqual(state["cash"], cash)
                self.assertEqual(state["inventory"], inventory)
                if state["best_bid"] and state["best_ask"]:
                    self.assertLess(state["best_bid"].price, state["best_ask"].price)
                metrics = state["metrics"]
                self.assertEqual(metrics["market_maker_fills"], metrics["market_maker_buy_fills"] + metrics["market_maker_sell_fills"])

    def test_tick_end_exposure_does_not_claim_intratick_peak(self):
        engine = SimulationEngine(order_arrival_rate=2)
        engine.order_book.add_order(Order(900, OrderSide.BUY, 99, 100))
        engine.order_book.add_order(Order(901, OrderSide.SELL, 101, 100))
        orders = [Order(1, OrderSide.SELL, 99.98, 10), Order(2, OrderSide.BUY, 100.02, 10)]
        with patch.object(engine.order_flow, "generate_order", side_effect=orders):
            state = engine.step()
        self.assertEqual(state["inventory"], 0)
        self.assertEqual(state["metrics"]["maximum_absolute_inventory"], 0)
        self.assertEqual(state["metrics"]["average_absolute_inventory"], 0)
        self.assertAlmostEqual(state["pnl"], 0.40)
