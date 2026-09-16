import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import SweepRequest, app
from app.simulation.engine import SimulationEngine
from app.simulation.experiment import run_experiment
from app.simulation.sweep import run_sweep


class SweepTests(unittest.TestCase):
    def config(self, parameter="volatility", values=None):
        return SweepRequest(
            sweep_parameter=parameter,
            sweep_values=values if values is not None else [1, 3],
            simulations_per_value=2, starting_seed=17, ticks=50,
            starting_price=100, volatility=2, buy_pressure=0.5,
            order_arrival_rate=3, spread=0.04, order_size=10,
            inventory_risk_factor=0.001
        ).model_dump()

    def test_points_parameters_seeds_and_paired_order_flow(self):
        for parameter, values in (
            ("volatility", [1, 3]), ("buy_pressure", [0.4, 0.6]),
            ("order_arrival_rate", [1, 4]), ("spread", [0.02, 0.06]),
            ("inventory_risk_factor", [0, 0.005])
        ):
            with self.subTest(parameter=parameter):
                configs, flows = [], []

                def capture_engine(**config):
                    configs.append(config)
                    engine = SimulationEngine(**config)
                    generate = engine.order_flow.generate_order
                    flow = []
                    flows.append(flow)

                    def capture_order():
                        order = generate()
                        flow.append((order.side, order.price, order.quantity))
                        return order

                    engine.order_flow.generate_order = capture_order
                    return engine

                config = self.config(parameter, values)
                with patch("app.simulation.experiment.SimulationEngine", side_effect=capture_engine):
                    sweep = run_sweep(**config)
                self.assertEqual(len(sweep["results"]), 2)
                self.assertEqual([point["value"] for point in sweep["results"]], values)
                self.assertEqual(len(configs), 8)
                base_market = {key: config[key] for key in (
                    "starting_price", "volatility", "buy_pressure", "order_arrival_rate",
                    "spread", "order_size", "inventory_risk_factor"
                )}
                for point_index, value in enumerate(values):
                    for seed_index in range(2):
                        index = point_index * 4 + seed_index * 2
                        self.assertEqual(flows[index], flows[index + 1])
                        for offset, strategy in enumerate(("basic", "inventory")):
                            expected = dict(base_market, strategy=strategy, seed=17 + seed_index)
                            if parameter != "inventory_risk_factor" or strategy == "inventory":
                                expected[parameter] = value
                            self.assertEqual(configs[index + offset], expected)
                if parameter == "inventory_risk_factor":
                    self.assertEqual(configs[0], configs[4])
                    self.assertEqual(configs[2], configs[6])
                    self.assertEqual(sweep["results"][0]["basic"], sweep["results"][1]["basic"])

    def test_aggregates_equal_direct_experiments(self):
        for parameter, values in (
            ("volatility", [1, 3]), ("buy_pressure", [0.4, 0.6]),
            ("order_arrival_rate", [1, 4]), ("spread", [0.02, 0.06]),
            ("inventory_risk_factor", [0, 0.005])
        ):
            with self.subTest(parameter=parameter):
                config = self.config(parameter, values)
                sweep = run_sweep(**config)
                direct = {key: value for key, value in config.items() if key not in ("sweep_parameter", "sweep_values", "simulations_per_value")}
                for point in sweep["results"]:
                    experiment = run_experiment(
                        number_of_simulations=config["simulations_per_value"],
                        **{**direct, parameter: point["value"]}
                    )
                    self.assertEqual(point["basic"], experiment["aggregates"]["basic"])
                    self.assertEqual(point["inventory"], experiment["aggregates"]["inventory"])
                    self.assertEqual(sweep["aggregation"], experiment["aggregation"])

    def test_api_determinism_and_cors(self):
        with TestClient(app) as client:
            self.assertEqual(client.get("/health").status_code, 200)
            responses = []
            for _ in range(3):
                response = client.post("/sweeps/run", json=self.config(), headers={"Origin": "http://localhost:3000"})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:3000")
                responses.append(response.json())
            self.assertEqual(responses[0], responses[1])
            self.assertEqual(responses[0], responses[2])
            self.assertEqual(responses[0]["config"], self.config())
            self.assertEqual(responses[0]["sweep_parameter"], "volatility")
            response = client.options("/sweeps/run", headers={
                "Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type"
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:3000")

    def test_null_pnl_is_preserved(self):
        config = self.config("buy_pressure", [0, 1])
        config["ticks"] = 1
        with TestClient(app) as client:
            response = client.post("/sweeps/run", json=config)
            self.assertEqual(response.status_code, 200)
            for point in response.json()["results"]:
                for strategy in ("basic", "inventory"):
                    for metric in ("average_pnl", "pnl_standard_deviation", "best_pnl", "worst_pnl"):
                        self.assertIsNone(point[strategy][metric])
                    self.assertEqual(point[strategy]["unavailable_pnl_count"], 2)

    def test_invalid_parameters_values_and_limits_rejected_before_execution(self):
        invalid = [
            {"sweep_parameter": "ticks"}, {"sweep_values": []},
            {"sweep_values": [1] * 11}, {"sweep_values": [True]},
            {"sweep_values": ["1"]}, {"sweep_values": [None]},
            {"sweep_values": [-1]}, {"sweep_values": [21]}, {"sweep_values": [1.5]},
            {"sweep_parameter": "buy_pressure", "sweep_values": [-0.1, 0.5]},
            {"sweep_parameter": "buy_pressure", "sweep_values": [1.1]},
            {"sweep_parameter": "order_arrival_rate", "sweep_values": [0]},
            {"sweep_parameter": "order_arrival_rate", "sweep_values": [11]},
            {"sweep_parameter": "order_arrival_rate", "sweep_values": [1.5]},
            {"sweep_parameter": "spread", "sweep_values": [0]},
            {"sweep_parameter": "inventory_risk_factor", "sweep_values": [-0.001]},
            {"simulations_per_value": 0}, {"simulations_per_value": 101},
            {"simulations_per_value": 1.5}, {"ticks": 0}, {"ticks": 5001},
            {"starting_seed": 9007199254740991},
            {"simulations_per_value": 100, "ticks": 1000, "sweep_values": [1, 2]},
        ]
        with TestClient(app) as client, patch("app.main.run_sweep") as runner:
            for overrides in invalid:
                with self.subTest(overrides=overrides):
                    self.assertEqual(client.post("/sweeps/run", json={**self.config(), **overrides}).status_code, 422)
            runner.assert_not_called()
        for value in (float("inf"), float("-inf"), float("nan")):
            with self.assertRaises(ValidationError):
                SweepRequest(**{**self.config(), "sweep_values": [value]})

    def test_workload_uses_swept_arrival_rates(self):
        config = {**self.config("order_arrival_rate", [1, 4]), "simulations_per_value": 100, "ticks": 1000}
        self.assertEqual(SweepRequest(**config).sweep_values, [1, 4])
        with self.assertRaises(ValidationError):
            SweepRequest(**{**config, "sweep_values": [1, 5]})


if __name__ == "__main__":
    unittest.main()
