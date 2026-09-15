from app.market.order import Order, OrderSide
from app.market.order_book import OrderBook


book = OrderBook()

book.add_order(
    Order(
        order_id=1,
        side=OrderSide.BUY,
        price=99.98,
        quantity=10
    )
)

book.add_order(
    Order(
        order_id=2,
        side=OrderSide.SELL,
        price=100.02,
        quantity=10
    )
)


print("BEFORE")
print("Bids:", len(book.bids))
print("Asks:", len(book.asks))


cancelled = book.cancel_order(1)


print("\nAFTER")
print("Cancelled:", cancelled)
print("Bids:", len(book.bids))
print("Asks:", len(book.asks))