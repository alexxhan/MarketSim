import random

from app.market.order import Order, OrderSide


class OrderFlowGenerator:
    def __init__(
        self,
        starting_price: float = 100.0,
        tick_size: float = 0.01,
        seed: int | None = None
    ):
        self.reference_price = starting_price
        self.tick_size = tick_size
        self.next_order_id = 1

        # Each generator gets its own independent RNG.
        self.rng = random.Random(seed)

    def generate_order(self) -> Order:
        side = self.rng.choice([
            OrderSide.BUY,
            OrderSide.SELL
        ])

        price_move = (
            self.rng.choice([-1, 0, 1])
            * self.tick_size
        )

        self.reference_price += price_move

        offset = (
            self.rng.randint(-5, 5)
            * self.tick_size
        )

        price = round(
            self.reference_price + offset,
            2
        )

        quantity = self.rng.randint(1, 20)

        order = Order(
            order_id=self.next_order_id,
            side=side,
            price=price,
            quantity=quantity
        )

        self.next_order_id += 1

        return order