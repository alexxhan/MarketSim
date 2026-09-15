from app.market.order_book import OrderBook
from app.simulation.order_flow import OrderFlowGenerator
from app.strategies.basic_market_maker import BasicMarketMaker
from app.strategies.inventory_market_maker import InventoryMarketMaker


class SimulationEngine:
    def __init__(
        self,
        strategy: str = "basic",
        starting_price: float = 100.0,
        volatility: int = 1,
        buy_pressure: float = 0.50,
        order_arrival_rate: int = 1,
        spread: float = 0.04,
        order_size: int = 10,
        inventory_risk_factor: float = 0.001,
        seed: int | None = None
    ):
        if order_arrival_rate < 1:
            raise ValueError("Order arrival rate must be at least 1")

        self.strategy = strategy
        self.starting_price = starting_price
        self.volatility = volatility
        self.buy_pressure = buy_pressure
        self.order_arrival_rate = order_arrival_rate
        self.spread = spread
        self.order_size = order_size
        self.inventory_risk_factor = inventory_risk_factor
        self.seed = seed

        self.order_book = OrderBook()

        self.order_flow = OrderFlowGenerator(
            starting_price=starting_price,
            volatility=volatility,
            buy_pressure=buy_pressure,
            seed=seed
        )

        if strategy == "basic":
            self.market_maker = BasicMarketMaker(
                spread=spread,
                order_size=order_size
            )

        elif strategy == "inventory":
            self.market_maker = InventoryMarketMaker(
                spread=spread,
                order_size=order_size,
                inventory_risk_factor=inventory_risk_factor
            )

        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        self.tick = 0
        self.trades = []

    def step(self):
        self.tick += 1

        if self.market_maker.active_bid_id is not None:
            self.order_book.cancel_order(
                self.market_maker.active_bid_id
            )

        if self.market_maker.active_ask_id is not None:
            self.order_book.cancel_order(
                self.market_maker.active_ask_id
            )

        midprice = self.order_book.get_midprice()
        market_maker_quotes = None

        if midprice is not None:
            bid, ask = self.market_maker.generate_quotes(midprice)

            self.order_book.add_order(bid)
            self.order_book.add_order(ask)

            market_maker_quotes = {
                "bid": bid,
                "ask": ask
            }

        generated_orders = []
        new_trades = []

        for _ in range(self.order_arrival_rate):
            order = self.order_flow.generate_order()
            generated_orders.append(order)

            self.order_book.add_order(order)

            trades = self.order_book.match_orders()

            for trade in trades:
                self.market_maker.process_trade(trade)

            new_trades.extend(trades)

        self.trades.extend(new_trades)

        current_midprice = self.order_book.get_midprice()

        portfolio_value = None
        pnl = None

        if current_midprice is not None:
            portfolio_value = self.market_maker.portfolio.get_value(
                current_midprice
            )

            pnl = self.market_maker.portfolio.get_pnl(
                current_midprice
            )

        return {
            "tick": self.tick,
            "strategy": self.strategy,
            "seed": self.seed,
            "market_config": {
                "starting_price": self.starting_price,
                "volatility": self.volatility,
                "buy_pressure": self.buy_pressure,
                "order_arrival_rate": self.order_arrival_rate,
                "spread": self.spread,
                "order_size": self.order_size,
                "inventory_risk_factor": self.inventory_risk_factor
            },
            "orders": generated_orders,
            "trades": new_trades,
            "market_maker_quotes": market_maker_quotes,
            "best_bid": self.order_book.get_best_bid(),
            "best_ask": self.order_book.get_best_ask(),
            "midprice": current_midprice,
            "cash": self.market_maker.portfolio.cash,
            "inventory": self.market_maker.portfolio.inventory,
            "portfolio_value": portfolio_value,
            "pnl": pnl
        }