from app.strategies.basic_market_maker import BasicMarketMaker


market_maker = BasicMarketMaker(
    spread=0.04,
    order_size=10
)

bid, ask = market_maker.generate_quotes(
    midprice=100.00
)


print("MARKET MAKER QUOTES\n")

print(
    f"BID: {bid.quantity} @ ${bid.price:.2f}"
)

print(
    f"ASK: {ask.quantity} @ ${ask.price:.2f}"
)

print(
    f"Spread: ${ask.price - bid.price:.2f}"
)