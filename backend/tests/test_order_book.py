from app.market.order import Order, OrderSide
from app.market.order_book import OrderBook


book = OrderBook()

book.add_order(Order(1, OrderSide.BUY, 99.90, 10))
book.add_order(Order(2, OrderSide.BUY, 99.95, 5))

book.add_order(Order(3, OrderSide.SELL, 100.10, 8))
book.add_order(Order(4, OrderSide.SELL, 100.05, 12))


print("BIDS")
for order in book.bids:
    print(f"{order.quantity} @ ${order.price:.2f}")

print("\nASKS")
for order in book.asks:
    print(f"{order.quantity} @ ${order.price:.2f}")

print("\nMARKET")
print(f"Best Bid: ${book.get_best_bid().price:.2f}")
print(f"Best Ask: ${book.get_best_ask().price:.2f}")
print(f"Midprice: ${book.get_midprice():.2f}")