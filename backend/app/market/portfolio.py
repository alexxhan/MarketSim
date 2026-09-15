class Portfolio:
    def __init__(
        self,
        starting_cash: float = 100_000.0
    ):
        self.starting_cash = starting_cash

        self.cash = starting_cash
        self.inventory = 0

    def buy(
        self,
        price: float,
        quantity: int
    ):
        self.cash -= price * quantity
        self.inventory += quantity

    def sell(
        self,
        price: float,
        quantity: int
    ):
        self.cash += price * quantity
        self.inventory -= quantity

    def get_value(
        self,
        midprice: float
    ) -> float:
        return self.cash + self.inventory * midprice

    def get_pnl(
        self,
        midprice: float
    ) -> float:
        return self.get_value(midprice) - self.starting_cash