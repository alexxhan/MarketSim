import json
import math
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.market.order import Order, OrderSide
from app.market.validation import SimulationDomainError
from app.simulation.order_flow import OrderFlowGenerator


class DomainValidationTests(unittest.TestCase):
    def requests(self):
        return {
            "/simulation/run": {"ticks": 100, "seed": 42},
            "/experiments/run": {"ticks": 100, "number_of_simulations": 2, "starting_seed": 42},
            "/sweeps/run": {"ticks": 100, "simulations_per_value": 2, "starting_seed": 42,
                            "sweep_parameter": "volatility", "sweep_values": [1, 3]},
            "/scenarios/run": {"seed": 42, "regimes": [{"name": "Test", "duration_ticks": 100,
                                 "volatility": 1, "buy_pressure": 0.5, "order_arrival_rate": 3}]},
        }

    def test_nonfinite_and_wrong_numeric_types_are_rejected_by_every_endpoint(self):
        with TestClient(app) as client:
            for path, config in self.requests().items():
                for field in ("starting_price", "spread", "inventory_risk_factor", "order_size"):
                    for value in (float("nan"), float("inf"), float("-inf"), "Infinity", "NaN", True):
                        with self.subTest(path=path, field=field, value=value):
                            response = client.post(path, content=json.dumps({**config, field: value}),
                                                   headers={"Content-Type": "application/json"})
                            self.assertEqual(response.status_code, 422, response.text)
                            self.assertIn("detail", response.json())

    def test_invalid_parameter_domains(self):
        with TestClient(app) as client:
            for path, config in self.requests().items():
                for field, value in (("starting_price", 0), ("starting_price", -1), ("spread", 0),
                                     ("spread", -1), ("inventory_risk_factor", -1),
                                     ("order_size", 0), ("order_size", -1), ("order_size", 1.5)):
                    with self.subTest(path=path, field=field, value=value):
                        self.assertEqual(client.post(path, json={**config, field: value}).status_code, 422)
                for field, value in (("ticks", 0), ("ticks", 1.5), ("ticks", True),
                                     ("volatility", -1), ("volatility", 21), ("volatility", 1.5),
                                     ("buy_pressure", -0.1), ("buy_pressure", 1.1),
                                     ("buy_pressure", "NaN"), ("order_arrival_rate", 0),
                                     ("order_arrival_rate", 1.5), ("order_arrival_rate", True)):
                    invalid = {**config, field: value}
                    if path == "/scenarios/run":
                        regime_field = "duration_ticks" if field == "ticks" else field
                        invalid = {**config, "regimes": [{**config["regimes"][0], regime_field: value}]}
                    with self.subTest(path=path, field=field, value=value):
                        self.assertEqual(client.post(path, json=invalid).status_code, 422)
            for path in ("/simulation/run", "/scenarios/run"):
                self.assertEqual(client.post(path, json={**self.requests()[path], "strategy": "other"}).status_code, 422)

    def test_dynamic_price_failures_return_controlled_domain_responses(self):
        with TestClient(app) as client:
            for path, config in self.requests().items():
                for overrides in ({"starting_price": 0.01}, {"spread": 300}, {"inventory_risk_factor": 100},
                                  {"starting_price": 1e308}, {"order_size": 10 ** 400}):
                    with self.subTest(path=path, overrides=overrides):
                        response = client.post(path, json={**config, **overrides}, headers={"Origin": "http://localhost:3000"})
                        self.assertEqual(response.status_code, 422, response.text)
                        self.assertIsInstance(response.json()["detail"], str)
                        self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:3000")
                        self.assertNotIn("per_seed", response.json())

    def test_valid_one_sided_runs_keep_finite_marked_value(self):
        with TestClient(app) as client:
            for strategy in ("basic", "inventory"):
                for pressure in (0, 0.7, 1):
                    response = client.post("/simulation/run", json={"strategy": strategy, "seed": 15,
                                           "ticks": 100, "volatility": 3, "order_arrival_rate": 3, "buy_pressure": pressure})
                    self.assertEqual(response.status_code, 200)
                    data = response.json()
                    self.assertTrue(all(math.isfinite(pnl) for pnl in data["history"]["pnl"]))
                    self.assertEqual(data["history"]["reference_price"], data["history"]["mark_price"])
                    result = data["results"]
                    self.assertAlmostEqual(result["final_portfolio_value"], result["final_cash"] + result["final_inventory"] * result["final_mark_price"])
                    if pressure in (0, 1):
                        self.assertIsNone(result["final_midprice"])
                        self.assertEqual(result["final_pnl"], 0)

    def test_low_level_price_guards(self):
        for price in (0, -1, float("inf"), float("nan")):
            with self.subTest(price=price):
                with self.assertRaises(SimulationDomainError):
                    Order(1, OrderSide.BUY, price, 1)
                with self.assertRaises(SimulationDomainError):
                    OrderFlowGenerator(starting_price=price)

    def test_reference_and_external_limit_price_domain_failures_are_distinct(self):
        flow = OrderFlowGenerator(starting_price=0.01, volatility=3, seed=42)
        with patch.object(flow.rng, "randint", return_value=-3):
            with self.assertRaisesRegex(SimulationDomainError, "Reference price must remain positive"):
                flow.generate_order()
        flow = OrderFlowGenerator(starting_price=0.01, volatility=0, seed=42)
        with patch.object(flow.rng, "randint", side_effect=[0, -5, 1]):
            with self.assertRaisesRegex(SimulationDomainError, "Price must remain positive"):
                flow.generate_order()
        self.assertEqual(flow.reference_price, 0.01)
