from app.market.order import Order, OrderSide
from app.market.portfolio import Portfolio
from app.market.validation import positive_price, positive_quantity, SimulationDomainError
from app.strategies.quotes import quote_prices


class BasicMarketMaker:
    def __init__(
        self,
        spread: float = 0.04,
        order_size: int = 10,
        starting_order_id: int = 1
    ):
        positive_price(spread, "Spread")
        positive_quantity(order_size)
        self.owner = "market_maker"
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

        bid_price, ask_price = quote_prices(midprice, self.spread)

        bid = Order(
            order_id=self.next_order_id,
            side=OrderSide.BUY,
            price=bid_price,
            quantity=self.order_size,
            owner=self.owner
        )

        self.next_order_id += 1

        ask = Order(
            order_id=self.next_order_id,
            side=OrderSide.SELL,
            price=ask_price,
            quantity=self.order_size,
            owner=self.owner
        )

        self.next_order_id += 1

        self.active_bid_id = bid.order_id
        self.active_ask_id = ask.order_id

        return bid, ask

    def process_trade(self, trade):
        if trade.buyer_owner == self.owner and trade.seller_owner == self.owner:
            raise SimulationDomainError("Market-maker self-trade is not permitted")
        if trade.buyer_owner == self.owner:
            self.portfolio.buy(
                price=trade.price,
                quantity=trade.quantity
            )

        if trade.seller_owner == self.owner:
            self.portfolio.sell(
                price=trade.price,
                quantity=trade.quantity
            )
