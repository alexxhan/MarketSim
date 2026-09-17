import unittest

from app.market.order import Order, OrderSide
from app.market.order_book import OrderBook


class OrderBookTests(unittest.TestCase):
    def test_best_prices_ordering_and_midprice(self):
        book = OrderBook()
        self.assertIsNone(book.get_midprice())
        book.add_order(Order(1, OrderSide.BUY, 99.90, 10))
        book.add_order(Order(2, OrderSide.BUY, 99.95, 5))
        self.assertIsNone(book.get_midprice())
        book.add_order(Order(3, OrderSide.SELL, 100.10, 8))
        book.add_order(Order(4, OrderSide.SELL, 100.05, 12))
        self.assertEqual([o.order_id for o in book.bids], [2, 1])
        self.assertEqual([o.order_id for o in book.asks], [4, 3])
        self.assertEqual(book.get_best_bid().price, 99.95)
        self.assertEqual(book.get_best_ask().price, 100.05)
        self.assertEqual(book.get_midprice(), 100)
        self.assertEqual(book.match_orders(), [])
