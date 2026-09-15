import random

from app.market.order import Order, OrderSide


class OrderFlowGenerator:
    def __init__(
        self,
        starting_price: float = 100.0,
        tick_size: float = 0.01
    ):
        self.reference_price = starting_price
        self.tick_size = tick_size
        self.next_order_id = 1

    def generate_order(self) -> Order:
        side = random.choice([
            OrderSide.BUY,
            OrderSide.SELL
        ])

        # Randomly move the reference price slightly.
        price_move = random.choice([-1, 0, 1]) * self.tick_size
        self.reference_price += price_move

        # Generate an order near the current reference price.
        offset = random.randint(-5, 5) * self.tick_size
        price = round(self.reference_price + offset, 2)

        quantity = random.randint(1, 20)

        order = Order(
            order_id=self.next_order_id,
            side=side,
            price=price,
            quantity=quantity
        )

        self.next_order_id += 1

        return order