from app.simulation.engine import SimulationEngine


SEED = 42
TICKS = 1000


def run_simulation(strategy: str):
    engine = SimulationEngine(
        strategy=strategy,
        seed=SEED
    )

    inventory_history = []

    state = None

    for _ in range(TICKS):
        state = engine.step()

        inventory_history.append(
            abs(state["inventory"])
        )

    average_inventory = (
        sum(inventory_history)
        / len(inventory_history)
    )

    max_inventory = max(inventory_history)

    return {
        "strategy": strategy,
        "pnl": state["pnl"],
        "inventory": state["inventory"],
        "average_abs_inventory": average_inventory,
        "max_abs_inventory": max_inventory,
        "trades": len(engine.trades)
    }

basic_results = run_simulation(
    strategy="basic"
)

inventory_results = run_simulation(
    strategy="inventory"
)

print("MARKETSIM STRATEGY COMPARISON")

print(f"Seed: {SEED}")
print(f"Ticks: {TICKS}")

print("\nBASIC MARKET MAKER\n")

print(
    f"P&L: "
    f"${basic_results['pnl']:+.2f}"
)

print(
    f"Final Inventory: "
    f"{basic_results['inventory']:+d}"
)

print(
    f"Average |Inventory|: "
    f"{basic_results['average_abs_inventory']:.2f}"
)

print(
    f"Max |Inventory|: "
    f"{basic_results['max_abs_inventory']}"
)

print(
    f"Trades: "
    f"{basic_results['trades']}"
)


print("\nINVENTORY-AWARE MARKET MAKER\n")

print(
    f"P&L: "
    f"${inventory_results['pnl']:+.2f}"
)

print(
    f"Final Inventory: "
    f"{inventory_results['inventory']:+d}"
)

print(
    f"Average |Inventory|: "
    f"{inventory_results['average_abs_inventory']:.2f}"
)

print(
    f"Max |Inventory|: "
    f"{inventory_results['max_abs_inventory']}"
)

print(
    f"Trades: "
    f"{inventory_results['trades']}"
)