from .validation import finite_number, positive_price, positive_quantity


class Portfolio:
    def __init__(
        self,
        starting_cash: float = 100_000.0
    ):
        finite_number(starting_cash, "Starting cash")
        self.starting_cash = starting_cash

        self.cash = starting_cash
        self.inventory = 0

    def buy(
        self,
        price: float,
        quantity: int
    ):
        positive_price(price)
        positive_quantity(quantity)
        self.cash = finite_number(self.cash - price * quantity, "Cash")
        self.inventory += quantity

    def sell(
        self,
        price: float,
        quantity: int
    ):
        positive_price(price)
        positive_quantity(quantity)
        self.cash = finite_number(self.cash + price * quantity, "Cash")
        self.inventory -= quantity

    def get_value(
        self,
        mark_price: float
    ) -> float:
        positive_price(mark_price, "Mark price")
        return finite_number(self.cash + self.inventory * mark_price, "Portfolio value")

    def get_pnl(
        self,
        mark_price: float
    ) -> float:
        return finite_number(self.get_value(mark_price) - self.starting_cash, "P&L")
