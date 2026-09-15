from app.strategies.inventory_market_maker import (
    InventoryMarketMaker
)


market_maker = InventoryMarketMaker(
    spread=0.04,
    order_size=10,
    inventory_risk_factor=0.001
)


def show_quotes(label):
    bid, ask = market_maker.generate_quotes(
        midprice=100.00
    )

    print(f"\n{label}")
    print(
        f"Inventory: "
        f"{market_maker.portfolio.inventory:+d}"
    )
    print(f"Bid: ${bid.price:.2f}")
    print(f"Ask: ${ask.price:.2f}")


# Neutral
market_maker.portfolio.inventory = 0
show_quotes("NEUTRAL")

# Long
market_maker.portfolio.inventory = 30
show_quotes("LONG")

# Short
market_maker.portfolio.inventory = -30
show_quotes("SHORT")