from app.simulation.experiment import run_experiment


def run_sweep(sweep_parameter, sweep_values, simulations_per_value, starting_seed, ticks, **market_config):
    results = []
    for value in sweep_values:
        point_config = {**market_config, sweep_parameter: value}
        experiment = run_experiment(
            number_of_simulations=simulations_per_value,
            starting_seed=starting_seed,
            ticks=ticks,
            basic_inventory_risk_factor=market_config.get("inventory_risk_factor", 0.001),
            **point_config
        )
        results.append({"value": value, **experiment["aggregates"]})
    return {
        "sweep_parameter": sweep_parameter,
        "results": results,
        "aggregation": experiment["aggregation"]
    }
