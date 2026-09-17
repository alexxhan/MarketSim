from app.market.order_book import OrderBook
from app.market.validation import finite_number, SimulationDomainError
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
        finite_number(inventory_risk_factor, "Inventory risk factor")
        if inventory_risk_factor < 0:
            raise SimulationDomainError("Inventory risk factor must be nonnegative")
        if type(order_arrival_rate) is not int or order_arrival_rate < 1:
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
        self.market_maker_fills = 0
        self.market_maker_buy_fills = 0
        self.market_maker_sell_fills = 0
        self.market_maker_executed_volume = 0
        self.total_absolute_inventory = 0
        self.maximum_absolute_inventory = 0

    def step(self):
        self.tick += 1

        if self.market_maker.active_bid_id is not None:
            self.order_book.cancel_order(
                self.market_maker.active_bid_id, self.market_maker.owner
            )

        if self.market_maker.active_ask_id is not None:
            self.order_book.cancel_order(
                self.market_maker.active_ask_id, self.market_maker.owner
            )

        midprice = self.order_book.get_midprice()
        market_maker_quotes = None
        new_trades = []

        if midprice is not None:
            bid, ask = self.market_maker.generate_quotes(midprice)

            new_trades.extend(self._execute_order(bid))
            new_trades.extend(self._execute_order(ask))

            market_maker_quotes = {
                "bid": bid,
                "ask": ask
            }

        generated_orders = []
        for _ in range(self.order_arrival_rate):
            order = self.order_flow.generate_order()
            generated_orders.append(order)
            new_trades.extend(self._execute_order(order))

        self.trades.extend(new_trades)

        current_midprice = self.order_book.get_midprice()

        mark_price = self.order_flow.reference_price
        portfolio_value = self.market_maker.portfolio.get_value(mark_price)
        pnl = self.market_maker.portfolio.get_pnl(mark_price)

        absolute_inventory = abs(self.market_maker.portfolio.inventory)
        self.total_absolute_inventory += absolute_inventory
        self.maximum_absolute_inventory = max(
            self.maximum_absolute_inventory,
            absolute_inventory
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
            "reference_price": self.order_flow.reference_price,
            "mark_price": mark_price,
            "cash": self.market_maker.portfolio.cash,
            "inventory": self.market_maker.portfolio.inventory,
            "portfolio_value": portfolio_value,
            "pnl": pnl,
            "metrics": {
                "total_market_trades": len(self.trades),
                "market_maker_fills": self.market_maker_fills,
                "market_maker_buy_fills": self.market_maker_buy_fills,
                "market_maker_sell_fills": self.market_maker_sell_fills,
                "market_maker_executed_volume": self.market_maker_executed_volume,
                "average_absolute_inventory": self.total_absolute_inventory / self.tick,
                "maximum_absolute_inventory": self.maximum_absolute_inventory,
                "pnl_per_fill": (
                    pnl / self.market_maker_fills
                    if self.market_maker_fills > 0
                    else None
                )
            }
        }

    def _execute_order(self, order):
        self.order_book.add_order(order)
        trades = self.order_book.match_orders()
        for trade in trades:
            self.market_maker.process_trade(trade)
            bought = trade.buyer_owner == self.market_maker.owner
            sold = trade.seller_owner == self.market_maker.owner
            if bought:
                self.market_maker_buy_fills += 1
            if sold:
                self.market_maker_sell_fills += 1
            if bought or sold:
                self.market_maker_fills += 1
                self.market_maker_executed_volume += trade.quantity
        return trades
