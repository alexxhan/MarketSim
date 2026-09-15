from dataclasses import dataclass
from enum import Enum
from time import time


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

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time()

        if self.price <= 0:
            raise ValueError("Price must be greater than 0")

        if self.quantity <= 0:
            raise ValueError("Quantity must be greater than 0")