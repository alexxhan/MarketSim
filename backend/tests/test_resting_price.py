from app.market.order import Order, OrderSide
from app.market.order_book import OrderBook


book = OrderBook()

resting_bid = Order(
    order_id=1,
    side=OrderSide.BUY,
    price=100.00,
    quantity=10,
    timestamp=1.0
)

aggressive_sell = Order(
    order_id=2,
    side=OrderSide.SELL,
    price=99.98,
    quantity=10,
    timestamp=2.0
)

book.add_order(resting_bid)
book.add_order(aggressive_sell)

trades = book.match_orders()

assert len(trades) == 1
assert trades[0].price == 100.00
assert trades[0].quantity == 10

print("Aggressive SELL executed at resting BID price")

book = OrderBook()

resting_ask = Order(
    order_id=3,
    side=OrderSide.SELL,
    price=100.00,
    quantity=10,
    timestamp=1.0
)

aggressive_buy = Order(
    order_id=4,
    side=OrderSide.BUY,
    price=100.02,
    quantity=10,
    timestamp=2.0
)

book.add_order(resting_ask)
book.add_order(aggressive_buy)

trades = book.match_orders()

assert len(trades) == 1
assert trades[0].price == 100.00
assert trades[0].quantity == 10

print("Aggressive BUY executed at resting ASK price.")

print("\nResting-order execution price tests passed.")