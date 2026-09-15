from app.simulation.engine import SimulationEngine


TICKS = 1000
SEED = 42


def run_scenario(
    name: str,
    volatility: int,
    buy_pressure: float
):
    engine = SimulationEngine(
        strategy="inventory",
        volatility=volatility,
        buy_pressure=buy_pressure,
        seed=SEED
    )

    buy_orders = 0
    sell_orders = 0
    state = None

    for _ in range(TICKS):
        state = engine.step()

        for order in state["orders"]:
            if order.side.value == "BUY":
                buy_orders += 1
            else:
                sell_orders += 1

    print(f"\n{name}\n")
    print(f"Volatility: {volatility}")
    print(f"Buy Pressure: {buy_pressure:.0%}")
    print(f"BUY Orders: {buy_orders}")
    print(f"SELL Orders: {sell_orders}")
    print(
        f"Reference Price: "
        f"${engine.order_flow.reference_price:.2f}"
    )
    print(f"Final Inventory: {state['inventory']:+d}")

    if state["pnl"] is not None:
        print(f"P&L: ${state['pnl']:+.2f}")
    else:
        print("P&L: unavailable")


print("\nMarketSim Market Conditions Test")

run_scenario(
    name="Normal Market",
    volatility=1,
    buy_pressure=0.50
)

run_scenario(
    name="Buying Pressure",
    volatility=1,
    buy_pressure=0.75
)

run_scenario(
    name="Selling Pressure",
    volatility=1,
    buy_pressure=0.25
)

run_scenario(
    name="High Volatility",
    volatility=5,
    buy_pressure=0.50
)

print("\nMarket condition tests finished.\n")