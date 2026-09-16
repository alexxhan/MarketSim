import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.simulation.engine import SimulationEngine
from app.simulation.order_flow import OrderFlowGenerator
from app.simulation.scenario import run_scenario


class ScenarioTests(unittest.TestCase):
    def regimes(self):
        return [
            dict(name="Normal", duration_ticks=2, volatility=1, buy_pressure=0.5, order_arrival_rate=2),
            dict(name="Shock", duration_ticks=3, volatility=5, buy_pressure=0.7, order_arrival_rate=4),
            dict(name="Recovery", duration_ticks=2, volatility=0, buy_pressure=0.3, order_arrival_rate=1)
        ]

    def test_boundaries_total_ticks_and_regime_histories(self):
        response = run_scenario(self.regimes(), seed=42)
        self.assertEqual(response["total_ticks"], 7)
        self.assertEqual(response["regime_boundaries"], [
            dict(regime_id=0, name="Normal", start_tick=1, end_tick=2),
            dict(regime_id=1, name="Shock", start_tick=3, end_tick=5),
            dict(regime_id=2, name="Recovery", start_tick=6, end_tick=7)
        ])
        for run in response["runs"].values():
            self.assertEqual(run["results"]["ticks"], 7)
            self.assertEqual(run["history"]["regime_id"], [0, 0, 1, 1, 1, 2, 2])
            self.assertEqual(run["history"]["regime_name"], ["Normal"] * 2 + ["Shock"] * 3 + ["Recovery"] * 2)
            for values in run["history"].values():
                self.assertEqual(len(values), 7)

    def test_continuous_rng_reference_price_parameters_and_paired_flow(self):
        records = []

        def capture_engine(**config):
            engine = SimulationEngine(**config)
            flow = engine.order_flow
            rng = flow.rng
            record = {"orders": [], "before": [], "after": [], "conditions": []}
            records.append(record)
            generate = flow.generate_order
            step = engine.step

            def capture_order():
                order = generate()
                record["orders"].append((order.order_id, order.side, order.price, order.quantity))
                return order

            def capture_step():
                self.assertIs(engine.order_flow, flow)
                self.assertIs(flow.rng, rng)
                record["before"].append((rng.getstate(), flow.reference_price, flow.next_order_id))
                record["conditions"].append((engine.volatility, engine.buy_pressure, engine.order_arrival_rate, flow.volatility, flow.buy_pressure))
                state = step()
                record["after"].append((rng.getstate(), flow.reference_price, flow.next_order_id))
                return state

            flow.generate_order = capture_order
            engine.step = capture_step
            return engine

        with patch("app.simulation.scenario.SimulationEngine", side_effect=capture_engine) as factory:
            run_scenario(self.regimes(), seed=42, starting_price=100)
        self.assertEqual(factory.call_count, 2)
        self.assertEqual(records[0]["orders"], records[1]["orders"])
        expected_conditions = [(1, 0.5, 2, 1, 0.5)] * 2 + [(5, 0.7, 4, 5, 0.7)] * 3 + [(0, 0.3, 1, 0, 0.3)] * 2
        for record in records:
            self.assertEqual(record["conditions"], expected_conditions)
            self.assertEqual(record["before"][1:], record["after"][:-1])
            self.assertNotEqual(record["before"][2][1], 100)
            self.assertNotEqual(record["before"][2][0], record["before"][0][0])
        generator = OrderFlowGenerator(starting_price=100, seed=42)
        expected_orders = []
        for regime in self.regimes():
            generator.volatility = regime["volatility"]
            generator.buy_pressure = regime["buy_pressure"]
            for _ in range(regime["duration_ticks"] * regime["order_arrival_rate"]):
                order = generator.generate_order()
                expected_orders.append((order.order_id, order.side, order.price, order.quantity))
        self.assertEqual(records[0]["orders"], expected_orders)
        self.assertEqual(records[0]["after"][-1][1], generator.reference_price)
        self.assertEqual(records[0]["after"][-1][0], generator.rng.getstate())

    def test_constant_scenario_matches_existing_simulation(self):
        regime = dict(name="Constant", duration_ticks=100, volatility=3, buy_pressure=0.5, order_arrival_rate=3)
        with TestClient(app) as client:
            for strategy in ("basic", "inventory"):
                config = dict(strategy=strategy, seed=42, starting_price=100, spread=0.04, order_size=10, inventory_risk_factor=0.001)
                original = client.post("/simulation/run", json={**config, "ticks": 100, "volatility": 3, "buy_pressure": 0.5, "order_arrival_rate": 3})
                scenario = client.post("/scenarios/run", json={**config, "regimes": [regime]})
                self.assertEqual(original.status_code, 200)
                self.assertEqual(scenario.status_code, 200)
                run = scenario.json()["runs"][strategy]
                self.assertEqual(run["results"], original.json()["results"])
                for key in ("pnl", "inventory", "midprice"):
                    self.assertEqual(run["history"][key], original.json()["history"][key])
                self.assertEqual(list(scenario.json()["runs"]), [strategy])

    def test_splitting_unchanged_regimes_does_not_change_outcomes(self):
        regime = dict(name="Constant", duration_ticks=100, volatility=3, buy_pressure=0.5, order_arrival_rate=3)
        whole = run_scenario([regime], seed=42)
        split = run_scenario([{**regime, "duration_ticks": 30}, {**regime, "duration_ticks": 70}], seed=42)
        for strategy in ("basic", "inventory"):
            self.assertEqual(whole["runs"][strategy]["results"], split["runs"][strategy]["results"])
            for key in ("pnl", "inventory", "midprice"):
                self.assertEqual(whole["runs"][strategy]["history"][key], split["runs"][strategy]["history"][key])

    def test_api_determinism_paired_equivalence_and_cors(self):
        config = dict(regimes=self.regimes(), seed=42)
        with TestClient(app) as client:
            self.assertEqual(client.get("/health").status_code, 200)
            runs = []
            for _ in range(3):
                response = client.post("/scenarios/run", json=config, headers={"Origin": "http://localhost:3000"})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:3000")
                runs.append(response.json())
            self.assertEqual(runs[0], runs[1])
            self.assertEqual(runs[0], runs[2])
            for strategy in ("basic", "inventory"):
                single = client.post("/scenarios/run", json={**config, "strategy": strategy}).json()
                self.assertEqual(single["runs"][strategy], runs[0]["runs"][strategy])
            response = client.options("/scenarios/run", headers={
                "Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type"
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:3000")

    def test_invalid_regimes_rejected_before_execution(self):
        invalid = [{"regimes": []}, {"regimes": self.regimes() * 4}, {"strategy": "unknown"}, {"seed": None}]
        for field, value in (
            ("name", ""), ("name", " "), ("duration_ticks", 0), ("duration_ticks", 1.5),
            ("duration_ticks", True), ("volatility", -1), ("volatility", 21),
            ("volatility", 1.5), ("buy_pressure", -0.1), ("buy_pressure", 1.1),
            ("order_arrival_rate", 0), ("order_arrival_rate", 11), ("unknown", 1)
        ):
            invalid.append({"regimes": [{**self.regimes()[0], field: value}]})
        invalid.append({"regimes": [{**regime, "duration_ticks": 2000} for regime in self.regimes()]})
        with TestClient(app) as client, patch("app.main.run_scenario") as runner:
            for overrides in invalid:
                with self.subTest(overrides=overrides):
                    self.assertEqual(client.post("/scenarios/run", json={"regimes": self.regimes(), **overrides}).status_code, 422)
            runner.assert_not_called()


if __name__ == "__main__":
    unittest.main()
