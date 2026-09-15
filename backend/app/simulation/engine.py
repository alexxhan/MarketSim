from app.market.order_book import OrderBook
from app.simulation.order_flow import OrderFlowGenerator
from app.strategies.basic_market_maker import BasicMarketMaker


class SimulationEngine:
    def __init__(self):
        self.order_book = OrderBook()

        self.order_flow = OrderFlowGenerator(
            starting_price=100.0
        )

        self.market_maker = BasicMarketMaker(
            spread=0.04,
            order_size=10
        )

        self.tick = 0
        self.trades = []

    def step(self):
        self.tick += 1

        # Cancel previous market-maker quotes
        if self.market_maker.active_bid_id is not None:
            self.order_book.cancel_order(
                self.market_maker.active_bid_id
            )

        if self.market_maker.active_ask_id is not None:
            self.order_book.cancel_order(
                self.market_maker.active_ask_id
            )

        # Observe existing market
        midprice = self.order_book.get_midprice()

        market_maker_quotes = None

        # Place new market-maker quotes
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

        # Generate new simulated trader order
        order = self.order_flow.generate_order()

        self.order_book.add_order(order)

        # Match orders
        new_trades = self.order_book.match_orders()

        self.trades.extend(new_trades)

        # Update market-maker portfolio
        for trade in new_trades:
            self.market_maker.process_trade(trade)

        # Calculate portfolio statistics
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