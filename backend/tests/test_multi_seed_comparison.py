import unittest
from unittest.mock import patch

from app.market.validation import SimulationDomainError
from app.simulation.engine import SimulationEngine
from app.simulation.experiment import run_experiment


class MultiSeedComparisonTests(unittest.TestCase):
    def test_failed_member_rejects_entire_paired_experiment(self):
        def engine_factory(**config):
            engine = SimulationEngine(**config)
            if config["seed"] == 43 and config["strategy"] == "inventory":
                def fail():
                    raise SimulationDomainError("Invalid reference price")
                engine.step = fail
            return engine

        with patch("app.simulation.experiment.SimulationEngine", side_effect=engine_factory):
            with self.assertRaisesRegex(SimulationDomainError, r"seed 43 \(inventory\)"):
                run_experiment(3, 42, 10)
