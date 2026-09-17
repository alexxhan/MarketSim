import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import ExperimentRequest, app
from app.market.validation import SimulationDomainError
from app.simulation.engine import SimulationEngine
from app.simulation.experiment import aggregate_results, run_experiment


class ExperimentTests(unittest.TestCase):
    def test_seed_pairs_config_and_external_flow(self):
        engines = []
        flows = []

        def capture_engine(**config):
            engine = SimulationEngine(**config)
            engines.append(engine)
            flow = []
            flows.append(flow)
            generate = engine.order_flow.generate_order

            def capture_order():
                order = generate()
                flow.append((order.side, order.price, order.quantity, engine.order_flow.reference_price))
                return order

            engine.order_flow.generate_order = capture_order
            return engine

        config = dict(
            number_of_simulations=3, starting_seed=17, ticks=100,
            starting_price=123, volatility=2, buy_pressure=0.6,
            order_arrival_rate=3, spread=0.06, order_size=7,
            inventory_risk_factor=0.002
        )
        with patch("app.simulation.experiment.SimulationEngine", side_effect=capture_engine) as factory:
            result = run_experiment(**config)
        self.assertEqual(factory.call_count, 6)
        self.assertEqual([pair["seed"] for pair in result["per_seed"]], [17, 18, 19])
        for index, pair in enumerate(result["per_seed"]):
            basic, inventory = engines[2 * index:2 * index + 2]
            self.assertEqual((basic.strategy, inventory.strategy), ("basic", "inventory"))
            self.assertEqual((basic.seed, inventory.seed), (17 + index, 17 + index))
            self.assertEqual((basic.tick, inventory.tick), (100, 100))
            for key in config.keys() - {"number_of_simulations", "starting_seed", "ticks"}:
                self.assertEqual(getattr(basic, key), config[key])
                self.assertEqual(getattr(inventory, key), config[key])
            self.assertEqual(flows[2 * index], flows[2 * index + 1])
            self.assertEqual(len(flows[2 * index]), 300)
            self.assertEqual(pair["basic"]["final_mark_price"], pair["inventory"]["final_mark_price"])
            for strategy in ("basic", "inventory"):
                self.assertEqual(pair[strategy]["seed"], pair["seed"])

    def sample_results(self, pnl_values):
        return [
            dict(
                final_pnl=pnl, final_inventory=inventory,
                average_absolute_inventory=average,
                maximum_absolute_inventory=maximum,
                market_maker_fills=fills, market_maker_executed_volume=volume
            )
            for pnl, inventory, average, maximum, fills, volume in zip(
                pnl_values, [-4, 2, 8], [2, 4, 6], [5, 8, 11], [1, 3, 5], [10, 20, 30]
            )
        ]

    def test_aggregate_formulas(self):
        result = aggregate_results(self.sample_results([-2, 0, 4]))
        self.assertAlmostEqual(result["average_pnl"], 2 / 3)
        self.assertAlmostEqual(result["pnl_standard_deviation"], (56 / 9) ** 0.5)
        self.assertEqual(result["best_pnl"], 4)
        self.assertEqual(result["worst_pnl"], -2)
        self.assertEqual(result["average_final_inventory"], 2)
        self.assertEqual(result["average_absolute_inventory"], 4)
        self.assertEqual(result["average_maximum_absolute_inventory"], 8)
        self.assertEqual(result["worst_maximum_absolute_inventory"], 11)
        self.assertEqual(result["average_market_maker_fills"], 3)
        self.assertEqual(result["average_market_maker_executed_volume"], 20)
        self.assertEqual(result["valid_pnl_count"], 3)
        self.assertEqual(result["unavailable_pnl_count"], 0)

    def test_incomplete_or_nonfinite_results_are_rejected(self):
        for values in ([None, -2, 4], [None, None, None], [0, float("nan"), 1], [0, float("inf"), 1]):
            with self.subTest(values=values), self.assertRaises(SimulationDomainError):
                aggregate_results(self.sample_results(values))

    def test_single_seed_population_standard_deviation(self):
        result = aggregate_results(self.sample_results([4]))
        self.assertEqual(result["average_pnl"], 4)
        self.assertEqual(result["pnl_standard_deviation"], 0)
        self.assertEqual(result["valid_pnl_count"], 1)

    def test_api_determinism_and_single_run_equivalence(self):
        config = dict(
            number_of_simulations=3, starting_seed=42, ticks=100,
            starting_price=100, volatility=3, buy_pressure=0.5,
            order_arrival_rate=3, spread=0.04, order_size=10,
            inventory_risk_factor=0.001
        )
        with TestClient(app) as client:
            self.assertEqual(client.get("/health").status_code, 200)
            runs = []
            for _ in range(3):
                response = client.post("/experiments/run", json=config)
                self.assertEqual(response.status_code, 200)
                runs.append(response.json())
            self.assertEqual(runs[0], runs[1])
            self.assertEqual(runs[0], runs[2])
            self.assertEqual(runs[0]["aggregation"]["pnl_standard_deviation"], "population")
            for pair in runs[0]["per_seed"]:
                for strategy in ("basic", "inventory"):
                    single_config = {key: value for key, value in config.items() if key not in ("number_of_simulations", "starting_seed")}
                    response = client.post("/simulation/run", json=dict(single_config, seed=pair["seed"], strategy=strategy))
                    self.assertEqual(response.status_code, 200)
                    single = response.json()["results"]
                    for key, value in pair[strategy].items():
                        if key != "seed":
                            self.assertEqual(value, single["final_portfolio_value" if key == "portfolio_value" else key])
            for strategy in ("basic", "inventory"):
                self.assertEqual(runs[0]["aggregates"][strategy], aggregate_results([pair[strategy] for pair in runs[0]["per_seed"]]))

    def test_api_one_sided_book_and_one_simulation(self):
        with TestClient(app) as client:
            response = client.post("/experiments/run", json={"number_of_simulations": 1, "ticks": 1, "buy_pressure": 1})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(len(data["per_seed"]), 1)
            for strategy in ("basic", "inventory"):
                self.assertEqual(data["per_seed"][0][strategy]["final_pnl"], 0)
                self.assertEqual(data["per_seed"][0][strategy]["portfolio_value"], 100000)
                self.assertEqual(data["aggregates"][strategy]["average_pnl"], 0)
                self.assertEqual(data["aggregates"][strategy]["unavailable_pnl_count"], 0)

    def test_validation_and_cors(self):
        invalid = [
            {"number_of_simulations": value} for value in (0, 101, 1.5, True)
        ] + [
            {"ticks": 5001}, {"order_arrival_rate": 11},
            {"number_of_simulations": 100, "ticks": 5000, "order_arrival_rate": 10},
            {"starting_seed": 9007199254740991, "number_of_simulations": 2}
        ]
        with TestClient(app) as client:
            with patch("app.main.run_experiment") as runner:
                for config in invalid:
                    with self.subTest(config=config):
                        self.assertEqual(client.post("/experiments/run", json=config).status_code, 422)
                runner.assert_not_called()
            response = client.options("/experiments/run", headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type"
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:3000")
        boundary = ExperimentRequest(number_of_simulations=100, ticks=5000, order_arrival_rate=1)
        self.assertEqual(boundary.number_of_simulations, 100)


if __name__ == "__main__":
    unittest.main()
