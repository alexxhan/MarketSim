from app.market.order import Order, OrderSide
from app.market.order_book import OrderBook


book = OrderBook()

book.add_order(
    Order(1, OrderSide.SELL, 100.05, 10)
)

book.add_order(
    Order(2, OrderSide.SELL, 100.10, 15)
)

book.add_order(
    Order(3, OrderSide.BUY, 100.10, 20)
)


print("BEFORE MATCHING")

print("\nBIDS")
for order in book.bids:
    print(f"{order.quantity} @ ${order.price:.2f}")

print("\nASKS")
for order in book.asks:
    print(f"{order.quantity} @ ${order.price:.2f}")


trades = book.match_orders()


print("\nTRADES")

for trade in trades:
    print(
        f"{trade.quantity} shares @ ${trade.price:.2f}"
    )


print("\nAFTER MATCHING")

print("\nBIDS")
for order in book.bids:
    print(f"{order.quantity} @ ${order.price:.2f}")

print("\nASKS")
for order in book.asks:
    print(f"{order.quantity} @ ${order.price:.2f}")