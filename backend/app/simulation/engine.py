from app.market.order_book import OrderBook
from app.simulation.order_flow import OrderFlowGenerator
from app.strategies.basic_market_maker import BasicMarketMaker
from app.strategies.inventory_market_maker import InventoryMarketMaker


class SimulationEngine:
    def __init__(
        self,
        strategy: str = "basic",
        seed: int | None = None
    ):
        
        self.order_book = OrderBook()

        self.order_flow = OrderFlowGenerator(
            starting_price=100.0,
            seed=seed
        )

        self.strategy = strategy
        self.seed = seed

        if strategy == "basic":
            self.market_maker = BasicMarketMaker(
                spread=0.04,
                order_size=10
            )

        elif strategy == "inventory":
            self.market_maker = InventoryMarketMaker(
                spread=0.04,
                order_size=10,
                inventory_risk_factor=0.001
            )

        else:
            raise ValueError(
                f"Unknown strategy: {strategy}"
            )

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
            bid, ask = self.market_maker.generate_quotes(
                midprice
            )

            self.order_book.add_order(bid)
            self.order_book.add_order(ask)

            market_maker_quotes = {
                "bid": bid,
                "ask": ask
            }

        order = self.order_flow.generate_order()

        self.order_book.add_order(order)

        new_trades = self.order_book.match_orders()

        self.trades.extend(new_trades)

        for trade in new_trades:
            self.market_maker.process_trade(trade)

        current_midprice = self.order_book.get_midprice()

        portfolio_value = None
        pnl = None

        if current_midprice is not None:
            portfolio_value = (
                self.market_maker.portfolio.get_value(
                    current_midprice
                )
            )

            pnl = (
                self.market_maker.portfolio.get_pnl(
                    current_midprice
                )
            )

        return {
            "tick": self.tick,
            "strategy": self.strategy,
            "seed": self.seed,
            "order": order,
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