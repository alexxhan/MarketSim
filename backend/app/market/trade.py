from dataclasses import dataclass
from time import time


@dataclass
class Trade:
    buy_order_id: int
    sell_order_id: int
    price: float
    quantity: int
    timestamp: float = 0.0
    buyer_owner: str | None = None
    seller_owner: str | None = None

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time()
