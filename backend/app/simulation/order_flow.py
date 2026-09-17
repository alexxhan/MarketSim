import random

from app.market.order import Order, OrderSide
from app.market.validation import positive_price


class OrderFlowGenerator:
    def __init__(
        self,
        starting_price: float = 100.0,
        tick_size: float = 0.01,
        volatility: int = 1,
        buy_pressure: float = 0.50,
        seed: int | None = None
    ):
        positive_price(starting_price, "Starting price")
        positive_price(tick_size, "Tick size")
        if type(volatility) is not int or volatility < 0:
            raise ValueError("Volatility must be 0 or greater")

        if not 0.0 <= buy_pressure <= 1.0:
            raise ValueError("Buy pressure must be between 0 and 1")

        self.reference_price = starting_price
        self.tick_size = tick_size
        self.volatility = volatility
        self.buy_pressure = buy_pressure
        self.next_order_id = 1
        self.rng = random.Random(seed)

    def generate_order(self) -> Order:
        if self.rng.random() < self.buy_pressure:
            side = OrderSide.BUY
        else:
            side = OrderSide.SELL

        price_move = (
            self.rng.randint(-self.volatility, self.volatility)
            * self.tick_size
        )

        self.reference_price = positive_price(self.reference_price + price_move, "Reference price")

        offset = self.rng.randint(-5, 5) * self.tick_size

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