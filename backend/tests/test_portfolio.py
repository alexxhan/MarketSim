from app.market.portfolio import Portfolio


portfolio = Portfolio(
    starting_cash=100_000
)


print("START")
print(f"Cash: ${portfolio.cash:.2f}")
print(f"Inventory: {portfolio.inventory}")


portfolio.buy(
    price=99.98,
    quantity=10
)


print("\nAFTER BUY")
print(f"Cash: ${portfolio.cash:.2f}")
print(f"Inventory: {portfolio.inventory}")


portfolio.sell(
    price=100.02,
    quantity=10
)


print("\nAFTER SELL")
print(f"Cash: ${portfolio.cash:.2f}")
print(f"Inventory: {portfolio.inventory}")


print(
    f"P&L: ${portfolio.get_pnl(100.00):.2f}"
)