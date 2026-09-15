from app.market.order import Order, OrderSide
from app.market.portfolio import Portfolio


class BasicMarketMaker:
    def __init__(
        self,
        spread: float = 0.04,
        order_size: int = 10,
        starting_order_id: int = 1_000_000
    ):
        self.spread = spread
        self.order_size = order_size
        self.next_order_id = starting_order_id

        self.active_bid_id = None
        self.active_ask_id = None

        self.portfolio = Portfolio(
            starting_cash=100_000
        )

    def generate_quotes(
        self,
        midprice: float
    ) -> tuple[Order, Order]:

        half_spread = self.spread / 2

        bid_price = round(midprice - half_spread, 2)
        ask_price = round(midprice + half_spread, 2)

        bid = Order(
            order_id=self.next_order_id,
            side=OrderSide.BUY,
            price=bid_price,
            quantity=self.order_size
        )

        self.next_order_id += 1

        ask = Order(
            order_id=self.next_order_id,
            side=OrderSide.SELL,
            price=ask_price,
            quantity=self.order_size
        )

        self.next_order_id += 1

        self.active_bid_id = bid.order_id
        self.active_ask_id = ask.order_id

        return bid, ask

    def process_trade(self, trade):
        if trade.buy_order_id >= 1_000_000:
            self.portfolio.buy(
                price=trade.price,
                quantity=trade.quantity
            )

        if trade.sell_order_id >= 1_000_000:
            self.portfolio.sell(
                price=trade.price,
                quantity=trade.quantity
            )