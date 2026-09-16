from .order import Order, OrderSide
from .trade import Trade


class OrderBook:
    def __init__(self):
        self.bids: list[Order] = []
        self.asks: list[Order] = []
        self._next_arrival_sequence = 0
        self._arrival_sequences: dict[int, int] = {}


    def add_order(self, order: Order):
        self._arrival_sequences[id(order)] = self._next_arrival_sequence
        self._next_arrival_sequence += 1

        if order.side == OrderSide.BUY:
            self.bids.append(order)

            self.bids.sort(
                key=lambda order: (
                    -order.price,
                    self._arrival_sequences[id(order)]
                )
            )

        elif order.side == OrderSide.SELL:
            self.asks.append(order)

            self.asks.sort(
                key=lambda order: (
                    order.price,
                    self._arrival_sequences[id(order)]
                )
            )


    def cancel_order(self, order_id: int) -> bool:
        for index, order in enumerate(self.bids):
            if order.order_id == order_id:
                self.bids.pop(index)
                del self._arrival_sequences[id(order)]
                return True

        for index, order in enumerate(self.asks):
            if order.order_id == order_id:
                self.asks.pop(index)
                del self._arrival_sequences[id(order)]
                return True

        return False


    def get_best_bid(self):
        if not self.bids:
            return None

        return self.bids[0]


    def get_best_ask(self):
        if not self.asks:
            return None

        return self.asks[0]


    def get_midprice(self):
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()

        if best_bid is None or best_ask is None:
            return None

        return (
            best_bid.price
            + best_ask.price
        ) / 2


    def match_orders(self) -> list[Trade]:
        trades = []

        while self.bids and self.asks:
            best_bid = self.bids[0]
            best_ask = self.asks[0]

            if best_bid.price < best_ask.price:
                break

            trade_quantity = min(
                best_bid.quantity,
                best_ask.quantity
            )

            if (
                self._arrival_sequences[id(best_bid)]
                < self._arrival_sequences[id(best_ask)]
            ):
                trade_price = best_bid.price
            else:
                trade_price = best_ask.price

            trade = Trade(
                buy_order_id=best_bid.order_id,
                sell_order_id=best_ask.order_id,
                price=trade_price,
                quantity=trade_quantity
            )

            trades.append(trade)

            best_bid.quantity -= trade_quantity
            best_ask.quantity -= trade_quantity

            if best_bid.quantity == 0:
                self.bids.pop(0)
                del self._arrival_sequences[id(best_bid)]

            if best_ask.quantity == 0:
                self.asks.pop(0)
                del self._arrival_sequences[id(best_ask)]

        return trades
