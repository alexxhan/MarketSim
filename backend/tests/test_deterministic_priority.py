import unittest
from itertools import count
from unittest.mock import patch

from app.market.order import Order, OrderSide
from app.market.order_book import OrderBook
from app.simulation.engine import SimulationEngine


class DeterministicPriorityTests(unittest.TestCase):
    def test_resting_order_execution_price_ignores_timestamps(self):
        for side, incoming_price in (
            (OrderSide.BUY, 99.98),
            (OrderSide.SELL, 100.02)
        ):
            for timestamps in ((1.0, 2.0), (1.0, 1.0), (2.0, 1.0)):
                with self.subTest(side=side, timestamps=timestamps):
                    book = OrderBook()
                    opposite = (
                        OrderSide.SELL if side == OrderSide.BUY
                        else OrderSide.BUY
                    )
                    book.add_order(Order(1, side, 100.0, 10, timestamps[0]))
                    book.add_order(Order(2, opposite, incoming_price, 10, timestamps[1]))

                    trades = book.match_orders()

                    self.assertEqual(len(trades), 1)
                    self.assertEqual(trades[0].price, 100.0)
                    self.assertEqual(trades[0].quantity, 10)
                    self.assertEqual(book.bids, [])
                    self.assertEqual(book.asks, [])

    def test_price_then_fifo_with_partial_fills(self):
        for side, better_price in ((OrderSide.BUY, 101), (OrderSide.SELL, 99)):
            with self.subTest(side=side):
                book = OrderBook()
                opposite = OrderSide.SELL if side == OrderSide.BUY else OrderSide.BUY
                book.add_order(Order(30, side, 100, 2, 30))
                book.add_order(Order(20, side, 100, 2, 20))
                book.add_order(Order(10, side, better_price, 1, 10))
                book.add_order(Order(40, opposite, 100, 2, 1))

                trades = book.match_orders()
                ids = [
                    trade.buy_order_id if side == OrderSide.BUY else trade.sell_order_id
                    for trade in trades
                ]
                self.assertEqual(ids, [10, 30])
                self.assertEqual([trade.price for trade in trades], [better_price, 100])
                book.add_order(Order(50, opposite, 100, 3, 1))
                trades = book.match_orders()
                ids = [
                    trade.buy_order_id if side == OrderSide.BUY else trade.sell_order_id
                    for trade in trades
                ]
                self.assertEqual(ids, [30, 20])
                self.assertEqual([trade.quantity for trade in trades], [1, 2])

    def test_cancelled_order_reenters_at_back_of_queue(self):
        book = OrderBook()
        first = Order(1, OrderSide.BUY, 100, 1, 1)
        second = Order(2, OrderSide.BUY, 100, 1, 1)
        book.add_order(first)
        book.add_order(second)
        self.assertTrue(book.cancel_order(first.order_id))
        book.add_order(first)
        book.add_order(Order(3, OrderSide.SELL, 100, 2, 1))
        self.assertEqual(
            [trade.buy_order_id for trade in book.match_orders()],
            [2, 1]
        )

    def test_arrival_priority_is_local_to_each_book(self):
        first_book = OrderBook()
        second_book = OrderBook()
        first = Order(1, OrderSide.BUY, 100, 2, 1)
        second = Order(2, OrderSide.BUY, 100, 2, 1)
        first_book.add_order(first)
        first_book.add_order(second)
        second_book.add_order(second)
        second_book.add_order(first)
        for book, expected in ((first_book, 1), (second_book, 2)):
            book.add_order(Order(3, OrderSide.SELL, 99, 1, 1))
            trade, = book.match_orders()
            self.assertEqual(trade.buy_order_id, expected)
            self.assertEqual(trade.price, 100)

    def test_repeated_seeded_runs_ignore_clock_behavior(self):
        for strategy in ("basic", "inventory"):
            expected = self.run_simulation(strategy)
            for repeat in range(4):
                with self.subTest(strategy=strategy, repeat=repeat):
                    self.assertEqual(self.run_simulation(strategy), expected)
            for step in (0, 1, -1):
                with self.subTest(strategy=strategy, clock_step=step):
                    clock = count(1000000, step)
                    with patch("app.market.order.time", side_effect=lambda: next(clock)):
                        self.assertEqual(self.run_simulation(strategy), expected)

    @staticmethod
    def run_simulation(strategy):
        engine = SimulationEngine(
            strategy=strategy,
            starting_price=100,
            volatility=3,
            buy_pressure=0.5,
            order_arrival_rate=3,
            spread=0.04,
            order_size=10,
            inventory_risk_factor=0.001,
            seed=42
        )
        history = []
        for _ in range(1000):
            state = engine.step()
            history.append((
                state["pnl"],
                state["inventory"],
                state["cash"],
                len(engine.trades),
                state["midprice"],
                state["portfolio_value"]
            ))
        trades = [
            (trade.buy_order_id, trade.sell_order_id, trade.price, trade.quantity)
            for trade in engine.trades
        ]
        return history, trades


if __name__ == "__main__":
    unittest.main()
