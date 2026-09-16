from statistics import mean, pstdev

from app.simulation.engine import SimulationEngine


def aggregate_results(results):
    pnl_values = [result["final_pnl"] for result in results if result["final_pnl"] is not None]
    return {
        "valid_pnl_count": len(pnl_values),
        "unavailable_pnl_count": len(results) - len(pnl_values),
        "average_pnl": mean(pnl_values) if pnl_values else None,
        "pnl_standard_deviation": pstdev(pnl_values) if pnl_values else None,
        "best_pnl": max(pnl_values) if pnl_values else None,
        "worst_pnl": min(pnl_values) if pnl_values else None,
        "average_final_inventory": mean(result["final_inventory"] for result in results),
        "average_absolute_inventory": mean(result["average_absolute_inventory"] for result in results),
        "average_maximum_absolute_inventory": mean(result["maximum_absolute_inventory"] for result in results),
        "worst_maximum_absolute_inventory": max(result["maximum_absolute_inventory"] for result in results),
        "average_market_maker_fills": mean(result["market_maker_fills"] for result in results),
        "average_market_maker_executed_volume": mean(result["market_maker_executed_volume"] for result in results)
    }


def run_experiment(number_of_simulations, starting_seed, ticks, **market_config):
    per_seed = []
    for seed in range(starting_seed, starting_seed + number_of_simulations):
        pair = {"seed": seed}
        for strategy in ("basic", "inventory"):
            engine = SimulationEngine(strategy=strategy, seed=seed, **market_config)
            for _ in range(ticks):
                state = engine.step()
            pair[strategy] = {
                "seed": seed,
                "final_pnl": state["pnl"],
                "final_inventory": state["inventory"],
                "portfolio_value": state["portfolio_value"],
                **state["metrics"]
            }
        per_seed.append(pair)
    return {
        "per_seed": per_seed,
        "aggregates": {
            strategy: aggregate_results([pair[strategy] for pair in per_seed])
            for strategy in ("basic", "inventory")
        },
        "aggregation": {
            "pnl_standard_deviation": "population",
            "pnl_null_handling": "Exclude unavailable P&L separately for each strategy; return null P&L statistics when none are available. Inventory and execution statistics include every seed."
        }
    }
