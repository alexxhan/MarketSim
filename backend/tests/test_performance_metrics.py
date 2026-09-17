import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.market.order import Order, OrderSide
from app.simulation.engine import SimulationEngine


class PerformanceMetricsTests(unittest.TestCase):
    def make_engine(self, strategy="basic"):
        engine = SimulationEngine(strategy=strategy, seed=42)
        engine.order_book.add_order(Order(100, OrderSide.BUY, 99, 100))
        engine.order_book.add_order(Order(101, OrderSide.SELL, 101, 100))
        return engine

    def test_external_trades_are_not_market_maker_fills(self):
        for strategy in ("basic", "inventory"):
            with self.subTest(strategy=strategy):
                engine = SimulationEngine(strategy=strategy, order_arrival_rate=2)
                orders = [
                    Order(1, OrderSide.BUY, 100, 4),
                    Order(2, OrderSide.SELL, 99, 4)
                ]
                with patch.object(engine.order_flow, "generate_order", side_effect=orders):
                    metrics = engine.step()["metrics"]
                self.assertEqual(metrics["total_market_trades"], 1)
                for key in (
                    "market_maker_fills", "market_maker_buy_fills",
                    "market_maker_sell_fills", "market_maker_executed_volume"
                ):
                    self.assertEqual(metrics[key], 0)
                self.assertIsNone(metrics["pnl_per_fill"])

    def test_fill_counts_volume_and_inventory_statistics(self):
        for strategy in ("basic", "inventory"):
            with self.subTest(strategy=strategy):
                engine = self.make_engine(strategy)
                orders = [
                    Order(1, OrderSide.SELL, 99, 4),
                    Order(2, OrderSide.BUY, 101, 7),
                    Order(3, OrderSide.BUY, 98, 1)
                ]
                with patch.object(engine.order_flow, "generate_order", side_effect=orders):
                    states = [engine.step() for _ in orders]
                self.assertEqual([state["inventory"] for state in states], [4, -3, -3])
                first = states[0]["metrics"]
                self.assertEqual(first["market_maker_buy_fills"], 1)
                self.assertEqual(first["market_maker_sell_fills"], 0)
                self.assertEqual(first["market_maker_executed_volume"], 4)
                metrics = states[-1]["metrics"]
                self.assertEqual(metrics["total_market_trades"], 2)
                self.assertEqual(metrics["market_maker_fills"], 2)
                self.assertEqual(metrics["market_maker_buy_fills"], 1)
                self.assertEqual(metrics["market_maker_sell_fills"], 1)
                self.assertEqual(metrics["market_maker_executed_volume"], 11)
                self.assertEqual(metrics["average_absolute_inventory"], 10 / 3)
                self.assertEqual(metrics["maximum_absolute_inventory"], 4)
                self.assertEqual(metrics["pnl_per_fill"], states[-1]["pnl"] / 2)

    def test_partial_fills_count_each_trade_and_exclude_external_remainder(self):
        engine = self.make_engine()
        engine.order_arrival_rate = 2
        orders = [Order(1, OrderSide.SELL, 99, 3), Order(2, OrderSide.SELL, 99, 12)]
        with patch.object(engine.order_flow, "generate_order", side_effect=orders):
            state = engine.step()
        metrics = state["metrics"]
        self.assertEqual(metrics["total_market_trades"], 3)
        self.assertEqual(metrics["market_maker_fills"], 2)
        self.assertEqual(metrics["market_maker_buy_fills"], 2)
        self.assertEqual(metrics["market_maker_sell_fills"], 0)
        self.assertEqual(metrics["market_maker_executed_volume"], 10)
        self.assertEqual(state["inventory"], 10)

    def test_zero_fills_with_valid_pnl(self):
        engine = self.make_engine()
        with patch.object(engine.order_flow, "generate_order", return_value=Order(1, OrderSide.BUY, 98, 1)):
            state = engine.step()
        self.assertEqual(state["pnl"], 0)
        self.assertEqual(state["metrics"]["market_maker_fills"], 0)
        self.assertIsNone(state["metrics"]["pnl_per_fill"])
        self.assertEqual(state["metrics"]["average_absolute_inventory"], 0)
        self.assertEqual(state["metrics"]["maximum_absolute_inventory"], 0)

    def test_one_sided_book_retains_marked_pnl(self):
        engine = SimulationEngine(seed=42)
        engine.order_book.add_order(Order(100, OrderSide.BUY, 99, 1))
        engine.order_book.add_order(Order(101, OrderSide.SELL, 101, 1))
        with patch.object(engine.order_flow, "generate_order", return_value=Order(1, OrderSide.BUY, 102, 11)):
            state = engine.step()
        self.assertIsNone(state["midprice"])
        self.assertEqual(state["mark_price"], 100)
        self.assertAlmostEqual(state["pnl"], 0.20)
        self.assertEqual(state["metrics"]["market_maker_fills"], 1)
        self.assertEqual(state["metrics"]["market_maker_sell_fills"], 1)
        self.assertEqual(state["metrics"]["market_maker_executed_volume"], 10)
        self.assertAlmostEqual(state["metrics"]["pnl_per_fill"], 0.20)

    def test_seeded_api_results_and_metrics_are_deterministic(self):
        with TestClient(app) as client:
            self.assertEqual(client.get("/health").status_code, 200)
            for strategy in ("basic", "inventory"):
                with self.subTest(strategy=strategy):
                    config = dict(
                        strategy=strategy, ticks=1000, seed=42,
                        starting_price=100, volatility=3, buy_pressure=0.5,
                        order_arrival_rate=3, spread=0.04, order_size=10,
                        inventory_risk_factor=0.001
                    )
                    runs = []
                    for _ in range(3):
                        response = client.post("/simulation/run", json=config)
                        self.assertEqual(response.status_code, 200)
                        runs.append(response.json())
                    self.assertEqual(runs[0], runs[1])
                    self.assertEqual(runs[0], runs[2])
                    results = runs[0]["results"]
                    inventories = runs[0]["history"]["inventory"]
                    self.assertEqual(results["total_market_trades"], results["total_trades"])
                    self.assertEqual(results["average_absolute_inventory"], sum(map(abs, inventories)) / 1000)
                    self.assertEqual(results["maximum_absolute_inventory"], max(map(abs, inventories)))
                    self.assertEqual(results["pnl_per_fill"], results["final_pnl"] / results["market_maker_fills"])


if __name__ == "__main__":
    unittest.main()
