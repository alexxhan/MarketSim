from app.simulation.engine import SimulationEngine


engine = SimulationEngine(
    strategy="inventory"
)


for _ in range(100):
    result = engine.step()

    print(f"\nTick {result['tick']:03d}")

    for order in result["orders"]:
        print(
            f"Trader: {order.side.value:<4} "
            f"{order.quantity:>2} @ ${order.price:.2f}"
        )

    quotes = result["market_maker_quotes"]

    if quotes:
        print(
            f"MM: BID ${quotes['bid'].price:.2f} | "
            f"ASK ${quotes['ask'].price:.2f}"
        )

    for trade in result["trades"]:
        print(
            f">>> TRADE "
            f"{trade.quantity} @ ${trade.price:.2f}"
        )

    if result["pnl"] is not None:
        print(
            f"Inventory: {result['inventory']:+d} | "
            f"P&L: ${result['pnl']:+.2f}"
        )


print("\nFinal Market Maker Performance\n")

portfolio = engine.market_maker.portfolio
midprice = engine.order_book.get_midprice()

print(f"Strategy: {engine.strategy}")
print(f"Cash: ${portfolio.cash:,.2f}")
print(f"Inventory: {portfolio.inventory:+d}")

if midprice is not None:
    print(f"Midprice: ${midprice:.2f}")
    print(
        f"Portfolio Value: "
        f"${portfolio.get_value(midprice):,.2f}"
    )
    print(
        f"P&L: "
        f"${portfolio.get_pnl(midprice):+.2f}"
    )
else:
    print("Midprice: unavailable")
    print("Portfolio Value: unavailable")
    print("P&L: unavailable")

print(f"Total Market Trades: {len(engine.trades)}")