from app.simulation.engine import SimulationEngine


TICKS = 500
SEED = 42


def run_scenario(
    name: str,
    order_arrival_rate: int
):
    engine = SimulationEngine(
        strategy="inventory",
        order_arrival_rate=order_arrival_rate,
        seed=SEED
    )

    total_orders = 0
    state = None

    for _ in range(TICKS):
        state = engine.step()
        total_orders += len(state["orders"])

    print(f"\n{name}\n")
    print(f"Order Arrival Rate: {order_arrival_rate}")
    print(f"Ticks: {TICKS}")
    print(f"Generated Orders: {total_orders}")
    print(f"Trades: {len(engine.trades)}")
    print(f"Final Inventory: {state['inventory']:+d}")

    if state["pnl"] is not None:
        print(f"P&L: ${state['pnl']:+.2f}")
    else:
        print("P&L: unavailable")


print("\nMarketSim Liquidity Test")

run_scenario(
    name="Low Activity",
    order_arrival_rate=1
)

run_scenario(
    name="Medium Activity",
    order_arrival_rate=3
)

run_scenario(
    name="High Activity",
    order_arrival_rate=10
)

print("\nLiquidity tests finished.\n")