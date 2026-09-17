from dataclasses import dataclass
from enum import Enum
from time import time

from .validation import positive_price, positive_quantity


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class Order:
    order_id: int
    side: OrderSide
    price: float
    quantity: int
    timestamp: float = 0.0
    owner: str | None = None

    @property
    def identity(self) -> tuple[str | None, int]:
        return self.owner, self.order_id

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time()

        positive_price(self.price)
        positive_quantity(self.quantity)
        if self.side not in (OrderSide.BUY, OrderSide.SELL):
            raise ValueError("Unsupported order side")
