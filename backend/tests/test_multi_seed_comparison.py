import statistics

from app.simulation.engine import SimulationEngine


NUM_SEEDS = 100
TICKS_PER_RUN = 1000


def run_simulation(strategy: str, seed: int):
    engine = SimulationEngine(
        strategy=strategy,
        seed=seed
    )

    inventory_history = []

    state = None

    for _ in range(TICKS_PER_RUN):
        state = engine.step()

        inventory_history.append(
            abs(state["inventory"])
        )

    return {
        "pnl": state["pnl"],
        "final_inventory": state["inventory"],
        "average_abs_inventory": (
            sum(inventory_history)
            / len(inventory_history)
        ),
        "max_abs_inventory": max(inventory_history),
        "trades": len(engine.trades)
    }


def run_experiment(strategy: str):
    results = []

    for seed in range(NUM_SEEDS):
        result = run_simulation(
            strategy=strategy,
            seed=seed
        )

        results.append(result)

    return results


def summarize(results):
    pnl_values = [
        result["pnl"]
        for result in results
    ]

    average_inventory_values = [
        result["average_abs_inventory"]
        for result in results
    ]

    max_inventory_values = [
        result["max_abs_inventory"]
        for result in results
    ]

    trade_values = [
        result["trades"]
        for result in results
    ]

    return {
        "average_pnl": statistics.mean(
            pnl_values
        ),

        "pnl_std_dev": statistics.stdev(
            pnl_values
        ),

        "average_abs_inventory": statistics.mean(
            average_inventory_values
        ),

        "average_max_inventory": statistics.mean(
            max_inventory_values
        ),

        "worst_max_inventory": max(
            max_inventory_values
        ),

        "average_trades": statistics.mean(
            trade_values
        )
    }

print("\nRunning Basic Market Maker...")

basic_results = run_experiment(
    strategy="basic"
)

print("Running Inventory-Aware Market Maker...")

inventory_results = run_experiment(
    strategy="inventory"
)

basic_summary = summarize(
    basic_results
)

inventory_summary = summarize(
    inventory_results
)

print("\nMulti-seed strategy test\n")

print(
    f"Simulations per strategy: {NUM_SEEDS}"
)

print(
    f"Ticks per simulation: {TICKS_PER_RUN}"
)


print("\nBASIC MARKET MAKER\n")

print(
    f"Average P&L: "
    f"${basic_summary['average_pnl']:+.2f}"
)

print(
    f"P&L Std Dev: "
    f"${basic_summary['pnl_std_dev']:.2f}"
)

print(
    f"Average |Inventory|: "
    f"{basic_summary['average_abs_inventory']:.2f}"
)

print(
    f"Average Max |Inventory|: "
    f"{basic_summary['average_max_inventory']:.2f}"
)

print(
    f"Worst Max |Inventory|: "
    f"{basic_summary['worst_max_inventory']}"
)

print(
    f"Average Trades: "
    f"{basic_summary['average_trades']:.2f}"
)


print("\nINVENTORY-AWARE MARKET MAKER\n")

print(
    f"Average P&L: "
    f"${inventory_summary['average_pnl']:+.2f}"
)

print(
    f"P&L Std Dev: "
    f"${inventory_summary['pnl_std_dev']:.2f}"
)

print(
    f"Average |Inventory|: "
    f"{inventory_summary['average_abs_inventory']:.2f}"
)

print(
    f"Average Max |Inventory|: "
    f"{inventory_summary['average_max_inventory']:.2f}"
)

print(
    f"Worst Max |Inventory|: "
    f"{inventory_summary['worst_max_inventory']}"
)

print(
    f"Average Trades: "
    f"{inventory_summary['average_trades']:.2f}"
)